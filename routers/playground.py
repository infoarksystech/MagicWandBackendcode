from fastapi import APIRouter, Form, Depends
from fastapi.responses import JSONResponse, StreamingResponse
from app.schemas.playground import ImageGenerationRequest
from app.services.playground import PlaygroundService
from sqlalchemy.orm import Session
from app.db.database import get_db
import io

router = APIRouter(prefix="/images", tags=["Image Generator"])

@router.post("/generate")
async def generate_image(
    provider: str = Form(...),
    prompt: str = Form(...),
    aspect_ratio: str = Form(""),
    seed: int = Form(0),
    style_preset: str = Form("None"),
    output_format: str = Form("jpeg"),
    db: Session = Depends(get_db)
):
    request_data = ImageGenerationRequest(
        provider=provider,
        prompt=prompt,
        aspect_ratio=aspect_ratio,
        seed=seed,
        style_preset=style_preset,
        output_format=output_format
    )

    result = await PlaygroundService.generate_image(request_data, db)

    if isinstance(result[0], bytes):  # stability (binary image)
        return StreamingResponse(io.BytesIO(result[0]), media_type=f"image/{output_format}")
    else:
        return JSONResponse(content={
            "image_url": result[0],
            "prompt": result[1],
            "error": result[2]
        })
