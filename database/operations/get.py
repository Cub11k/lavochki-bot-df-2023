from typing import Optional

from sqlalchemy import select, func
import sqlalchemy.exc as exc

from database.models import Role, User, Point, Queue, BlackList
from database.config import Session


def user(tg_id: Optional[int] = None, user_id: Optional[int] = None) -> User | None:
    try:
        with Session() as session:
            user_ = None
            if user_id is not None:
                user_ = session.get(User, user_id)
            elif tg_id is not None:
                user_ = session.execute(
                    select(User)
                    .where(User.tg_id == tg_id)
                ).first()
            else:
                raise ValueError("Both user_id and tg_id are None!")
        return user_ if user_ is None else user_[0]
    except exc.SQLAlchemyError:
        raise ConnectionError("Something wrong with the database while get.user!")


def user_balance(tg_id: int) -> int | None:
    try:
        with Session() as session:
            balance = session.execute(
                select(User.balance)
                .where(User.tg_id == tg_id)
            ).first()
        return balance if balance is None else balance[0]
    except exc.SQLAlchemyError:
        raise ConnectionError("Something wrong with the database while get.user_balance!")


def user_role(tg_id: int) -> Role | None:
    try:
        with Session() as session:
            role = session.execute(
                select(User.role)
                .where(User.tg_id == tg_id)
            ).first()
        return role if role is None else role[0]
    except exc.SQLAlchemyError:
        raise ConnectionError("Something wrong with the database while get.user_role!")


def user_queue(tg_id: int) -> Queue | None:
    try:
        with Session() as session:
            queue = session.execute(
                select(Queue)
                .join(User.queue.and_(User.tg_id == tg_id))
            ).first()
        return queue if queue is None else queue[0]
    except exc.SQLAlchemyError:
        raise ConnectionError("Something wrong with the database while get.user_queue!")


def user_queue_place(tg_id: int) -> int | None:
    try:
        date = (
            select(Queue.date)
            .join(User.queue.and_(User.tg_id == tg_id))
            .scalar_subquery()
        )
        point_id = (
            select(Queue.point_id)
            .join(User.queue.and_(User.tg_id == tg_id))
            .scalar_subquery()
        )
        main = (
            select(func.count())
            .select_from(Queue)
            .where(Queue.date <= date)
            .where(Queue.point_id == point_id)
        )
        with Session() as session:
            place = session.execute(main).first()
        return place if place is None else place[0]
    except exc.SQLAlchemyError:
        raise ConnectionError("Something wrong with the database while get.user_queue_place!")


def point(host_tg_id: Optional[int] = None, point_id: Optional[int] = None) -> Point | None:
    try:
        with Session() as session:
            if point_id is not None:
                point_ = session.get(Point, point_id)
            elif host_tg_id is not None:
                point_ = session.execute(
                    select(Point)
                    .where(Point.host_tg_id == host_tg_id)
                ).first()
            else:
                raise ValueError("Both point_id and host_tg_id are None!")
        return point_ if point_ is None else point_[0]
    except exc.SQLAlchemyError:
        raise ConnectionError("Something wrong with the database while get.point!")


def point_next_team(host_tg_id: int) -> User | None:
    try:
        point_id = (
            select(Point.id)
            .where(Point.host_tg_id == host_tg_id)
            .scalar_subquery()
        )
        with Session() as session:
            user_ = session.execute(
                select(User)
                .join(Queue.team.and_(Queue.point_id == point_id))
                .order_by(Queue.date.asc())
                .limit(1)
            ).first()
        return user_ if user_ is None else user_[0]
    except exc.SQLAlchemyError:
        raise ConnectionError("Something wrong with the database while get.point_queue!")


def point_balance(point_id: int) -> int | None:
    try:
        with Session() as session:
            balance = session.execute(
                select(Point.balance)
                .where(Point.id == point_id)
            ).first()
        return balance if balance is None else balance[0]
    except exc.SQLAlchemyError:
        raise ConnectionError("Something wrong with the database while get.point_balance!")


def free_points(tg_id: int) -> list[tuple[int, str]]:
    try:
        blacklisted_point_ids = (
            select(BlackList.point_id)
            .join(User.blacklist.and_(User.tg_id == tg_id))
            .scalar_subquery()
        )
        with Session() as session:
            points = session.execute(
                select(Point.id, Point.name)
                .outerjoin(Queue.point)
                .where(Queue.point_id.is_(None))
                .where(Point.id.notin_(blacklisted_point_ids))
                .where(Point.active.is_(True))
            ).all()
        return [point_[0] for point_ in points]
    except exc.SQLAlchemyError:
        raise ConnectionError("Something wrong with the database while get.free_points!")


def all_points() -> list[tuple[int, str]]:
    try:
        with Session() as session:
            points = session.execute(
                select(Point.id, Point.name)
            ).all()
        return [point_[0] for point_ in points]
    except exc.SQLAlchemyError:
        raise ConnectionError("Something wrong with the database while get.all_points!")
