# -*- coding: utf-8 -*-
"""관리 기능 라우터: 휴지통 / 메타데이터 새로고침·가져오기 / 예약 스캔 / 태그 규칙 / 분석."""
import os
import datetime as dt

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from .. import (security, schemas, serializers, scanner, metadata,
                settings_store, thumbnails, config)
from ..database import get_db
from ..models import (User, Library, Series, Book, Tag, BookTag, Rating,
                      ReadProgress, utcnow)

router = APIRouter(prefix="/api", tags=["manage"])


def _acc_ids(db, user):
    return set(security.accessible_library_ids(db, user))


def _require_book(db, user, book_id) -> Book:
    book = db.get(Book, book_id)
    if not book or book.library_id not in _acc_ids(db, user):
        raise HTTPException(status_code=404, detail="책을 찾을 수 없습니다.")
    return book


# =========================================================================
# 휴지통 (소프트 삭제)
# =========================================================================
@router.get("/trash")
def list_trash(_: User = Depends(security.require_admin), db: Session = Depends(get_db),
               page: int = Query(1, ge=1), size: int = Query(50, ge=1, le=200)):
    stmt = select(Book).where(Book.status == "trashed").order_by(Book.trashed_at.desc())
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(stmt.offset((page - 1) * size).limit(size)).all()
    items = [{
        "id": b.id,
        "title": b.title,
        "series_name": b.series.name if b.series else None,
        "library_id": b.library_id,
        "format": b.fmt,
        "file_size": b.file_size,
        "path": b.path,
        "trashed_at": b.trashed_at.isoformat() if b.trashed_at else None,
        "file_exists": os.path.exists(b.path),
    } for b in rows]
    return {"items": items, "total": total, "page": page, "size": size}


@router.post("/trash/{book_id}/restore")
def restore_trash(book_id: int, _: User = Depends(security.require_admin),
                  db: Session = Depends(get_db)):
    b = db.get(Book, book_id)
    if not b or b.status != "trashed":
        raise HTTPException(status_code=404, detail="휴지통 항목을 찾을 수 없습니다.")
    if not os.path.exists(b.path):
        raise HTTPException(status_code=400,
                            detail="원본 파일이 없어 복구할 수 없습니다. (파일이 돌아오면 스캔 시 자동 복구됩니다)")
    b.status = "active"
    b.trashed_at = None
    db.flush()
    scanner._recompute_series(db, b.library, {b.series_id})
    db.commit()
    return {"ok": True}


@router.delete("/trash/{book_id}")
def delete_trash(book_id: int, _: User = Depends(security.require_admin),
                 db: Session = Depends(get_db)):
    """휴지통 항목 영구 삭제 (DB 레코드/썸네일 제거)."""
    b = db.get(Book, book_id)
    if not b or b.status != "trashed":
        raise HTTPException(status_code=404, detail="휴지통 항목을 찾을 수 없습니다.")
    sid, lib = b.series_id, b.library
    thumbnails.delete_book_thumbnail(b.id)
    db.delete(b)
    db.flush()
    scanner._recompute_series(db, lib, {sid})
    db.commit()
    return {"ok": True}


@router.post("/trash/empty")
def empty_trash(_: User = Depends(security.require_admin), db: Session = Depends(get_db)):
    rows = db.scalars(select(Book).where(Book.status == "trashed")).all()
    libs = {}
    touched = {}
    n = 0
    for b in rows:
        libs[b.library_id] = b.library
        touched.setdefault(b.library_id, set()).add(b.series_id)
        thumbnails.delete_book_thumbnail(b.id)
        db.delete(b)
        n += 1
    db.flush()
    for lid, sids in touched.items():
        scanner._recompute_series(db, libs[lid], sids)
    db.commit()
    return {"ok": True, "deleted": n}


# =========================================================================
# 메타데이터 새로고침 (파일 재파싱)
# =========================================================================
@router.post("/books/{book_id}/refresh")
def refresh_book(book_id: int, admin: User = Depends(security.require_admin),
                 db: Session = Depends(get_db)):
    book = db.get(Book, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="책을 찾을 수 없습니다.")
    ok = scanner.refresh_book(db, book, regen_thumb=True)
    if not ok:
        raise HTTPException(status_code=400, detail="파일을 읽을 수 없습니다.")
    db.refresh(book)
    return {"ok": True, "book": serializers.book_to_dict(db, book, admin, with_tags=True)}


