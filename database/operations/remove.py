from typing import Optional

from sqlalchemy import delete, select
import sqlalchemy.exc as exc

from database.models import User, Point, Queue, BlackList
from database.config import Session
from database.logger import log


@log
def user(user_id: int) -> bool:
    try:
        with Session.begin() as session:
            result = session.execute(
                delete(User)
                .where(User.id == user_id)
            ).rowcount
        return result != 0
    except exc.IntegrityError:
        return False


@log
def point(point_id: int) -> bool:
    try:
        with Session.begin() as session:
            result = session.execute(
                delete(Point)
                .where(Point.id == point_id)
            ).rowcount
        return result != 0
    except exc.IntegrityError:
        return False


@log
def queue(user_id: Optional[int] = None, tg_id: Optional[int] = None) -> bool:
    try:
        with Session.begin() as session:
            result = 0
            if user_id is not None:
                result = session.execute(
                    delete(Queue)
                    .where(Queue.team_id == user_id)
                ).rowcount
            elif tg_id is not None:
                result = session.execute(
                    delete(Queue)
                    .where(Queue.team_id == select(User.id).where(User.tg_id == tg_id).scalar_subquery())
                ).rowcount
            else:
                raise ValueError("Both user_id and tg_id are None!")
        return result != 0
    except exc.IntegrityError:
        return False


@log
def all_point_queues(point_id: int) -> bool:
    try:
        with Session.begin() as session:
            result = session.execute(
                delete(Queue)
                .where(Queue.point_id == point_id)
            ).rowcount
        return result != 0
    except exc.IntegrityError:
        return False


@log
def blacklist(user_id: int, point_id: int) -> bool:
    try:
        with Session.begin() as session:
            result = session.execute(
                delete(BlackList)
                .where(BlackList.team_id == user_id)
                .where(BlackList.point_id == point_id)
            ).rowcount
        return result != 0
    except exc.IntegrityError:
        return False
