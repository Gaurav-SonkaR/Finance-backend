from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date
import math

from app.db.session import get_db
from app.schemas.schemas import RecordCreateRequest, RecordUpdateRequest, RecordOut
from app.services import record_service
from app.middleware.auth import require_admin, require_any
from app.models.user import User
from app.models.financial_record import RecordType

router = APIRouter(prefix="/records", tags=["Financial Records"])


@router.get("/", response_model=dict, summary="List all financial records")
def list_records(
    type: Optional[RecordType] = Query(None, description="Filter by type: income or expense"),
    category: Optional[str] = Query(None, description="Filter by category (partial match)"),
    date_from: Optional[date] = Query(None, description="Filter from date (YYYY-MM-DD)"),
    date_to: Optional[date] = Query(None, description="Filter to date (YYYY-MM-DD)"),
    search: Optional[str] = Query(None, description="Search in notes and category"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any),
):
    """
    List financial records with powerful filtering.

    Access: **Viewer, Analyst, Admin**

    Filters:
    - `type`: income or expense
    - `category`: partial text match
    - `date_from` / `date_to`: date range (YYYY-MM-DD)
    - `search`: searches notes and category fields
    """
    records, total = record_service.get_records(
        db,
        record_type=type,
        category=category,
        date_from=date_from,
        date_to=date_to,
        search=search,
        page=page,
        limit=limit,
    )
    return {
        "success": True,
        "data": [RecordOut.model_validate(r).model_dump() for r in records],
        "pagination": {
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": math.ceil(total / limit) if total > 0 else 1,
        },
    }


@router.get("/{record_id}", response_model=dict, summary="Get a single record")
def get_record(
    record_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any),
):
    """
    Get a single financial record by ID.

    Access: **Viewer, Analyst, Admin**
    """
    record = record_service.get_record_by_id(db, record_id)
    return {"success": True, "data": RecordOut.model_validate(record).model_dump()}


@router.post("/", response_model=dict, status_code=201, summary="Create a financial record")
def create_record(
    payload: RecordCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    Create a new financial record.

    Access: **Admin only**

    Fields:
    - `amount`: positive number (e.g. 1500.00)
    - `type`: income or expense
    - `category`: e.g. Salary, Rent, Marketing
    - `date`: YYYY-MM-DD format
    - `notes`: optional description
    """
    record = record_service.create_record(db, payload, current_user)
    return {
        "success": True,
        "message": "Financial record created successfully.",
        "data": RecordOut.model_validate(record).model_dump(),
    }


@router.patch("/{record_id}", response_model=dict, summary="Update a financial record")
def update_record(
    record_id: str,
    payload: RecordUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    Update one or more fields of a financial record.

    Access: **Admin only**

    All fields are optional — only send what you want to change.
    """
    record = record_service.update_record(db, record_id, payload)
    return {
        "success": True,
        "message": "Record updated successfully.",
        "data": RecordOut.model_validate(record).model_dump(),
    }


@router.delete("/{record_id}", response_model=dict, summary="Soft delete a record")
def delete_record(
    record_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    Soft-delete a financial record (marks as deleted, not removed from DB).

    Access: **Admin only**
    """
    record_service.soft_delete_record(db, record_id)
    return {"success": True, "message": "Record deleted successfully."}