@router.post("/series/{series_id}/refresh")
def refresh_series(series_id: int, admin: User = Depends(security.require_admin),
                   db: Session = Depends(get_db)):
    s = db.get(Series, series_id)
    if not s:
        raise HTTPException(status_code=404, detail="시리즈를 찾을 수 없습니다.")
    n = scanner.refresh_series(db, s)
    return {"ok": True, "refreshed": n}


# =========================================================================
# 외부 메타데이터 가져오기
# =========================================================================
@router.get("/metadata/providers")
def metadata_providers(_: User = Depends(security.require_admin)):
    return {"enabled": config.METADATA_ENABLED, "providers": metadata.list_providers()}


@router.get("/books/{book_id}/metadata/search")
def metadata_search(book_id: int, provider: str = Query(...), query: str = Query(None),
                    admin: User = Depends(security.require_admin),
                    db: Session = Depends(get_db)):
    if not config.METADATA_ENABLED:
        raise HTTPException(status_code=400, detail="메타데이터 기능이 비활성화되어 있습니다.")
    book = db.get(Book, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="책을 찾을 수 없습니다.")
    q = (query or book.title or "").strip()
    results = metadata.search(provider, q)
    return {"query": q, "provider": provider, "results": results}


@router.post("/books/{book_id}/metadata/apply")
def metadata_apply(book_id: int, body: schemas.MetadataApplyIn,
                   admin: User = Depends(security.require_admin),
                   db: Session = Depends(get_db)):
    if not config.METADATA_ENABLED:
        raise HTTPException(status_code=400, detail="메타데이터 기능이 비활성화되어 있습니다.")
    book = db.get(Book, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="책을 찾을 수 없습니다.")
    cand = metadata.fetch(body.provider, body.external_id)
    if not cand:
        raise HTTPException(status_code=502, detail="공급자에서 메타데이터를 가져오지 못했습니다.")

    applied = []
    f = set(body.fields or [])
    if "description" in f and cand.get("description"):
        book.description = cand["description"]; applied.append("description")
    if "author" in f and cand.get("authors"):
        book.author = ", ".join(cand["authors"]); applied.append("author")
    if "publisher" in f and cand.get("publisher"):
        book.publisher = cand["publisher"]; applied.append("publisher")
    if "language" in f and cand.get("language"):
        book.language = cand["language"]; applied.append("language")
    if "title" in f and cand.get("title"):
        book.title = cand["title"]; book.sort_title = cand["title"].lower(); applied.append("title")

    if "tags" in f and cand.get("tags"):
        # 외부 태그는 수동(manual) 로 저장 → 재스캔해도 유지
        for name in cand["tags"]:
            name = (name or "").strip()
            if not name:
                continue
            t = db.scalar(select(Tag).where(Tag.name == name))
            if not t:
                t = Tag(name=name); db.add(t); db.flush()
            ex = db.scalar(select(BookTag).where(
                BookTag.book_id == book.id, BookTag.tag_id == t.id))
            if not ex:
                db.add(BookTag(book_id=book.id, tag_id=t.id, source="manual"))
        applied.append("tags")

    if body.replace_cover and cand.get("cover_url"):
        raw = metadata.download_image(cand["cover_url"])
        if raw and thumbnails.save_cover_from_bytes(book.id, raw):
            book.has_thumb = True
            if book.series and book.series.cover_book_id == book.id:
                thumbnails.link_series_thumbnail(book.series_id, book.id)
            applied.append("cover")

    book.meta_updated_at = utcnow()
    book.updated_at = utcnow()
    db.commit()
    db.refresh(book)
    return {"ok": True, "applied": applied,
            "book": serializers.book_to_dict(db, book, admin, with_tags=True)}


# =========================================================================
# 예약 스캔 스케줄
# =========================================================================
@router.get("/scan/schedule")
def get_schedule(_: User = Depends(security.require_admin), db: Session = Depends(get_db)):
    cfg = settings_store.get_scan_schedule(db)
    cfg["last_quick"] = (settings_store.get_last_run(db, "quick") or None)
    cfg["last_deep"] = (settings_store.get_last_run(db, "deep") or None)
    cfg["last_quick"] = cfg["last_quick"].isoformat() if cfg["last_quick"] else None
    cfg["last_deep"] = cfg["last_deep"].isoformat() if cfg["last_deep"] else None
    return cfg


