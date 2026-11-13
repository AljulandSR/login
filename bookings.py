from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from datetime import datetime, date
from typing import List
import os
import secrets

router = APIRouter(prefix="/bookings", tags=["bookings"])
security = HTTPBasic()

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "rawahna2025")

def get_db():
    from server import db as server_db
    return server_db

def verify_admin(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, ADMIN_USERNAME)
    correct_password = secrets.compare_digest(credentials.password, ADMIN_PASSWORD)
    if not (correct_username and correct_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return credentials.username

class BookingCreate(BaseModel):
    tour_id: int
    tour_name: str
    customer_name: str
    customer_email: str
    customer_phone: str
    booking_date: date
    number_of_people: int
    total_price: float
    notes: str = ""

@router.post("/")
async def create_booking(booking: BookingCreate):
    """Create a new booking"""
    try:
        db = get_db()
        
        booking_doc = {
            "id": str(datetime.now().timestamp()),
            "tour_id": booking.tour_id,
            "tour_name": booking.tour_name,
            "customer_name": booking.customer_name,
            "customer_email": booking.customer_email,
            "customer_phone": booking.customer_phone,
            "booking_date": booking.booking_date.isoformat(),
            "number_of_people": booking.number_of_people,
            "total_price": booking.total_price,
            "status": "pending",
            "notes": booking.notes,
            "created_at": datetime.utcnow().isoformat()
        }
        
        await db.bookings.insert_one(booking_doc)
        booking_doc.pop('_id', None)
        
        return {"success": True, "booking": booking_doc}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/availability")
async def check_availability(tour_id: int, date: date):
    """Check availability for a tour on a specific date"""
    try:
        db = get_db()
        
        # Count existing bookings for this tour on this date
        count = await db.bookings.count_documents({
            "tour_id": tour_id,
            "booking_date": date.isoformat(),
            "status": {"$in": ["pending", "confirmed"]}
        })
        
        # Each tour can have max 2 bookings per day
        max_bookings = 2
        available = count < max_bookings
        
        return {
            "available": available,
            "slots_remaining": max_bookings - count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/admin/list")
async def list_bookings(admin: str = Depends(verify_admin)):
    """List all bookings (admin only)"""
    try:
        db = get_db()
        bookings = await db.bookings.find().sort("created_at", -1).to_list(100)
        
        for booking in bookings:
            booking.pop('_id', None)
            
        return {"bookings": bookings}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/admin/{booking_id}")
async def update_booking_status(booking_id: str, status: str, admin: str = Depends(verify_admin)):
    """Update booking status (admin only)"""
    try:
        db = get_db()
        
        if status not in ["pending", "confirmed", "cancelled"]:
            raise HTTPException(status_code=400, detail="Invalid status")
        
        result = await db.bookings.update_one(
            {"id": booking_id},
            {"$set": {"status": status}}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Booking not found")
        
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))