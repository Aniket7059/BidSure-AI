from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:
    """
    Database operations related to users.
    """

    @staticmethod
    def get_by_id(db: Session, user_id: int) -> User | None:
        return (
            db.query(User)
            .filter(User.id == user_id)
            .first()
        )

    @staticmethod
    def get_by_email(db: Session, email: str) -> User | None:
        return (
            db.query(User)
            .filter(User.email == email)
            .first()
        )

    @staticmethod
    def create(
        db: Session,
        full_name: str,
        email: str,
        hashed_password: str,
        role: str = "PROCUREMENT_OFFICER",
    ) -> User:
        user = User(
            full_name=full_name,
            email=email,
            hashed_password=hashed_password,
            role=role,
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        return user