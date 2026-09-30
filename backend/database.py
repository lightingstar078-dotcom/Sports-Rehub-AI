from pathlib import Path
import os
from sqlalchemy import create_engine, String, Integer, Float, DateTime, Text, JSON
from sqlalchemy.orm import declarative_base, sessionmaker, Mapped, mapped_column
from datetime import datetime

BASE = Path(__file__).resolve().parent
DB_PATH = Path(os.getenv("SQLITE_PATH", BASE / "storage" / "sports_ai.db"))
DB_PATH.parent.mkdir(parents=True, exist_ok=True)
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
if DATABASE_URL:
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg://", 1)
    elif DATABASE_URL.startswith("postgresql://"):
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    DATABASE_MODE = "postgresql"
else:
    engine = create_engine(f"sqlite:///{DB_PATH.as_posix()}", connect_args={"check_same_thread": False})
    DATABASE_MODE = "sqlite"
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

class Athlete(Base):
    __tablename__ = "athletes"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120))
    age: Mapped[int] = mapped_column(Integer)
    sport: Mapped[str] = mapped_column(String(120))
    injury: Mapped[str] = mapped_column(String(200))
    injury_side: Mapped[str] = mapped_column(String(30), default="N/A")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Assessment(Base):
    __tablename__ = "assessments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    athlete_id: Mapped[int] = mapped_column(Integer, index=True)
    exercise: Mapped[str] = mapped_column(String(80))
    date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    movement_quality: Mapped[float] = mapped_column(Float)
    symmetry: Mapped[float] = mapped_column(Float)
    rom: Mapped[float] = mapped_column(Float)
    stability: Mapped[float] = mapped_column(Float)
    landing_control: Mapped[float] = mapped_column(Float, default=0)
    movement_consistency: Mapped[float] = mapped_column(Float, default=0)
    pain: Mapped[float] = mapped_column(Float)
    psychological_readiness: Mapped[float] = mapped_column(Float)
    readiness_score: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(20))
    video_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    original_size: Mapped[int] = mapped_column(Integer, default=0)
    compressed_size: Mapped[int] = mapped_column(Integer, default=0)
    video_duration: Mapped[float] = mapped_column(Float, default=0)
    video_resolution: Mapped[str] = mapped_column(String(40), default="unknown")
    analysis_json: Mapped[dict] = mapped_column(JSON, default=dict)
    sync_status: Mapped[str] = mapped_column(String(20), default="PENDING")

class PsychologicalResponse(Base):
    __tablename__ = "psychological_responses"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    assessment_id: Mapped[int] = mapped_column(Integer, index=True)
    question: Mapped[str] = mapped_column(Text)
    response: Mapped[int] = mapped_column(Integer)

class SyncQueue(Base):
    __tablename__ = "sync_queue"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    entity_type: Mapped[str] = mapped_column(String(50))
    entity_id: Mapped[int] = mapped_column(Integer)
    operation: Mapped[str] = mapped_column(String(20))
    payload: Mapped[dict] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(20), default="PENDING")
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

def init_db() -> None:
    Base.metadata.create_all(engine)
    s = SessionLocal()
    try:
        if s.query(Athlete).count() == 0:
            s.add(Athlete(name="Demo Athlete", age=21, sport="Football", injury="Lower-limb injury recovery", injury_side="Right"))
            s.commit()
    finally:
        s.close()
