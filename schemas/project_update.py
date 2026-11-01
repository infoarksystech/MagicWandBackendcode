from typing import List, Optional
from pydantic import BaseModel


class ImagePreview(BaseModel):
    image_url: str
    story: Optional[List[str]] = None
    story_title: Optional[List[str]] = None

class ProductPreviewListResponse(BaseModel):
    product_id: int
    previews: List[ImagePreview]