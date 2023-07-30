DB_USERNAME = "testuser1"
DB_PASSWORD = "testuser1pwd"
DB_NAME = "testproj1"


class MYSQLConfig:
    DATABASE_URL = "mysql://" + DB_USERNAME + ":" + DB_PASSWORD + "@localhost/" + DB_NAME + \
                    "?unix_socket=/var/run/mysqld/mysqld.sock&charset=utf8mb4"
    ECHO = False
    AUTO_FLUSH = True
    AUTO_COMMIT = False
    POOL_SIZE = 15
    MAX_OVERFLOW = 10
    POOL_PRE_PING = True


class MongoDBConfig:
    DATABASE_URL = "mongodb://localhost:27017"


class PostgreSQLConfig:
    DATABASE_URL = "mysql://" + DB_USERNAME + ":" + DB_PASSWORD + "@localhost/" + DB_NAME + \
                    "?unix_socket=/var/run/mysqld/mysqld.sock&charset=utf8mb4"
    ECHO = False
    AUTO_FLUSH = True
    AUTO_COMMIT = False
    POOL_SIZE = 15
    MAX_OVERFLOW = 10
    POOL_PRE_PING = True