from sqlalchemy import (
    create_engine, Column, Integer, String, Float,
    DateTime, Text, Index, Boolean, ForeignKey, JSON
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from app.core.config import config

engine = create_engine(
    config.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id            = Column(Integer, primary_key=True, index=True)
    email         = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name     = Column(String(255), nullable=False)
    role          = Column(String(20), default="individual")
    department    = Column(String(100))
    created_at    = Column(DateTime, default=datetime.utcnow)
    assessments   = relationship("Assessment", back_populates="user")
    trait_scores  = relationship("TraitScore", back_populates="user")


class Assessment(Base):
    __tablename__ = "assessments"
    id            = Column(Integer, primary_key=True, index=True)
    user_id       = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    responses     = Column(JSON, nullable=False)
    completed_at  = Column(DateTime, default=datetime.utcnow, index=True)
    version       = Column(String(10), default="1.0")
    user          = relationship("User", back_populates="assessments")
    trait_scores  = relationship("TraitScore", back_populates="assessment")

    __table_args__ = (
        Index("idx_assessment_user_date", "user_id", "completed_at"),
    )


class TraitScore(Base):
    __tablename__ = "trait_scores"
    id                    = Column(Integer, primary_key=True, index=True)
    user_id               = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    assessment_id         = Column(Integer, ForeignKey("assessments.id"), nullable=False)
    openness              = Column(Float, nullable=False)
    conscientiousness     = Column(Float, nullable=False)
    extraversion          = Column(Float, nullable=False)
    agreeableness         = Column(Float, nullable=False)
    neuroticism           = Column(Float, nullable=False)
    openness_pct          = Column(Float)
    conscientiousness_pct = Column(Float)
    extraversion_pct      = Column(Float)
    agreeableness_pct     = Column(Float)
    neuroticism_pct       = Column(Float)
    dominant_trait        = Column(String(30))
    created_at            = Column(DateTime, default=datetime.utcnow, index=True)
    user                  = relationship("User", back_populates="trait_scores")
    assessment            = relationship("Assessment", back_populates="trait_scores")

    __table_args__ = (
        Index("idx_trait_user_trait", "user_id", "dominant_trait"),
        Index("idx_trait_user_date",  "user_id", "created_at"),
    )


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    Base.metadata.create_all(bind=engine)
    print("✅ Traitlytics tables created")