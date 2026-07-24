# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse, Response
from sqlalchemy import select, func, or_, and_
from sqlalchemy.orm import Session

from .. import security, schemas, serializers, thumbnails, formats
from ..database import get_db
from ..models import (
    SeriesRating, Favorite,
    User, Library, Series, Book, Tag, BookTag, ReadProgress, Rating, utcnow,
)

router = APIRouter(prefix="/api", tags=["browse"])


def _acc_ids(db, user):
    return set(security.accessible_library_ids(db, user))


def _require_book(db, user, book_id) -> Book:
    book = db.get(Book, book_id)
    if not book or book.library_id not in _acc_ids(db, user):
        raise HTTPException(status_code=404, detail="책을 찾을 수 없습니다.")
    return book


def _require_series(db, user, series_id) -> Series:
    s = db.get(Series, series_id)
    if not s or s.library_id not in _acc_ids(db, user):
        raise HTTPException(status_code=404, detail="시리즈를 찾을 수 없습니다.")
    return s


# ============================ 홈 ============================
# 홈 응답 캐시 (사용자별). 스캔으로 내용이 바뀌면 버전이 올라가 자동 무효화된다.
_HOME_CACHE = {}
_HOME_TTL = 20.0


def set_home_ttl(sec):
    global _HOME_TTL
    try:
        _HOME_TTL = float(max(0, min(600, int(sec))))
    except (TypeError, ValueError):
        pass


def _home_cache_get(user_id: int):
    import time as _t
    from .. import scanner as _sc
    ent = _HOME_CACHE.get(user_id)
    if not ent:
        return None
    ts, ver, data = ent
    cur_ver = int(_sc.scan_status.get("added", 0)) + int(_sc.scan_status.get("updated", 0))
    if ver != cur_ver or (_t.time() - ts) > _HOME_TTL:
        return None
    return data


def _home_invalidate(user_id: int):
    _HOME_CACHE.pop(user_id, None)


def _home_cache_put(user_id: int, data):
    import time as _t
    from .. import scanner as _sc
    ver = int(_sc.scan_status.get("added", 0)) + int(_sc.scan_status.get("updated", 0))
    _HOME_CACHE[user_id] = (_t.time(), ver, data)
    if len(_HOME_CACHE) > 200:
        _HOME_CACHE.clear()


