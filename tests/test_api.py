"""
Test suite for Finance Backend API.
Run: pytest tests/ -v
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.session import Base, get_db

# Use in-memory SQLite for tests
TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

# Create tables
Base.metadata.create_all(bind=engine)

client = TestClient(app)


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def clean_db():
    """Wipe tables before each test for isolation."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture
def admin_token():
    client.post("/api/v1/auth/register", json={
        "name": "Admin User", "email": "admin@test.com",
        "password": "admin123", "role": "admin",
    })
    res = client.post("/api/v1/auth/login", json={"email": "admin@test.com", "password": "admin123"})
    return res.json()["access_token"]


@pytest.fixture
def analyst_token():
    client.post("/api/v1/auth/register", json={
        "name": "Analyst User", "email": "analyst@test.com",
        "password": "analyst123", "role": "analyst",
    })
    res = client.post("/api/v1/auth/login", json={"email": "analyst@test.com", "password": "analyst123"})
    return res.json()["access_token"]


@pytest.fixture
def viewer_token():
    client.post("/api/v1/auth/register", json={
        "name": "Viewer User", "email": "viewer@test.com",
        "password": "viewer123", "role": "viewer",
    })
    res = client.post("/api/v1/auth/login", json={"email": "viewer@test.com", "password": "viewer123"})
    return res.json()["access_token"]


@pytest.fixture
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def analyst_headers(analyst_token):
    return {"Authorization": f"Bearer {analyst_token}"}


@pytest.fixture
def viewer_headers(viewer_token):
    return {"Authorization": f"Bearer {viewer_token}"}


@pytest.fixture
def sample_record(admin_headers):
    res = client.post("/api/v1/records/", json={
        "amount": 5000.00, "type": "income",
        "category": "Salary", "date": "2026-01-15",
        "notes": "Test record",
    }, headers=admin_headers)
    return res.json()["data"]


# ── Health ────────────────────────────────────────────────────────────────────

def test_health_check():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"


def test_root():
    res = client.get("/")
    assert res.status_code == 200
    assert "docs" in res.json()


# ── Auth ──────────────────────────────────────────────────────────────────────

def test_register_success():
    res = client.post("/api/v1/auth/register", json={
        "name": "Test User", "email": "test@test.com",
        "password": "pass123", "role": "viewer",
    })
    assert res.status_code == 201
    data = res.json()
    assert data["success"] is True
    assert data["data"]["email"] == "test@test.com"
    assert data["data"]["role"] == "viewer"
    assert "access_token" in data


def test_register_duplicate_email():
    payload = {"name": "User", "email": "dup@test.com", "password": "pass123"}
    client.post("/api/v1/auth/register", json=payload)
    res = client.post("/api/v1/auth/register", json=payload)
    assert res.status_code == 409


def test_register_invalid_password():
    res = client.post("/api/v1/auth/register", json={
        "name": "User", "email": "u@test.com", "password": "123",
    })
    assert res.status_code == 422


def test_login_success(admin_token):
    assert admin_token is not None and len(admin_token) > 10


def test_login_wrong_password():
    client.post("/api/v1/auth/register", json={
        "name": "User", "email": "x@test.com", "password": "correct",
    })
    res = client.post("/api/v1/auth/login", json={"email": "x@test.com", "password": "wrong"})
    assert res.status_code == 401


def test_get_me(admin_headers):
    res = client.get("/api/v1/auth/me", headers=admin_headers)
    assert res.status_code == 200
    assert res.json()["data"]["email"] == "admin@test.com"


def test_get_me_no_token():
    res = client.get("/api/v1/auth/me")
    assert res.status_code == 401


# ── Records ───────────────────────────────────────────────────────────────────

def test_create_record_admin(admin_headers):
    res = client.post("/api/v1/records/", json={
        "amount": 1000.00, "type": "income",
        "category": "Salary", "date": "2026-01-01",
    }, headers=admin_headers)
    assert res.status_code == 201
    assert res.json()["data"]["amount"] == 1000.0


def test_create_record_viewer_forbidden(viewer_headers):
    res = client.post("/api/v1/records/", json={
        "amount": 1000.00, "type": "income",
        "category": "Salary", "date": "2026-01-01",
    }, headers=viewer_headers)
    assert res.status_code == 403


def test_create_record_analyst_forbidden(analyst_headers):
    res = client.post("/api/v1/records/", json={
        "amount": 1000.00, "type": "income",
        "category": "Salary", "date": "2026-01-01",
    }, headers=analyst_headers)
    assert res.status_code == 403