@router.put("/scan/schedule")
def put_schedule(body: schemas.ScheduleIn, _: User = Depends(security.require_admin),
                 db: Session = Depends(get_db)):
    patch = {k: v for k, v in body.model_dump().items() if v is not None}
    if "deep_at" in patch:
        # 형식 검증
        try:
            hh, mm = patch["deep_at"].split(":")
            int(hh); int(mm)
        except Exception:
            raise HTTPException(status_code=400, detail="deep_at 은 HH:MM 형식이어야 합니다.")
    return settings_store.set_scan_schedule(db, patch)


# =========================================================================
# 파일명 태그 규칙
# =========================================================================
@router.get("/scan/tag-rules")
def get_tag_rules(_: User = Depends(security.require_admin), db: Session = Depends(get_db)):
    return settings_store.get_tag_rules(db)


@router.put("/scan/tag-rules")
def put_tag_rules(body: schemas.TagRulesIn, _: User = Depends(security.require_admin),
                  db: Session = Depends(get_db)):
    patch = {k: v for k, v in body.model_dump().items() if v is not None}
    return settings_store.set_tag_rules(db, patch)


# =========================================================================
# 분석 (라이브러리 통계)
# =========================================================================
@router.get("/analytics")
def analytics(admin: User = Depends(security.require_admin), db: Session = Depends(get_db)):
    active = Book.status == "active"
    total_books = db.scalar(select(func.count(Book.id)).where(active)) or 0
    trashed_books = db.scalar(
        select(func.count(Book.id)).where(Book.status == "trashed")) or 0
    total_series = db.scalar(
        select(func.count(Series.id)).where(Series.book_count > 0)) or 0
    total_libs = db.scalar(select(func.count(Library.id))) or 0
    total_tags = db.scalar(select(func.count(Tag.id))) or 0
    total_size = db.scalar(select(func.coalesce(func.sum(Book.file_size), 0)).where(active)) or 0

    by_format = [
        {"format": fmt, "count": cnt}
        for fmt, cnt in db.execute(
            select(Book.fmt, func.count(Book.id)).where(active)
            .group_by(Book.fmt).order_by(func.count(Book.id).desc())
        ).all()
    ]

    by_library = []
    for lib in db.scalars(select(Library).order_by(Library.name)).all():
        bcount = db.scalar(select(func.count(Book.id)).where(
            Book.library_id == lib.id, active)) or 0
        scount = db.scalar(select(func.count(Series.id)).where(
            Series.library_id == lib.id, Series.book_count > 0)) or 0
        size = db.scalar(select(func.coalesce(func.sum(Book.file_size), 0)).where(
            Book.library_id == lib.id, active)) or 0
        by_library.append({"id": lib.id, "name": lib.name, "restricted": lib.restricted,
                           "series": scount, "books": bcount, "size": size})

    top_tags = [
        {"name": n, "count": c}
        for n, c in db.execute(
            select(Tag.name, func.count(BookTag.book_id))
            .join(BookTag, BookTag.tag_id == Tag.id)
            .join(Book, Book.id == BookTag.book_id)
            .where(active)
            .group_by(Tag.name).order_by(func.count(BookTag.book_id).desc(), Tag.name)
            .limit(20)
        ).all()
    ]

    largest = [
        {"id": bid, "title": title, "format": fmt, "size": size}
        for bid, title, fmt, size in db.execute(
            select(Book.id, Book.title, Book.fmt, Book.file_size)
            .where(active).order_by(Book.file_size.desc()).limit(5)
        ).all()
    ]

    since = utcnow() - dt.timedelta(days=30)
    recent_added = db.scalar(
        select(func.count(Book.id)).where(active, Book.created_at >= since)) or 0

    completed = db.scalar(
        select(func.count(ReadProgress.id)).join(Book, Book.id == ReadProgress.book_id)
        .where(ReadProgress.user_id == admin.id, ReadProgress.completed == True, active)  # noqa
    ) or 0
    in_progress = db.scalar(
        select(func.count(ReadProgress.id)).join(Book, Book.id == ReadProgress.book_id)
        .where(ReadProgress.user_id == admin.id, ReadProgress.completed == False, active)  # noqa
    ) or 0

    return {
        "totals": {
            "libraries": total_libs, "series": total_series, "books": total_books,
            "trashed": trashed_books, "tags": total_tags, "size": int(total_size),
        },
        "by_format": by_format,
        "by_library": by_library,
        "top_tags": top_tags,
        "largest_books": largest,
        "recent_added_30d": recent_added,
        "my_reading": {"completed": completed, "in_progress": in_progress},
    }


