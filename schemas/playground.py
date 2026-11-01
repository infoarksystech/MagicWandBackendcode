from pydantic import BaseModel, Field
from typing import Optional


class ImageGenerationRequest(BaseModel):
    provider: str = Field(..., description="Enter provider, e.g., ideogram-generate or stability-ai-ultra or gpt-image or imagen")
    prompt: str = Field(..., description="Enter prompt for image generation")
    aspect_ratio: Optional[str] = "null"
    seed: Optional[int] = 0
    style_preset: Optional[str] = "None"
    output_format: str = Field("jpeg", description="Enter output format, e.g., jpeg, png, jpg")