def test_create_record_negative_amount(admin_headers):
    res = client.post("/api/v1/records/", json={
        "amount": -500, "type": "income",
        "category": "Salary", "date": "2026-01-01",
    }, headers=admin_headers)
    assert res.status_code == 422


def test_list_records_viewer(viewer_headers, sample_record):
    res = client.get("/api/v1/records/", headers=viewer_headers)
    assert res.status_code == 200
    assert res.json()["pagination"]["total"] == 1


def test_filter_records_by_type(admin_headers, sample_record):
    res = client.get("/api/v1/records/?type=income", headers=admin_headers)
    assert res.status_code == 200
    for r in res.json()["data"]:
        assert r["type"] == "income"


def test_filter_records_by_date_range(admin_headers, sample_record):
    res = client.get("/api/v1/records/?date_from=2026-01-01&date_to=2026-01-31", headers=admin_headers)
    assert res.status_code == 200
    assert res.json()["pagination"]["total"] >= 1


def test_get_record_by_id(admin_headers, sample_record):
    res = client.get(f"/api/v1/records/{sample_record['id']}", headers=admin_headers)
    assert res.status_code == 200
    assert res.json()["data"]["id"] == sample_record["id"]


def test_get_record_not_found(admin_headers):
    res = client.get("/api/v1/records/nonexistent-id", headers=admin_headers)
    assert res.status_code == 404


def test_update_record(admin_headers, sample_record):
    res = client.patch(f"/api/v1/records/{sample_record['id']}",
        json={"amount": 9999.00, "notes": "Updated"},
        headers=admin_headers,
    )
    assert res.status_code == 200
    assert res.json()["data"]["amount"] == 9999.0
    assert res.json()["data"]["notes"] == "Updated"


def test_delete_record(admin_headers, sample_record):
    res = client.delete(f"/api/v1/records/{sample_record['id']}", headers=admin_headers)
    assert res.status_code == 200
    # Verify soft delete - record should not appear in list
    res2 = client.get("/api/v1/records/", headers=admin_headers)
    assert res2.json()["pagination"]["total"] == 0


def test_delete_record_viewer_forbidden(viewer_headers, sample_record):
    res = client.delete(f"/api/v1/records/{sample_record['id']}", headers=viewer_headers)
    assert res.status_code == 403


# ── Dashboard ─────────────────────────────────────────────────────────────────

def test_overview_viewer(viewer_headers, sample_record):
    res = client.get("/api/v1/dashboard/overview", headers=viewer_headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert "total_income" in data
    assert "net_balance" in data
    assert data["total_income"] == 5000.0


def test_summary_analyst(analyst_headers, sample_record):
    res = client.get("/api/v1/dashboard/summary", headers=analyst_headers)
    assert res.status_code == 200
    assert "category_breakdown" in res.json()["data"]


def test_summary_viewer_forbidden(viewer_headers):
    res = client.get("/api/v1/dashboard/summary", headers=viewer_headers)
    assert res.status_code == 403


def test_trends_monthly(analyst_headers, sample_record):
    res = client.get("/api/v1/dashboard/trends?period=monthly", headers=analyst_headers)
    assert res.status_code == 200
    assert res.json()["data"]["period_type"] == "monthly"


def test_trends_invalid_period(analyst_headers):
    res = client.get("/api/v1/dashboard/trends?period=daily", headers=analyst_headers)
    assert res.status_code == 400


def test_recent_activity(analyst_headers, sample_record):
    res = client.get("/api/v1/dashboard/recent", headers=analyst_headers)
    assert res.status_code == 200
    assert len(res.json()["data"]) == 1


# ── User Management ───────────────────────────────────────────────────────────

def test_list_users_admin(admin_headers):
    res = client.get("/api/v1/users/", headers=admin_headers)
    assert res.status_code == 200
    assert res.json()["pagination"]["total"] >= 1


def test_list_users_viewer_forbidden(viewer_headers):
    res = client.get("/api/v1/users/", headers=viewer_headers)
    assert res.status_code == 403


def test_update_user_role(admin_headers, viewer_token):
    # Get viewer user id
    me_res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {viewer_token}"})
    user_id = me_res.json()["data"]["id"]

    res = client.patch(f"/api/v1/users/{user_id}",
        json={"role": "analyst"},
        headers=admin_headers,
    )
    assert res.status_code == 200
    assert res.json()["data"]["role"] == "analyst"


def test_admin_cannot_deactivate_self(admin_headers):
    me_res = client.get("/api/v1/auth/me", headers=admin_headers)
    user_id = me_res.json()["data"]["id"]
    res = client.patch(f"/api/v1/users/{user_id}",
        json={"status": "inactive"},
        headers=admin_headers,
    )
    assert res.status_code == 400
