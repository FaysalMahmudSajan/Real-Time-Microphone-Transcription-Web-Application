from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import Column, Integer, String, Float, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///./transcriptions.db"

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
AsyncSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()

class TranscriptionSession(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    transcript = Column(Text, default="")
    duration = Column(Float, default=0.0)
    word_count = Column(Integer, default=0)
    created_at = Column(Float, default=0.0)