from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import uuid

class VisitorPhoto(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    filename: str
    original_filename: str
    uploader_name: str
    uploader_email: Optional[str] = None
    caption: Optional[str] = None
    tour_name: Optional[str] = None
    status: str = "pending"  # pending, approved, rejected
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    approved_at: Optional[datetime] = None

class VisitorPhotoCreate(BaseModel):
    uploader_name: str
    uploader_email: Optional[str] = None
    caption: Optional[str] = None
    tour_name: Optional[str] = None

class PhotoApproval(BaseModel):
    status: str  # approved, rejected