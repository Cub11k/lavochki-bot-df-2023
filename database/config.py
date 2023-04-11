import sqlalchemy
from sqlalchemy.orm import sessionmaker

import config

engine = sqlalchemy.create_engine(
    "{}+{}://{}:{}@{}:{}/{}".format(config.dbms_name, config.dbms_driver, config.dbms_user, config.dbms_password,
                                    config.dbms_host, config.dbms_port, config.db_name),
    pool_size=20, max_overflow=10, echo=config.db_echo)

Session = sessionmaker(engine)
