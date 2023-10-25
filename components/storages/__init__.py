import redis
from cassandra.cluster import ExecutionProfile, EXEC_PROFILE_DEFAULT, ConsistencyLevel
from cassandra.policies import WhiteListRoundRobinPolicy
from cassandra.cqlengine import connection
from cassandra.query import tuple_factory
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from configurations.conf import Postgres, SQLAlchemy, Redis, Scylla
from .models import postgres_models, scylla_models

# For PostgresSQL
Engine = create_engine(url=Postgres.DB_URL, echo=SQLAlchemy.ECHO, pool_size=SQLAlchemy.POOL_SIZE,
                       max_overflow=SQLAlchemy.MAX_OVERFLOW, pool_pre_ping=SQLAlchemy.POOL_PRE_PING)
postgres_models.Base.metadata.create_all(Engine)
PostgresSession = sessionmaker(bind=Engine, autoflush=SQLAlchemy.AUTO_FLUSH, autocommit=SQLAlchemy.AUTO_COMMIT)

# For Redis
RedisSession = redis.Redis(host='localhost', port=Redis.DB_PORT, db=0, password=Redis.DB_PWD)

# For ScyllaDB
profile = ExecutionProfile(
    load_balancing_policy=WhiteListRoundRobinPolicy([Scylla.DB_HOST]),
    consistency_level=ConsistencyLevel.LOCAL_QUORUM,
    serial_consistency_level=ConsistencyLevel.LOCAL_SERIAL,
    request_timeout=15,
    row_factory=tuple_factory
)

connection.setup([Scylla.DB_HOST], Scylla.DB_KEYSPACE,
                 execution_profiles={EXEC_PROFILE_DEFAULT: profile}, port=Scylla.DB_PORT)
# connection.execute(f"DROP KEYSPACE IF EXISTS {Scylla.DB_KEYSPACE}")
connection.execute(
    f"CREATE KEYSPACE IF NOT EXISTS {Scylla.DB_KEYSPACE} WITH replication = " +
    f"{{'class': 'NetworkTopologyStrategy', 'replication_factor': {Scylla.DB_REPLICATION_FACTOR}}}")
connection.execute(f"USE {Scylla.DB_KEYSPACE}")
scylla_models.sync_tables()
ScyllaSession = connection.get_session()
