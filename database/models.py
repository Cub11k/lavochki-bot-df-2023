from enum import IntEnum
import uuid

from sqlalchemy import Boolean, Identity, Integer, BigInteger, String, DateTime, Enum, ForeignKey
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

    id = mapped_column(Integer, Identity(start=1048576, increment=2048), primary_key=True)
    tg_id = mapped_column(BigInteger, unique=True, nullable=True)
    role = mapped_column(Enum(Role))
    name = mapped_column(String(255), unique=True)
    balance = mapped_column(Integer, CheckConstraint('balance >= 0'), default=0)
    passed_points = mapped_column(Integer, CheckConstraint('passed_points >= 0'), default=0)

    point = relationship('Point', back_populates='host')
    queues = relationship('Queue', back_populates='team')
    blacklist = relationship('BlackList', back_populates='team')


class Point(BaseModel):
    __tablename__ = 'points'

    id = mapped_column(Integer, Identity(start=1, increment=1), primary_key=True)
    host_tg_id = mapped_column(BigInteger, ForeignKey('users.tg_id'), unique=True, nullable=True)
    name = mapped_column(String(255))
    balance = mapped_column(Integer, CheckConstraint('balance >= 0'), default=0)
    one_time = mapped_column(Boolean)

    host = relationship('User', back_populates='points')
    queues = relationship('Queue', back_populates='point')
    blacklist = relationship('BlackList', back_populates='point')


class Queue(BaseModel):
    __tablename__ = 'queues'

    team_id = mapped_column(Integer, ForeignKey('users.id'), primary_key=True)
    point_id = mapped_column(Integer, ForeignKey('points.id'))
    date = mapped_column(DateTime)

    team = relationship('User', back_populates='queues')
    point = relationship('Point', back_populates='queues')


class BlackList(BaseModel):
    __tablename__ = 'blacklist'

    team_id = mapped_column(Integer, ForeignKey('users.id'), primary_key=True)
    point_id = mapped_column(Integer, ForeignKey('points.id'), primary_key=True)

    team = relationship('User', back_populates='blacklist')
    point = relationship('Point', back_populates='blacklist')
