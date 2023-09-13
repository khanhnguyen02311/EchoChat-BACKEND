from os import environ


class Env:
    PS_DB = environ.get("POSTGRES_DB")
    PS_USR = environ.get("POSTGRES_USR")
    PS_PWD = environ.get("POSTGRES_PWD")
    PS_PORT = int(environ.get("POSTGRES_PORT"))

    APP_PORT = int(environ.get("APP_PORT"))
    APP_FRONTEND_URL = environ.get("APP_FRONTEND_URL")
    APP_DEBUG = bool(environ.get("APP_DEBUG"))

    SCR_JWT_SECRET_KEY = environ.get("SECURITY_JWT_SECRET_KEY")
    SCR_JWT_ALGORITHM = "HS256"
    SCR_ACCESS_TOKEN_EXPIRE_MINUTES = int(environ.get("SECURITY_ACCESS_TOKEN_MINUTE"))
    SCR_REFRESH_TOKEN_EXPIRE_MINUTES = int(environ.get("SECURITY_REFRESH_TOKEN_MINUTE"))


class Postgres:
    DB_URL = f"postgresql+psycopg2://{Env.PS_USR}:{Env.PS_PWD}@localhost:{Env.PS_PORT}/{Env.PS_DB}?sslmode=disable"


class SQLAlchemy:
    ECHO = True
    AUTO_FLUSH = True  # flush after committing
    AUTO_COMMIT = False
    POOL_SIZE = 15
    MAX_OVERFLOW = 10
    POOL_PRE_PING = True


class Redis:
    DB_PORT = int(environ.get("REDIS_PORT"))
    DB_PWD = environ.get("REDIS_PWD")


class Scylla:
    DB_PORT = int(environ.get("SCYLLA_PORT"))
    DB_KEYSPACE = environ.get("SCYLLA_KEYSPACE")
    DB_REPLICATION_FACTOR = int(environ.get("SCYLLA_REPLICATION_FACTOR"))
