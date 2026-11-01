from http import client
import json
import logging
import os
import re
import shutil
from typing import List
import uuid
from fastapi import HTTPException, Path, UploadFile
from sqlalchemy import text,or_,String
from sqlalchemy.orm import Session,joinedload
from dotenv import load_dotenv
import openai
from datetime import datetime, time, date
from app import db
from app.models.models import ImageStyle, Product, Project, Prompt
from app.schemas.projects import ProjectCreate, ProjectResponse, ProjectResponsebyUser,ProjectResponsebyAdmin
from app.services.genai import generate_images_from_prompt_record, remix_images_from_reference
from app.routers.overlay import process_overlay
from app.services.safety_guard import SafetyGuard
from typing import Optional
from app.utils.faiss_database import FAISSDatabase
from app.utils.setup_env import setup_environment
# from app.utils.time_log import log_time

# Load env and OpenAI key
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

# Ensure the log folder exists
log_folder = "app"
os.makedirs(log_folder, exist_ok=True)
log_file_path = os.path.join(log_folder, 'faiss_search.log')

# Clear existing log handlers (for Jupyter or repeat runs)
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

# Set up logging to both file and console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file_path, mode='a'),
        logging.StreamHandler()
    ]
)

class ProjectService:

    @staticmethod
    def all_projects(
        db: Session,
        search: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[dict]:

        query = db.query(Project).options(joinedload(Project.product))

        # Apply keyword search
        if search:
            keyword = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    Project.prompt_id.cast(String).ilike(keyword),
                    Project.preview_image_urls.ilike(keyword),
                    Project.product.has(Product.title.ilike(keyword))
                )
            )

        # Convert date to datetime (whole day range)
        if start_date:
            start_datetime = datetime.combine(start_date, time.min)
        else:
            start_datetime = None

        if end_date:
            end_datetime = datetime.combine(end_date, time.max)
        else:
            end_datetime = None

        # Apply date filters
        if start_datetime and end_datetime:
            query = query.filter(Project.created_at.between(start_datetime, end_datetime))
        elif start_datetime:
            query = query.filter(Project.created_at >= start_datetime)
        elif end_datetime:
            query = query.filter(Project.created_at <= end_datetime)

        projects = query.all()

        # Prepare response
        project_list = []
        for project in projects:
            project_dict = {
                "id": project.id,
                "prompt_id": project.prompt_id,
                "user_id": project.user_id,
                "product_id": project.product_id,
                "product_title": project.product.title if project.product else None,
                "preview_image_urls": project.preview_image_urls,
                "display_on_ui": project.display_on_ui,
                "created_at": project.created_at,
            }
            project_list.append(project_dict)

        return project_list

    @staticmethod
    def create_project(
        db: Session,
        project_data: ProjectCreate,
        user_id: int,
        ref_image_file: UploadFile = None
    ) -> ProjectResponse:
        user_params_dict = project_data.user_parameters

        print("user_params_dict:", user_params_dict if user_params_dict else {})
        # === Inject ref_keyword into otherKeywords based on imageStyle ===
        ref_keyword = ""
        image_style_name = user_params_dict.get("imageStyle")
        if image_style_name:
            image_style = db.query(ImageStyle).filter_by(style_name=image_style_name).first()
            if image_style and image_style.ref_keywords:
                ref_keyword = image_style.ref_keywords.strip()

        if ref_keyword:
            other_keywords = user_params_dict.get("otherKeywords", "")
            combined_keywords = f"{ref_keyword}, {other_keywords}".strip(", ")
            user_params_dict["otherKeywords"] = combined_keywords
            print(f"OtherKeywords---------->: {combined_keywords}")
        # === Safety Check ===
        safety_guard = SafetyGuard()
        combined_input = " ".join(str(v) for v in user_params_dict.values())
        if not safety_guard.is_safe(combined_input):
            return ProjectResponse(
                message=["Your input contains inappropriate or unsafe content. Please revise and try again."],
                project_id=None, prompt_id=None, preview_img=None, image_results=[]
            )

        # === Get metadata ===
        aspect_ratio = ProjectService.get_metadata_value(db, project_data.product_id, "aspect_ratio")
        no_of_images_raw = ProjectService.get_metadata_value(db, project_data.product_id, "no_of_images")

        try:
            no_of_images = int(no_of_images_raw)
            if no_of_images <= 0:
                no_of_images = 1
        except (TypeError, ValueError):
            no_of_images = 1

        # === Handle reference image ===
        reference_image_path = None
        if project_data.remix and ref_image_file:
            upload_dir = "assets/ref_image/"
            os.makedirs(upload_dir, exist_ok=True)
            file_ext = os.path.splitext(ref_image_file.filename)[1]
            file_name = f"{uuid.uuid4()}{file_ext}"
            saved_path = os.path.join(upload_dir, file_name).replace("\\", "/")
            reference_image_path = saved_path

            with open(reference_image_path, "wb") as buffer:
                shutil.copyfileobj(ref_image_file.file, buffer)

        # === Generate Prompt, Story, Titles ===
        if project_data.remix and reference_image_path:
            subject_only = {"subject": user_params_dict.get("subject", "")}
            story_result = ProjectService.generate_story_and_title_using_chatgpt(subject_only)

            story = story_result.get("story", [])
            story_titles = story_result.get("story_titles", [])

            if isinstance(story, str):
                story = [story]
            if isinstance(story_titles, str):
                story_titles = [story_titles]

            prompt_text = user_params_dict.get("subject", "")
        else:
            prompt_result = ProjectService.generate_prompt_using_faiss(user_params_dict)
            prompt_text = prompt_result.get("prompt_text", [])
            story = prompt_result.get("story", [])
            story_titles = prompt_result.get("story_titles", [])

        # === Create new Prompt ===
        new_prompt = Prompt(
            user_id=user_id,
            prompt=prompt_text,
            user_parameters=user_params_dict,
            story_title=story_titles,
            story=story,
            image_urls=[],
        )
        db.add(new_prompt)
        db.commit()
        db.refresh(new_prompt)

        # === Generate Images ===
        if project_data.remix and reference_image_path:
            image_results = remix_images_from_reference(
                db=db,
                user_id=user_id,
                prompt_record=new_prompt,
                user_params_dict=user_params_dict,
                ref_image_url=reference_image_path,
                aspect_ratio=aspect_ratio,
                no_of_images=no_of_images
            )
        else:
            image_results = generate_images_from_prompt_record(
                db=db,
                user_id=user_id,
                prompt_record=new_prompt,
                user_params_dict=user_params_dict,
                aspect_ratio=aspect_ratio,
                no_of_images=no_of_images
            )

        # === Update prompt with image URLs ===
        image_urls = [img.get("image_path") or img.get("image_url") for img in image_results if img.get("image_path") or img.get("image_url")]
        new_prompt.image_urls = image_urls
        db.commit()
        db.refresh(new_prompt)

        # === Process overlays ===
        preview = process_overlay(project_data.product_id, image_urls, db)
        overlay_urls = preview.get("overlay_image_urls", []) or []

        preview_img_dict = {
            "overlay_image_url": overlay_urls,
            "warnings": None if overlay_urls else ["No overlay image available"]
        }

        # === Check for existing project ===
        existing_project = db.query(Project).filter_by(
            user_id=user_id,
            product_id=project_data.product_id
        ).first()

        if existing_project and existing_project.user_parameters == user_params_dict:
            if project_data.regenerated:
                existing_project.user_parameters = user_params_dict
                existing_project.prompt_id = new_prompt.id
                existing_project.preview_image_urls = overlay_urls
                if reference_image_path:
                    existing_project.reference_image = reference_image_path
                    existing_project.remix = project_data.remix
                db.commit()
                db.refresh(existing_project)
                return ProjectResponse(
                    message=["Project regenerated successfully"],
                    project_id=existing_project.id,
                    prompt_id=new_prompt.id,
                    preview_img=preview_img_dict,
                    image_results=image_results,
                    story_titles=story_titles,
                    story=story
                )
            else:
                return ProjectResponse(
                    message=["Project already exists, no changes made."],
                    project_id=existing_project.id,
                    prompt_id=existing_project.prompt_id,
                    preview_img=preview_img_dict,
                    image_results=image_results,
                    story_titles=story_titles,
                    story=story
                )

        # === Create new project ===
        new_project = Project(
            user_id=user_id,
            product_id=project_data.product_id,
            user_parameters=user_params_dict,
            prompt_id=new_prompt.id,
            preview_image_urls=overlay_urls,
            reference_image=reference_image_path,
            remix=project_data.remix
        )
        db.add(new_project)
        db.commit()
        db.refresh(new_project)

        return ProjectResponse(
            message=["Project created successfully"],
            product_id=project_data.product_id,
            project_id=new_project.id,
            prompt_id=new_prompt.id,
            preview_img=preview_img_dict,
            image_results=image_results,
            story_titles=story_titles,
            story=story
        )

    @staticmethod
    def generate_story_and_title_using_chatgpt(subject_only: dict):
        client = openai.OpenAI()
        subject = subject_only.get("subject", "")
        if not subject:
            return {"story": "", "story_titles": ""}

        try:
            logging.info("Generating short story for the image...")
            story_response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a creative writer."},
                    {"role": "user", "content": f"Write a short note strictly within 50 words about the image based on this prompt: {subject}"}
                ]
            )
            story_raw = story_response.choices[0].message.content.strip()
            story = ProjectService.clean_response(ProjectService.clean_story_text(story_raw))
            logging.info("Story generated successfully.")

            logging.info("Generating title for the story...")
            title_response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a creative writer."},
                    {"role": "user", "content": f"Give a title (max 10 words) for this image:\n\n{story}"}
                ]
            )
            title_raw = title_response.choices[0].message.content.strip()
            title = ProjectService.clean_response(title_raw)
            logging.info("Title generated successfully.")

            return {
                "story": story,
                "story_titles": title
            }

        except Exception as e:
            logging.error(f"Error generating story or title: {str(e)}")
            return {"story": "", "story_titles": ""}


    @staticmethod
    def get_metadata_value(db: Session, product_id: int, key: str) -> str:
        result = db.execute(
            text("SELECT meta_value FROM product_metadata WHERE product_id = :pid AND meta_key = :key"),
            {"pid": product_id, "key": key}
        ).fetchone()
        return result[0] if result else ""

    @staticmethod
    def clean_story_text(text):
        text = re.sub(r"^\d+\.\s*", "", text)
        text = text.replace("\n", " ")
        return re.sub(r"\s{2,}", " ", text).strip()

    @staticmethod
    def clean_response(text):
        restricted_phrases = [
            "I'm sorry, I can't provide images",
            "As an AI language model",
            "I cannot draw pictures"
        ]
        return "\n".join(line for line in text.split("\n") if not any(phrase in line for phrase in restricted_phrases))

    @staticmethod
    def generate_prompt_using_faiss(user_parameters: dict) -> dict:
        logging.info("Starting prompt generation with FAISS...")

        nlp = setup_environment()
        db_faiss = FAISSDatabase(nlp)
        safety_guard = SafetyGuard()
        client = openai.OpenAI()

        subject_value = user_parameters.get("subject", "")
        if not subject_value:
            logging.error("Subject is missing in user parameters.")
            raise ValueError("Subject is required for prompt generation.")

        logging.info(f"Searching similar prompts for subject: {subject_value}")
        similar_prompts = db_faiss.search_similar(subject_value, k=1)
        logging.info(f"similar prompts: {similar_prompts}")
        similarity_score = similar_prompts[0].get("similarity_score", 0)
        logging.info(f"Top similarity score: {similarity_score}")

        if similarity_score < 0.70:
            logging.info("Similarity score too low; using ChatGPT fallback.")
            return ProjectService.generate_prompt_using_chatgpt(user_parameters)

        context = "\n".join([f"- {item['text']}" for item in similar_prompts])
        remaining_params = {k: v for k, v in user_parameters.items() if k != "subject" and v}
        additional_context = "\n".join(f"{k}: {v}" for k, v in remaining_params.items())

        full_prompt = f"{context}\n\nAdditional Details:\n{additional_context}\n\nNow generate one creative prompt for an AI image."
        logging.info(f"Full Prompt:{full_prompt}")
        logging.info("Sending prompt to GPT for enhancement.")

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert prompt strictly 250 words generator for AI image generation."},
                {"role": "user", "content": full_prompt}
            ]
        )

        enhanced = ProjectService.clean_story_text(response.choices[0].message.content.strip())
        logging.info("Prompt enhanced successfully.")

        if not safety_guard.is_safe(enhanced):
            logging.warning("Unsafe content detected in enhanced prompt.")
            raise ValueError("Unsafe content detected in enhanced prompt.")

        logging.info("Generating short story for the image...")
        story_response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a creative writer."},
                {"role": "user", "content": f"Write a short note strictly within 50 words about the image based on this prompt: {enhanced}"}
            ]
        )
        story = ProjectService.clean_response(ProjectService.clean_story_text(story_response.choices[0].message.content.strip()))
        logging.info("Story generated successfully.")

        logging.info("Generating title for the story...")
        title_response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a creative writer."},
                {"role": "user", "content": f"Give a title (max 10 words) for this image:\n\n{story}"}
            ]
        )
        title = ProjectService.clean_response(title_response.choices[0].message.content.strip())
        logging.info(f"Title generated: {title}")

        logging.info("Saving prompt to FAISS database.")
        db_faiss.add_prompt(enhanced, {
            "source": "generated",
            "base_prompt": similar_prompts,
            "story_title": title,
            "story": story
        })

        logging.info("Prompt generation completed successfully.")
        return {
            "prompt_text": [enhanced],
            "story_titles": [title],
            "story": [story]
        }

    @staticmethod
    def generate_prompt_using_chatgpt(user_parameters: dict) -> dict:
        query_text = " ".join(f"{k}: {v}" for k, v in user_parameters.items())
        safety_guard = SafetyGuard()
        client = openai.OpenAI()

        prompt_response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert prompt generator for AI image generation."},
                {"role": "user", "content": f"Based on the following details, generate a highly creative and vivid image prompt strictly within 250 words :\n\n{query_text}"}
            ]
        )
        enhanced_prompt = ProjectService.clean_story_text(prompt_response.choices[0].message.content.strip())
        if not safety_guard.is_safe(enhanced_prompt):
            raise ValueError("Generated prompt flagged as unsafe. Please revise your input.")

        story_response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a creative writer."},
                {"role": "user", "content": f"Write a short note strictly within 50 words about the image based on this prompt:\n{enhanced_prompt}"}
            ]
        )
        story = ProjectService.clean_response(ProjectService.clean_story_text(story_response.choices[0].message.content.strip()))

        title_response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a creative writer."},
                {"role": "user", "content": f"Give a title (max 10 words) for this image:\n\n{story}"}
            ]
        )
        title = ProjectService.clean_response(title_response.choices[0].message.content.strip())

        return {
            "prompt_text": [enhanced_prompt],
            "story_titles": [title],
            "story": [story]
        }

    @staticmethod
    def get_projects_by_user_id(db: Session, user_id: int):
        projects = db.query(Project).filter(Project.user_id == user_id,Project.is_deleted == False).all()
        project_list = []

        for project in projects:
            # Fetch product title
            product = db.query(Product).filter(Product.id == project.product_id).first()
            product_title = product.title if product else None

            # Parse preview images
            preview_urls = []
            if isinstance(project.preview_image_urls, list):
                preview_urls = project.preview_image_urls
            elif isinstance(project.preview_image_urls, str):
                try:
                    preview_urls = json.loads(project.preview_image_urls)
                    if not isinstance(preview_urls, list):
                        preview_urls = [preview_urls]
                except Exception:
                    preview_urls = [project.preview_image_urls]

            project_list.append(ProjectResponsebyUser(
                project_id=project.id,
                prompt_id=project.prompt_id,
                product_id=project.product_id,
                product_title=product_title,  # ✅ Include product title here
                price=product.price if product else None,
                user_parameters=project.user_parameters,
                ref_image=project.reference_image,
                preview_img=preview_urls,
                display_on_ui=project.display_on_ui if project.display_on_ui is not None else False,
                created_at=project.created_at
            ))

        return project_list

    

    @staticmethod
    def get_project_by_id(db: Session, project_id: int, user_id: int):
        project = db.query(Project).options(joinedload(Project.product)).filter(
            Project.id == project_id,
            Project.user_id == user_id,
            Project.is_deleted == False
        ).first()

        if not project:
            raise HTTPException(status_code=404, detail="Project not found or deleted")
        

        # Parse preview_image_urls
        preview_urls = []
        if isinstance(project.preview_image_urls, list):
            preview_urls = project.preview_image_urls
        elif isinstance(project.preview_image_urls, str):
            try:
                preview_urls = json.loads(project.preview_image_urls)
            except Exception:
                preview_urls = [project.preview_image_urls]

        return ProjectResponsebyUser(
            project_id=project.id,
            prompt_id=project.prompt_id,
            product_id=project.product_id,
            product_title=project.product.title if project.product else None,
            price=project.product.price if project.product else None,
            user_parameters=project.user_parameters,
            ref_image=project.reference_image,
            preview_img=preview_urls,
            display_on_ui=project.display_on_ui,
            created_at=project.created_at
        )




    
   
