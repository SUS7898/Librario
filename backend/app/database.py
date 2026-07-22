# -*- coding: utf-8 -*-
from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.engine import Engine

from . import config

config.ensure_dirs()

DATABASE_URL = f"sqlite:///{config.DB_PATH}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    future=True,
)


@event.listens_for(Engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    # 스캔(쓰기)과 조회(읽기) 동시성 향상
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA busy_timeout=8000")
    cursor.close()


SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# 기존 DB 에 새 컬럼을 추가하기 위한 경량 마이그레이션.
# (SQLAlchemy create_all 은 기존 테이블에 컬럼을 추가하지 않으므로 직접 ALTER)
_COLUMN_MIGRATIONS = {
    "books": [
        ("description", "TEXT"),
        ("publisher", "VARCHAR(300)"),
        ("language", "VARCHAR(40)"),
        ("series_index", "VARCHAR(40)"),
        ("meta_updated_at", "DATETIME"),
        ("status", "VARCHAR(10) NOT NULL DEFAULT 'active'"),
        ("trashed_at", "DATETIME"),
    ],
    "series": [
        ("description", "TEXT"),
    ],
}


def _migrate_columns():
    from sqlalchemy import text
    with engine.begin() as conn:
        for table, cols in _COLUMN_MIGRATIONS.items():
            existing = {
                row[1] for row in conn.exec_driver_sql(f"PRAGMA table_info({table})").all()
            }
            if not existing:
                continue  # 테이블 자체가 없으면 create_all 이 새로 만듦
            for name, decl in cols:
                if name not in existing:
                    conn.exec_driver_sql(f"ALTER TABLE {table} ADD COLUMN {name} {decl}")


def init_db():
    from . import models  # noqa: F401  (모델 등록)
    Base.metadata.create_all(bind=engine)
    _migrate_columns()
    Base.metadata.create_all(bind=engine)  # 인덱스 등 재확인
