from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, date
import uuid

class Booking(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tour_id: int
    tour_name: str
    customer_name: str
    customer_email: str
    customer_phone: str
    booking_date: date
    number_of_people: int
    total_price: float
    status: str = "pending"  # pending, confirmed, cancelled
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class BookingCreate(BaseModel):
    tour_id: int
    tour_name: str
    customer_name: str
    customer_email: str
    customer_phone: str
    booking_date: date
    number_of_people: int
    total_price: float
    notes: Optional[str] = None

class BookingUpdate(BaseModel):
    status: str