@router.get("/home")
def home(user: User = Depends(security.get_current_user), db: Session = Depends(get_db),
         limit: int = Query(12, le=50)):
    cached = _home_cache_get(user.id)
    if cached is not None:
        return cached
    ids = _acc_ids(db, user)
    if not ids:
        return {"favorite_series": [], "continue_reading": [], "recently_read_books": [], "recently_read_series": [],
                "recently_added_books": [], "recently_added_series": [],
                "recently_updated_series": [], "recently_updated_books": [],
                "on_deck": []}

    # 이어보기: 진행 중(미완독), 최근 갱신 순
    cont_rows = db.scalars(
        select(Book).join(ReadProgress, ReadProgress.book_id == Book.id)
        .where(ReadProgress.user_id == user.id, ReadProgress.completed == False,  # noqa
               Book.library_id.in_(ids), Book.status == "active")
        .order_by(ReadProgress.updated_at.desc()).limit(limit)
    ).all()

    added = db.scalars(
        select(Book).where(Book.library_id.in_(ids), Book.status == "active")
        .order_by(Book.created_at.desc(), Book.id.desc()).limit(limit)
    ).all()

    upd_series = db.scalars(
        select(Series).where(Series.library_id.in_(ids), Series.book_count > 0)
        .order_by(Series.updated_at.desc()).limit(limit)
    ).all()

    upd_books = db.scalars(
        select(Book).where(Book.library_id.in_(ids), Book.status == "active")
        .order_by(Book.updated_at.desc()).limit(limit)
    ).all()

    # 최근 읽은 책: 완독 여부와 무관하게 마지막으로 읽은 순
    read_books = db.scalars(
        select(Book).join(ReadProgress, ReadProgress.book_id == Book.id)
        .where(ReadProgress.user_id == user.id,
               Book.library_id.in_(ids), Book.status == "active")
        .order_by(ReadProgress.updated_at.desc()).limit(limit)
    ).all()

    # 최근 읽은 시리즈: 위 기록에서 시리즈 단위로 중복 제거(읽은 순서 유지)
    read_series = []
    seen_sid = set()
    for b in db.scalars(
        select(Book).join(ReadProgress, ReadProgress.book_id == Book.id)
        .where(ReadProgress.user_id == user.id,
               Book.library_id.in_(ids), Book.status == "active")
        .order_by(ReadProgress.updated_at.desc()).limit(limit * 5)
    ).all():
        if b.series_id and b.series_id not in seen_sid:
            seen_sid.add(b.series_id)
            if b.series is not None and (b.series.book_count or 0) > 0:
                read_series.append(b.series)
            if len(read_series) >= limit:
                break

    # 즐겨찾기한 시리즈 (최근 추가한 순)
    fav_series = db.scalars(
        select(Series).join(Favorite, Favorite.series_id == Series.id)
        .where(Favorite.user_id == user.id, Series.library_id.in_(ids),
               Series.book_count > 0)
        .order_by(Favorite.created_at.desc()).limit(limit)
    ).all()

    # 최근 추가된 시리즈
    added_series = db.scalars(
        select(Series).where(Series.library_id.in_(ids), Series.book_count > 0)
        .order_by(Series.created_at.desc(), Series.id.desc()).limit(limit)
    ).all()

    result = {
        "favorite_series": [serializers.series_to_dict(db, x, user, with_tags=False) for x in fav_series],
        "continue_reading": [serializers.book_to_dict(db, b, user, with_tags=False) for b in cont_rows],
        "recently_read_books": [serializers.book_to_dict(db, b, user, with_tags=False) for b in read_books],
        "recently_read_series": [serializers.series_to_dict(db, s, user, with_tags=False) for s in read_series],
        "recently_added_books": [serializers.book_to_dict(db, b, user, with_tags=False) for b in added],
        "recently_added_series": [serializers.series_to_dict(db, s, user, with_tags=False) for s in added_series],
        "recently_updated_series": [serializers.series_to_dict(db, s, user, with_tags=False) for s in upd_series],
        "recently_updated_books": [serializers.book_to_dict(db, b, user, with_tags=False) for b in upd_books],
    }
    _home_cache_put(user.id, result)
    return result


