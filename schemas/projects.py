from datetime import datetime
from pydantic import BaseModel
from typing import Any, Dict, List, Optional,Union
#from app.schemas.prompt import PromptBase


class UserParameters(BaseModel):
    type: Optional[str] = None
    imageType: Optional[str] = None
    imageStyle: Optional[str] = None
    subject: Optional[str] = None
    background: Optional[str] = None
    colorPreference: Optional[str] = None  # Allow null or blank
    otherKeywords: Optional[str] = None
    text: Optional[str] = None
    textStyle: Optional[str] = None
    textColor: Optional[str] = None
    imageFormat: Optional[str] = None

class ProjectCreate(BaseModel):
    product_id: int
    user_parameters: Dict[str, Optional[str]]
    regenerated: Optional[bool] = False
    remix: bool = False


class PreviewImageResponse(BaseModel):
    overlay_image_url: List[str]
    warnings: Optional[List[str]] = None
    
class ProjectResponse(BaseModel):
    message: List[str]
    project_id: int
    prompt_id: int
    product_id: Optional[int] = None
    product_title: Optional[str] = None  # ✅ Add this
    # generated_prompt: List[str]
    story_titles: Optional[List[str]] = None  # ✅ Add this
    story: Optional[List[str]] = None
    preview_img: PreviewImageResponse
    image_results: Optional[List[dict]] = None

class ProjectResponsebyUser(BaseModel):
    project_id: int
    prompt_id: int
    product_id: int 
    product_title: Optional[str] = None  # ✅ Add this
    price :  Optional[int] = None    
    preview_img: Optional[List[str]] = None
    user_parameters: Dict[str, Any]
    ref_image: Optional[str] = None
    display_on_ui:Optional[bool] = False
    created_at: Optional[datetime]   # ✅ Add this line

    class Config:
        from_attributes = True  # <== VERY IMPORTANT
   
class ProjectDisplayOnUi(BaseModel):
    project_id: int
    display_on_ui: Optional[bool] = None
    class Config:
        from_attributes = True  # ✅ important


class ProjectResponsebyAdmin(BaseModel):
    id: int
    prompt_id: int
    user_id: int
    product_id: int
    product_title: Optional[str] = None  # ✅ Add this
    preview_img: Optional[List[str]] = None
    display_on_ui: Optional[bool] = None
    created_at: datetime

    class Config:
        from_attributes = True  # Needed for ORM to Pydantic conversion
