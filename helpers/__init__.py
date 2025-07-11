from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from config import Config


def start() -> scoped_session:
    """Initialize the SQLAlchemy scoped session.

    Falls back to a local sqlite database when *Config.DATABASE_URL* is not
    provided – this makes local development friction-less while still
    allowing production deployments to inject a proper database URL via
    environment variables.
    """
    db_url = Config.DATABASE_URL or "sqlite:///gdrive_uploader.db"
    engine = create_engine(db_url, echo=False)
    BASE.metadata.bind = engine
    BASE.metadata.create_all(engine)
    return scoped_session(sessionmaker(bind=engine, autoflush=False))


BASE = declarative_base()
SESSION = start()