# ============================ 시리즈 ============================
@router.get("/series")
def list_series(user: User = Depends(security.get_current_user), db: Session = Depends(get_db),
                library: int = Query(None), search: str = Query(None), tag: str = Query(None),
                tags: str = Query(None), fmt: str = Query(None),
                favorite: bool = Query(False), min_rating: int = Query(0, ge=0, le=5),
                sort: str = Query("name"), order: str = Query("asc"),
                page: int = Query(1, ge=1), size: int = Query(40, ge=1, le=200)):
    ids = _acc_ids(db, user)
    if library is not None:
        if library not in ids:
            raise HTTPException(status_code=404, detail="라이브러리를 찾을 수 없습니다.")
        ids = {library}
    if not ids:
        return {"items": [], "total": 0, "page": page, "size": size}

    stmt = select(Series).where(Series.library_id.in_(ids), Series.book_count > 0)
    if search:
        if formats.is_chosung_query(search):
            cho = formats.chosung_of(search)
            stmt = stmt.where(Series.chosung.like(f"%{cho}%"))
        else:
            stmt = stmt.where(Series.name.like(f"%{search}%"))
    if tags:
        for tn in [x.strip() for x in tags.split(",") if x.strip()]:
            stmt = stmt.where(Series.id.in_(
                select(Book.series_id).join(BookTag, BookTag.book_id == Book.id)
                .join(Tag, Tag.id == BookTag.tag_id).where(Tag.name == tn)))
    if fmt:
        fl = [x.strip().lower() for x in fmt.split(",") if x.strip()]
        if fl:
            stmt = stmt.where(Series.id.in_(
                select(Book.series_id).where(Book.fmt.in_(fl))))
    if tag:
        stmt = stmt.where(
            Series.id.in_(
                select(Book.series_id).join(BookTag, BookTag.book_id == Book.id)
                .join(Tag, Tag.id == BookTag.tag_id).where(Tag.name == tag)
            )
        )

    # 즐겨찾기 / 별점 필터 (내 기준)
    fav_sub = (select(Favorite.id).where(
        Favorite.user_id == user.id, Favorite.series_id == Series.id)
        .correlate(Series).exists())
    my_rating_sub = (select(SeriesRating.value).where(
        SeriesRating.user_id == user.id, SeriesRating.series_id == Series.id)
        .correlate(Series).scalar_subquery())
    if favorite:
        stmt = stmt.where(fav_sub)
    if min_rating:
        stmt = stmt.where(my_rating_sub >= int(min_rating))

    if sort == "favorite":
        # 즐겨찾기를 맨 위로, 그다음 이름순
        stmt = stmt.order_by(fav_sub.desc(), Series.sort_name.asc())
        total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        rows = db.scalars(stmt.offset((page - 1) * size).limit(size)).all()
        return {"items": [serializers.series_to_dict(db, x, user) for x in rows],
                "total": total, "page": page, "size": size}
    if sort == "rating":
        sort_col = func.coalesce(my_rating_sub, 0)
    elif sort == "read":
        # 시리즈 내 책들의 마지막 읽은 시각 기준. 읽은 기록이 있는 시리즈만.
        last_read = (
            select(func.max(ReadProgress.updated_at))
            .select_from(ReadProgress).join(Book, Book.id == ReadProgress.book_id)
            .where(Book.series_id == Series.id, ReadProgress.user_id == user.id)
            .correlate(Series).scalar_subquery()
        )
        stmt = stmt.where(last_read.isnot(None))
        sort_col = last_read
    else:
        sort_col = {
            "name": Series.sort_name,
            "created": Series.created_at,
            "updated": Series.updated_at,
            "books": Series.book_count,
        }.get(sort, Series.sort_name)
    sort_col = sort_col.desc() if order == "desc" else sort_col.asc()

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(stmt.order_by(sort_col).offset((page - 1) * size).limit(size)).all()
    return {
        "items": [serializers.series_to_dict(db, s, user, with_tags=True) for s in rows],
        "total": total, "page": page, "size": size,
    }


@router.get("/series/{series_id}")
def series_detail(series_id: int, user: User = Depends(security.get_current_user),
                  db: Session = Depends(get_db)):
    s = _require_series(db, user, series_id)
    from ..formats import natural_key
    books = db.scalars(
        select(Book).where(Book.series_id == s.id, Book.status == "active")
    ).all()
    books.sort(key=lambda b: natural_key(b.sort_title))
    d = serializers.series_to_dict(db, s, user, with_tags=True)
    d["library_name"] = s.library.name if s.library else None
    d["books"] = [serializers.book_to_dict(db, b, user, with_tags=True) for b in books]
    return d


