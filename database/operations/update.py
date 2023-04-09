from typing import Optional

from sqlalchemy import select, update, func
import sqlalchemy.exc as exc

from database.models import Role, User, Point, Queue, BlackList
from database.config import Session


def transfer(to_user_id: int, amount: int, from_user_id: Optional[int] = None,
             from_user_tg_id: Optional[int] = None) -> bool:
    try:
        with Session.begin() as session:
            result = 0
            if from_user_id is not None:
                result = session.execute(
                    update(User)
                    .where(User.id == from_user_id)
                    .values(balance=User.balance - amount)
                ).rowcount
            elif from_user_tg_id is not None:
                result = session.execute(
                    update(User)
                    .where(User.tg_id == from_user_tg_id)
                    .values(balance=User.balance - amount)
                ).rowcount
            else:
                raise ValueError("Both from_user_id and from_user_tg_id are None!")
            if result != 0:
                result = session.execute(
                    update(User)
                    .where(User.id == to_user_id)
                    .values(balance=User.balance + amount)
                ).rowcount
            if result == 0:
                session.rollback()
    except exc.IntegrityError:
        return False
    except exc.SQLAlchemyError:
        raise ConnectionError("Something wrong with the database!")
    else:
        if result == 0:
            return False
        return True


def host(host_tg_id: int, point_id: int) -> bool:
    try:
        with Session.begin() as session:
            result = session.execute(
                update(Point)
                .where(Point.id == point_id)
                .where(Point.host_tg_id.is_(None))
                .values(host_tg_id=host_tg_id, active=True)
            ).rowcount
    except exc.IntegrityError:
        return False
    except exc.SQLAlchemyError:
        raise ConnectionError("Something wrong with the database!")
    else:
        if result == 0:
            return False
        return True


def payment(host_tg_id: int, amount: int, cash: bool) -> bool:
    try:
        point_id = (
            select(Point.id)
            .where(Point.host_tg_id == host_tg_id)
            .scalar_subquery()
        )
        user_id = (
            select(User.id)
            .join(Queue.team.and_(Queue.point_id == point_id))
            .order_by(Queue.date.asc())
            .limit(1)
            .scalar_subquery()
        )
        with Session.begin() as session:
            result = session.execute(
                update(User)
                .where(User.id == user_id)
                .values(balance=User.balance - amount)
            ).rowcount
            if cash and result != 0:
                result = session.execute(
                    update(Point)
                    .where(Point.host_tg_id == host_tg_id)
                    .values(balance=Point.balance + amount)
                ).rowcount
            if result == 0:
                session.rollback()
    except exc.IntegrityError:
        return False
    except exc.SQLAlchemyError:
        raise ConnectionError("Something wrong with the database!")
    else:
        if result == 0:
            return False
        return True


def pay(host_tg_id: int, user_id: int, amount: int, cash: bool) -> bool:
    try:
        with Session.begin() as session:
            result = session.execute(
                update(User)
                .where(User.id == user_id)
                .values(balance=User.balance + amount, passed_points=User.passed_points + 1)
            ).rowcount
            if cash and result != 0:
                result = session.execute(
                    update(Point)
                    .where(Point.host_tg_id == host_tg_id)
                    .values(balance=Point.balance - amount)
                ).rowcount
            if result == 0:
                session.rollback()
    except exc.IntegrityError:
        return False
    except exc.SQLAlchemyError:
        raise ConnectionError("Something wrong with the database!")
    else:
        if result == 0:
            return False
        return True


def pause(host_tg_id: int) -> bool:
    try:
        with Session.begin() as session:
            result = session.execute(
                update(Point)
                .where(Point.host_tg_id == host_tg_id)
                .where(Point.active.is_(True))
                .values(active=False)
            ).rowcount
    except exc.IntegrityError:
        return False
    except exc.SQLAlchemyError:
        raise ConnectionError("Something wrong with the database!")
    else:
        if result == 0:
            return False
        return True


def resume(host_tg_id: int) -> bool:
    try:
        with Session.begin() as session:
            result = session.execute(
                update(Point)
                .where(Point.host_tg_id == host_tg_id)
                .where(Point.active.is_(False))
                .values(active=True)
            ).rowcount
    except exc.IntegrityError:
        return False
    except exc.SQLAlchemyError:
        raise ConnectionError("Something wrong with the database!")
    else:
        if result == 0:
            return False
        return True
