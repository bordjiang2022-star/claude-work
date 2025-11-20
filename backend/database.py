# database.py - 数据库模型和配置
from datetime import datetime
from typing import Optional
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

Base = declarative_base()

class User(Base):
    """用户表"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    # 关系
    sessions = relationship("TranslationSession", back_populates="user")
    statistics = relationship("UserStatistics", back_populates="user", uselist=False)


class TranslationSession(Base):
    """翻译会话表"""
    __tablename__ = "translation_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    source_language = Column(String(10), nullable=True)  # 自动检测时为None
    target_language = Column(String(10), nullable=False)
    voice = Column(String(50), nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, default=0.0)

    # 关系
    user = relationship("User", back_populates="sessions")
    transcripts = relationship("Transcript", back_populates="session", cascade="all, delete-orphan")


class Transcript(Base):
    """转录文本表（原文和译文）"""
    __tablename__ = "transcripts"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("translation_sessions.id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    source_text = Column(Text, nullable=True)
    translated_text = Column(Text, nullable=True)

    # 关系
    session = relationship("TranslationSession", back_populates="transcripts")


class UserStatistics(Base):
    """用户统计表"""
    __tablename__ = "user_statistics"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    total_sessions = Column(Integer, default=0)
    total_duration_seconds = Column(Float, default=0.0)
    total_characters_translated = Column(Integer, default=0)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    user = relationship("User", back_populates="statistics")


# 数据库连接配置
DATABASE_URL = "sqlite+aiosqlite:///./livetranslate.db"

engine = create_async_engine(DATABASE_URL, echo=False)
async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db():
    """初始化数据库"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db():
    """获取数据库会话"""
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()
