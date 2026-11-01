import json
import os
import re
from sqlalchemy import text
from sqlalchemy.orm import Session
from dotenv import load_dotenv
import openai

from app.models.models import Project, Prompt
from app.schemas.projects import ProjectCreate, ProjectResponse
from app.services.genai import generate_images_from_prompt_record
from app.routers.overlay import process_overlay
from app.services.safety_guard import SafetyGuard
from app.utils.prompt_generator import generate_multi_panel_prompts

from app.utils.faiss_database import FAISSDatabase
from app.utils.setup_env import setup_environment
# from app.utils.time_log import log_time

# Load env and OpenAI key
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

class ProjectService:
    @staticmethod
    # @log_time
    def get_metadata_value(db: Session, product_id: int, key: str) -> str:
        result = db.execute(
            text("SELECT meta_value FROM product_metadata WHERE product_id = :pid AND meta_key = :key"),
            {"pid": product_id, "key": key}
        ).fetchone()
        return result[0] if result else ""
    
    @staticmethod
    # @log_time
    def clean_story_text(text):
        # Remove "1.", "2.", etc. at the beginning of lines
        text = re.sub(r"^\d+\.\s*", "", text)
        # Replace newlines with spaces
        text = text.replace("\n", " ")
        # Normalize extra spaces
        return re.sub(r"\s{2,}", " ", text).strip()

    @staticmethod
    # @log_time
    def generate_prompt_using_faiss(user_parameters: dict, meta_value: int = 1) -> dict:
        nlp = setup_environment()
        db = FAISSDatabase(nlp)
        safety_guard = SafetyGuard()
        client = openai.OpenAI()

        query_text = " ".join(f"{k}: {v}" for k, v in user_parameters.items())
        similar_prompts = db.search_similar(query_text, k=1)
        context = "\n".join([f"- {item['text']}" for item in similar_prompts])

        scene_elements = ["" for _ in range(meta_value)]
        panel_prompts = generate_multi_panel_prompts(similar_prompts, scene_elements, style="consistent")

        enhanced_prompts = []
        stories = []
        story_titles = []

        for panel in panel_prompts:
            full_prompt = f"{context}"

            # Generate enhanced prompt
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert prompt (within 250 words) generator for AI image generation."},
                    {"role": "user", "content": full_prompt}
                ]
            )
            enhanced = response.choices[0].message.content.strip()
            enhanced = ProjectService.clean_story_text(enhanced)

            if not safety_guard.is_safe(enhanced):
                raise ValueError("Unsafe content detected in enhanced prompt.")

            enhanced_prompts.append(enhanced)

            # Generate story
            story_response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a creative storyteller."},
                    {"role": "user", "content": f"Write a short story (within 100 words) based on this prompt: {enhanced}"}
                ]
            )
            story = story_response.choices[0].message.content.strip()
            cleaned_story = ProjectService.clean_story_text(story)
            stories.append(cleaned_story)

            # Generate story title (max 10 words)
            title_response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a creative writer."},
                    {"role": "user", "content": f"Give a title (max 10 words) for this story:\n\n{cleaned_story}"}
                ]
            )
            title = title_response.choices[0].message.content.strip()
            story_titles.append(title)

            db.add_prompt(enhanced, {
                "source": "generated",
                "base_prompt": similar_prompts,
                "story_title": title,
                "story": cleaned_story
            })

        return {
            "prompt_text": enhanced_prompts,
            "story_titles": story_titles,
            "story": stories
        }

    @staticmethod
    # @log_time
    def create_project(db: Session, project_data: ProjectCreate, user_id: int) -> ProjectResponse:
        user_params_dict = project_data.user_parameters.dict()

        # ✅ Safety check
        safety_guard = SafetyGuard()
        combined_input = " ".join(str(v) for v in user_params_dict.values())
        if not safety_guard.is_safe(combined_input):
            return ProjectResponse(
                message=["Your input contains inappropriate or unsafe content. Please revise and try again."],
                project_id=None,
                prompt_id=None,
                preview_img=None,
                image_results=[]
            )

        # ✅ Fetch existing project (if any)
        existing_project = db.query(Project).filter_by(
            user_id=user_id,
            product_id=project_data.product_id
        ).first()

        # ✅ Fetch metadata
        meta_value_raw = ProjectService.get_metadata_value(db, project_data.product_id, "number_of_panels") or "1"
        aspect_ratio = ProjectService.get_metadata_value(db, project_data.product_id, "aspect_ratio")

        try:
            meta_value = int(meta_value_raw)
        except:
            meta_value = 1

        # ✅ Generate prompts using FAISS
        prompt_result = ProjectService.generate_prompt_using_faiss(user_params_dict, meta_value=meta_value)

        prompt_text = prompt_result.get("prompt_text", [])
        story = prompt_result.get("story", [])
        story_titles = prompt_result.get("story_titles", [])

        # ✅ Create prompt record
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

        # ✅ Generate images
        image_results = generate_images_from_prompt_record(
            db=db,
            user_id=user_id,
            prompt_record=new_prompt,
            aspect_ratio=aspect_ratio
        )

        image_urls = [img.get("image_url") for img in image_results if img.get("image_url")]
        preview = process_overlay(project_data.product_id, image_urls, db)
        overlay_url = preview.get("overlay_image_url")

        # ✅ Logic for existing project with same user & product
        if existing_project:
            existing_params = existing_project.user_parameters

            if existing_params == user_params_dict:
                if project_data.regenerated:
                    # ✅ Regenerate using new prompt
                    existing_project.user_parameters = user_params_dict
                    existing_project.prompt_id = new_prompt.id
                    existing_project.preview_image_urls = overlay_url
                    db.commit()
                    db.refresh(existing_project)
                    return ProjectResponse(
                        message=["Project regenerated successfully"],
                        project_id=existing_project.id,
                        prompt_id=new_prompt.id,
                        preview_img=preview,
                        image_results=image_results,
                        story_titles=story_titles,
                        story=story
                    )
                else:
                    return ProjectResponse(
                        message=["Project already exists, no changes made."],
                        project_id=existing_project.id,
                        prompt_id=existing_project.prompt_id,
                        preview_img=preview,
                        image_results=image_results,
                        story_titles=story_titles,
                        story=story
                    )
            # ⚠️ Parameters are different — continue to create new project

        # ✅ Create new project
        new_project = Project(
            user_id=user_id,
            product_id=project_data.product_id,
            user_parameters=user_params_dict,
            prompt_id=new_prompt.id,
            preview_image_urls=overlay_url
        )
        db.add(new_project)
        db.commit()
        db.refresh(new_project)

        return ProjectResponse(
            message=["Project created successfully"],
            product_id=project_data.product_id,
            project_id=new_project.id,
            prompt_id=new_prompt.id,
            preview_img=preview,
            image_results=image_results,
            story_titles=story_titles,
            story=story
            
        )