# ============================ 책 ============================
@router.get("/books")
def list_books(user: User = Depends(security.get_current_user), db: Session = Depends(get_db),
               library: int = Query(None), series: int = Query(None), search: str = Query(None),
               tag: str = Query(None), tags: str = Query(None), fmt: str = Query(None),
               favorite: bool = Query(False), min_rating: int = Query(0, ge=0, le=5),
               progress: str = Query(None),  # reading | completed | unread
               sort: str = Query("title"), order: str = Query("asc"),
               page: int = Query(1, ge=1), size: int = Query(40, ge=1, le=200)):
    ids = _acc_ids(db, user)
    if library is not None:
        if library not in ids:
            raise HTTPException(status_code=404, detail="라이브러리를 찾을 수 없습니다.")
        ids = {library}
    if not ids:
        return {"items": [], "total": 0, "page": page, "size": size}

    stmt = select(Book).where(Book.library_id.in_(ids), Book.status == "active")
    if series is not None:
        stmt = stmt.where(Book.series_id == series)
    if search:
        if formats.is_chosung_query(search):
            cho = formats.chosung_of(search)
            stmt = stmt.where(Book.chosung.like(f"%{cho}%"))
        else:
            stmt = stmt.where(or_(Book.title.like(f"%{search}%"),
                                  Book.author.like(f"%{search}%")))
    if fmt:
        fl = [x.strip().lower() for x in fmt.split(",") if x.strip()]
        if len(fl) == 1:
            stmt = stmt.where(Book.fmt == fl[0])
        elif fl:
            stmt = stmt.where(Book.fmt.in_(fl))
    # 여러 태그를 '모두' 가진 책만 (쉼표 구분)
    if tags:
        for tn in [x.strip() for x in tags.split(",") if x.strip()]:
            stmt = stmt.where(Book.id.in_(
                select(BookTag.book_id).join(Tag, Tag.id == BookTag.tag_id)
                .where(Tag.name == tn)))
    if tag:
        stmt = stmt.where(
            Book.id.in_(
                select(BookTag.book_id).join(Tag, Tag.id == BookTag.tag_id).where(Tag.name == tag)
            )
        )

    # 즐겨찾기 / 내 별점 필터
    bfav_sub = (select(Favorite.id).where(
        Favorite.user_id == user.id, Favorite.book_id == Book.id)
        .correlate(Book).exists())
    brate_sub = (select(Rating.value).where(
        Rating.user_id == user.id, Rating.book_id == Book.id)
        .correlate(Book).scalar_subquery())
    if favorite:
        stmt = stmt.where(bfav_sub)
    if min_rating:
        stmt = stmt.where(brate_sub >= int(min_rating))

    # 미독(읽은 기록 없음)은 조인 대신 NOT EXISTS 로 처리
    if progress == "unread":
        stmt = stmt.where(~select(ReadProgress.id).where(
            ReadProgress.book_id == Book.id, ReadProgress.user_id == user.id
        ).correlate(Book).exists())

    # 읽기 기록 기반(최근 읽은/이어보기/완독)은 ReadProgress 를 조인
    need_progress = (sort == "read") or (progress in ("reading", "completed"))
    if need_progress:
        stmt = stmt.join(ReadProgress, and_(ReadProgress.book_id == Book.id,
                                            ReadProgress.user_id == user.id))
        if progress == "reading":
            stmt = stmt.where(ReadProgress.completed == False)  # noqa: E712
        elif progress == "completed":
            stmt = stmt.where(ReadProgress.completed == True)   # noqa: E712

    if sort == "favorite":
        stmt = stmt.order_by(bfav_sub.desc(), Book.sort_title.asc())
        total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        rows = db.scalars(stmt.offset((page - 1) * size).limit(size)).all()
        return {"items": [serializers.book_to_dict(db, b, user, with_tags=True) for b in rows],
                "total": total, "page": page, "size": size}
    if sort == "rating":
        sort_col = func.coalesce(brate_sub, 0)
    elif sort == "read":
        sort_col = ReadProgress.updated_at
    else:
        sort_col = {
            "title": Book.sort_title,
            "created": Book.created_at,
            "updated": Book.updated_at,
            "size": Book.file_size,
        }.get(sort, Book.sort_title)
    sort_col = sort_col.desc() if order == "desc" else sort_col.asc()

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(stmt.order_by(sort_col).offset((page - 1) * size).limit(size)).all()
    return {
        "items": [serializers.book_to_dict(db, b, user, with_tags=True) for b in rows],
        "total": total, "page": page, "size": size,
    }


@router.get("/books/{book_id}")
def book_detail(book_id: int, user: User = Depends(security.get_current_user),
                db: Session = Depends(get_db)):
    book = _require_book(db, user, book_id)
    return serializers.book_to_dict(db, book, user, with_tags=True)


# ============================ 태그 ============================
@router.get("/tags")
def list_tags(user: User = Depends(security.get_current_user), db: Session = Depends(get_db),
              library: int = Query(None)):
    ids = _acc_ids(db, user)
    if library is not None and library in ids:
        ids = {library}
    if not ids:
        return {"tags": []}
    rows = db.execute(
        select(Tag.name, func.count(BookTag.book_id))
        .join(BookTag, BookTag.tag_id == Tag.id)
        .join(Book, Book.id == BookTag.book_id)
        .where(Book.library_id.in_(ids), Book.status == "active")
        .group_by(Tag.name).order_by(func.count(BookTag.book_id).desc(), Tag.name)
    ).all()
    return {"tags": [{"name": n, "count": c} for (n, c) in rows]}


def _get_or_create_tag(db, name):
    name = name.strip()
    if not name:
        return None
    t = db.scalar(select(Tag).where(Tag.name == name))
    if not t:
        t = Tag(name=name)
        db.add(t)
        db.flush()
    return t


