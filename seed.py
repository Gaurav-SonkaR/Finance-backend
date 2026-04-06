"""
Seed script — creates default users and sample financial records.

Usage:
    python seed.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db.session import SessionLocal, engine, Base
from app.models.user import User, UserRole, UserStatus
from app.models.financial_record import FinancialRecord, RecordType
from app.core.security import hash_password
from datetime import date
import uuid


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # ── Users ────────────────────────────────────────────────────────────
        users_data = [
            {"name": "Admin User",    "email": "admin@finance.com",   "password": "admin123",   "role": UserRole.admin},
            {"name": "Alice Analyst", "email": "analyst@finance.com", "password": "analyst123", "role": UserRole.analyst},
            {"name": "Victor Viewer", "email": "viewer@finance.com",  "password": "viewer123",  "role": UserRole.viewer},
        ]

        created_users = {}
        for u in users_data:
            existing = db.query(User).filter(User.email == u["email"]).first()
            if not existing:
                user = User(
                    id=str(uuid.uuid4()),
                    name=u["name"],
                    email=u["email"],
                    hashed_password=hash_password(u["password"]),
                    role=u["role"],
                    status=UserStatus.active,
                )
                db.add(user)
                db.flush()
                created_users[u["email"]] = user
                print(f"  Created user: {u['email']} [{u['role'].value}]")
            else:
                created_users[u["email"]] = existing
                print(f"  Skipped (exists): {u['email']}")

        db.commit()

        admin = created_users["admin@finance.com"]

        # ── Financial Records ─────────────────────────────────────────────────
        if db.query(FinancialRecord).count() > 0:
            print("  Records already seeded, skipping.")
        else:
            records_data = [
                # Income
                {"amount": 85000.00, "type": RecordType.income,  "category": "Salary",      "date": date(2026, 1, 1),  "notes": "Monthly salary - January"},
                {"amount": 85000.00, "type": RecordType.income,  "category": "Salary",      "date": date(2026, 2, 1),  "notes": "Monthly salary - February"},
                {"amount": 85000.00, "type": RecordType.income,  "category": "Salary",      "date": date(2026, 3, 1),  "notes": "Monthly salary - March"},
                {"amount": 12000.00, "type": RecordType.income,  "category": "Freelance",   "date": date(2026, 1, 15), "notes": "Web development project"},
                {"amount": 8500.00,  "type": RecordType.income,  "category": "Freelance",   "date": date(2026, 2, 20), "notes": "Mobile app consulting"},
                {"amount": 5000.00,  "type": RecordType.income,  "category": "Investment",  "date": date(2026, 1, 31), "notes": "Mutual fund dividend"},
                {"amount": 3200.00,  "type": RecordType.income,  "category": "Investment",  "date": date(2026, 2, 28), "notes": "Stock dividend payout"},
                {"amount": 2500.00,  "type": RecordType.income,  "category": "Rental",      "date": date(2026, 1, 5),  "notes": "Property rental income"},
                {"amount": 2500.00,  "type": RecordType.income,  "category": "Rental",      "date": date(2026, 2, 5),  "notes": "Property rental income"},
                {"amount": 2500.00,  "type": RecordType.income,  "category": "Rental",      "date": date(2026, 3, 5),  "notes": "Property rental income"},
                # Expenses
                {"amount": 18000.00, "type": RecordType.expense, "category": "Rent",        "date": date(2026, 1, 3),  "notes": "Office rent - January"},
                {"amount": 18000.00, "type": RecordType.expense, "category": "Rent",        "date": date(2026, 2, 3),  "notes": "Office rent - February"},
                {"amount": 18000.00, "type": RecordType.expense, "category": "Rent",        "date": date(2026, 3, 3),  "notes": "Office rent - March"},
                {"amount": 4500.00,  "type": RecordType.expense, "category": "Utilities",   "date": date(2026, 1, 10), "notes": "Electricity and internet"},
                {"amount": 4200.00,  "type": RecordType.expense, "category": "Utilities",   "date": date(2026, 2, 10), "notes": "Electricity and internet"},
                {"amount": 4800.00,  "type": RecordType.expense, "category": "Utilities",   "date": date(2026, 3, 10), "notes": "Electricity and internet"},
                {"amount": 9500.00,  "type": RecordType.expense, "category": "Marketing",   "date": date(2026, 1, 20), "notes": "Social media ads campaign"},
                {"amount": 7200.00,  "type": RecordType.expense, "category": "Marketing",   "date": date(2026, 2, 18), "notes": "Google Ads spend"},
                {"amount": 3100.00,  "type": RecordType.expense, "category": "Software",    "date": date(2026, 1, 12), "notes": "SaaS subscriptions (Slack, Notion, GitHub)"},
                {"amount": 3100.00,  "type": RecordType.expense, "category": "Software",    "date": date(2026, 2, 12), "notes": "SaaS subscriptions"},
                {"amount": 3100.00,  "type": RecordType.expense, "category": "Software",    "date": date(2026, 3, 12), "notes": "SaaS subscriptions"},
                {"amount": 6800.00,  "type": RecordType.expense, "category": "Salaries",    "date": date(2026, 1, 31), "notes": "Part-time staff payroll"},
                {"amount": 6800.00,  "type": RecordType.expense, "category": "Salaries",    "date": date(2026, 2, 28), "notes": "Part-time staff payroll"},
                {"amount": 1200.00,  "type": RecordType.expense, "category": "Travel",      "date": date(2026, 1, 25), "notes": "Client visit - Mumbai"},
                {"amount": 2400.00,  "type": RecordType.expense, "category": "Travel",      "date": date(2026, 2, 22), "notes": "Conference - Bangalore"},
                {"amount": 850.00,   "type": RecordType.expense, "category": "Office",      "date": date(2026, 1, 8),  "notes": "Stationery and supplies"},
                {"amount": 1100.00,  "type": RecordType.expense, "category": "Office",      "date": date(2026, 3, 8),  "notes": "Office furniture"},
            ]

            for r in records_data:
                record = FinancialRecord(
                    id=str(uuid.uuid4()),
                    amount=r["amount"],
                    type=r["type"],
                    category=r["category"],
                    date=r["date"],
                    notes=r["notes"],
                    created_by=admin.id,
                )
                db.add(record)

            db.commit()
            print(f"  Created {len(records_data)} financial records.")

        print("\nSeed complete!")
        print("\nDefault login credentials:")
        print("  admin@finance.com    / admin123   (admin)")
        print("  analyst@finance.com  / analyst123 (analyst)")
        print("  viewer@finance.com   / viewer123  (viewer)")

    except Exception as e:
        db.rollback()
        print(f"Seed failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("Seeding database...")
    seed()
