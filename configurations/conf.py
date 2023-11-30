from os import environ
from arguments import args


class Env:
    APP_PORT_API = int(environ.get("APP_PORT_API"))
    APP_PORT_GRPC = int(environ.get("APP_PORT_GRPC"))
    APP_FRONTEND_URL = environ.get("APP_FRONTEND_URL")
    APP_DEBUG = args.debug
    APP_STAGE = args.stage

    SCR_JWT_SECRET_KEY = environ.get("SECURITY_JWT_SECRET_KEY")
    SCR_JWT_ALGORITHM = "HS256"
    SCR_ACCESS_TOKEN_EXPIRE_MINUTES = int(environ.get("SECURITY_ACCESS_TOKEN_MINUTE"))
    SCR_REFRESH_TOKEN_EXPIRE_MINUTES = int(environ.get("SECURITY_REFRESH_TOKEN_MINUTE"))


class Postgres:
    DB_HOST = environ.get("POSTGRES_HOST")
    DB_DB = environ.get("POSTGRES_DB")
    DB_USR = environ.get("POSTGRES_USR")
    DB_PWD = environ.get("POSTGRES_PWD")
    DB_PORT = int(environ.get("POSTGRES_PORT"))
    DB_URL = f"postgresql+psycopg2://{DB_USR}:{DB_PWD}@{DB_HOST}:{DB_PORT}/{DB_DB}?sslmode=disable"


class SQLAlchemy:
    ECHO = True
    AUTO_FLUSH = True  # flush after committing
    AUTO_COMMIT = False
    POOL_SIZE = 15
    MAX_OVERFLOW = 10
    POOL_PRE_PING = True


class Redis:
    DB_HOST = environ.get("REDIS_HOST")
    DB_PORT = int(environ.get("REDIS_PORT"))
    DB_PWD = environ.get("REDIS_PWD")


class Scylla:
    DB_HOST = environ.get("SCYLLA_HOST")
    DB_PORT = int(environ.get("SCYLLA_PORT"))
    DB_KEYSPACE = environ.get("SCYLLA_KEYSPACE")
    DB_REPLICATION_FACTOR = int(environ.get("SCYLLA_REPLICATION_FACTOR"))


class Observability:
    TRACING_ENDPOINT = "0.0.0.0:" + environ.get("OBSERVABILITY_TRACING_PORT")
    OBSERVABILITY_SERVICE_NAME = environ.get("OBSERVABILITY_SERVICE_NAME")
