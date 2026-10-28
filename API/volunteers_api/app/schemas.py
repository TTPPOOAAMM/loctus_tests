from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import date, datetime
from enum import Enum

class UserCreate(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    role_id: int

class UserResponse(BaseModel):
    ID_user: int
    full_name: str
    email: EmailStr
    role_id: int
    is_deleted: bool

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: Optional[str] = None
    role_id: Optional[int] = None

class SkillBase(BaseModel):
    skill_name: str

class ProfileBase(BaseModel):
    phone: Optional[str] = None
    birth_date: Optional[date] = None
    interests: Optional[str] = None

class ProfileUpdate(ProfileBase):
    skills: Optional[List[str]] = None 

class ProfileResponse(ProfileBase):
    user_id: int
    skills: List[SkillBase] = []

    class Config:
        from_attributes = True

class UserProfileResponse(UserResponse):
    profile: Optional[ProfileResponse] = None

class EventStatusEnum(str, Enum):
    active = "active"
    closed = "closed"
    completed = "completed"
    archived = "archived"

class EventBase(BaseModel):
    title: str
    description: Optional[str] = None
    location_id: int
    event_date: datetime
    max_participants: int

class EventCreate(EventBase):
    category_ids: List[int] = [] 

class EventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    location_id: Optional[int] = None
    event_date: Optional[datetime] = None
    max_participants: Optional[int] = None
    status: Optional[EventStatusEnum] = None
    category_ids: Optional[List[int]] = None 

class CategoryResponse(BaseModel):
    ID_Categories: int
    name: str

    class Config:
        from_attributes = True

class EventResponse(EventBase):
    ID_event: int
    organizer_id: int
    status: EventStatusEnum
    categories: List[CategoryResponse] = [] 
    pending_count: int = 0      
    remaining_seats: int = 0    

    class Config:
        from_attributes = True

class AppStatusEnum(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    expired = "expired"
    completed = "completed"

class ApplicationCreate(BaseModel):
    event_id: int

class ApplicationStatusUpdate(BaseModel):
    status: AppStatusEnum

class ApplicationResponse(BaseModel):
    ID_application: int
    volunteer_id: int
    event_id: int
    status: AppStatusEnum
    applied_at: datetime

    class Config:
        from_attributes = True

class ApplicationWithVolunteerResponse(ApplicationResponse):
    volunteer: UserResponse 

    class Config:
        from_attributes = True

class LocationResponse(BaseModel):
    ID_Locations: int
    district_name: str

    class Config:
        from_attributes = True

class ApplicationWithEventResponse(ApplicationResponse):
    event: EventResponse 

    class Config:
        from_attributes = True