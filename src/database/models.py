from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, Boolean
from sqlalchemy.exc import ArgumentError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

Base = declarative_base()

class Trade(Base):
    __tablename__ = 'trades'

    id = Column(String(100), primary_key=True)
    symbol = Column(String(20), nullable=False)
    signal = Column(String(10))
    side = Column(String(10), nullable=False)
    size = Column(Float, nullable=False)
    entry_price = Column(Float, nullable=False)
    exit_price = Column(Float)
    pnl = Column(Float, default=0.0)
    entry_time = Column(DateTime, nullable=False)
    exit_time = Column(DateTime)
    status = Column(String(10), default='open')
    explanation = Column(Text)
    reason = Column(String(20))

class SystemState(Base):
    __tablename__ = 'system_state'

    id = Column(Integer, primary_key=True, default=1)
    equity = Column(Float, default=1000.0)
    running = Column(Boolean, default=False)
    virtual_mode = Column(Boolean, default=True)
    last_updated = Column(DateTime, default=datetime.now)

class LogEntry(Base):
    __tablename__ = 'logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.now)
    level = Column(String(10), default='INFO')
    message = Column(Text, nullable=False)

class OpenPosition(Base):
    __tablename__ = 'open_positions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False, unique=True)
    side = Column(String(10), nullable=False)
    size = Column(Float, nullable=False)
    entry_price = Column(Float, nullable=False)
    stop_loss = Column(Float, nullable=False)
    take_profit = Column(Float, nullable=False)
    entry_time = Column(DateTime, nullable=False)
    status = Column(String(10), default='open')

import os

DB_ENV_NAMES = [
    "DATABASE_URL",
    "RAILWAY_DATABASE_URL",
    "MYSQL_URL",
    "MYSQL_DATABASE_URL",
    "MYSQLCONNSTR",
    "CLEARDB_DATABASE_URL",
]

# Engine and session factory are created lazily on first call to init_db() so
# that this module can be imported before the DATABASE_URL environment variable
# has been resolved (e.g. Railway reference variables are only available at
# runtime, not at module-import time).
_engine = None
_SessionLocal = None


def _build_engine():
    """Resolve the database URL and create the SQLAlchemy engine.

    Called once from init_db(); raises RuntimeError with a clear message when
    no supported environment variable is set.
    """
    global _engine, _SessionLocal

    database_url = next((os.getenv(name) for name in DB_ENV_NAMES if os.getenv(name)), None)
    if database_url is None:
        raise RuntimeError(
            "No database connection string was found. "
            "Set one of the supported environment variables: "
            + ", ".join(DB_ENV_NAMES)
            + ".\nExample: mysql+pymysql://user:pass@host:port/db"
        )

    database_url = database_url.strip()
    if database_url.startswith("mysql://"):
        database_url = "mysql+pymysql://" + database_url[len("mysql://"):]

    try:
        _engine = create_engine(database_url, echo=False)
    except ArgumentError as exc:
        raise RuntimeError(
            f"Invalid database connection URL: {database_url!r}. "
            "Ensure it is a valid SQLAlchemy URL, e.g. mysql+pymysql://user:pass@host:port/db"
        ) from exc

    _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)


def init_db():
    """Resolve the database URL, create the engine, and initialise tables.

    Safe to call multiple times; engine creation is skipped on subsequent
    calls.
    """
    if _engine is None:
        _build_engine()
    Base.metadata.create_all(bind=_engine)


def get_db():
    """Return a new database session.

    init_db() must have been called before this function is used.
    """
    if _SessionLocal is None:
        raise RuntimeError(
            "Database has not been initialised. "
            "Call init_db() (via TradingExecutor.initialize_database()) before using get_db()."
        )
    db = _SessionLocal()
    try:
        return db
    finally:
        db.close()