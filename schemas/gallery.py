from pydantic import BaseModel

class GalleryBase(BaseModel):
    key: str
    image_url: str
    original_img_url: str

class GalleryCreate(GalleryBase):
    pass

class GalleryUpdate(BaseModel):
    key: str | None = None
    image_url: str | None = None
    original_img_url: str | None = None

class GalleryResponse(GalleryBase):
    id: int

    class Config:
        from_attributes = True


class GalleryKeywordBase(BaseModel):
    keyword: str
    is_display: bool = True
    is_suggest: bool = False

class GalleryKeywordCreate(GalleryKeywordBase):
    pass

class GalleryKeywordUpdate(BaseModel):
    keyword: str
    is_display: bool | None = None
    is_suggest: bool | None = None

class GalleryKeywordResponse(GalleryKeywordBase):
    id: int

    class Config:
        from_attributes = True       