# =========================================================================
# 스캔 옵션
# =========================================================================
@router.get("/scan/options")
def get_scan_options(_: User = Depends(security.require_admin),
                     db: Session = Depends(get_db)):
    return settings_store.get_scan_options(db)


@router.put("/scan/options")
def put_scan_options(body: schemas.ScanOptionsIn,
                     _: User = Depends(security.require_admin),
                     db: Session = Depends(get_db)):
    return settings_store.set_scan_options(db, body.model_dump(exclude_none=True))


# =========================================================================
# 쓰레드 설정 (읽기용 / 작업용)
# =========================================================================
@router.get("/threads")
def get_threads(_: User = Depends(security.require_admin),
                db: Session = Depends(get_db)):
    import os
    cur = settings_store.get_threads(db)
    return {**cur, "cpu_count": os.cpu_count() or 1,
            "auto_scan_workers": config.scan_workers()}


@router.put("/threads")
def put_threads(body: schemas.ThreadsIn,
                _: User = Depends(security.require_admin),
                db: Session = Depends(get_db)):
    cur = settings_store.set_threads(db, body.model_dump(exclude_none=True))
    from ..main import apply_read_threads
    applied = apply_read_threads(int(cur.get("read_threads") or 0))
    return {**cur, "applied_read_threads": applied}


# =========================================================================
# 데이터베이스 최적화
# =========================================================================
@router.post("/db/optimize")
def db_optimize(full: bool = True, _: User = Depends(security.require_admin),
                db: Session = Depends(get_db)):
    import datetime as _dt
    from ..database import optimize_db
    if scanner.scan_status.get("running"):
        raise HTTPException(status_code=409, detail="스캔 중에는 실행할 수 없습니다.")
    r = optimize_db(full=full)
    settings_store.set_json(db, "last_db_optimize", _dt.datetime.utcnow().isoformat())
    return r


@router.get("/db/info")
def db_info(_: User = Depends(security.require_admin), db: Session = Depends(get_db)):
    import os
    from .. import config as cfg
    size = 0
    for suffix in ("", "-wal", "-shm"):
        p = str(cfg.DB_PATH) + suffix
        if os.path.exists(p):
            size += os.path.getsize(p)
    return {"size": size,
            "last_optimize": settings_store.get_json(db, "last_db_optimize", None),
            "auto_optimize_days": (settings_store.get_scan_schedule(db) or {}).get("optimize_every_days", 7)}


# =========================================================================
# 중복 파일 찾기
# =========================================================================
@router.get("/duplicates")
def find_duplicates(mode: str = "size_name", limit: int = 200,
                    _: User = Depends(security.require_admin),
                    db: Session = Depends(get_db)):
    """중복 후보를 묶어서 반환.
       mode=size_name : 파일 크기 + 파일명이 같은 것 (기본, 빠름)
       mode=title     : 정리된 제목이 같은 것 (다른 버전까지 넓게)
    """
    from collections import defaultdict
    rows = db.execute(
        select(Book.id, Book.path, Book.title, Book.file_size, Book.fmt,
               Book.library_id, Book.series_id)
        .where(Book.status == "active")
    ).all()
    groups = defaultdict(list)
    for bid, bpath, title, size, fmt, lib_id, sid in rows:
        if mode == "title":
            key = (str(title or "").strip().lower(),)
        else:
            key = (int(size or 0), os.path.basename(bpath).lower())
        groups[key].append({"id": bid, "path": bpath, "title": title,
                            "size": int(size or 0), "fmt": fmt,
                            "library_id": lib_id, "series_id": sid})
    dups = [g for g in groups.values() if len(g) > 1]
    dups.sort(key=lambda g: (-sum(b["size"] for b in g[1:]), g[0]["title"]))
    wasted = sum(b["size"] for g in dups for b in g[1:])
    return {"mode": mode, "groups": dups[:limit],
            "group_count": len(dups), "wasted": wasted}


