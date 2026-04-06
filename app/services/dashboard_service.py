from sqlalchemy.orm import Session
from sqlalchemy import func, case
from datetime import date
from typing import Optional
from app.models.financial_record import FinancialRecord, RecordType


def get_overview(db: Session):
    rows = db.query(
        func.coalesce(func.sum(case((FinancialRecord.type == RecordType.income, FinancialRecord.amount), else_=0)), 0).label("total_income"),
        func.coalesce(func.sum(case((FinancialRecord.type == RecordType.expense, FinancialRecord.amount), else_=0)), 0).label("total_expenses"),
        func.count(FinancialRecord.id).label("total_records"),
        func.sum(case((FinancialRecord.type == RecordType.income, 1), else_=0)).label("income_records"),
        func.sum(case((FinancialRecord.type == RecordType.expense, 1), else_=0)).label("expense_records"),
    ).filter(FinancialRecord.is_deleted == False).one()

    return {
        "total_income": round(rows.total_income, 2),
        "total_expenses": round(rows.total_expenses, 2),
        "net_balance": round(rows.total_income - rows.total_expenses, 2),
        "total_records": rows.total_records,
        "income_records": rows.income_records or 0,
        "expense_records": rows.expense_records or 0,
    }


def get_summary(db: Session, date_from: Optional[date] = None, date_to: Optional[date] = None):
    query = db.query(FinancialRecord).filter(FinancialRecord.is_deleted == False)
    if date_from:
        query = query.filter(FinancialRecord.date >= date_from)
    if date_to:
        query = query.filter(FinancialRecord.date <= date_to)

    # Totals
    totals = db.query(
        func.coalesce(func.sum(case((FinancialRecord.type == RecordType.income, FinancialRecord.amount), else_=0)), 0).label("total_income"),
        func.coalesce(func.sum(case((FinancialRecord.type == RecordType.expense, FinancialRecord.amount), else_=0)), 0).label("total_expenses"),
        func.count(FinancialRecord.id).label("total_records"),
    ).filter(FinancialRecord.is_deleted == False)

    if date_from:
        totals = totals.filter(FinancialRecord.date >= date_from)
    if date_to:
        totals = totals.filter(FinancialRecord.date <= date_to)

    totals = totals.one()

    # Category breakdown
    cat_query = db.query(
        FinancialRecord.category,
        FinancialRecord.type,
        func.sum(FinancialRecord.amount).label("total"),
        func.count(FinancialRecord.id).label("count"),
    ).filter(FinancialRecord.is_deleted == False)

    if date_from:
        cat_query = cat_query.filter(FinancialRecord.date >= date_from)
    if date_to:
        cat_query = cat_query.filter(FinancialRecord.date <= date_to)

    cat_query = cat_query.group_by(FinancialRecord.category, FinancialRecord.type).order_by(func.sum(FinancialRecord.amount).desc())

    category_breakdown = [
        {"category": r.category, "type": r.type, "total": round(r.total, 2), "count": r.count}
        for r in cat_query.all()
    ]

    return {
        "total_income": round(totals.total_income, 2),
        "total_expenses": round(totals.total_expenses, 2),
        "net_balance": round(totals.total_income - totals.total_expenses, 2),
        "total_records": totals.total_records,
        "category_breakdown": category_breakdown,
    }


def get_trends(db: Session, period: str = "monthly"):
    records = db.query(FinancialRecord).filter(FinancialRecord.is_deleted == False).all()

    grouped: dict = {}
    for r in records:
        if period == "monthly":
            key = r.date.strftime("%Y-%m")
        else:
            key = r.date.strftime("%Y-W%W")

        if key not in grouped:
            grouped[key] = {"period": key, "income": 0.0, "expenses": 0.0, "transactions": 0}

        if r.type == RecordType.income:
            grouped[key]["income"] += r.amount
        else:
            grouped[key]["expenses"] += r.amount
        grouped[key]["transactions"] += 1

    trends = sorted(grouped.values(), key=lambda x: x["period"])
    for t in trends:
        t["income"] = round(t["income"], 2)
        t["expenses"] = round(t["expenses"], 2)
        t["net"] = round(t["income"] - t["expenses"], 2)

    return {"period_type": period, "trends": trends[-12:]}  # Last 12 periods


def get_recent_activity(db: Session, limit: int = 10):
    records = (
        db.query(FinancialRecord)
        .filter(FinancialRecord.is_deleted == False)
        .order_by(FinancialRecord.created_at.desc())
        .limit(limit)
        .all()
    )
    return records
