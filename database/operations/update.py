from typing import Optional

import sqlalchemy
import sqlalchemy.exc

from database.models import Role, User, Point, Queue, BlackList
from database.engine import engine


def transfer(from_user_id: int, to_user_id: int, amount: int) -> bool:
    try:
        with engine.begin() as conn:
            conn.execute(sqlalchemy.update(User).where(User.id == from_user_id).values(balance=User.balance - amount))
            conn.execute(sqlalchemy.update(User).where(User.id == to_user_id).values(balance=User.balance + amount))
    except sqlalchemy.exc.SQLAlchemyError:
        return False
    return True
