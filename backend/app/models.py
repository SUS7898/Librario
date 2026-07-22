# -*- coding: utf-8 -*-
import datetime as dt

from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, ForeignKey, Text,
    UniqueConstraint, Index, BigInteger, Table,
)
from sqlalchemy.orm import relationship

from .database import Base


def utcnow():
    return dt.datetime.utcnow()


# 사용자 <-> 제한 라이브러리 접근 권한 (다대다)
user_library_grants = Table(
    "user_library_grants",
    Base.metadata,
    Column("user_id", ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("library_id", ForeignKey("libraries.id", ondelete="CASCADE"), primary_key=True),
)


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="user")  # admin | user
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=utcnow)

    granted_libraries = relationship(
        "Library", secondary=user_library_grants, backref="allowed_users"
    )

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"


class Library(Base):
    __tablename__ = "libraries"
    id = Column(Integer, primary_key=True)
    name = Column(String(120), nullable=False)
    path = Column(String(1024), unique=True, nullable=False)
    # restricted=True 이면 명시적으로 권한 부여받은 사용자(+관리자)만 접근 가능 (예: 성인물)
    restricted = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=utcnow)

    series = relationship("Series", back_populates="library", cascade="all, delete-orphan")
    books = relationship("Book", back_populates="library", cascade="all, delete-orphan")


class Series(Base):
    __tablename__ = "series"
    id = Column(Integer, primary_key=True)
    library_id = Column(ForeignKey("libraries.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(500), nullable=False)
    sort_name = Column(String(500), nullable=False, default="")
    path = Column(String(1024), unique=True, nullable=False)
    book_count = Column(Integer, nullable=False, default=0)  # status='active' 인 책 수
    cover_book_id = Column(Integer, nullable=True)  # 표지로 쓸 book id
    description = Column(Text, nullable=True)        # 메타데이터에서 추출한 시리즈 설명
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, index=True)

    library = relationship("Library", back_populates="series")
    books = relationship("Book", back_populates="series", cascade="all, delete-orphan")

    __table_args__ = (Index("ix_series_lib_sort", "library_id", "sort_name"),)


class Book(Base):
    __tablename__ = "books"
    id = Column(Integer, primary_key=True)
    series_id = Column(ForeignKey("series.id", ondelete="CASCADE"), nullable=False, index=True)
    library_id = Column(ForeignKey("libraries.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    sort_title = Column(String(500), nullable=False, default="")
    path = Column(String(1024), unique=True, nullable=False)
    fmt = Column(String(10), nullable=False)  # cbz | zip | pdf | epub | txt
    file_size = Column(BigInteger, nullable=False, default=0)
    mtime = Column(Integer, nullable=False, default=0)  # 정수 초 (증분 스캔용)
    page_count = Column(Integer, nullable=True)  # 만화/PDF 만
    author = Column(String(300), nullable=True)
    # ---- 확장 메타데이터 ----
    description = Column(Text, nullable=True)        # 줄거리/설명
    publisher = Column(String(300), nullable=True)   # 출판사
    language = Column(String(40), nullable=True)     # 언어(ISO)
    series_index = Column(String(40), nullable=True) # 권/화 번호(ComicInfo Number 등)
    meta_updated_at = Column(DateTime, nullable=True) # 마지막 메타데이터 추출 시각
    # ---- 휴지통(소프트 삭제) ----
    status = Column(String(10), nullable=False, default="active", index=True)  # active | trashed
    trashed_at = Column(DateTime, nullable=True)     # 휴지통 이동 시각
    has_thumb = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=utcnow, index=True)
    updated_at = Column(DateTime, default=utcnow, index=True)

    series = relationship("Series", back_populates="books")
    library = relationship("Library", back_populates="books")
    tags = relationship("BookTag", back_populates="book", cascade="all, delete-orphan")


class Tag(Base):
    __tablename__ = "tags"
    id = Column(Integer, primary_key=True)
    name = Column(String(200), unique=True, nullable=False, index=True)
    book_links = relationship("BookTag", back_populates="tag", cascade="all, delete-orphan")


class BookTag(Base):
    __tablename__ = "book_tags"
    book_id = Column(ForeignKey("books.id", ondelete="CASCADE"), primary_key=True)
    tag_id = Column(ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True)
    source = Column(String(10), nullable=False, default="auto")  # auto | manual

    book = relationship("Book", back_populates="tags")
    tag = relationship("Tag", back_populates="book_links")


class ReadProgress(Base):
    __tablename__ = "read_progress"
    id = Column(Integer, primary_key=True)
    user_id = Column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    book_id = Column(ForeignKey("books.id", ondelete="CASCADE"), nullable=False, index=True)
    page = Column(Integer, nullable=False, default=0)          # 만화/PDF 현재 페이지(0-based)
    position = Column(Text, nullable=True)                      # epub CFI / txt 스크롤% 등
    completed = Column(Boolean, nullable=False, default=False)
    updated_at = Column(DateTime, default=utcnow, index=True)

    __table_args__ = (UniqueConstraint("user_id", "book_id", name="uq_progress_user_book"),)


class Rating(Base):
    __tablename__ = "ratings"
    id = Column(Integer, primary_key=True)
    user_id = Column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    book_id = Column(ForeignKey("books.id", ondelete="CASCADE"), nullable=False, index=True)
    value = Column(Integer, nullable=False, default=0)  # 1~5
    updated_at = Column(DateTime, default=utcnow)

    __table_args__ = (UniqueConstraint("user_id", "book_id", name="uq_rating_user_book"),)


class Setting(Base):
    """전역 설정 저장용 key-value (스케줄/태그 규칙 등을 JSON 문자열로 보관)."""
    __tablename__ = "settings"
    key = Column(String(80), primary_key=True)
    value = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)
