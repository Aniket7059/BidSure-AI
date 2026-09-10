import sys
import os
from sqlalchemy import text

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database.session import SessionLocal, engine
from app.database.base import Base
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.core.security import hash_password

def seed_default_users():
    """
    Creates default initial user accounts in the SQLite database if they do not exist.
    """
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    # Ensure is_active column exists on existing SQLite users table
    try:
        db.execute(text("ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT 1"))
        db.commit()
    except Exception:
        db.rollback()

    try:
        # 1. Procurement Officer
        officer = UserRepository.get_by_email(db, "officer@cpcl.gov.in")
        if not officer:
            officer = UserRepository.create(
                db=db,
                full_name="Procurement Officer (CPCL)",
                email="officer@cpcl.gov.in",
                hashed_password=hash_password("Password123!"),
                role="PROCUREMENT_OFFICER",
            )
            print("Successfully created Procurement Officer account: officer@cpcl.gov.in / Password123!")
        else:
            print("Procurement Officer account already exists: officer@cpcl.gov.in")

        # 2. Admin User
        admin = UserRepository.get_by_email(db, "admin@cpcl.gov.in")
        if not admin:
            admin = UserRepository.create(
                db=db,
                full_name="System Administrator",
                email="admin@cpcl.gov.in",
                hashed_password=hash_password("AdminPassword123!"),
                role="ADMIN",
            )
            print("Successfully created Admin account: admin@cpcl.gov.in / AdminPassword123!")
        else:
            print("Admin account already exists: admin@cpcl.gov.in")

    finally:
        db.close()

if __name__ == "__main__":
    seed_default_users()
