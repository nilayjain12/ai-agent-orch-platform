from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from .models import Base

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./sql_app.db")  # Fallback for local testing

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
