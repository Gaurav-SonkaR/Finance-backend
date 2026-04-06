from pydantic import BaseModel, EmailStr, field_validator, ConfigDict
from typing import Optional
from datetime import datetime, date
from app.models.user import UserRole, UserStatus
from app.models.financial_record import RecordType


# ─── Auth Schemas ────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: UserRole = UserRole.viewer

    @field_validator("name")
    @classmethod
    def name_must_be_valid(cls, v):
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Name must be at least 2 characters.")
        return v

    @field_validator("password")
    @classmethod
    def password_must_be_strong(cls, v):
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters.")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ─── User Schemas ─────────────────────────────────────────────────────────────

class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    email: str
    role: UserRole
    status: UserStatus
    created_at: datetime
    updated_at: datetime


class UserUpdateRequest(BaseModel):
    name: Optional[str] = None
    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None

    @field_validator("name")
    @classmethod
    def name_must_be_valid(cls, v):
        if v is not None:
            v = v.strip()
            if len(v) < 2:
                raise ValueError("Name must be at least 2 characters.")
        return v


# ─── Financial Record Schemas ─────────────────────────────────────────────────

class RecordCreateRequest(BaseModel):
    amount: float
    type: RecordType
    category: str
    date: date
    notes: Optional[str] = None

    @field_validator("amount")
    @classmethod
    def amount_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("Amount must be greater than 0.")
        return round(v, 2)

    @field_validator("category")
    @classmethod
    def category_must_be_valid(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("Category cannot be empty.")
        return v


class RecordUpdateRequest(BaseModel):
    amount: Optional[float] = None
    type: Optional[RecordType] = None
    category: Optional[str] = None
    date: Optional[date] = None
    notes: Optional[str] = None

    @field_validator("amount")
    @classmethod
    def amount_must_be_positive(cls, v):
        if v is not None and v <= 0:
            raise ValueError("Amount must be greater than 0.")
        return round(v, 2) if v is not None else v

    @field_validator("category")
    @classmethod
    def category_must_be_valid(cls, v):
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("Category cannot be empty.")
        return v


class RecordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    amount: float
    type: RecordType
    category: str
    date: date
    notes: Optional[str]
    is_deleted: bool
    created_by: str
    created_at: datetime
    updated_at: datetime


# ─── Dashboard Schemas ────────────────────────────────────────────────────────

class CategoryBreakdown(BaseModel):
    category: str
    type: RecordType
    total: float
    count: int


class DashboardSummary(BaseModel):
    total_income: float
    total_expenses: float
    net_balance: float
    total_records: int
    category_breakdown: list[CategoryBreakdown]


class TrendPeriod(BaseModel):
    period: str
    income: float
    expenses: float
    net: float
    transactions: int


class TrendsResponse(BaseModel):
    period_type: str
    trends: list[TrendPeriod]


class OverviewResponse(BaseModel):
    total_income: float
    total_expenses: float
    net_balance: float
    total_records: int
    income_records: int
    expense_records: int


# ─── Generic Response Wrappers ────────────────────────────────────────────────

class PaginationMeta(BaseModel):
    total: int
    page: int
    limit: int
    total_pages: int


class SuccessResponse(BaseModel):
    success: bool = True
    message: str
    data: Optional[dict] = None
