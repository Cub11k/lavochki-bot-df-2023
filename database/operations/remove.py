from typing import Optional

from sqlalchemy import delete, func
import sqlalchemy.exc as exc

from database.models import User, Point, Queue, BlackList
from database.config import Session


def user(user_id: int) -> bool:
    try:
        with Session.begin() as session:
            result = session.execute(
                delete(User)
                .where(User.id == user_id)
            ).rowcount
    except exc.IntegrityError:
        return False
    except exc.SQLAlchemyError:
        raise ConnectionError("Something wrong with the database!")
    else:
        if result == 0:
            return False
        return True


def point(point_id: int) -> bool:
    try:
        with Session.begin() as session:
            result = session.execute(
                delete(Point)
                .where(Point.id == point_id)
            ).rowcount
    except exc.IntegrityError:
        return False
    except exc.SQLAlchemyError:
        raise ConnectionError("Something wrong with the database!")
    else:
        if result == 0:
            return False
        return True


def queue(user_id: Optional[int] = None, tg_id: Optional[int] = None) -> bool:
    try:
        join_clause = None
        if user_id is not None:
            join_clause = User.queue.and_(User.id == user_id)
        elif tg_id is not None:
            join_clause = User.queue.and_(User.tg_id == tg_id)
        else:
            raise ValueError("Both user_id and tg_id are None!")
        with Session.begin() as session:
            result = session.execute(
                delete(Queue)
                .join(join_clause)
            ).rowcount
    except exc.IntegrityError:
        return False
    except exc.SQLAlchemyError:
        raise ConnectionError("Something wrong with the database!")
    else:
        if result == 0:
            return False
        return True


def all_point_queues(point_id: int) -> bool:
    try:
        with Session.begin() as session:
            result = session.execute(
                delete(Queue)
                .where(Queue.point_id == point_id)
            ).rowcount
    except exc.IntegrityError:
        return False
    except exc.SQLAlchemyError:
        raise ConnectionError("Something wrong with the database!")
    else:
        if result == 0:
            return False
        return True


def blacklist(user_id: int, point_id: int) -> bool:
    try:
        with Session.begin() as session:
            result = session.execute(
                delete(BlackList)
                .where(BlackList.team_id == user_id)
                .where(BlackList.point_id == point_id)
            ).rowcount
    except exc.IntegrityError:
        return False
    except exc.SQLAlchemyError:
        raise ConnectionError("Something wrong with the database!")
    else:
        if result == 0:
            return False
        return True
