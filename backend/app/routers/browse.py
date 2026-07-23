# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse, Response
from sqlalchemy import select, func, or_, and_
from sqlalchemy.orm import Session

from .. import security, schemas, serializers, thumbnails
from ..database import get_db
from ..models import (
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
@router.get("/home")
def home(user: User = Depends(security.get_current_user), db: Session = Depends(get_db),
         limit: int = Query(20, le=50)):
    ids = _acc_ids(db, user)
    if not ids:
        return {"continue_reading": [], "recently_read_books": [], "recently_read_series": [],
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

    # 최근 추가된 시리즈
    added_series = db.scalars(
        select(Series).where(Series.library_id.in_(ids), Series.book_count > 0)
        .order_by(Series.created_at.desc(), Series.id.desc()).limit(limit)
    ).all()

    return {
        "continue_reading": [serializers.book_to_dict(db, b, user, with_tags=False) for b in cont_rows],
        "recently_read_books": [serializers.book_to_dict(db, b, user, with_tags=False) for b in read_books],
        "recently_read_series": [serializers.series_to_dict(db, s, user, with_tags=False) for s in read_series],
        "recently_added_books": [serializers.book_to_dict(db, b, user, with_tags=False) for b in added],
        "recently_added_series": [serializers.series_to_dict(db, s, user, with_tags=False) for s in added_series],
        "recently_updated_series": [serializers.series_to_dict(db, s, user, with_tags=False) for s in upd_series],
        "recently_updated_books": [serializers.book_to_dict(db, b, user, with_tags=False) for b in upd_books],
    }


# ============================ 시리즈 ============================
@router.get("/series")
def list_series(user: User = Depends(security.get_current_user), db: Session = Depends(get_db),
                library: int = Query(None), search: str = Query(None), tag: str = Query(None),
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
        stmt = stmt.where(Series.name.like(f"%{search}%"))
    if tag:
        stmt = stmt.where(
            Series.id.in_(
                select(Book.series_id).join(BookTag, BookTag.book_id == Book.id)
                .join(Tag, Tag.id == BookTag.tag_id).where(Tag.name == tag)
            )
        )

    if sort == "read":
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
               tag: str = Query(None), fmt: str = Query(None),
               progress: str = Query(None),  # reading | completed
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
        stmt = stmt.where(or_(Book.title.like(f"%{search}%"), Book.author.like(f"%{search}%")))
    if fmt:
        stmt = stmt.where(Book.fmt == fmt.lower())
    if tag:
        stmt = stmt.where(
            Book.id.in_(
                select(BookTag.book_id).join(Tag, Tag.id == BookTag.tag_id).where(Tag.name == tag)
            )
        )

    # 읽기 기록 기반(최근 읽은/이어보기/완독)은 ReadProgress 를 조인
    need_progress = (sort == "read") or (progress in ("reading", "completed"))
    if need_progress:
        stmt = stmt.join(ReadProgress, and_(ReadProgress.book_id == Book.id,
                                            ReadProgress.user_id == user.id))
        if progress == "reading":
            stmt = stmt.where(ReadProgress.completed == False)  # noqa: E712
        elif progress == "completed":
            stmt = stmt.where(ReadProgress.completed == True)   # noqa: E712

    if sort == "read":
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
    return FileResponse(str(p), media_type="image/jpeg",
                        headers={"Cache-Control": "public, max-age=86400"})
