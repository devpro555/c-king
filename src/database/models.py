import logging
import os

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
    symbol = Column(String(20), nullable=False)
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

# Remove module-level DATABASE_URL and engine creation
# Move to init_db()

def init_db():
    """Initialize database tables and connection"""
    global engine, SessionLocal

    DATABASE_URL = next((os.getenv(name) for name in DB_ENV_NAMES if os.getenv(name) and os.getenv(name).strip()), None)
    if DATABASE_URL is None:
        logging.warning(
            "No database environment variable found; falling back to local SQLite database at ./local.db. "
            "Set DATABASE_URL or another supported env var for production/Railway deployments."
        )
        DATABASE_URL = "sqlite:///./local.db"
    else:
        DATABASE_URL = DATABASE_URL.strip()
        if DATABASE_URL.startswith("mysql://"):
            DATABASE_URL = "mysql+pymysql://" + DATABASE_URL[len("mysql://"):]

    try:
        engine = create_engine(DATABASE_URL, echo=False)
    except ArgumentError as exc:
        raise RuntimeError(
            f"Invalid database connection URL: {DATABASE_URL!r}. "
            "Ensure it is a valid SQLAlchemy URL, e.g. mysql+pymysql://user:pass@host:port/db"
        ) from exc
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    # Drop stale unique constraint on open_positions.symbol if it exists (MySQL only).
    # This constraint was created in an earlier schema version and prevents the bot
    # from correctly tracking open positions after a restart.
    if DATABASE_URL and "mysql" in DATABASE_URL:
        try:
            with engine.connect() as conn:
                conn.execute(
                    __import__("sqlalchemy").text(
                        "ALTER TABLE open_positions DROP INDEX symbol"
                    )
                )
                conn.commit()
                logging.info("Dropped unique constraint 'symbol' from open_positions table")
        except Exception:
            # Constraint doesn't exist or already dropped — safe to ignore
            pass

def get_db():
    """Get database session"""
    if 'SessionLocal' not in globals():
        raise RuntimeError("Database not initialized. Call init_db() first.")
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()