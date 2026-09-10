from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.security import (
    bearer_scheme,
    get_user_id_from_token,
)
from app.database.session import get_db
from app.models.user import User
from app.repositories.user_repository import UserRepository


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:

    token = credentials.credentials

    user_id = get_user_id_from_token(token)

    user = UserRepository.get_by_id(
        db=db,
        user_id=user_id,
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    if not getattr(user, "is_active", True):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive",
        )

    return user


class RoleChecker:
    """
    Dependency helper to enforce role-based access control (RBAC).
    """

    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = allowed_roles

    def __call__(
        self,
        current_user: User = Depends(get_current_user),
    ) -> User:
        if current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operation not permitted for current user role",
            )
        return current_user


def require_role(*allowed_roles: str):
    """
    Returns a RoleChecker dependency for the specified allowed roles.
    Example: require_role("ADMIN", "PROCUREMENT_OFFICER")
    """
    return RoleChecker(list(allowed_roles))