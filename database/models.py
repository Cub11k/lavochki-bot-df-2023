from enum import IntEnum

from sqlalchemy import Boolean, Integer, BigInteger, String, DateTime, Enum, Identity, ForeignKey
from sqlalchemy import CheckConstraint

from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship


class Role(IntEnum):
    player = 0
    host = 1
    admin = 2


class BaseModel(DeclarativeBase):
    pass


class User(BaseModel):
    __tablename__ = 'users'

    id = mapped_column(Integer, Identity(start=10, increment=3), primary_key=True)
    tg_id = mapped_column(BigInteger, unique=True, nullable=True)
    role = mapped_column(Enum(Role), nullable=False)
    name = mapped_column(String(255), unique=True, nullable=False)
    balance = mapped_column(Integer, CheckConstraint('balance >= 0'), default=0, nullable=False)
    passed_points = mapped_column(Integer, CheckConstraint('passed_points >= 0'), default=0, nullable=False)

    point = relationship('Point', back_populates='host')
    queue = relationship('Queue', back_populates='team')
    blacklist = relationship('BlackList', back_populates='team')

    __table_args__ = (
        CheckConstraint('(tg_id is null and role = \'player\') or tg_id is not null'),
    )


class Point(BaseModel):
    __tablename__ = 'points'

    id = mapped_column(Integer, Identity(start=1, increment=1), primary_key=True)
    host_tg_id = mapped_column(BigInteger, ForeignKey('users.tg_id'), unique=True, nullable=True)
    active = mapped_column(Boolean, default=False, nullable=False)
    name = mapped_column(String(255), unique=True, nullable=False)
    balance = mapped_column(Integer, CheckConstraint('balance >= 0'), default=0, nullable=False)
    one_time = mapped_column(Boolean, nullable=False)

    host = relationship('User', back_populates='point')
    queues = relationship('Queue', back_populates='point')
    blacklist = relationship('BlackList', back_populates='point')

    __table_args__ = (
        CheckConstraint('(host_tg_id is null and active is false) or host_tg_id is not null'),
    )


class Queue(BaseModel):
    __tablename__ = 'queues'

    team_id = mapped_column(Integer, ForeignKey('users.id'), primary_key=True)
    point_id = mapped_column(Integer, ForeignKey('points.id'), nullable=False)
    date = mapped_column(DateTime, nullable=False)

    team = relationship('User', back_populates='queue')
    point = relationship('Point', back_populates='queues')


class BlackList(BaseModel):
    __tablename__ = 'blacklist'

    team_id = mapped_column(Integer, ForeignKey('users.id'), primary_key=True)
    point_id = mapped_column(Integer, ForeignKey('points.id'), primary_key=True)

    team = relationship('User', back_populates='blacklist')
    point = relationship('Point', back_populates='blacklist')
