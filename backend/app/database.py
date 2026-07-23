# -*- coding: utf-8 -*-
from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.engine import Engine

from . import config

config.ensure_dirs()

DATABASE_URL = f"sqlite:///{config.DB_PATH}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False, "timeout": 20},
    pool_size=config.DB_POOL_SIZE,
    max_overflow=config.DB_MAX_OVERFLOW,
    pool_timeout=config.DB_POOL_TIMEOUT,
    pool_recycle=1800,
    pool_pre_ping=True,
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
    # 대량 스캔 시 쓰기 처리량 향상 (수만 권 스캔에서 체감 차이가 큼)
    cursor.execute("PRAGMA cache_size=-40000")   # 약 40MB 페이지 캐시
    cursor.execute("PRAGMA temp_store=MEMORY")
    cursor.execute("PRAGMA mmap_size=268435456") # 256MB
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
        ("epub_meta", "TEXT"),
    ],
    "series": [
        ("description", "TEXT"),
    ],
    "libraries": [
        ("sort_order", "INTEGER NOT NULL DEFAULT 0"),
        ("private", "BOOLEAN NOT NULL DEFAULT 0"),
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


# ---------------------------------------------------------------------------
# DB 최적화 (주기 실행 / 관리자 수동 실행)
#  - WAL 체크포인트: 커진 -wal 파일을 본체로 합침
#  - ANALYZE/optimize: 쿼리 계획 통계 갱신 (대량 스캔 후 조회 속도에 영향)
#  - VACUUM: 삭제로 생긴 빈 공간 회수 (파일 크기 감소)
# ---------------------------------------------------------------------------
def optimize_db(full: bool = True) -> dict:
    import os as _os
    from sqlalchemy import text as _text
    path = str(config.DB_PATH)
    before = None
    try:
        if path and _os.path.exists(path):
            before = _os.path.getsize(path)
    except OSError:
        before = None
    steps = []
    with engine.connect() as conn:
        raw = conn.connection
        try:
            conn.exec_driver_sql("PRAGMA wal_checkpoint(TRUNCATE)")
            steps.append("wal_checkpoint")
        except Exception:
            pass
        try:
            conn.exec_driver_sql("ANALYZE")
            steps.append("analyze")
        except Exception:
            pass
        try:
            conn.exec_driver_sql("PRAGMA optimize")
            steps.append("optimize")
        except Exception:
            pass
        if full:
            try:
                old_iso = raw.isolation_level
                raw.isolation_level = None      # VACUUM 은 트랜잭션 밖에서만 가능
                raw.execute("VACUUM")
                raw.isolation_level = old_iso
                steps.append("vacuum")
            except Exception:
                pass
    after = None
    try:
        if path and _os.path.exists(path):
            after = _os.path.getsize(path)
    except OSError:
        after = None
    return {"ok": True, "steps": steps, "size_before": before, "size_after": after,
            "freed": (before - after) if (before and after) else 0}
