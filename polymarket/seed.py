"""
Run once to create the first admin user:
  python seed.py
"""
from app.database import SessionLocal
from app.models import User
from app.auth.hashing import hash_password

ADMIN_EMAIL = "admin@example.com"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin1234"
STARTING_BALANCE = 1000.0


def seed():
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == ADMIN_EMAIL).first()
        if existing:
            print(f"Admin already exists: {existing.email}")
            return

        admin = User(
            email=ADMIN_EMAIL,
            username=ADMIN_USERNAME,
            hashed_password=hash_password(ADMIN_PASSWORD),
            balance=STARTING_BALANCE,
            is_admin=True,
            is_active=True,
        )
        db.add(admin)
        db.commit()
        print(f"✓ Admin created: {ADMIN_EMAIL} / {ADMIN_PASSWORD}")
        print(f"  Starting balance: ${STARTING_BALANCE}")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
