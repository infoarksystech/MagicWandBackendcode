from pydantic import BaseModel

class GenerationRequest(BaseModel):
    prompt: str
    product_id: int
    negative_prompt: str = ""
    aspect_ratio: str = ""
    seed: int = 0
    output_format: str
    samples: int = 1  # ✅ Ensure it's an integer
    steps: int = 30
    cfg_scale: int = 7
    width: int = 512
    height: int = 512
