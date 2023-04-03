import sqlalchemy

engine = sqlalchemy.create_engine('postgresql+psycopg://postgres:postgres@localhost:5432/postgres')