@router.post("/duplicates/resolve")
def resolve_duplicates(body: schemas.IdsIn, permanent: bool = False,
                       _: User = Depends(security.require_admin),
                       db: Session = Depends(get_db)):
    """선택한 책들을 휴지통으로 보내거나(기본) 영구 삭제한다. 원본 파일은 건드리지 않는다."""
    n = 0
    for bid in body.ids:
        b = db.get(Book, bid)
        if not b:
            continue
        if permanent:
            thumbnails.delete_book_thumbnail(b.id)
            db.delete(b)
        else:
            b.status = "trashed"
            b.trashed_at = utcnow()
        n += 1
    db.commit()
    return {"ok": True, "count": n, "permanent": permanent}


# =========================================================================
# 백업 / 복원  (별점·즐겨찾기·읽은 기록·수동 태그·설정)
#   파일 경로를 기준으로 저장하므로, DB 를 새로 만들어 다시 스캔해도 복원된다.
# =========================================================================
BACKUP_VERSION = 1


@router.get("/backup")
def export_backup(_: User = Depends(security.require_admin),
                  db: Session = Depends(get_db)):
    from ..models import SeriesRating, Favorite, Setting, Tag, BookTag, User as U
    users = {u.id: u.username for u in db.scalars(select(U)).all()}
    bpath = {b.id: b.path for b in db.scalars(select(Book)).all()}
    spath = {s.id: s.path for s in db.scalars(select(Series)).all()}

    progress = [{"user": users.get(p.user_id), "path": bpath.get(p.book_id),
                 "page": p.page, "position": p.position, "completed": bool(p.completed),
                 "updated_at": p.updated_at.isoformat() if p.updated_at else None}
                for p in db.scalars(select(ReadProgress)).all()
                if users.get(p.user_id) and bpath.get(p.book_id)]
    ratings = [{"user": users.get(r.user_id), "path": bpath.get(r.book_id), "value": r.value}
               for r in db.scalars(select(Rating)).all()
               if users.get(r.user_id) and bpath.get(r.book_id)]
    sratings = [{"user": users.get(r.user_id), "series_path": spath.get(r.series_id),
                 "value": r.value}
                for r in db.scalars(select(SeriesRating)).all()
                if users.get(r.user_id) and spath.get(r.series_id)]
    favs = [{"user": users.get(f.user_id),
             "path": bpath.get(f.book_id) if f.book_id else None,
             "series_path": spath.get(f.series_id) if f.series_id else None}
            for f in db.scalars(select(Favorite)).all() if users.get(f.user_id)]
    tags = [{"path": bpath.get(bt.book_id), "tag": t.name}
            for bt, t in db.execute(
                select(BookTag, Tag).join(Tag, Tag.id == BookTag.tag_id)
                .where(BookTag.source == "manual")).all()
            if bpath.get(bt.book_id)]
    settings = {s.key: s.value for s in db.scalars(select(Setting)).all()}
    libs = [{"name": l.name, "path": l.path, "restricted": bool(l.restricted),
             "private": bool(getattr(l, "private", False)),
             "sort_order": l.sort_order or 0}
            for l in db.scalars(select(Library)).all()]
    return {"version": BACKUP_VERSION, "app": config.APP_VERSION,
            "created_at": utcnow().isoformat(),
            "libraries": libs, "settings": settings,
            "progress": progress, "ratings": ratings, "series_ratings": sratings,
            "favorites": favs, "manual_tags": tags,
            "counts": {"progress": len(progress), "ratings": len(ratings),
                       "series_ratings": len(sratings), "favorites": len(favs),
                       "manual_tags": len(tags), "libraries": len(libs)}}