@router.put("/books/{book_id}/tags")
def set_book_tags(book_id: int, body: schemas.TagsSetIn,
                  user: User = Depends(security.get_current_user), db: Session = Depends(get_db)):
    """수동 태그 전체 교체 (auto 태그는 유지)."""
    book = _require_book(db, user, book_id)
    # 기존 manual 링크 제거
    for bt in list(book.tags):
        if bt.source == "manual":
            db.delete(bt)
    db.flush()
    auto_names = {bt.tag.name for bt in book.tags if bt.source == "auto"}
    for name in body.tags:
        t = _get_or_create_tag(db, name)
        if t and t.name not in auto_names:
            exists = db.scalar(select(BookTag).where(
                BookTag.book_id == book.id, BookTag.tag_id == t.id))
            if not exists:
                db.add(BookTag(book_id=book.id, tag_id=t.id, source="manual"))
    db.commit()
    return {"tags": serializers.book_tags(db, book.id)}


@router.post("/books/{book_id}/tags")
def add_book_tag(book_id: int, body: schemas.TagAddIn,
                 user: User = Depends(security.get_current_user), db: Session = Depends(get_db)):
    book = _require_book(db, user, book_id)
    t = _get_or_create_tag(db, body.tag)
    if not t:
        raise HTTPException(status_code=400, detail="태그명이 비어있습니다.")
    exists = db.scalar(select(BookTag).where(BookTag.book_id == book.id, BookTag.tag_id == t.id))
    if not exists:
        db.add(BookTag(book_id=book.id, tag_id=t.id, source="manual"))
        db.commit()
    return {"tags": serializers.book_tags(db, book.id)}


@router.delete("/books/{book_id}/tags/{tag_name}")
def remove_book_tag(book_id: int, tag_name: str,
                    user: User = Depends(security.get_current_user), db: Session = Depends(get_db)):
    book = _require_book(db, user, book_id)
    t = db.scalar(select(Tag).where(Tag.name == tag_name))
    if t:
        bt = db.scalar(select(BookTag).where(BookTag.book_id == book.id, BookTag.tag_id == t.id))
        if bt:
            db.delete(bt)
            db.commit()
    return {"tags": serializers.book_tags(db, book.id)}


@router.post("/series/{series_id}/tags")
def add_series_tag(series_id: int, body: schemas.TagAddIn,
                   user: User = Depends(security.get_current_user), db: Session = Depends(get_db)):
    """시리즈 내 모든 책에 수동 태그 추가."""
    s = _require_series(db, user, series_id)
    t = _get_or_create_tag(db, body.tag)
    if not t:
        raise HTTPException(status_code=400, detail="태그명이 비어있습니다.")
    books = db.scalars(select(Book).where(Book.series_id == s.id)).all()
    for b in books:
        exists = db.scalar(select(BookTag).where(BookTag.book_id == b.id, BookTag.tag_id == t.id))
        if not exists:
            db.add(BookTag(book_id=b.id, tag_id=t.id, source="manual"))
    db.commit()
    return {"tags": serializers.series_tags(db, s.id)}


# ============================ 평점 ============================
@router.put("/books/{book_id}/rating")
def set_rating(book_id: int, body: schemas.RatingIn,
               user: User = Depends(security.get_current_user), db: Session = Depends(get_db)):
    _home_invalidate(user.id)
    book = _require_book(db, user, book_id)
    r = db.scalar(select(Rating).where(Rating.user_id == user.id, Rating.book_id == book.id))
    if body.value == 0:
        if r:
            db.delete(r)
            db.commit()
        return serializers.book_to_dict(db, book, user, with_tags=False)
    if r:
        r.value = body.value
        r.updated_at = utcnow()
    else:
        db.add(Rating(user_id=user.id, book_id=book.id, value=body.value))
    db.commit()
    return serializers.book_to_dict(db, book, user, with_tags=False)


