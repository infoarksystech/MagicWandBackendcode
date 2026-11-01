import json
import logging
from typing import List
from sqlalchemy.orm import Session
from app.models.models import Project, Prompt
from app.routers.overlay import process_overlay
#from app.schemas.projects import ProjectResponse
from app.schemas.project_update import ImagePreview, ProductPreviewListResponse
from app.schemas.projects import  ProjectResponse,PreviewImageResponse

#from app.utils.time_log import log_time # type: ignore

class ProjectServiceUpdate:
    @staticmethod
    def get_related_previews(db: Session, product_id: int, current_user_id: int) -> ProductPreviewListResponse:
        try:
            projects = db.query(Project).filter(
                Project.product_id == product_id,
                Project.user_id != current_user_id,
                Project.display_on_ui == True,
                Project.preview_image_urls.isnot(None)
            ).all()

            previews: List[ImagePreview] = []

            for project in projects:
                prompt = db.query(Prompt).filter(Prompt.id == project.prompt_id).first()
                raw_urls = project.preview_image_urls
                logging.info(f"Raw preview_image_urls: {repr(raw_urls)}")

                urls = []
                if raw_urls:
                    if isinstance(raw_urls, list):
                        urls = raw_urls
                    elif isinstance(raw_urls, str):
                        try:
                            urls = json.loads(raw_urls)
                            if not isinstance(urls, list):
                                urls = [urls]
                        except json.JSONDecodeError:
                            urls = [raw_urls]
                    else:
                        urls = [str(raw_urls)]
                else:
                    urls = []

                logging.info(f"Parsed URLs: {urls}")

                for url in urls:
                    previews.append(
                        ImagePreview(
                            image_url=url,
                            story=ProjectServiceUpdate.ensure_list(prompt.story if prompt else None),
                            story_title=ProjectServiceUpdate.ensure_list(prompt.story_title if prompt else None)
                        )
                    )

            return ProductPreviewListResponse(
                product_id=product_id,
                previews=previews
            )

        except Exception as e:
            logging.error(f"Error in get_related_previews: {e}", exc_info=True)
            raise  # re-raise so you see the error in server response or handle as needed

    @staticmethod
    def ensure_list(value):
        if value is None:
            return None
        if isinstance(value, list):
            return [v for v in value if v and v != "null"]
        if isinstance(value, str):
            stripped = value.strip()
            if not stripped or stripped == "null":
                return None
            return [stripped]
        if isinstance(value, dict):
            return [v for v in value.values() if v and v != "null"]
        return [str(value)]

    @staticmethod
    def update_product_with_existing_prompt(
        db: Session,
        user_id: int,
        new_product_id: int,
        original_project_id: int
    ) -> ProjectResponse:
        # Fetch original project
        print("1")
        original_project = db.query(Project).filter_by(id=original_project_id, user_id=user_id).first()
        if not original_project:
            raise ValueError("Original project not found.")
        print("2")

        # Process new overlay image using existing image URLs
        image_urls = []
        print("3")
        if original_project.prompt_id:
            print("4")
            image_urls = db.query(Prompt.image_urls).filter_by(id=original_project.prompt_id).scalar()
            print("6")
        if not image_urls:
            raise ValueError("No image URLs found for the original project.")

        # Generate new overlay image for the new product
        new_preview_raw = process_overlay(new_product_id, image_urls, db)
        overlay_urls = new_preview_raw.get("overlay_image_urls", [])
        warnings = new_preview_raw.get("warnings", [])

        # ✅ Properly wrap response using Pydantic model
        preview_img = PreviewImageResponse(
            overlay_image_url=overlay_urls,
            warnings=warnings
        )

        # Update the project
        original_project.product_id = new_product_id
        original_project.preview_image_urls = overlay_urls  # Save as list of URLs

        db.commit()
        db.refresh(original_project)

        return ProjectResponse(
            message=["Project updated with new product successfully."],
            project_id=original_project.id,
            prompt_id=original_project.prompt_id,
            product_id=new_product_id,
            preview_img=preview_img,
            image_results=[{"image_url": url} for url in image_urls],
        )


   
