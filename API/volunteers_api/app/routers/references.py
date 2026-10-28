from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app import models, schemas
from app.database import get_db

router = APIRouter(
    prefix="/api/references",
    tags=["References (Static Data)"]
)

@router.get("/categories", response_model=List[schemas.CategoryResponse])
def get_categories(db: Session = Depends(get_db)):
    """Получить список всех категорий мероприятий"""
    return db.query(models.Category).all()

@router.get("/locations", response_model=List[schemas.LocationResponse])
def get_locations(db: Session = Depends(get_db)):
    """Получить список всех районов/локаций"""
    return db.query(models.Location).all()