# ============================ 진행률 ============================
@router.put("/books/{book_id}/progress")
def set_progress(book_id: int, body: schemas.ProgressIn,
                 user: User = Depends(security.get_current_user), db: Session = Depends(get_db)):
    _home_invalidate(user.id)
    book = _require_book(db, user, book_id)
    p = db.scalar(select(ReadProgress).where(
        ReadProgress.user_id == user.id, ReadProgress.book_id == book.id))
    if not p:
        p = ReadProgress(user_id=user.id, book_id=book.id, page=0)
        db.add(p)
    if body.page is not None:
        p.page = max(0, body.page)
    if body.position is not None:
        p.position = body.position
    if body.completed is not None:
        p.completed = body.completed
    # 마지막 페이지 도달 시 자동 완독 처리(만화/PDF)
    if book.page_count and p.page >= book.page_count - 1 and body.completed is None:
        p.completed = True
    p.updated_at = utcnow()
    db.commit()
    return serializers.book_to_dict(db, book, user, with_tags=False)


@router.delete("/books/{book_id}/progress")
def clear_progress(book_id: int, user: User = Depends(security.get_current_user),
                   db: Session = Depends(get_db)):
    book = _require_book(db, user, book_id)
    p = db.scalar(select(ReadProgress).where(
        ReadProgress.user_id == user.id, ReadProgress.book_id == book.id))
    if p:
        db.delete(p)
        db.commit()
    return {"ok": True}


# ============================ 썸네일 ============================
@router.get("/books/{book_id}/thumbnail")
def book_thumbnail(book_id: int, user: User = Depends(security.get_current_user),
                   db: Session = Depends(get_db)):
    book = _require_book(db, user, book_id)
    p = thumbnails.book_thumb_path(book.id)
    if not p.exists():
        return Response(status_code=404)
    db.close()  # 스트리밍 동안 DB 연결을 붙잡지 않도록 먼저 반납 (풀 고갈 방지)
    return FileResponse(str(p), media_type="image/jpeg",
                        headers={"Cache-Control": "public, max-age=86400"})


@router.get("/series/{series_id}/thumbnail")
def series_thumbnail(series_id: int, user: User = Depends(security.get_current_user),
                     db: Session = Depends(get_db)):
    s = _require_series(db, user, series_id)
    p = thumbnails.series_thumb_path(s.id)
    if not p.exists() and s.cover_book_id:
        thumbnails.link_series_thumbnail(s.id, s.cover_book_id)
    if not p.exists():
        return Response(status_code=404)
    db.close()  # 스트리밍 동안 DB 연결을 붙잡지 않도록 먼저 반납 (풀 고갈 방지)
    return FileResponse(str(p), media_type="image/jpeg",
                        headers={"Cache-Control": "public, max-age=86400"})


# ============================ EPUB 구조(목차/삽화) ============================
def _epub_meta_of(book) -> dict:
    import json
    if not book.epub_meta:
        return {}
    try:
        return json.loads(book.epub_meta)
    except Exception:
        return {}


@router.get("/books/{book_id}/toc")
def book_toc(book_id: int, user: User = Depends(security.get_current_user),
             db: Session = Depends(get_db)):
    """EPUB 챕터 목록. 스캔 시 미리 분석해 둔 결과를 즉시 반환."""
    book = _require_book(db, user, book_id)
    meta = _epub_meta_of(book)
    if not meta and book.fmt == "epub":
        # 아직 분석 전이면 지금 한 번 분석해서 저장 (다음부터는 즉시)
        from .. import scanner
        if scanner._precompute_epub_meta(book, book.path):
            db.commit()
            meta = _epub_meta_of(book)
    return {"indexed": bool(meta),
            "spine_len": meta.get("spine_len", 0),
            "chapters": meta.get("chapters", [])}


@router.get("/books/{book_id}/epub-images")
def book_epub_images(book_id: int, user: User = Depends(security.get_current_user),
                     db: Session = Depends(get_db)):
    """EPUB 삽화 목록(썸네일 URL 포함). 클릭 시 이동할 챕터 href 도 함께."""
    book = _require_book(db, user, book_id)
    meta = _epub_meta_of(book)
    if not meta and book.fmt == "epub":
        from .. import scanner
        if scanner._precompute_epub_meta(book, book.path):
            db.commit()
            meta = _epub_meta_of(book)
    imgs = meta.get("images", [])
    return {"indexed": bool(meta), "images": imgs}


