from os import environ


class Env:
    PS_DB = environ.get("POSTGRES_DB")
    PS_USR = environ.get("POSTGRES_USR")
    PS_PWD = environ.get("POSTGRES_PWD")
    PS_PORT = int(environ.get("POSTGRES_PORT"))

    APP_PORT = int(environ.get("APP_PORT"))
    APP_FRONTEND_URL = environ.get("APP_FRONTEND_URL")
    APP_DEBUG = bool(environ.get("APP_DEBUG"))

    SCR_HASHSALT = environ.get("SECURITY_HASHSALT")


# class MySQL:
#     DB_URL = f"mysql://{Env.MS_USR}:{Env.MS_PWD}@localhost:{Env.MS_PORT}/{Env.MS_DB}"
#            + "?unix_socket=/var/run/mysqld/mysqld.sock&charset=utf8mb4"


class Postgres:
    DB_URL = f"postgresql+psycopg2://{Env.PS_USR}:{Env.PS_PWD}@localhost:{Env.PS_PORT}/{Env.PS_DB}?sslmode=disable"


class SQLAlchemy:
    ECHO = True
    AUTO_FLUSH = True  # flush after committing
    AUTO_COMMIT = False
    POOL_SIZE = 15
    MAX_OVERFLOW = 10
    POOL_PRE_PING = True
