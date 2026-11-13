from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import FileResponse
import os
import secrets
import uuid
from datetime import datetime
from pathlib import Path

router = APIRouter(prefix="/gallery", tags=["gallery"])
security = HTTPBasic()

UPLOAD_DIR = Path("/app/backend/uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "rawahna2025")

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

def verify_admin(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, ADMIN_USERNAME)
    correct_password = secrets.compare_digest(credentials.password, ADMIN_PASSWORD)
    if not (correct_username and correct_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return credentials.username

def get_db():
    from server import db as server_db
    return server_db

@router.post("/upload")
async def upload_photo(
    file: UploadFile = File(...),
    uploader_name: str = Form(...),
    uploader_email: str = Form(""),
    caption: str = Form(""),
    tour_name: str = Form("")
):
    """Upload a visitor photo"""
    try:
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read file content
        content = await file.read()
        
        # Check file size
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="File size must be less than 10MB")
        
        # Generate unique filename
        file_ext = file.filename.split('.')[-1]
        unique_filename = f"{uuid.uuid4()}.{file_ext}"
        file_path = UPLOAD_DIR / unique_filename
        
        # Save file
        with open(file_path, 'wb') as f:
            f.write(content)
        
        # Save to database
        db = get_db()
        photo_doc = {
            "id": str(uuid.uuid4()),
            "filename": unique_filename,
            "original_filename": file.filename,
            "uploader_name": uploader_name,
            "uploader_email": uploader_email,
            "caption": caption,
            "tour_name": tour_name,
            "status": "pending",
            "uploaded_at": datetime.utcnow().isoformat()
        }
        
        await db.visitor_photos.insert_one(photo_doc)
        photo_doc.pop('_id', None)
        
        return {"success": True, "photo": photo_doc}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/visitor")
async def get_visitor_photos():
    """Get approved visitor photos"""
    try:
        db = get_db()
        photos = await db.visitor_photos.find(
            {"status": "approved"}
        ).sort("uploaded_at", -1).to_list(50)
        
        for photo in photos:
            photo.pop('_id', None)
        
        return {"photos": photos}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/image/{filename}")
async def get_image(filename: str):
    """Serve uploaded image"""
    file_path = UPLOAD_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(file_path)

@router.get("/admin/pending")
async def get_pending_photos(admin: str = Depends(verify_admin)):
    """Get pending photos for moderation (admin only)"""
    try:
        db = get_db()
        photos = await db.visitor_photos.find(
            {"status": "pending"}
        ).sort("uploaded_at", -1).to_list(100)
        
        for photo in photos:
            photo.pop('_id', None)
        
        return {"photos": photos}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/admin/{photo_id}")
async def moderate_photo(photo_id: str, status: str, admin: str = Depends(verify_admin)):
    """Approve or reject a photo (admin only)"""
    try:
        db = get_db()
        
        if status not in ["approved", "rejected"]:
            raise HTTPException(status_code=400, detail="Invalid status")
        
        update_data = {"status": status}
        if status == "approved":
            update_data["approved_at"] = datetime.utcnow().isoformat()
        
        result = await db.visitor_photos.update_one(
            {"id": photo_id},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Photo not found")
        
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))