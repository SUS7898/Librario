# -*- coding: utf-8 -*-
"""settings 테이블(key-value)에 JSON 설정을 읽고 쓰는 헬퍼.

예약 스캔 스케줄, 파일명 태그 규칙, 마지막 스캔 시각 등을 보관합니다.
"""
import json
import datetime as dt
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Setting, utcnow

# ---- 기본값 ----
DEFAULT_SCAN_SCHEDULE = {
    # 빠른(증분) 예약 스캔: 변경/신규 파일만
    "quick_enabled": False,
    "quick_every_hours": 6,
    # 심층 예약 스캔: 모든 파일 메타데이터/표지 재확인
    "deep_enabled": False,
    "deep_every_days": 7,
    "deep_at": "04:00",   # HH:MM (컨테이너 로컬 시간)
}

# 파일명에서 태그를 뽑는 기본 규칙.
#   - keyword: 파일명(대소문자 무시)에 해당 문자열이 있으면 tag 부여
#   - regex:   정규식이 매치되면 tag 부여(고정 태그) 또는 group=N 으로 매치 그룹을 태그로
DEFAULT_TAG_RULES = {
    "enabled": True,
    # 대괄호 [ ... ] 안의 내용을 태그로 추출 (스캔레이션/번역 표기 관행)
    "bracket_tags": True,
    "keywords": [
        {"match": "완결", "tag": "완결"},
        {"match": "연재중", "tag": "연재중"},
        {"match": "단행본", "tag": "단행본"},
        {"match": "합본", "tag": "합본"},
        {"match": "개정판", "tag": "개정판"},
        {"match": "무삭제", "tag": "무삭제"},
        {"match": "외전", "tag": "외전"},
        {"match": "번외", "tag": "번외"},
        {"match": "RAW", "tag": "RAW"},
        {"match": "BL", "tag": "BL"},
        {"match": "GL", "tag": "GL"},
        {"match": "백합", "tag": "백합"},
    ],
    "regex": [
        # 화수/권수 범위 표기가 있으면 '연재분' 태그 (예: 1-120화, 001~050)
        {"pattern": r"\d+\s*[-~]\s*\d+\s*(?:화|회|권)", "tag": "연재분"},
        # R18/R19/R17/성인 표기
        {"pattern": r"(?i)R\s?1[789]|성인|adult", "tag": "성인"},
    ],
}


def get_json(db: Session, key: str, default: Any = None) -> Any:
    row = db.get(Setting, key)
    if row is None or row.value is None:
        return default
    try:
        return json.loads(row.value)
    except (ValueError, TypeError):
        return default


def set_json(db: Session, key: str, value: Any) -> None:
    row = db.get(Setting, key)
    payload = json.dumps(value, ensure_ascii=False)
    if row is None:
        db.add(Setting(key=key, value=payload, updated_at=utcnow()))
    else:
        row.value = payload
        row.updated_at = utcnow()
    db.commit()


def get_scan_schedule(db: Session) -> dict:
    cfg = dict(DEFAULT_SCAN_SCHEDULE)
    saved = get_json(db, "scan_schedule", {})
    if isinstance(saved, dict):
        cfg.update({k: v for k, v in saved.items() if k in DEFAULT_SCAN_SCHEDULE})
    return cfg


def set_scan_schedule(db: Session, cfg: dict) -> dict:
    merged = get_scan_schedule(db)
    for k, v in cfg.items():
        if k in DEFAULT_SCAN_SCHEDULE:
            merged[k] = v
    set_json(db, "scan_schedule", merged)
    return merged


def get_tag_rules(db: Session) -> dict:
    saved = get_json(db, "tag_rules", None)
    if not isinstance(saved, dict):
        return dict(DEFAULT_TAG_RULES)
    cfg = dict(DEFAULT_TAG_RULES)
    cfg.update(saved)
    return cfg


def set_tag_rules(db: Session, cfg: dict) -> dict:
    merged = get_tag_rules(db)
    merged.update(cfg or {})
    set_json(db, "tag_rules", merged)
    return merged


# ---- 마지막 스캔 시각(스케줄 판단용) ----
def get_last_run(db: Session, kind: str) -> Optional[dt.datetime]:
    v = get_json(db, f"last_scan_{kind}", None)
    if not v:
        return None
    try:
        return dt.datetime.fromisoformat(v)
    except (ValueError, TypeError):
        return None


def set_last_run(db: Session, kind: str, when: Optional[dt.datetime] = None) -> None:
    when = when or utcnow()
    set_json(db, f"last_scan_{kind}", when.isoformat())


# ---- 스캔 옵션 (스캔/예약 스캔 시 무엇을 미리 처리할지) ----
DEFAULT_SCAN_OPTIONS = {
    "thumbnails": True,       # 표지 썸네일 생성
    "page_count": True,       # 만화/PDF 페이지 수 계산
    "metadata": True,         # ComicInfo.xml / EPUB 메타데이터 읽기
    "filename_tags": True,    # 파일명에서 태그 추출
    "epub_structure": True,   # EPUB 목차·삽화 미리 분석 (열 때 대기 없음)
}


def get_scan_options(db) -> dict:
    return get_json(db, "scan_options", DEFAULT_SCAN_OPTIONS)


def set_scan_options(db, value: dict) -> dict:
    cur = get_scan_options(db)
    cur.update({k: bool(v) for k, v in (value or {}).items()
                if k in DEFAULT_SCAN_OPTIONS})
    set_json(db, "scan_options", cur)
    return cur


# ---- 쓰레드 설정 (읽기용 / 작업용 분리) ----
DEFAULT_THREADS = {
    "read_threads": 0,   # 0 = 자동. 페이지·이미지 전송 등 사용자 요청 처리용
    "scan_workers": 0,   # 0 = 자동. 스캔(표지·메타·EPUB 분석)용
}


def get_threads(db) -> dict:
    return get_json(db, "threads", DEFAULT_THREADS)


def set_threads(db, value: dict) -> dict:
    cur = get_threads(db)
    for k in DEFAULT_THREADS:
        if k in (value or {}) and value[k] is not None:
            try:
                cur[k] = max(0, min(32, int(value[k])))
            except (TypeError, ValueError):
                pass
    set_json(db, "threads", cur)
    return cur
