import sqlalchemy
import sqlalchemy.exc

from database.models import User, Point, Queue, BlackList
from database.engine import engine


def user(user_id: int) -> bool:
    try:
        with engine.begin() as conn:
            conn.execute(sqlalchemy.delete(User).where(User.id == user_id))
    except sqlalchemy.exc.SQLAlchemyError:
        return False
    return True


def point(point_id: int) -> bool:
    try:
        with engine.begin() as conn:
            conn.execute(sqlalchemy.delete(Point).where(Point.id == point_id))
    except sqlalchemy.exc.SQLAlchemyError:
        return False
    return True


def queue(user_id: int, point_id: int) -> bool:
    try:
        with engine.begin() as conn:
            conn.execute(sqlalchemy.delete(Queue).where(Queue.team_id == user_id).where(Queue.point_id == point_id))
    except sqlalchemy.exc.SQLAlchemyError:
        return False
    return True


def blacklist(user_id: int, point_id: int) -> bool:
    try:
        with engine.begin() as conn:
            conn.execute(
                sqlalchemy.delete(BlackList).where(BlackList.team_id == user_id).where(BlackList.point_id == point_id))
    except sqlalchemy.exc.SQLAlchemyError:
        return False
    return True
