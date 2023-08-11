from sqlalchemy import create_engine
from configurations.conf import Postgres, SQLAlchemy
from sqlalchemy.orm import sessionmaker

# from sqlalchemy.orm import scoped_session

# For PostgresSQL
Engine = create_engine(url=Postgres.DB_URL, echo=SQLAlchemy.ECHO, pool_size=SQLAlchemy.POOL_SIZE,
                       max_overflow=SQLAlchemy.MAX_OVERFLOW, pool_pre_ping=SQLAlchemy.POOL_PRE_PING)

Session = sessionmaker(bind=Engine, autoflush=SQLAlchemy.AUTO_FLUSH, autocommit=SQLAlchemy.AUTO_COMMIT)

# def newSession():
#     return sessionmaker(bind=Engine, autoflush=SQLAlchemy.AUTO_FLUSH, autocommit=SQLAlchemy.AUTO_COMMIT)

# def newScopedSession():
#     return scoped_session(sessionmaker(bind=Engine, autoflush=scfg.AUTO_FLUSH, autocommit=scfg.AUTO_COMMIT))
