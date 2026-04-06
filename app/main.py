from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.api.v1.router import api_router
from app.db.session import engine, Base

# Import models so SQLAlchemy registers them before create_all
from app.models import user, financial_record  # noqa: F401

# Create all tables
Base.metadata.create_all(bind=engine)

# Rate limiter
limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
## Finance Data Processing and Access Control Backend

A RESTful API for managing financial records with role-based access control.

### Roles
| Role | Permissions |
|------|------------|
| **viewer** | Read dashboard overview only |
| **analyst** | Read records + detailed analytics + trends |
| **admin** | Full access — create, update, delete records and manage users |

### Quick Start
1. **Register** → `POST /api/v1/auth/register`
2. **Login** → `POST /api/v1/auth/login` → copy the `access_token`
3. Click **Authorize** (top right) → paste token
4. Start calling endpoints!

### Default Seed Users (after running `python seed.py`)
| Email | Password | Role |
|-------|----------|------|
| admin@finance.com | admin123 | admin |
| analyst@finance.com | analyst123 | analyst |
| viewer@finance.com | viewer123 | viewer |
""",
    openapi_tags=[
        {"name": "Authentication", "description": "Register, login, and get current user"},
        {"name": "User Management", "description": "Admin-only user CRUD and role management"},
        {"name": "Financial Records", "description": "Create, read, update, delete financial transactions"},
        {"name": "Dashboard & Analytics", "description": "Summary stats, trends, and recent activity"},
    ],
    docs_url="/docs",
    redoc_url="/redoc",
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routes
app.include_router(api_router)


@app.get("/", tags=["Health"], summary="Health check")
def root():
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"], summary="Health check")
def health():
    return {"status": "healthy"}


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"success": False, "message": "Internal server error.", "detail": str(exc)},
    )
