import hashlib

import bcrypt

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.database.models.user import User


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def _check_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), password_hash.encode())
    except ValueError:
        return False


def _is_sha256_hash(h: str) -> bool:
    return len(h) == 64 and all(c in "0123456789abcdef" for c in h)


class UserService:
    def __init__(self, session: Session):
        self.session = session

    def authenticate(self, username: str, password: str) -> User | None:
        user = self.session.scalar(
            select(User).where(
                User.username == username,
                User.is_active,
            )
        )
        if user is None:
            return None
        if _check_password(password, user.password_hash):
            return user
        if _is_sha256_hash(user.password_hash):
            if user.password_hash == hashlib.sha256(password.encode()).hexdigest():
                user.password_hash = _hash_password(password)
                self.session.commit()
                return user
        return None

    def create_user(
        self,
        username: str,
        password: str,
        display_name: str,
        role: str,
    ) -> User:
        user = User(
            username=username,
            password_hash=_hash_password(password),
            display_name=display_name,
            role=role,
        )
        self.session.add(user)
        self.session.commit()
        return user

    def get_all_users(self) -> list[User]:
        return list(self.session.scalars(select(User).order_by(User.display_name)).all())

    def get_user_by_id(self, user_id: int) -> User | None:
        return self.session.get(User, user_id)

    def update_user(self, user_id: int, **kwargs) -> User | None:
        user = self.session.get(User, user_id)
        if user is None:
            return None
        if "password" in kwargs:
            kwargs["password_hash"] = _hash_password(kwargs.pop("password"))
        for key, value in kwargs.items():
            setattr(user, key, value)
        self.session.commit()
        return user