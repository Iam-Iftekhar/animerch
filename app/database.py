# app/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base # Add this import if missing
from app.core.config import settings

# --- DEBUG LINE ---
print("--------------------------------------------------")
print(f"DEBUG: The DB URL is: {settings.DATABASE_URL}")
print("--------------------------------------------------")
# ------------------

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()