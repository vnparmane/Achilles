import hashlib

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.database.models.user import User


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


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
        if user.password_hash != _hash_password(password):
            return None
        return user

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
