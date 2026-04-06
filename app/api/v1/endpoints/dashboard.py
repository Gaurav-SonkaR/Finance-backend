from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date

from app.db.session import get_db
from app.schemas.schemas import RecordOut
from app.services import dashboard_service
from app.middleware.auth import require_any, require_analyst_or_admin
from app.models.user import User

router = APIRouter(prefix="/dashboard", tags=["Dashboard & Analytics"])


@router.get("/overview", response_model=dict, summary="Quick dashboard overview")
def overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any),
):
    """
    High-level financial snapshot.

    Access: **Viewer, Analyst, Admin**

    Returns total income, expenses, net balance, and record counts.
    This is intentionally simple for the dashboard header.
    """
    data = dashboard_service.get_overview(db)
    return {"success": True, "data": data}


@router.get("/summary", response_model=dict, summary="Detailed summary with category breakdown")
def summary(
    date_from: Optional[date] = Query(None, description="Start date filter (YYYY-MM-DD)"),
    date_to: Optional[date] = Query(None, description="End date filter (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_analyst_or_admin),
):
    """
    Detailed financial summary with category-wise breakdown.

    Access: **Analyst, Admin**

    Supports optional date range filtering. Returns:
    - Total income / expenses / net balance
    - Category-wise totals (e.g. Salary, Rent, Marketing)
    """
    data = dashboard_service.get_summary(db, date_from=date_from, date_to=date_to)
    return {"success": True, "data": data}


@router.get("/trends", response_model=dict, summary="Monthly or weekly income/expense trends")
def trends(
    period: str = Query("monthly", description="Period type: 'monthly' or 'weekly'"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_analyst_or_admin),
):
    """
    Time-series trends for income and expenses.

    Access: **Analyst, Admin**

    - `period=monthly` → grouped by YYYY-MM (last 12 months)
    - `period=weekly` → grouped by ISO week (last 12 weeks)

    Returns income, expenses, net, and transaction count per period.
    """
    if period not in ("monthly", "weekly"):
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="period must be 'monthly' or 'weekly'.")
    data = dashboard_service.get_trends(db, period=period)
    return {"success": True, "data": data}


@router.get("/recent", response_model=dict, summary="Recent financial activity")
def recent_activity(
    limit: int = Query(10, ge=1, le=50, description="Number of recent records to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_analyst_or_admin),
):
    """
    Fetch the most recent financial transactions.

    Access: **Analyst, Admin**
    """
    records = dashboard_service.get_recent_activity(db, limit=limit)
    return {
        "success": True,
        "data": [RecordOut.model_validate(r).model_dump() for r in records],
    }