@router.get("/books/{book_id}/epub-thumb")
def book_epub_thumb(book_id: int, href: str = Query(...),
                    user: User = Depends(security.get_current_user),
                    db: Session = Depends(get_db)):
    """삽화 썸네일. 스캔 때 미리 만들어 둔 작은 이미지를 우선 사용하고,
    없으면 그 자리에서 만들어 저장한다(다음부터는 즉시)."""
    from ..formats import epub_asset_bytes
    book = _require_book(db, user, book_id)
    p = thumbnails.epub_img_thumb_path(book.id, href)
    if not p.exists():
        got = epub_asset_bytes(book.path, href)
        if not got:
            raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다.")
        small = thumbnails._resize_small(got[0])
        if small:
            try:
                p.parent.mkdir(parents=True, exist_ok=True)
                with open(p, "wb") as f:
                    f.write(small)
            except OSError:
                return Response(content=got[0], media_type=got[1])
        else:
            return Response(content=got[0], media_type=got[1])
    db.close()  # 스트리밍 동안 DB 연결을 붙잡지 않도록 먼저 반납 (풀 고갈 방지)
    return FileResponse(p, media_type="image/jpeg",
                        headers={"Cache-Control": "private, max-age=604800"})


@router.get("/books/{book_id}/epub-asset")
def book_epub_asset(book_id: int, href: str = Query(...),
                    user: User = Depends(security.get_current_user),
                    db: Session = Depends(get_db)):
    """EPUB 내부 파일(삽화)을 꺼내서 전달."""
    from ..formats import epub_asset_bytes
    book = _require_book(db, user, book_id)
    if book.fmt != "epub":
        raise HTTPException(status_code=400, detail="EPUB 이 아닙니다.")
    book_path = book.path
    db.close()  # zip 읽기/전송 동안 연결 반납
    got = epub_asset_bytes(book_path, href)
    if not got:
        raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다.")
    data, ctype = got
    db.close()  # 스트리밍 동안 DB 연결을 붙잡지 않도록 먼저 반납 (풀 고갈 방지)
    return Response(content=data, media_type=ctype,
                    headers={"Cache-Control": "private, max-age=86400"})


# ============================ 즐겨찾기 / 시리즈 별점 ============================


def _require_series(db, user, series_id):
    s = db.get(Series, series_id)
    if not s or s.library_id not in set(security.accessible_library_ids(db, user)):
        raise HTTPException(status_code=404, detail="시리즈를 찾을 수 없습니다.")
    return s


@router.put("/series/{series_id}/rating")
def set_series_rating(series_id: int, body: schemas.RatingIn,
                      user: User = Depends(security.get_current_user),
                      db: Session = Depends(get_db)):
    _home_invalidate(user.id)
    s = _require_series(db, user, series_id)
    r = db.scalar(select(SeriesRating).where(
        SeriesRating.user_id == user.id, SeriesRating.series_id == s.id))
    if body.value and body.value > 0:
        if not r:
            r = SeriesRating(user_id=user.id, series_id=s.id)
            db.add(r)
        r.value = max(1, min(5, int(body.value)))
        r.updated_at = utcnow()
    elif r:
        db.delete(r)
    db.commit()
    val = int(body.value or 0)
    return {"ok": True, "value": max(0, min(5, val))}


@router.post("/favorites/{kind}/{item_id}")
def add_favorite(kind: str, item_id: int,
                 user: User = Depends(security.get_current_user),
                 db: Session = Depends(get_db)):
    _home_invalidate(user.id)
    if kind not in ("series", "book"):
        raise HTTPException(status_code=400, detail="잘못된 종류입니다.")
    if kind == "series":
        _require_series(db, user, item_id)
        exist = db.scalar(select(Favorite).where(
            Favorite.user_id == user.id, Favorite.series_id == item_id))
        if not exist:
            db.add(Favorite(user_id=user.id, series_id=item_id))
    else:
        _require_book(db, user, item_id)
        exist = db.scalar(select(Favorite).where(
            Favorite.user_id == user.id, Favorite.book_id == item_id))
        if not exist:
            db.add(Favorite(user_id=user.id, book_id=item_id))
    db.commit()
    return {"ok": True, "favorite": True}


