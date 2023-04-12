from typing import Optional, Literal
from datetime import datetime

from sqlalchemy import select, insert, exists
import sqlalchemy.exc as exc

from database.models import Role, User, Point, Queue, BlackList
from database.config import Session
from database.logger import log


@log
def user(role: Role, name: str, tg_id: Optional[int] = None, balance: Optional[int] = 0) -> int | Literal[False]:
    try:
        with Session.begin() as session:
            result = session.execute(
                insert(User)
                .values(tg_id=tg_id, role=role, name=name, balance=balance)
            ).inserted_primary_key
        return result[0]
    except exc.IntegrityError:
        return False


@log
def point(name: str, one_time: bool, host_tg_id: Optional[int] = None, balance: int = 0) -> int | Literal[False]:
    try:
        with Session.begin() as session:
            result = session.execute(
                insert(Point)
                .values(host_tg_id=host_tg_id, name=name, balance=balance, one_time=one_time)
            ).inserted_primary_key
        return result[0]
    except exc.IntegrityError:
        return False


@log
def queue(point_id: int, date: datetime, user_id: Optional[int] = None, tg_id: Optional[int] = None) -> bool:
    try:
        team_id = None
        if tg_id is not None:
            team_id = (
                select(User.id)
                .where(User.tg_id == tg_id)
                .scalar_subquery()
            )
        elif user_id is not None:
            team_id = user_id
        else:
            raise ValueError("Both tg_id and user_id are None!")
        with Session.begin() as session:
            result = 0
            black_list_exists = session.execute(
                select(
                    exists()
                    .where(BlackList.team_id == team_id)
                    .where(BlackList.point_id == point_id)
                )
            ).scalar()
            point_is_active = session.execute(
                select(Point.active)
                .where(Point.id == point_id)
            ).scalar()
            if point_is_active and not black_list_exists:
                result = session.execute(
                    insert(Queue)
                    .values(team_id=team_id,
                            point_id=point_id,
                            date=date)
                ).rowcount
        return result != 0
    except exc.IntegrityError:
        return False


@log
def blacklist(point_id: int, user_id: Optional[int] = None, tg_id: Optional[int] = None) -> bool:
    try:
        team_id = None
        if tg_id is not None:
            team_id = select(User.id).where(User.tg_id == tg_id).scalar_subquery()
        elif user_id is not None:
            team_id = user_id
        else:
            raise ValueError("Both tg_id and user_id are None!")
        with Session.begin() as session:
            result = session.execute(
                insert(BlackList)
                .values(team_id=team_id,
                        point_id=point_id)
            ).rowcount
        return result != 0
    except exc.IntegrityError:
        return False
