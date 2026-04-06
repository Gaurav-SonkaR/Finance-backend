from sqlalchemy.orm import Session
from sqlalchemy import func, case
from fastapi import HTTPException, status
from datetime import date
from typing import Optional
from app.models.financial_record import FinancialRecord, RecordType
from app.models.user import User
from app.schemas.schemas import RecordCreateRequest, RecordUpdateRequest


def get_records(
    db: Session,
    record_type: Optional[RecordType] = None,
    category: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    search: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
):
    query = db.query(FinancialRecord).filter(FinancialRecord.is_deleted == False)

    if record_type:
        query = query.filter(FinancialRecord.type == record_type)
    if category:
        query = query.filter(FinancialRecord.category.ilike(f"%{category}%"))
    if date_from:
        query = query.filter(FinancialRecord.date >= date_from)
    if date_to:
        query = query.filter(FinancialRecord.date <= date_to)
    if search:
        query = query.filter(
            FinancialRecord.notes.ilike(f"%{search}%") |
            FinancialRecord.category.ilike(f"%{search}%")
        )

    total = query.count()
    records = query.order_by(FinancialRecord.date.desc(), FinancialRecord.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
    return records, total


def get_record_by_id(db: Session, record_id: str) -> FinancialRecord:
    record = db.query(FinancialRecord).filter(
        FinancialRecord.id == record_id,
        FinancialRecord.is_deleted == False,
    ).first()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found.")
    return record


def create_record(db: Session, payload: RecordCreateRequest, current_user: User) -> FinancialRecord:
    record = FinancialRecord(
        amount=payload.amount,
        type=payload.type,
        category=payload.category.strip(),
        date=payload.date,
        notes=payload.notes,
        created_by=current_user.id,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def update_record(db: Session, record_id: str, payload: RecordUpdateRequest) -> FinancialRecord:
    record = get_record_by_id(db, record_id)

    if payload.amount is not None:
        record.amount = payload.amount
    if payload.type is not None:
        record.type = payload.type
    if payload.category is not None:
        record.category = payload.category.strip()
    if payload.date is not None:
        record.date = payload.date
    if payload.notes is not None:
        record.notes = payload.notes

    db.commit()
    db.refresh(record)
    return record


def soft_delete_record(db: Session, record_id: str):
    record = get_record_by_id(db, record_id)
    record.is_deleted = True
    db.commit()
