from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app import models, schemas, auth
from app.database import get_db

router = APIRouter(
    prefix="/api/applications",
    tags=["Applications"]
)

@router.post("/", response_model=schemas.ApplicationResponse, status_code=status.HTTP_201_CREATED)
def create_application(
    app_data: schemas.ApplicationCreate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Подача заявки на мероприятие (Только для Волонтеров)"""
    if current_user.role_id != 1:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Только волонтеры могут подавать заявки")
    
    event = db.query(models.Event).filter(models.Event.ID_event == app_data.event_id).first()
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Мероприятие не найдено")
    if event.status != models.EventStatus.active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Набор на это мероприятие закрыт")

    existing_app = db.query(models.Application).filter(
        models.Application.event_id == app_data.event_id,
        models.Application.volunteer_id == current_user.ID_user
    ).first()
    if existing_app:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Вы уже подали заявку на это мероприятие")

    new_app = models.Application(
        volunteer_id=current_user.ID_user,
        event_id=app_data.event_id,
        status=models.AppStatus.pending
    )
    db.add(new_app)
    db.commit()
    db.refresh(new_app)
    return new_app


@router.put("/{application_id}/status", response_model=schemas.ApplicationResponse)
@router.patch("/{application_id}/status", response_model=schemas.ApplicationResponse)
def update_application_status(
    application_id: int,
    status_data: schemas.ApplicationStatusUpdate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Изменение статуса заявки (Поддерживает PUT и PATCH, только для Организатора)"""
    if current_user.role_id != 2:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Только организаторы могут управлять заявками")

    application = db.query(models.Application).filter(models.Application.ID_application == application_id).first()
    if not application:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Заявка не найдена")

    event = db.query(models.Event).filter(models.Event.ID_event == application.event_id).first()
    if not event or event.organizer_id != current_user.ID_user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Вы можете управлять заявками только своих мероприятий")

    requested_status = status_data.status

    # СЦЕНАРИЙ 1: Организатор одобряет заявку (занятие свободного места)
    if requested_status == schemas.AppStatusEnum.approved and application.status != models.AppStatus.approved:
        approved_count = db.query(models.Application).filter(
            models.Application.event_id == event.ID_event,
            models.Application.status == models.AppStatus.approved
        ).count()

        if approved_count >= event.max_participants:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Достигнут лимит участников для этого мероприятия")

        # Если это одобряемое место было последним свободным — закрываем набор на мероприятие
        if approved_count + 1 == event.max_participants:
            event.status = models.EventStatus.closed

    # ДОБАВЛЕНО -> СЦЕНАРИЙ 2: Организатор отменяет одобрение (освобождение места)
    elif application.status == models.AppStatus.approved and requested_status != schemas.AppStatusEnum.approved:
        # Если мероприятие было "закрыто" из-за нехватки мест, мы возвращаем его в "активное" состояние
        if event.status == models.EventStatus.closed:
            event.status = models.EventStatus.active

    # Обновляем статус заявки
    application.status = requested_status
    db.commit()
    db.refresh(application)

    # Записываем действие в логи мероприятия
    log_action_text = f"Статус заявки #{application.ID_application} изменен на {requested_status.value}"
    new_log = models.EventLog(event_id=event.ID_event, action=log_action_text)
    db.add(new_log)
    db.commit()
    
    return application


@router.get("/me", response_model=List[schemas.ApplicationWithEventResponse])
def get_my_applications(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Получить историю своих заявок с деталями мероприятий (Только для Волонтера)"""
    if current_user.role_id != 1:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Только волонтеры")
        
    apps = db.query(models.Application).filter(models.Application.volunteer_id == current_user.ID_user).all()
    return apps