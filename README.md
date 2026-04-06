# Finance Data Processing and Access Control Backend

A production-ready RESTful API built with **FastAPI**, **SQLAlchemy**, and **SQLite** for managing financial records with role-based access control.

**Assignment by:** Gaurav Sonkar | Zorvyn FinTech Pvt. Ltd.

---

## Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| Framework | FastAPI | Auto Swagger docs, Pydantic validation, fast development |
| ORM | SQLAlchemy 2.0 | Clean models, easy switch to PostgreSQL later |
| Database | SQLite | Zero-config, perfect for assignment/demo |
| Auth | JWT (python-jose) | Stateless, industry standard |
| Password | passlib + bcrypt | Secure hashing |
| Rate Limiting | slowapi | Prevent abuse |
| Testing | pytest + httpx | Reliable test coverage |

> **Database note:** SQLite is used for simplicity and zero-config setup. Switching to PostgreSQL requires only changing `DATABASE_URL` in `.env` — no code changes needed.

---

## Project Structure

```
finance-backend/
├── app/
│   ├── api/v1/
│   │   ├── endpoints/
│   │   │   ├── auth.py          # Register, login, /me
│   │   │   ├── users.py         # User management (Admin only)
│   │   │   ├── records.py       # Financial records CRUD
│   │   │   └── dashboard.py     # Analytics & summary
│   │   └── router.py            # All routes combined
│   ├── core/
│   │   ├── config.py            # Settings from .env
│   │   └── security.py          # JWT + bcrypt helpers
│   ├── db/
│   │   └── session.py           # SQLAlchemy engine + session
│   ├── middleware/
│   │   └── auth.py              # JWT auth + role guards
│   ├── models/
│   │   ├── user.py              # User ORM model
│   │   └── financial_record.py  # FinancialRecord ORM model
│   ├── schemas/
│   │   └── schemas.py           # Pydantic request/response schemas
│   ├── services/
│   │   ├── auth_service.py      # Register/login business logic
│   │   ├── user_service.py      # User management logic
│   │   ├── record_service.py    # Financial record logic
│   │   └── dashboard_service.py # Analytics queries
│   └── main.py                  # FastAPI app + startup
├── tests/
│   └── test_api.py              # 31 automated tests
├── seed.py                      # Seed default users + sample data
├── requirements.txt
├── Procfile                     # For Railway/Render deployment
├── .env
└── README.md
```

---

## Role-Based Access Control

| Endpoint | Viewer | Analyst | Admin |
|----------|--------|---------|-------|
| GET /dashboard/overview | YES | YES | YES |
| GET /records | YES | YES | YES |
| GET /records/:id | YES | YES | YES |
| GET /dashboard/summary | NO | YES | YES |
| GET /dashboard/trends | NO | YES | YES |
| GET /dashboard/recent | NO | YES | YES |
| POST /records | NO | NO | YES |
| PATCH /records/:id | NO | NO | YES |
| DELETE /records/:id | NO | NO | YES |
| GET /users | NO | NO | YES |
| PATCH /users/:id | NO | NO | YES |
| DELETE /users/:id | NO | NO | YES |

---

## Local Setup & Run

### Prerequisites
- Python 3.10+
- pip

### Step 1 — Clone and enter the project

```bash
git clone https://github.com/YOUR_USERNAME/finance-backend.git
cd finance-backend
```

### Step 2 — Create virtual environment

```bash
python -m venv venv

# On Windows:
venv\Scripts\activate

# On Mac/Linux:
source venv/bin/activate
```

### Step 3 — Install dependencies

```bash
pip install -r requirements.txt
```

### Step 4 — Configure environment

```bash
cp .env.example .env
```

Edit `.env` if needed (defaults work out of the box):
```
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///./finance.db
```

### Step 5 — Seed the database

```bash
python seed.py
```

This creates 3 default users and 27 sample financial records.

### Step 6 — Run the server

```bash
uvicorn app.main:app --reload
```

Server starts at: **http://localhost:8000**

### Step 7 — Open Swagger UI

Visit **http://localhost:8000/docs** in your browser.

---

## Default Login Credentials (after seed)

| Email | Password | Role |
|-------|----------|------|
| admin@finance.com | admin123 | admin |
| analyst@finance.com | analyst123 | analyst |
| viewer@finance.com | viewer123 | viewer |

