from typing import Optional

import sqlalchemy
import sqlalchemy.exc

from database.models import Role, User, Point, Queue, BlackList
from database.engine import engine


def user(user_id: Optional[int] = None, tg_id: Optional[int] = None) -> User | None:
    if user_id is None and tg_id is None:
        return None
    try:
        with engine.connect() as conn:
            if user_id is not None:
                user_ = conn.execute(sqlalchemy.select(User).where(User.id == user_id)).first()
            else:
                user_ = conn.execute(sqlalchemy.select(User).where(User.tg_id == tg_id)).first()
            return user_ if user_ is None else user_[0]
    except sqlalchemy.exc.SQLAlchemyError:
        return None


def user_balance(user_id: int) -> int | None:
    try:
        with engine.connect() as conn:
            balance = conn.execute(sqlalchemy.select(User.balance).where(User.id == user_id)).first()
        return balance if balance is None else balance[0]
    except sqlalchemy.exc.SQLAlchemyError:
        return None


def point(point_id: Optional[int] = None, host_tg_id: Optional[int] = None) -> Point | None:
    if point_id is None and host_tg_id is None:
        return None
    with engine.connect() as conn:
        if point_id is not None:
            point_ = conn.execute(sqlalchemy.select(Point).where(Point.id == point_id)).first()
        else:
            point_ = conn.execute(sqlalchemy.select(Point).where(Point.host_tg_id == host_tg_id)).first()
        return point_ if point_ is None else point_[0]


def point_balance(point_id: int) -> int | None:
    with engine.connect() as conn:
        balance = conn.execute(sqlalchemy.select(Point.balance).where(Point.id == point_id)).first()
    return balance if balance is None else balance[0]
