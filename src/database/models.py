from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, Boolean
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

# Database connection
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "mysql+pymysql://root:password@localhost:3306/cr_king"
)
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()