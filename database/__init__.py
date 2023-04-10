from database.models import (
    Role as Role,
    User as User,
    Point as Point,
    Queue as Queue,
    BlackList as BlackList,
)

from database.operations import (
    add as add,
    get as get,
    update as update,
    remove as remove,
)


# STRICTLY FOR TESTING PURPOSES
def drop_all():
    from database.config import engine
    from database.models import BaseModel

    BaseModel.metadata.drop_all(engine)


def create_all():
    from database.config import engine
    from database.models import BaseModel

    BaseModel.metadata.create_all(engine)
