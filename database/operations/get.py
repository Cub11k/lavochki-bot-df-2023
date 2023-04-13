from typing import Optional

from sqlalchemy import select, func
import sqlalchemy.exc as exc

from database.models import Role, User, Point, Queue, BlackList
from database.config import Session
from database.logger import log


@log
def user(tg_id: Optional[int] = None, user_id: Optional[int] = None, name: Optional[str] = None) -> User | None:
    with Session() as session:
        user_ = None
        if user_id is not None:
            user_ = (session.get(User, user_id),)
        elif tg_id is not None:
            user_ = session.execute(
                select(User)
                .where(User.tg_id == tg_id)
            ).first()
        elif name is not None:
            user_ = session.execute(
                select(User)
                .where(User.name == name)
            ).first()
        else:
            raise ValueError("user_id, tg_id and name are None!")
    return user_ if user_ is None else user_[0]


@log
def user_balance(tg_id: int) -> int | None:
    with Session() as session:
        balance = session.execute(
            select(User.balance)
            .where(User.tg_id == tg_id)
        ).first()
    return balance if balance is None else balance[0]


@log
def user_role(tg_id: int) -> Role | None:
    with Session() as session:
        role = session.execute(
            select(User.role)
            .where(User.tg_id == tg_id)
        ).first()
    return role if role is None else role[0]


@log
def user_queue(tg_id: int) -> Queue | None:
    with Session() as session:
        queue = session.execute(
            select(Queue)
            .join(User.queue.and_(User.tg_id == tg_id))
        ).first()
    return queue if queue is None else queue[0]


@log
def user_queue_place(tg_id: int) -> int | None:
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


@log
def all_users(role: Role) -> list[User]:
    with Session() as session:
        users = session.execute(
            select(User)
            .where(User.role == role)
        ).all()
    return [user_[0] for user_ in users]


@log
def point(host_tg_id: Optional[int] = None, point_id: Optional[int] = None, name: Optional[str] = None) -> Point | None:
    with Session() as session:
        if point_id is not None:
            point_ = (session.get(Point, point_id),)
        elif host_tg_id is not None:
            point_ = session.execute(
                select(Point)
                .where(Point.host_tg_id == host_tg_id)
            ).first()
        elif name is not None:
            point_ = session.execute(
                select(Point)
                .where(Point.name == name)
            ).first()
        else:
            raise ValueError("point_id, host_tg_id and name are None!")
    return point_ if point_ is None else point_[0]


@log
def point_next_team(host_tg_id: int) -> User | None:
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


@log
def point_queues(point_id: int) -> list[str, int]:
    with Session() as session:
        queues = session.execute(
            select(User.name, User.id)
            .join(Queue.team.and_(Queue.point_id == point_id))
            .order_by(Queue.date.asc())
        ).all()
    return queues


@log
def point_balance(point_id: int) -> int | None:
    with Session() as session:
        balance = session.execute(
            select(Point.balance)
            .where(Point.id == point_id)
        ).first()
    return balance if balance is None else balance[0]


@log
def point_is_free(point_id: int) -> bool:
    with Session() as session:
        is_free = session.execute(
            select(Queue.point_id)
            .where(Queue.point_id == point_id)
        ).first()
    return is_free is None


@log
def free_points(tg_id: int) -> list[tuple[int, str]]:
    blacklisted_point_ids = (
        select(BlackList.point_id)
        .join(User.blacklist.and_(User.tg_id == tg_id))
        .scalar_subquery()
    )
    with Session() as session:
        points = session.execute(
            select(Point.id, Point.name)
            .select_from(Point)
            .outerjoin(Queue)
            .where(Queue.point_id.is_(None))
            .where(Point.id.notin_(blacklisted_point_ids))
            .where(Point.active.is_(True))
        ).all()
    return points


@log
def all_points() -> list[tuple[int, str, int]]:
    with Session() as session:
        points = session.execute(
            select(Point.name, Point.id, Point.balance)
            .order_by(Point.balance.asc())
        ).all()
    return points


@log
def total_money() -> tuple[int, int]:
    with Session() as session:
        points_total = session.execute(
            select(func.sum(Point.balance))
        ).first()
        users_total = session.execute(
            select(func.sum(User.balance))
            .where(User.role == Role.player)
        ).first()
    return 0 if points_total is None else points_total[0], 0 if users_total is None else users_total[0]
