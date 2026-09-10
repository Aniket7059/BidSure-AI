from sqlalchemy.orm import Session

from app.core.audit_actions import AuditAction, AuditEntityType
from app.core.security import create_access_token, verify_password
from app.repositories.user_repository import UserRepository
from app.services.audit_log_service import audit_log_service


class AuthService:
    @staticmethod
    def login(
        db: Session,
        email: str,
        password: str,
        ip_address: str | None = None,
    ) -> str | None:
        user = UserRepository.get_by_email(db, email)

        if user is None or not verify_password(password, user.hashed_password):
            audit_log_service.record_event(
                db=db,
                action=AuditAction.AUTH_LOGIN_FAILED,
                entity_type=AuditEntityType.USER,
                entity_id=user.id if user else None,
                details={"email": email, "reason": "Invalid credentials"},
                ip_address=ip_address,
            )
            return None

        token = create_access_token(
            user_id=user.id,
            role=user.role,
        )

        audit_log_service.record_event(
            db=db,
            action=AuditAction.AUTH_LOGIN,
            entity_type=AuditEntityType.USER,
            entity_id=user.id,
            user_id=user.id,
            new_value={"role": user.role, "email": user.email},
            details="User logged in successfully",
            ip_address=ip_address,
        )

        return token