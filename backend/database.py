from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, JSON, ForeignKey, text, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from config import settings
import logging

logger = logging.getLogger(__name__)

Base = declarative_base()

# Database Models
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(320), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class Watchlist(Base):
    __tablename__ = "watchlists"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    ticker = Column(String(10), nullable=False, index=True)
    company_name = Column(String(200))
    added_at = Column(DateTime, default=datetime.utcnow)

class Strategy(Base):
    __tablename__ = "strategies"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    conditions = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ResearchReport(Base):
    __tablename__ = "research_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    ticker = Column(String(10), nullable=False, index=True)
    company_name = Column(String(200))
    report_data = Column(JSON, nullable=False)
    generated_at = Column(DateTime, default=datetime.utcnow)
    data_timestamp = Column(DateTime)

# Database connection
engine = None
SessionLocal = None

def init_db():
    """Initialize database connection and create tables"""
    global engine, SessionLocal
    
    if not settings.has_database:
        logger.warning("No database URL configured. Database features will be unavailable.")
        return False
    
    try:
        engine = create_engine(
            settings.database_url,
            pool_pre_ping=True,  # Verify connections before using
            pool_recycle=3600,   # Recycle connections after 1 hour
            connect_args={"connect_timeout": 10}
        )
        # Test actual connectivity
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        Base.metadata.create_all(bind=engine)
        # Add ownership columns to existing deployments without destroying user data.
        inspector = inspect(engine)
        for table in ("watchlists", "strategies", "research_reports"):
            if table in inspector.get_table_names() and "user_id" not in {c["name"] for c in inspector.get_columns(table)}:
                with engine.begin() as conn:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN user_id INTEGER NULL"))
                    conn.execute(text(f"CREATE INDEX IF NOT EXISTS ix_{table}_user_id ON {table} (user_id)"))
        logger.info("Database initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        engine = None
        SessionLocal = None
        return False

def get_db():
    """Get database session"""
    if SessionLocal is None:
        return None
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def is_database_available() -> bool:
    """Check if database is available with actual connectivity test"""
    if engine is None or SessionLocal is None:
        return False
    
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Database connectivity check failed: {e}")
        return False
