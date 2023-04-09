import sqlalchemy
from sqlalchemy.orm import sessionmaker

# import config

# engine = sqlalchemy.create_engine(
#     "{}+{}://{}:{}@{}:{}/{}".format(config.dbms_name, config.dbms_driver, config.dbms_user, config.dbms_password,
#                                     config.dbms_host, config.dbms_port, config.db_name))
#
# Session = sessionmaker(engine)


# For local testing
engine = sqlalchemy.create_engine('postgresql+psycopg://test:12345678@127.0.0.1:5432/test', echo=True)
Session = sessionmaker(engine)
