from typing import Optional
from datetime import datetime

import sqlalchemy
import sqlalchemy.exc

from database.models import Role, User, Point, Queue, BlackList
from database.engine import engine


def user(role: Role, name: str, tg_id: Optional[int] = None) -> bool:
    try:
        with engine.begin() as conn:
            conn.execute(sqlalchemy.insert(User).values(tg_id=tg_id, role=role, name=name))
    except sqlalchemy.exc.SQLAlchemyError:
        return False
    return True


def point(name: str, one_time: bool, host_tg_id: Optional[int] = None, balance: int = 0) -> bool:
    try:
        with engine.begin() as conn:
            conn.execute(sqlalchemy.insert(Point).values(host_tg_id=host_tg_id, name=name, balance=balance,
                                                         one_time=one_time))
    except sqlalchemy.exc.SQLAlchemyError:
        return False
    return True


def queue(user_id: int, point_id: int, date: datetime) -> bool:
    try:
        with engine.begin() as conn:
            conn.execute(sqlalchemy.insert(Queue).values(team_id=user_id, point_id=point_id, date=date))
    except sqlalchemy.exc.SQLAlchemyError:
        return False
    return True


def blacklist(user_id: int, point_id: int) -> bool:
    try:
        with engine.begin() as conn:
            conn.execute(sqlalchemy.insert(BlackList).values(team_id=user_id, point_id=point_id))
    except sqlalchemy.exc.SQLAlchemyError:
        return False
    return True
