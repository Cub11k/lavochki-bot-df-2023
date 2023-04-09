from typing import Optional
from datetime import datetime

from sqlalchemy import select, insert, exists
import sqlalchemy.exc as exc

from database.models import Role, User, Point, Queue, BlackList
from database.config import Session


def user(role: Role, name: str, tg_id: Optional[int] = None) -> int | bool:
    try:
        with Session.begin() as session:
            result = session.execute(
                insert(User)
                .values(tg_id=tg_id, role=role, name=name)
            ).rowcount
    except exc.IntegrityError:
        return False
    except exc.SQLAlchemyError:
        raise ConnectionError("Something wrong with the database!")
    else:
        if result == 0:
            return False
        return True


def point(name: str, one_time: bool, host_tg_id: Optional[int] = None, balance: int = 0) -> bool:
    try:
        with Session.begin() as session:
            result = session.execute(
                insert(Point)
                .values(host_tg_id=host_tg_id, name=name, balance=balance, one_time=one_time)
            ).rowcount
    except exc.IntegrityError:
        return False
    except exc.SQLAlchemyError:
        raise ConnectionError("Something wrong with the database!")
    else:
        if result == 0:
            return False
        return True


def queue(point_id: int, date: datetime, user_id: Optional[int] = None, tg_id: Optional[int] = None) -> bool:
    try:
        team_id = None
        if tg_id is not None:
            team_id = select(User.id).where(User.tg_id == tg_id).scalar_subquery()
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
            if not black_list_exists:
                result = session.execute(
                    insert(Queue)
                    .values(team_id=team_id,
                            point_id=point_id,
                            date=date)
                ).rowcount
    except exc.IntegrityError:
        return False
    except exc.SQLAlchemyError:
        raise ConnectionError("Something wrong with the database!")
    else:
        if result == 0:
            return False
        return True


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
    except exc.IntegrityError:
        return False
    except exc.SQLAlchemyError:
        raise ConnectionError("Something wrong with the database!")
    else:
        if result == 0:
            return False
        return True
