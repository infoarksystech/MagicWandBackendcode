from pydantic import BaseModel, Field, validator
from typing import Any, Dict, Union, Optional, List
import json
from enum import Enum


class FieldTypeEnum(str, Enum):
    text = "text"
    text_area = "text_area"
    number = "number"
    select = "select"
    checkbox = "checkbox"

class LabelEnum(str, Enum):
    subject = "Subject"
    subject_suggestions="Subject Suggestions"
    OtherKeywords = "Other Keywords"
    background="Background"
    colorPreference="Color Preference"

class UIParameter(BaseModel):
    label: LabelEnum = Field(..., description="Field label")
    subject_suggestions: str = Field(..., description="Subject suggestions")
    is_mandatory: bool = Field(..., description="Is field required?")
    placeholder: str = Field(..., description="Placeholder text")
    field_type: FieldTypeEnum = Field(..., description="Type of input field")
    
class UIParameter(BaseModel):
    label: Optional[str] = None
    subject_suggestions: Optional[str] = None
    is_mandatory: Optional[bool] = None
    placeholder: Optional[str] = None
    field_type: Optional[str] = None

class LabelDeleteRequest(BaseModel):
    label: LabelEnum

class ImageStyleBase(BaseModel):
    slno:Optional[str]
    style_category: Optional[str]
    style_name: str
    url: str
    endpoint: Union[str, dict]
    ref_keywords: Optional[str] = None
    ui_parameters: Optional[Union[str, List[UIParameter]]] = []
    is_ai: Optional[bool] = None
    is_display: Optional[bool] = True

    @validator("endpoint", pre=True)
    def parse_endpoint(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return {}
        return v

    @validator("ui_parameters", pre=True)
    def parse_ui_parameters(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return []
        return v

    class Config:
        from_attributes = True

class ImageStyleOut(BaseModel):
    id: int
    slno:Optional[str]
    style_category:Optional[str]
    style_name: str
    url: Optional[str] = None
    ref_keywords: Optional[str] = None
    endpoint: Dict[str, Any] = {}
    ui_parameters: List[UIParameter] = []
    is_ai: bool = False
    is_display: Optional[bool] = True

    @validator("endpoint", pre=True)
    def parse_endpoint_out(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return {}
        return v or {}

    @validator("ui_parameters", pre=True)
    def parse_ui_out(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return []
        return v or []

    @validator("is_ai", pre=True)
    def parse_bool(cls, v):
        if isinstance(v, str):
            return v.lower() in ["true", "1", "yes"]
        return bool(v)

    class Config:
        from_attributes = True