@router.post("/restore")
def import_backup(data: dict, restore_libraries: bool = False,
                  _: User = Depends(security.require_admin),
                  db: Session = Depends(get_db)):
    """백업 JSON 을 되돌린다. 현재 DB 에 있는 항목만 매칭되며, 없는 건 건너뛴다."""
    from ..models import SeriesRating, Favorite, Setting, Tag, BookTag, User as U
    if not isinstance(data, dict) or "version" not in data:
        raise HTTPException(status_code=400, detail="백업 파일 형식이 아닙니다.")
    uid = {u.username: u.id for u in db.scalars(select(U)).all()}
    bid = {b.path: b.id for b in db.scalars(select(Book)).all()}
    sid = {s.path: s.id for s in db.scalars(select(Series)).all()}
    applied = {"progress": 0, "ratings": 0, "series_ratings": 0,
               "favorites": 0, "manual_tags": 0, "settings": 0, "libraries": 0}

    for it in data.get("progress", []):
        u, b = uid.get(it.get("user")), bid.get(it.get("path"))
        if not u or not b:
            continue
        p = db.scalar(select(ReadProgress).where(
            ReadProgress.user_id == u, ReadProgress.book_id == b))
        if not p:
            p = ReadProgress(user_id=u, book_id=b)
            db.add(p)
        p.page = int(it.get("page") or 0)
        p.position = it.get("position")
        p.completed = bool(it.get("completed"))
        p.updated_at = utcnow()
        applied["progress"] += 1

    for it in data.get("ratings", []):
        u, b = uid.get(it.get("user")), bid.get(it.get("path"))
        if not u or not b:
            continue
        r = db.scalar(select(Rating).where(Rating.user_id == u, Rating.book_id == b))
        if not r:
            r = Rating(user_id=u, book_id=b)
            db.add(r)
        r.value = max(1, min(5, int(it.get("value") or 0)))
        applied["ratings"] += 1

    for it in data.get("series_ratings", []):
        u, s = uid.get(it.get("user")), sid.get(it.get("series_path"))
        if not u or not s:
            continue
        r = db.scalar(select(SeriesRating).where(
            SeriesRating.user_id == u, SeriesRating.series_id == s))
        if not r:
            r = SeriesRating(user_id=u, series_id=s)
            db.add(r)
        r.value = max(1, min(5, int(it.get("value") or 0)))
        applied["series_ratings"] += 1

    for it in data.get("favorites", []):
        u = uid.get(it.get("user"))
        if not u:
            continue
        b = bid.get(it.get("path")) if it.get("path") else None
        s = sid.get(it.get("series_path")) if it.get("series_path") else None
        if not b and not s:
            continue
        col = Favorite.book_id == b if b else Favorite.series_id == s
        if not db.scalar(select(Favorite).where(Favorite.user_id == u, col)):
            db.add(Favorite(user_id=u, book_id=b, series_id=s))
            applied["favorites"] += 1

    for it in data.get("manual_tags", []):
        b = bid.get(it.get("path"))
        name = (it.get("tag") or "").strip()
        if not b or not name:
            continue
        t = db.scalar(select(Tag).where(Tag.name == name))
        if not t:
            t = Tag(name=name)
            db.add(t)
            db.flush()
        if not db.scalar(select(BookTag).where(
                BookTag.book_id == b, BookTag.tag_id == t.id)):
            db.add(BookTag(book_id=b, tag_id=t.id, source="manual"))
            applied["manual_tags"] += 1

    for k, v in (data.get("settings") or {}).items():
        st = db.scalar(select(Setting).where(Setting.key == k))
        if not st:
            st = Setting(key=k)
            db.add(st)
        st.value = v
        applied["settings"] += 1

    if restore_libraries:
        for it in data.get("libraries", []):
            if db.scalar(select(Library).where(Library.path == it.get("path"))):
                continue
            db.add(Library(name=it.get("name") or it.get("path"), path=it.get("path"),
                           restricted=bool(it.get("restricted")),
                           private=bool(it.get("private")),
                           sort_order=int(it.get("sort_order") or 0)))
            applied["libraries"] += 1

    db.commit()
    return {"ok": True, "applied": applied}


# =========================================================================
# 메모리 설정 (RAM 이 넉넉한 NAS 에서 조회 속도 향상)
# =========================================================================
@router.get("/memory")
def get_memory(_: User = Depends(security.require_admin), db: Session = Depends(get_db)):
    from ..database import runtime_mem
    cur = settings_store.get_memory(db)
    total_mb = None
    try:
        with open("/proc/meminfo") as f:
            for line in f:
                if line.startswith("MemTotal:"):
                    total_mb = int(line.split()[1]) // 1024
                    break
    except OSError:
        pass
    return {**cur, "applied": dict(runtime_mem), "system_ram_mb": total_mb}


@router.put("/memory")
def put_memory(body: schemas.MemoryIn, _: User = Depends(security.require_admin),
               db: Session = Depends(get_db)):
    from ..database import apply_memory_settings
    cur = settings_store.set_memory(db, body.model_dump(exclude_none=True))
    applied = apply_memory_settings(cur["cache_mb"], cur["mmap_mb"])
    try:
        from .browse import set_home_ttl
        set_home_ttl(cur.get("home_cache_sec", 20))
    except Exception:
        pass
    return {**cur, "applied": applied}
