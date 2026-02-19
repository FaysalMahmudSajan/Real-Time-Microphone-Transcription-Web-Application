from sqlalchemy import create_engine, Column, Integer, String, Float, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./transcriptions.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class TranscriptionSession(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    transcript = Column(Text, default="")
    duration = Column(Float, default=0.0)
    word_count = Column(Integer, default=0)
    created_at = Column(Float, default=0.0)