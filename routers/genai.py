from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
import json
from sqlalchemy.orm import Session
from app.routers import overlay
from app.schemas.genai import GenerationRequest
from app.services.genai import generate_and_store_image
from app.db.database import get_db
from app.models.models import Prompt
from app.core.security import get_current_user
from app.routers.overlay import test_overlay_api

router = APIRouter()

@router.post("/generate-image/")
async def ai_generate_image(
    request: GenerationRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    params = request.dict()
    output_format = params.get("output_format", "jpeg")
    params["samples"] = int(params.get("samples", 1))

    # ✅ Generate and save image, get magic prompt too
    result = generate_and_store_image(current_user["id"], params["prompt"])

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    image_path = result["image_path"]
    magic_prompt = result.get("magic_prompt", params["prompt"])

    # 🔍 Check if same prompt already exists for the user
    existing_prompt = db.query(Prompt).filter_by(
        user_id=current_user["id"],
        prompt=params["prompt"]
    ).first()

    if existing_prompt:
        # ✅ Initialize image_urls if missing
        if existing_prompt.image_urls is None:
            existing_prompt.image_urls = []

        # ✅ Avoid duplicate image URLs
        if image_path not in existing_prompt.image_urls:
            existing_prompt.image_urls.append(image_path)

        # ✅ Update magic_prompt only if it is not already set
        if not existing_prompt.magic_prompt:
            existing_prompt.magic_prompt = magic_prompt

        prompt_id = existing_prompt.id
    else:
        # ✅ Create new prompt record
        new_prompt = Prompt(
            user_id=current_user["id"],
            prompt=params["prompt"],
            magic_prompt=magic_prompt,
            image_urls=[image_path]
        )
        db.add(new_prompt)
        db.commit()
        db.refresh(new_prompt)
        prompt_id = new_prompt.id

    db.commit()  # ✅ Commit after either update or insert
    result=await test_overlay_api(params["product_id"], image_path,db)
    encoded_value = json.loads(result.body.decode())
    return {
        "message": "Image(s) generated successfully",
        "image_urls": [image_path],
        "Overlay": encoded_value,
        "prompt_id": prompt_id,
        "magic_prompt": magic_prompt  # Optional to return in response
    }