---

## API Quick Reference

### Authentication

```bash
# Register
POST /api/v1/auth/register
{
  "name": "John Doe",
  "email": "john@example.com",
  "password": "secret123",
  "role": "viewer"    # viewer | analyst | admin
}

# Login
POST /api/v1/auth/login
{
  "email": "admin@finance.com",
  "password": "admin123"
}
# Returns: { "access_token": "eyJ..." }

# Get current user
GET /api/v1/auth/me
Authorization: Bearer <token>
```

### Financial Records

```bash
# List records (with filters)
GET /api/v1/records/
GET /api/v1/records/?type=income
GET /api/v1/records/?category=Salary
GET /api/v1/records/?date_from=2026-01-01&date_to=2026-03-31
GET /api/v1/records/?search=rent&page=1&limit=10

# Create record (Admin only)
POST /api/v1/records/
{
  "amount": 50000.00,
  "type": "income",        # income | expense
  "category": "Salary",
  "date": "2026-04-01",
  "notes": "Monthly salary"
}

# Update record (Admin only)
PATCH /api/v1/records/{id}
{ "amount": 55000.00 }

# Soft delete (Admin only)
DELETE /api/v1/records/{id}
```

### Dashboard Analytics

```bash
# Overview - all roles
GET /api/v1/dashboard/overview

# Detailed summary with category breakdown - analyst/admin
GET /api/v1/dashboard/summary
GET /api/v1/dashboard/summary?date_from=2026-01-01&date_to=2026-03-31

# Monthly/weekly trends - analyst/admin
GET /api/v1/dashboard/trends?period=monthly
GET /api/v1/dashboard/trends?period=weekly

# Recent activity - analyst/admin
GET /api/v1/dashboard/recent?limit=10
```

### User Management (Admin only)

```bash
# List users
GET /api/v1/users/
GET /api/v1/users/?role=viewer&status=active

# Update user role or status
PATCH /api/v1/users/{id}
{ "role": "analyst", "status": "active" }

# Delete user
DELETE /api/v1/users/{id}
```

---

## Running Tests

```bash
pytest tests/ -v
```

Expected: **31 passed**

Tests cover:
- Health check
- Registration, login, invalid credentials
- Role-based access control (viewer/analyst/admin)
- CRUD for financial records
- Input validation (negative amounts, missing fields)
- Soft delete behaviour
- Dashboard endpoints with role guards
- User management

---

## Deployment on Railway (Free)

### Step 1 — Push to GitHub
```bash
git init
git add .
git commit -m "Finance backend - Zorvyn assignment"
git push origin main
```

### Step 2 — Deploy on Railway
1. Go to [railway.app](https://railway.app)
2. Click **New Project** → **Deploy from GitHub**
3. Select your repository
4. Railway auto-detects Python and reads `Procfile`

### Step 3 — Set environment variables in Railway dashboard
```
SECRET_KEY=your-production-secret-key-here
DATABASE_URL=sqlite:///./finance.db
```

### Step 4 — Seed the database (one-time)
In Railway dashboard → your service → **Shell**:
```bash
python seed.py
```

### Step 5 — Get your public URL
Railway provides: `https://your-app.up.railway.app`

Submit: `https://your-app.up.railway.app/docs`

---

## Switching to PostgreSQL (optional)

No code changes needed. Just update `.env`:

```
DATABASE_URL=postgresql://user:password@host:5432/finance_db
```

And install the driver:
```bash
pip install psycopg2-binary
```

---

## Assumptions & Design Decisions

1. **SQLite for storage** — chosen for zero-config simplicity. SQLAlchemy ORM ensures easy switch to PostgreSQL by changing only `DATABASE_URL`.

2. **Soft delete** — records are marked `is_deleted=True` instead of being removed, preserving audit history.

3. **JWT expiry** — set to 7 days for convenience during evaluation. Production would use shorter-lived tokens + refresh tokens.

4. **Role assignment on register** — the `role` field is accepted during registration for testing convenience. In production, only admins should assign elevated roles.

5. **Rate limiting** — set to 200 requests/minute per IP using `slowapi`. Easily tunable.

6. **CORS** — set to `allow_origins=["*"]` for easy frontend integration during evaluation. Should be restricted in production.

---

## API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
