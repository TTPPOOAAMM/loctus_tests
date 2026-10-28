# app/models.py
import enum
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Date, ForeignKey, Enum, Table
from sqlalchemy.orm import relationship
from app.database import Base

class EventStatus(enum.Enum):
    active = "active"
    closed = "closed"
    completed = "completed"
    archived = "archived"

class AppStatus(enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    expired = "expired"
    completed = "completed"

event_categories = Table(
    'Event_Categories',
    Base.metadata,
    Column('event_id', Integer, ForeignKey('Events.ID_event'), primary_key=True),
    Column('category_id', Integer, ForeignKey('Categories.ID_Categories'), primary_key=True)
)

class Role(Base):
    __tablename__ = "Roles"
    ID_role = Column(Integer, primary_key=True, index=True)
    role_name = Column(String(100), unique=True, nullable=False)

    users = relationship("User", back_populates="role")

class User(Base):
    __tablename__ = "Users"
    ID_user = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(150), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role_id = Column(Integer, ForeignKey("Roles.ID_role"))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    is_deleted = Column(Boolean, default=False)

    role = relationship("Role", back_populates="users")
    profile = relationship("Profile", back_populates="user", uselist=False)
    events = relationship("Event", back_populates="organizer")
    applications = relationship("Application", back_populates="volunteer")

class Profile(Base):
    __tablename__ = "Profiles"
    user_id = Column(Integer, ForeignKey("Users.ID_user"), primary_key=True)
    phone = Column(String(20), nullable=True)
    birth_date = Column(Date, nullable=True)
    interests = Column(Text, nullable=True)

    user = relationship("User", back_populates="profile")
    skills = relationship("VolunteerSkill", back_populates="profile")

class VolunteerSkill(Base):
    __tablename__ = "Volunteer_Skills"
    id = Column(Integer, primary_key=True, index=True) # Суррогатный ключ для ORM
    profile_id = Column(Integer, ForeignKey("Profiles.user_id"))
    skill_name = Column(String(200), nullable=False)

    profile = relationship("Profile", back_populates="skills")

class Category(Base):
    __tablename__ = "Categories"
    ID_Categories = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)

    events = relationship("Event", secondary=event_categories, back_populates="categories")

class Location(Base):
    __tablename__ = "Locations"
    ID_Locations = Column(Integer, primary_key=True, index=True)
    district_name = Column(String(200), nullable=False)

    events = relationship("Event", back_populates="location")

class Event(Base):
    __tablename__ = "Events"
    ID_event = Column(Integer, primary_key=True, index=True)
    organizer_id = Column(Integer, ForeignKey("Users.ID_user"))
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    location_id = Column(Integer, ForeignKey("Locations.ID_Locations"))
    event_date = Column(DateTime, nullable=False)
    max_participants = Column(Integer, nullable=False)
    status = Column(Enum(EventStatus), default=EventStatus.active)

    organizer = relationship("User", back_populates="events")
    location = relationship("Location", back_populates="events")
    categories = relationship("Category", secondary=event_categories, back_populates="events")
    applications = relationship("Application", back_populates="event")
    logs = relationship("EventLog", back_populates="event")

class Application(Base):
    __tablename__ = "Applications"
    ID_application = Column(Integer, primary_key=True, index=True)
    volunteer_id = Column(Integer, ForeignKey("Users.ID_user"))
    event_id = Column(Integer, ForeignKey("Events.ID_event"))
    status = Column(Enum(AppStatus), default=AppStatus.pending)
    applied_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    volunteer = relationship("User", back_populates="applications")
    event = relationship("Event", back_populates="applications")

class EventLog(Base):
    __tablename__ = "Event_Logs"
    ID_log = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("Events.ID_event"))
    action = Column(String(255), nullable=False)
    changed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    event = relationship("Event", back_populates="logs")