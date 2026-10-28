from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone
from app import models, schemas, auth, database
from app.database import get_db

router = APIRouter(
    prefix="/api/events",
    tags=["Events / Board"]
)

def log_event_action(db: Session, event_id: int, action: str):
    """Записывает действие в таблицу Event_Logs"""
    new_log = models.EventLog(event_id=event_id, action=action)
    db.add(new_log)
    db.commit()

@router.post("/", response_model=schemas.EventResponse, status_code=status.HTTP_201_CREATED)
def create_event(
    event_data: schemas.EventCreate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Создать новое волонтерское мероприятие с категориями"""
    if current_user.role_id != 2:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Только организаторы")
    
    event_dict = event_data.model_dump(exclude={"category_ids"})
    
    new_event = models.Event(
        **event_dict,
        organizer_id=current_user.ID_user,
        status=models.EventStatus.active
    )
    
    if event_data.category_ids:
        categories = db.query(models.Category).filter(models.Category.ID_Categories.in_(event_data.category_ids)).all()
        new_event.categories = categories
    
    db.add(new_event)
    db.commit()
    db.refresh(new_event)
    
    log_event_action(db, new_event.ID_event, "Создано мероприятие")
    
    return new_event

@router.get("/", response_model=List[schemas.EventResponse])
def get_active_events(
    location_id: Optional[int] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Получить список всех активных объявлений.
    Включает автоматическую архивацию просроченных мероприятий.
    Сортировка: по дате проведения (сначала ближайшие).
    """
    current_time = datetime.now(timezone.utc)

    expired_events = db.query(models.Event).filter(
        models.Event.status == models.EventStatus.active,
        models.Event.event_date < current_time
    ).all()

    if expired_events:
        for event in expired_events:
            event.status = models.EventStatus.archived
            
            for app in event.applications:
                if app.status == models.AppStatus.pending:
                    app.status = models.AppStatus.expired
                    
            log_event_action(db, event.ID_event, "Автоматическая архивация (истек срок)")
            
        db.commit()

    query = db.query(models.Event).filter(models.Event.status == models.EventStatus.active)
    
    if location_id:
        query = query.filter(models.Event.location_id == location_id)
    if search:
        query = query.filter(models.Event.title.ilike(f"%{search}%"))
        
    events = query.order_by(models.Event.event_date.asc()).all()
    
    for event in events:
        event.pending_count = sum(1 for app in event.applications if app.status == models.AppStatus.pending)
        approved_count = sum(1 for app in event.applications if app.status == models.AppStatus.approved)
        event.remaining_seats = max(0, event.max_participants - approved_count)
        
    return events

@router.put("/{event_id}", response_model=schemas.EventResponse)
def update_event(
    event_id: int,
    event_data: schemas.EventUpdate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Изменить существующее мероприятие"""
    event = db.query(models.Event).filter(models.Event.ID_event == event_id).first()
    if not event or event.organizer_id != current_user.ID_user:
        raise HTTPException(status_code=403, detail="Нет доступа")

    update_data = event_data.model_dump(exclude_unset=True, exclude={"category_ids"})
    for key, value in update_data.items():
        setattr(event, key, value)

    if event_data.category_ids is not None:
        categories = db.query(models.Category).filter(models.Category.ID_Categories.in_(event_data.category_ids)).all()
        event.categories = categories

    db.commit()
    db.refresh(event)
    
    log_event_action(db, event.ID_event, "Обновлены данные мероприятия")
    return event

@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def archive_event(
    event_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Архивировать мероприятие"""
    event = db.query(models.Event).filter(models.Event.ID_event == event_id).first()
    if not event or event.organizer_id != current_user.ID_user:
        raise HTTPException(status_code=403, detail="Нет доступа")

    event.status = models.EventStatus.archived
    for app in event.applications:
        if app.status == models.AppStatus.pending:
            app.status = models.AppStatus.expired

    db.commit()
    log_event_action(db, event.ID_event, "Мероприятие досрочно переведено в архив")
    return None

@router.get("/me", response_model=List[schemas.EventResponse])
def get_my_events(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Получить список мероприятий, созданных текущим организатором"""
    if current_user.role_id != 2:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Доступно только организаторам"
        )
    
    events = db.query(models.Event).filter(models.Event.organizer_id == current_user.ID_user).all()
    
    for event in events:
        event.pending_count = sum(1 for app in event.applications if app.status == models.AppStatus.pending)
        approved_count = sum(1 for app in event.applications if app.status == models.AppStatus.approved)
        event.remaining_seats = max(0, event.max_participants - approved_count)
        
    return events

@router.get("/{event_id}/applications", response_model=List[schemas.ApplicationWithVolunteerResponse])
def get_event_applications(
    event_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Получить список заявок на мероприятие. 
    Включает анкеты волонтеров. (Только для Организатора этого мероприятия)
    """
    event = db.query(models.Event).filter(models.Event.ID_event == event_id).first()
    
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Мероприятие не найдено")
        
    if event.organizer_id != current_user.ID_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Вы можете просматривать заявки только на свои мероприятия"
        )

    return event.applications