@router.delete("/favorites/{kind}/{item_id}")
def remove_favorite(kind: str, item_id: int,
                    user: User = Depends(security.get_current_user),
                    db: Session = Depends(get_db)):
    _home_invalidate(user.id)
    col = Favorite.series_id if kind == "series" else Favorite.book_id
    f = db.scalar(select(Favorite).where(Favorite.user_id == user.id, col == item_id))
    if f:
        db.delete(f)
        db.commit()
    return {"ok": True, "favorite": False}



# ============================ 다음 권 / 중복 / 백업 ============================
@router.get("/books/{book_id}/next")
def next_book(book_id: int, user: User = Depends(security.get_current_user),
              db: Session = Depends(get_db)):
    """같은 시리즈에서 정렬상 다음 책을 돌려준다 (자동 이어읽기용)."""
    book = _require_book(db, user, book_id)
    if not book.series_id:
        return {"next": None}
    rows = db.scalars(
        select(Book).where(Book.series_id == book.series_id, Book.status == "active")
        .order_by(Book.sort_title)
    ).all()
    rows = sorted(rows, key=lambda b: formats.natural_key(b.sort_title or ""))
    idx = next((i for i, b in enumerate(rows) if b.id == book.id), None)
    if idx is None or idx + 1 >= len(rows):
        return {"next": None}
    return {"next": serializers.book_to_dict(db, rows[idx + 1], user, with_tags=False)}


# ============================ 다음 권 / 중복 찾기 ============================
@router.get("/books/{book_id}/next")
def next_book(book_id: int, user: User = Depends(security.get_current_user),
              db: Session = Depends(get_db)):
    """같은 시리즈의 다음 책. 연재물을 끊김 없이 이어 읽기 위한 것."""
    book = _require_book(db, user, book_id)
    if not book.series_id:
        return {"next": None}
    rows = db.scalars(
        select(Book).where(Book.series_id == book.series_id, Book.status == "active")
    ).all()
    from ..formats import natural_key
    rows.sort(key=lambda b: natural_key(b.sort_title or b.title or ""))
    idx = next((i for i, b in enumerate(rows) if b.id == book.id), None)
    if idx is None or idx + 1 >= len(rows):
        return {"next": None}
    nxt = rows[idx + 1]
    return {"next": serializers.book_to_dict(db, nxt, user, with_tags=False)}


@router.get("/books/{book_id}/chapter/{index}")
def book_chapter(book_id: int, index: int, part: int = Query(0, ge=0),
                 max_chars: int = Query(120000, ge=20000, le=500000),
                 user: User = Depends(security.get_current_user),
                 db: Session = Depends(get_db)):
    """EPUB 챕터 하나만 HTML 로 반환. 1~2GB 짜리도 전체를 내려받지 않는다."""
    from ..formats import epub_chapter_html
    book = _require_book(db, user, book_id)
    if book.fmt != "epub":
        raise HTTPException(status_code=400, detail="EPUB 이 아닙니다.")
    meta = _epub_meta_of(book)
    if not meta:
        from .. import scanner
        if scanner._precompute_epub_meta(book, book.path):
            db.commit()
            meta = _epub_meta_of(book)
    chapters = meta.get("chapters", [])
    if not chapters:
        raise HTTPException(status_code=404, detail="목차 정보가 없습니다.")
    if index < 0 or index >= len(chapters):
        raise HTTPException(status_code=404, detail="범위를 벗어난 챕터입니다.")
    ch = chapters[index]
    book_path, bid = book.path, book.id
    db.close()  # 압축 해제/전송 동안 연결 반납
    html = epub_chapter_html(book_path, ch["href"],
                             f"/api/books/{bid}/epub-asset?href=")
    if html is None:
        raise HTTPException(status_code=404, detail="챕터를 읽을 수 없습니다.")
    # 합본처럼 한 챕터가 매우 큰 경우 태그가 깨지지 않는 위치에서 나눠 보낸다
    from ..formats import split_html_parts
    pieces = split_html_parts(html, max_chars)
    if part >= len(pieces):
        part = len(pieces) - 1
    return {"index": index, "title": ch.get("title"), "href": ch.get("href"),
            "total": len(chapters), "part": part, "parts": len(pieces),
            "html": pieces[part]}
