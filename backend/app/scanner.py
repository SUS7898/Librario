# -*- coding: utf-8 -*-
"""
라이브러리 스캐너.
- 폴더 = 시리즈, 파일 = 책(권)
- 파일의 '바로 위 폴더'가 시리즈(제목), 그 위 조상 폴더들이 태그(장르)
- cbz/zip 은 ComicInfo.xml 태그를 읽어 병합
- 파일명/폴더명 정리 로직은 사용자의 komga_xml.py 를 이식
- mtime 기반 증분 스캔 + 사라진 파일 정리
"""
import os
import re
import time
import json
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import datetime as dt
from typing import List, Tuple, Dict, Set

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from . import formats, thumbnails, config, settings_store
from .database import SessionLocal
from .models import Library, Series, Book, Tag, BookTag, utcnow

# 태그로 만들지 않고 무시할 폴더명 (소문자)
IGNORE_FOLDER_NAMES = {
    "library", "단행본", "단행본_기타", "webtoon", "웹툰", "연재중", "완결",
    "comic", "tier_2", "tier", "webtoon", "성인_연재중", "성인_완결",
}
SPLIT_SPACE_IN_TAGS = False


# ---------------------------------------------------------------------------
# 텍스트 클리닝 (komga_xml.py 이식)
# ---------------------------------------------------------------------------
def clean_text(s: str) -> Tuple[str, bool]:
    is_completed = False
    if (re.search(r'[\(\[\s]완(?:결)?[\)\]\s]*$', s) or "(완)" in s or "(완결)" in s
            or "[완]" in s or "[완결]" in s):
        is_completed = True

    SEP = r'[\s_\-\.\(\)\[\]]*'
    anywhere_tokens = [
        r'(?:수정본|개정판|리마스터(?:판)?|무삭제|언센서드|합본|모음|패키지)',
        r'(?:번외|외전|특별|특별편|부록)\s*(?:포함)?',
        rf'(?:e\s*[-]?\s*book|ebook|e\s*북|이\s*북|전자\s*책)\s*(?:본|버전|판)?{SEP}',
        r'포함',
        r'\s+by\s+.*$',
    ]
    s = re.sub(r'\s*(?:' + r'|'.join(anywhere_tokens) + r')\s*', ' ', s, flags=re.I)
    s = re.sub(r'\b\d+(?:\.\d+)?\s*[-~]\s*\d+(?:\.\d+)?(?:\s*(?:화|회|권))?\b', ' ', s, flags=re.I)

    tail_patterns = [
        r'\s*[\(\[]?\s*완(?:결)?(?:\s*(?:수정본|개정판|리마스터(?:판)?|무삭제|언센서드|판)?)?\s*[\)\]]?\s*$',
        r'\s*(?:전편|전권)(?:\s*(?:수정본|개정판|리마스터(?:판)?|무삭제|언센서드|판)?)?\s*$',
        r'\s*(?:시즌|season|part|파트)\s*\d+\s*$',
        r'[,\.\-·:;]\s*$',
    ]
    for pattern in tail_patterns:
        s = re.sub(pattern, '', s, flags=re.I)

    s = re.sub(r'[\(\[]완(?:결)?[\)\]]', '', s)
    s = re.sub(r'\(\s*\)|\[\s*\]', '', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s, is_completed


def extract_path_tags(file_path: str, root_dir: str) -> Tuple[List[str], bool]:
    """조상 폴더(장르)에서 태그 추출. 바로 위 폴더(시리즈명)는 제외."""
    rel = os.path.relpath(os.path.dirname(file_path), root_dir)
    tags: Set[str] = set()
    path_completed = False
    if rel in (".", ""):
        return [], False
    parts = rel.replace("\\", "/").split("/")
    for p in parts:
        _, comp = clean_text(p)
        if comp:
            path_completed = True
    if parts:
        parts = parts[:-1]  # 시리즈(제목) 폴더 제외
    for p in parts:
        cp, _ = clean_text(p)
        if not cp or cp.lower() in IGNORE_FOLDER_NAMES:
            continue
        if SPLIT_SPACE_IN_TAGS:
            for sub in cp.split():
                if sub and sub.lower() not in IGNORE_FOLDER_NAMES:
                    tags.add(sub)
        else:
            tags.add(cp)
    return sorted(tags), path_completed


def _split_tag_field(value: str) -> List[str]:
    if not value:
        return []
    return [t.strip() for t in re.split(r"[,;/]", value) if t.strip()]


# ---------------------------------------------------------------------------
# 스캔 상태 (전역)
# ---------------------------------------------------------------------------
_scan_lock = threading.Lock()
_cancel_event = threading.Event()


class ScanCancelled(Exception):
    """스캔 취소 신호."""
    pass


scan_status: Dict[str, object] = {
    "running": False,
    "mode": "quick",          # quick | deep
    "library_id": None,
    "library_name": None,
    "found": 0,
    "processed": 0,
    "added": 0,
    "updated": 0,
    "trashed": 0,             # 사라진 파일 → 휴지통
    "restored": 0,            # 휴지통 → 복구(이동/복원)
    "epub_indexed": 0,        # EPUB 목차/삽화 사전분석 건수
    "workers": 1,             # 병렬 처리 스레드 수
    "removed": 0,             # (호환용, 영구삭제는 별도)
    "cancel_requested": False,  # 취소 요청됨(아직 진행 중)
    "cancelled": False,         # 취소로 종료됨
    "started_at": None,
    "finished_at": None,
    "error": None,
}


def _reset_status():
    scan_status.update({
        "found": 0, "processed": 0, "added": 0, "updated": 0,
        "trashed": 0, "restored": 0, "removed": 0, "epub_indexed": 0,
        "cancel_requested": False, "cancelled": False,
        "error": None, "finished_at": None,
    })


def request_cancel() -> bool:
    """진행 중인 스캔에 취소를 요청. 실제 중단은 다음 파일 처리 지점에서 이뤄짐."""
    _cancel_event.set()
    scan_status["cancel_requested"] = True
    return bool(scan_status.get("running"))


def _check_cancel():
    if _cancel_event.is_set():
        raise ScanCancelled()


# ---------------------------------------------------------------------------
# DB 헬퍼
# ---------------------------------------------------------------------------
def _get_or_create_tag(db: Session, name: str, tag_cache: Dict[str, Tag]) -> Tag:
    if name in tag_cache:
        return tag_cache[name]
    tag = db.scalar(select(Tag).where(Tag.name == name))
    if tag is None:
        tag = Tag(name=name)
        db.add(tag)
        db.flush()
    tag_cache[name] = tag
    return tag


def _apply_auto_tags(db: Session, book: Book, names: List[str], tag_cache: Dict[str, Tag]):
    """수동(manual) 태그는 유지하고 auto 태그만 새로 셋팅."""
    existing = {bt.tag.name: bt for bt in book.tags}
    manual_names = {n for n, bt in existing.items() if bt.source == "manual"}
    # 기존 auto 링크 제거
    for n, bt in list(existing.items()):
        if bt.source == "auto":
            db.delete(bt)
    db.flush()
    for n in names:
        if n in manual_names:
            continue
        tag = _get_or_create_tag(db, n, tag_cache)
        db.add(BookTag(book_id=book.id, tag_id=tag.id, source="auto"))
    db.flush()


def _series_name_for(file_path: str, root_dir: str) -> Tuple[str, str]:
    """(표시용 이름, 시리즈 폴더 절대경로)."""
    parent = os.path.dirname(file_path)
    base = os.path.basename(parent.rstrip("/"))
    if os.path.abspath(parent) == os.path.abspath(root_dir) or not base:
        base = os.path.basename(root_dir.rstrip("/")) or "기타"
    name, _ = clean_text(base)
    if not name:
        name = base
    return name, parent


def _get_or_create_series(db: Session, lib: Library, file_path: str,
                          series_cache: Dict[str, Series]) -> Series:
    name, folder = _series_name_for(file_path, lib.path)
    if folder in series_cache:
        return series_cache[folder]
    s = db.scalar(select(Series).where(Series.path == folder))
    if s is None:
        s = Series(library_id=lib.id, name=name, sort_name=name.lower(),
                   path=folder, book_count=0)
        db.add(s)
        db.flush()
    else:
        if s.name != name:
            s.name = name
            s.sort_name = name.lower()
    series_cache[folder] = s
    return s


# ---------------------------------------------------------------------------
# 파일명 태그 추출 (ComicInfo.xml 이 없어도 정규식/키워드로 태그 부여)
# ---------------------------------------------------------------------------
_NUMERIC_BRACKET = re.compile(r"^[\d\s\.\-~vV권화회話巻卷]+$")


def extract_filename_tags(stem: str, rules: dict) -> List[str]:
    if not rules or not rules.get("enabled", True):
        return []
    tags: Set[str] = set()
    # 대괄호 [ ... ] 내부를 태그로 (순수 숫자/권·화 표기는 제외)
    if rules.get("bracket_tags", True):
        for m in re.findall(r"\[([^\[\]]{1,40})\]", stem):
            t = m.strip()
            if t and not _NUMERIC_BRACKET.match(t):
                tags.add(t)
    low = stem.lower()
    for kw in rules.get("keywords", []) or []:
        m = (kw.get("match") or "").strip()
        tag = (kw.get("tag") or m).strip()
        if m and m.lower() in low and tag:
            tags.add(tag)
    for rx in rules.get("regex", []) or []:
        pat = rx.get("pattern")
        if not pat:
            continue
        try:
            mm = re.search(pat, stem)
        except re.error:
            continue
        if not mm:
            continue
        grp = rx.get("group")
        if grp:
            try:
                g = mm.group(int(grp))
            except (IndexError, ValueError):
                g = None
            if g and g.strip():
                tags.add(g.strip())
        elif rx.get("tag"):
            tags.add(rx["tag"].strip())
    return sorted(tags)


# ---------------------------------------------------------------------------
# 파일 메타데이터 추출
# ---------------------------------------------------------------------------
def _extract_meta(file_path: str, fmt: str) -> Dict[str, object]:
    """파일에서 제목/작가/출판사/언어/설명/권번호/추가태그/페이지수를 추출."""
    stem = os.path.splitext(os.path.basename(file_path))[0]
    title_clean, title_completed = clean_text(stem)
    meta: Dict[str, object] = {
        "title": title_clean or stem,
        "author": None,
        "publisher": None,
        "language": None,
        "series_index": None,
        "description": None,
        "extra_tags": [],
        "page_count": -1,
    }
    extra_tags: List[str] = []

    if fmt in ("cbz", "zip"):
        ci = formats.read_comicinfo(file_path)
        if ci.get("Title"):
            t, _ = clean_text(ci["Title"])
            meta["title"] = t or meta["title"]
        meta["author"] = ci.get("Writer") or ci.get("Penciller") or None
        meta["publisher"] = ci.get("Publisher") or None
        meta["language"] = ci.get("LanguageISO") or None
        meta["series_index"] = ci.get("Number") or None
        meta["description"] = ci.get("Summary") or None
        for key in ("Genre", "Tags"):
            extra_tags += _split_tag_field(ci.get(key, ""))
        pc = len(formats.list_comic_pages(file_path))
        meta["page_count"] = pc if pc > 0 else -1
    elif fmt == "epub":
        info = formats.epub_info(file_path)
        if info.get("title"):
            meta["title"] = str(info["title"]).strip() or meta["title"]
        meta["author"] = (info.get("author") or None)
        meta["publisher"] = (info.get("publisher") or None)
        meta["language"] = (info.get("language") or None)
        meta["description"] = (info.get("description") or None)
    elif fmt == "pdf":
        pc = formats.pdf_page_count(file_path)
        if pc:
            meta["page_count"] = pc

    if title_completed:
        extra_tags.append("완결")
    meta["extra_tags"] = extra_tags
    return meta


def _auto_tags_for(file_path: str, lib_path: str, fmt: str,
                   meta: Dict[str, object], rules: dict) -> List[str]:
    stem = os.path.splitext(os.path.basename(file_path))[0]
    path_tags, path_completed = extract_path_tags(file_path, lib_path)
    auto: Set[str] = set(path_tags) | set(meta.get("extra_tags") or [])
    if path_completed:
        auto.add("완결")
    if config.FILENAME_TAGS:
        auto.update(extract_filename_tags(stem, rules))
    return sorted(auto)



def _precompute_epub_meta(book: Book, file_path: str) -> bool:
    """EPUB 목차·삽화를 미리 분석해 DB에 저장. 리더가 열 때 대기하지 않도록."""
    try:
        st = formats.epub_structure(file_path)
    except Exception:
        st = None
    if not st:
        return False
    try:
        book.epub_meta = json.dumps(st, ensure_ascii=False)
    except Exception:
        return False
    return True


def _write_book_fields(book: Book, meta: Dict[str, object], size: int, mtime: int):
    pc = meta["page_count"]
    book.title = meta["title"]
    book.sort_title = str(meta["title"]).lower()
    book.file_size = size
    book.mtime = mtime
    book.author = meta["author"] or None
    book.publisher = meta["publisher"] or None
    book.language = meta["language"] or None
    book.series_index = meta["series_index"] or None
    if meta.get("description"):
        book.description = meta["description"]
    book.page_count = pc if isinstance(pc, int) and pc >= 0 else None
    book.meta_updated_at = utcnow()
    book.updated_at = utcnow()


# ---------------------------------------------------------------------------
# 스캔 본체
# ---------------------------------------------------------------------------
def _scan_library_inner(db: Session, lib: Library, deep: bool = False):
    rules = settings_store.get_tag_rules(db)
    opts = settings_store.get_scan_options(db)
    seen_paths: Set[str] = set()
    tag_cache: Dict[str, Tag] = {}
    series_cache: Dict[str, Series] = {}
    touched_series: Set[int] = set()

    # --- 기존 책 사전 로드 (파일당 개별 쿼리 방지 → 수만개도 빠르게) ---
    existing = {}   # path -> (id, mtime, has_thumb, status, size, series_id, has_epub_meta)
    trashed_index: Dict[Tuple[int, str], List[int]] = {}  # (size, basename) -> [book_id]
    for bid, bpath, bmtime, bthumb, bstatus, bsize, bsid, bemeta in db.execute(
        select(Book.id, Book.path, Book.mtime, Book.has_thumb, Book.status,
               Book.file_size, Book.series_id, Book.epub_meta)
        .where(Book.library_id == lib.id)
    ).all():
        existing[bpath] = (bid, bmtime, bool(bthumb), bstatus, bsize, bsid, bool(bemeta))
        if bstatus == "trashed":
            trashed_index.setdefault((int(bsize or 0), os.path.basename(bpath)), []).append(bid)

    def _pop_trashed_match(size: int, basename: str):
        key = (int(size), basename)
        lst = trashed_index.get(key)
        if lst:
            bid = lst.pop(0)
            if not lst:
                trashed_index.pop(key, None)
            return bid
        return None

    # --- 1단계: 파일 목록 수집 (가벼움). 처리 대상만 todo 에 모은다 ---
    todo: List[Tuple[str, str, int, int, str, bool, bool]] = []
    # (fpath, fn, mtime, size, fmt, need_thumb, need_epub)
    for base, dirs, files in os.walk(lib.path):
        _check_cancel()  # 취소 요청 시 여기서 중단 → 아래 '사라진 파일' 정리(휴지통) 단계로 가지 않음
        dirs[:] = [d for d in dirs if not d.startswith(".") and d.lower() != "__macosx"]
        for fn in files:
            _check_cancel()
            ext = os.path.splitext(fn)[1].lower()
            if ext not in config.SUPPORTED_EXTS:
                continue
            fpath = os.path.join(base, fn)
            seen_paths.add(fpath)
            try:
                st = os.stat(fpath)
            except OSError:
                continue
            mtime = int(st.st_mtime)
            size = st.st_size
            scan_status["found"] = int(scan_status["found"]) + 1  # type: ignore
            fmt = ext[1:]

            prior = existing.get(fpath)
            # 변경 없음 + 이미 활성 + 썸네일 있음 → 스킵 (증분). deep 이면 항상 재처리.
            if (prior and not deep and prior[3] == "active"
                    and prior[1] == mtime and prior[2]):
                touched_series.add(prior[5])  # 갱신시각 재계산용
                continue

            need_thumb = bool(deep or (prior is None) or (not prior[2]))
            need_epub = bool(fmt == "epub" and opts.get("epub_structure", True)
                             and (deep or prior is None or not prior[6]))
            todo.append((fpath, fn, mtime, size, fmt, need_thumb, need_epub))

    # --- 2단계: 무거운 작업(표지 추출/리사이즈, 메타 파싱, EPUB 구조)을 병렬 처리 ---
    # SQLite 세션은 스레드 안전하지 않으므로 DB 쓰기는 3단계(메인 스레드)에서만 한다.

    def _prepare(entry):
        fpath, fn, mtime, size, fmt, need_thumb, need_epub = entry
        out: Dict[str, object] = {}
        try:
            out["meta"] = _extract_meta(fpath, fmt)
        except Exception:
            return fpath, None
        try:
            out["tags"] = _auto_tags_for(fpath, lib.path, fmt, out["meta"], rules)
        except Exception:
            out["tags"] = []
        if need_thumb and opts.get("thumbnails", True):
            try:
                out["thumb"] = thumbnails.render_thumb_jpeg(
                    fpath, fmt, str(out["meta"].get("title") or ""))
            except Exception:
                out["thumb"] = None
        if need_epub:
            try:
                out["epub"] = formats.epub_structure(fpath)
            except Exception:
                out["epub"] = None
        return fpath, out

    workers = config.scan_workers()
    scan_status["workers"] = workers
    # 묶음 단위로 준비→DB반영을 반복한다.
    #  - 전체를 한 번에 준비하면 진행률이 멈춘 것처럼 보이고 메모리도 과도하게 쓴다.
    chunk_size = max(8, workers * 8)
    pool = ThreadPoolExecutor(max_workers=workers) if workers > 1 else None
    prepared: Dict[str, Dict[str, object]] = {}

    def _prepare_chunk(start: int):
        """todo[start:start+chunk_size] 를 병렬로 미리 처리."""
        prepared.clear()
        chunk = todo[start:start + chunk_size]
        if pool is not None and len(chunk) > 1:
            for fp, out in pool.map(_prepare, chunk):
                if out is not None:
                    prepared[fp] = out
        else:
            for e in chunk:
                fp, out = _prepare(e)
                if out is not None:
                    prepared[fp] = out

    # --- 3단계: 묶음 준비 + DB 반영 (DB 쓰기는 메인 스레드에서만) ---
    try:
        for idx, (fpath, fn, mtime, size, fmt, need_thumb, need_epub) in enumerate(todo):
            _check_cancel()
            if fpath not in prepared:
                _prepare_chunk(idx)
            pre = prepared.get(fpath)
            if pre is None:
                scan_status["processed"] = int(scan_status["processed"]) + 1  # type: ignore
                continue
            meta = pre["meta"]
            all_auto = pre.get("tags") or []
            prior = existing.get(fpath)
            series = _get_or_create_series(db, lib, fpath, series_cache)

            book = None
            was_trashed = False
            if prior:
                book = db.get(Book, prior[0])
                was_trashed = (prior[3] == "trashed")
            else:
                # 새 경로 → 휴지통에서 같은 (크기, 파일명) 매칭이 있으면 '이동'으로 간주해 복구
                mid = _pop_trashed_match(size, fn)
                if mid is not None:
                    book = db.get(Book, mid)
                    was_trashed = True
                    if book:
                        book.path = fpath  # 새 위치로 갱신 (태그/평점/진행률 유지)

            is_new = book is None
            if is_new:
                book = Book(
                    series_id=series.id, library_id=lib.id, path=fpath, fmt=fmt,
                    title=meta["title"], sort_title=str(meta["title"]).lower(),
                    file_size=size, mtime=mtime, status="active",
                    created_at=utcnow(), updated_at=utcnow(),
                )
                db.add(book)
                db.flush()
                scan_status["added"] = int(scan_status["added"]) + 1  # type: ignore
            else:
                book.series_id = series.id
                book.library_id = lib.id
                book.status = "active"
                book.trashed_at = None
                _write_book_fields(book, meta, size, mtime)
                db.flush()
                if was_trashed:
                    scan_status["restored"] = int(scan_status["restored"]) + 1  # type: ignore
                else:
                    scan_status["updated"] = int(scan_status["updated"]) + 1  # type: ignore

            if is_new:
                _write_book_fields(book, meta, size, mtime)
                db.flush()

            _apply_auto_tags(db, book, all_auto, tag_cache)

            # 병렬 단계에서 미리 만들어 둔 표지를 기록 (여기선 파일 쓰기만 → 빠름)
            want_thumb = need_thumb or (was_trashed and not thumbnails.book_thumb_path(book.id).exists())
            if want_thumb and opts.get("thumbnails", True):
                jpeg = pre.get("thumb")
                if jpeg is None and was_trashed:
                    jpeg = thumbnails.render_thumb_jpeg(fpath, fmt, str(meta["title"]))
                ok = thumbnails.write_thumb_jpeg(book.id, jpeg)
                book.has_thumb = bool(ok) or book.has_thumb

            # EPUB 목차·삽화: 병렬 단계 결과를 저장 (열 때 대기 없이 바로 보이도록)
            est = pre.get("epub")
            if est:
                try:
                    book.epub_meta = json.dumps(est, ensure_ascii=False)
                    scan_status["epub_indexed"] = int(scan_status.get("epub_indexed", 0)) + 1  # type: ignore
                except Exception:
                    pass
            db.flush()

            touched_series.add(series.id)
            scan_status["processed"] = int(scan_status["processed"]) + 1  # type: ignore
            if int(scan_status["processed"]) % 200 == 0:  # type: ignore
                db.commit()


    finally:
        if pool is not None:
            pool.shutdown(wait=False)
    db.commit()

    # --- 사라진 파일 → 휴지통(소프트 삭제). DB/태그/진행률/평점/썸네일 유지 ---
    for bpath, (bid, _m, _t, bstatus, _s, _sid, _em) in existing.items():
        if bpath not in seen_paths and bstatus == "active":
            b = db.get(Book, bid)
            if b:
                b.status = "trashed"
                b.trashed_at = utcnow()
                touched_series.add(b.series_id)
                scan_status["trashed"] = int(scan_status["trashed"]) + 1  # type: ignore
    db.commit()

    _recompute_series(db, lib, touched_series)
    db.commit()


def _recompute_series(db: Session, lib: Library, series_ids: Set[int]):
    all_series = db.scalars(select(Series).where(Series.library_id == lib.id)).all()
    for s in all_series:
        active = db.scalars(
            select(Book).where(Book.series_id == s.id, Book.status == "active")
        ).all()
        any_book = db.scalar(
            select(func.count(Book.id)).where(Book.series_id == s.id)
        ) or 0
        if any_book == 0:
            # 활성/휴지통 모두 없음 → 시리즈 삭제
            _safe_unlink_series_thumb(s.id)
            db.delete(s)
            continue
        s.book_count = len(active)   # 활성 책만 카운트 (휴지통 제외)
        if not active:
            # 전부 휴지통 → 시리즈는 남기되 목록엔 숨김(book_count=0)
            continue
        latest = max(active, key=lambda b: b.mtime)
        s.updated_at = dt.datetime.utcfromtimestamp(latest.mtime)
        books_sorted = sorted(active, key=lambda b: formats.natural_key(b.sort_title))
        cover_book = next((b for b in books_sorted if b.has_thumb), books_sorted[0])
        if s.cover_book_id != cover_book.id:
            s.cover_book_id = cover_book.id
            thumbnails.link_series_thumbnail(s.id, cover_book.id)
        elif not thumbnails.series_thumb_path(s.id).exists():
            thumbnails.link_series_thumbnail(s.id, cover_book.id)


def _safe_unlink_series_thumb(series_id: int):
    p = thumbnails.series_thumb_path(series_id)
    try:
        p.unlink(missing_ok=True)  # py3.8+ guard below
    except TypeError:
        if p.exists():
            p.unlink()
    except OSError:
        pass


# ---------------------------------------------------------------------------
# 단일 책 메타데이터 새로고침 (파일 재파싱, 사용자 데이터 유지)
# ---------------------------------------------------------------------------
def refresh_book(db: Session, book: Book, regen_thumb: bool = True) -> bool:
    """한 권의 임베드/경로/파일명 메타데이터를 강제로 다시 읽어 반영."""
    if not os.path.exists(book.path):
        return False
    rules = settings_store.get_tag_rules(db)
    fmt = book.fmt
    try:
        st = os.stat(book.path)
    except OSError:
        return False
    meta = _extract_meta(book.path, fmt)
    all_auto = _auto_tags_for(book.path, book.library.path, fmt, meta, rules)
    _write_book_fields(book, meta, st.st_size, int(st.st_mtime))
    db.flush()
    _apply_auto_tags(db, book, all_auto, {})
    if fmt == "epub":
        _precompute_epub_meta(book, book.path)
    if regen_thumb:
        ok = thumbnails.generate_book_thumbnail(book.id, book.path, fmt, str(meta["title"]))
        book.has_thumb = bool(ok) or book.has_thumb
    db.flush()
    # 시리즈 표지/통계 갱신
    _recompute_series(db, book.library, {book.series_id})
    db.commit()
    return True


def refresh_series(db: Session, series: Series) -> int:
    books = db.scalars(
        select(Book).where(Book.series_id == series.id, Book.status == "active")
    ).all()
    n = 0
    for b in books:
        if refresh_book(db, b, regen_thumb=True):
            n += 1
    return n


# ---------------------------------------------------------------------------
# 공개 진입점
# ---------------------------------------------------------------------------
def scan_library(library_id: int, deep: bool = False):
    """단일 라이브러리 스캔 (동기). 백그라운드 스레드에서 호출됨."""
    with _scan_lock:
        db = SessionLocal()
        try:
            lib = db.get(Library, library_id)
            if lib is None:
                return
            scan_status.update({
                "running": True, "mode": ("deep" if deep else "quick"),
                "library_id": lib.id, "library_name": lib.name,
                "started_at": utcnow().isoformat(),
            })
            _reset_status()
            _scan_library_inner(db, lib, deep=deep)
            settings_store.set_last_run(db, "deep" if deep else "quick")
        except ScanCancelled:
            db.rollback()
            scan_status["cancelled"] = True
        except Exception as e:  # noqa
            scan_status["error"] = str(e)
        finally:
            scan_status["running"] = False
            scan_status["cancel_requested"] = False
            scan_status["finished_at"] = utcnow().isoformat()
            db.close()


def scan_all(deep: bool = False):
    _cancel_event.clear()  # 전체 스캔 시작점: 취소 흔적 제거
    with _scan_lock:
        db = SessionLocal()
        try:
            lib_ids = [l.id for l in db.scalars(select(Library)).all()]
        finally:
            db.close()
    for lid in lib_ids:
        scan_library(lid, deep=deep)
        if scan_status.get("cancelled"):  # 취소되면 남은 라이브러리는 건너뜀
            break


def scan_library_async(library_id: int, deep: bool = False):
    if scan_status.get("running"):
        return False
    _cancel_event.clear()
    threading.Thread(target=scan_library, args=(library_id, deep), daemon=True).start()
    return True


def scan_all_async(deep: bool = False):
    if scan_status.get("running"):
        return False
    _cancel_event.clear()
    threading.Thread(target=scan_all, kwargs={"deep": deep}, daemon=True).start()
    return True
