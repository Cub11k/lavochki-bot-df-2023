from typing import Optional

from sqlalchemy import select, update, insert
import sqlalchemy.exc as exc

from database.models import User, Point, BlackList
from database.config import Session
from database.logger import log


@log
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


@log
def host(host_tg_id: int, point_id: Optional[int] = None, remove: Optional[bool] = False) -> bool:
    try:
        with Session.begin() as session:
            if remove is False and point_id is not None:
                result = session.execute(
                    update(Point)
                    .where(Point.id == point_id)
                    .where(Point.host_tg_id.is_(None))
                    .values(host_tg_id=host_tg_id, active=True)
                ).rowcount
            elif remove is True:
                result = session.execute(
                    update(Point)
                    .where(Point.host_tg_id == host_tg_id)
                    .values(host_tg_id=None, active=False)
                ).rowcount
            else:
                raise ValueError("Both point_id is None and remove is False!")
    except exc.IntegrityError:
        return False
    except exc.SQLAlchemyError:
        raise ConnectionError("Something wrong with the database!")
    else:
        if result == 0:
            return False
        return True


@log
def payment(host_tg_id: int, user_id: int, amount: int, cash: bool) -> bool:
    try:
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


@log
def pay(host_tg_id: int, user_id: int, amount: int, cash: bool) -> bool:
    try:
        with Session.begin() as session:
            one_time = session.execute(
                select(Point.one_time)
                .where(Point.host_tg_id == host_tg_id)
            ).scalar()
            result = session.execute(
                update(User)
                .where(User.id == user_id)
                .values(balance=User.balance + amount, passed_points=User.passed_points + 1)
            ).rowcount
            if result != 0 and one_time:
                result = session.execute(
                    insert(BlackList)
                    .values(team_id=user_id,
                            point_id=select(Point.id).where(Point.host_tg_id == host_tg_id))
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


@log
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


@log
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
