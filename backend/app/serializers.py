# -*- coding: utf-8 -*-
from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from .models import Book, Series, ReadProgress, Rating, Tag, BookTag, User


def _iso(v):
    return v.isoformat() if v is not None else None


def book_tags(db: Session, book_id: int):
    rows = db.execute(
        select(Tag.name, BookTag.source)
        .join(BookTag, BookTag.tag_id == Tag.id)
        .where(BookTag.book_id == book_id)
        .order_by(Tag.name)
    ).all()
    return [{"name": n, "source": s} for (n, s) in rows]


def _progress_for(db: Session, user_id: int, book_id: int, page_count: Optional[int]):
    p = db.scalar(
        select(ReadProgress).where(
            ReadProgress.user_id == user_id, ReadProgress.book_id == book_id
        )
    )
    if not p:
        return None
    percent = None
    if page_count and page_count > 0:
        percent = round(min(1.0, (p.page + 1) / page_count) * 100, 1)
    return {
        "page": p.page,
        "position": p.position,
        "completed": p.completed,
        "percent": percent,
        "updated_at": _iso(p.updated_at),
    }


def _ratings_for(db: Session, user_id: int, book_id: int):
    my = db.scalar(
        select(Rating.value).where(Rating.user_id == user_id, Rating.book_id == book_id)
    )
    avg = db.scalar(select(func.avg(Rating.value)).where(Rating.book_id == book_id))
    cnt = db.scalar(select(func.count(Rating.id)).where(Rating.book_id == book_id))
    return my or 0, (round(avg, 2) if avg else None), (cnt or 0)


def book_to_dict(db: Session, book: Book, user: User, with_tags: bool = True):
    my_rating, avg_rating, rating_count = _ratings_for(db, user.id, book.id)
    d = {
        "id": book.id,
        "series_id": book.series_id,
        "series_name": book.series.name if book.series else None,
        "library_id": book.library_id,
        "title": book.title,
        "author": book.author,
        "publisher": book.publisher,
        "language": book.language,
        "series_index": book.series_index,
        "description": book.description,
        "format": book.fmt,
        "file_size": book.file_size,
        "page_count": book.page_count,
        "has_thumb": book.has_thumb,
        "status": book.status,
        "trashed_at": _iso(book.trashed_at),
        "created_at": _iso(book.created_at),
        "updated_at": _iso(book.updated_at),
        "progress": _progress_for(db, user.id, book.id, book.page_count),
        "my_rating": my_rating,
        "avg_rating": avg_rating,
        "rating_count": rating_count,
    }
    if with_tags:
        d["tags"] = book_tags(db, book.id)
    return d


def series_tags(db: Session, series_id: int):
    rows = db.execute(
        select(Tag.name)
        .join(BookTag, BookTag.tag_id == Tag.id)
        .join(Book, Book.id == BookTag.book_id)
        .where(Book.series_id == series_id)
        .distinct()
        .order_by(Tag.name)
    ).all()
    return [r[0] for r in rows]


def series_to_dict(db: Session, series: Series, user: User, with_tags: bool = True):
    # 시리즈 내 완독/진행 통계
    total = series.book_count
    read_cnt = db.scalar(
        select(func.count(ReadProgress.id))
        .join(Book, Book.id == ReadProgress.book_id)
        .where(Book.series_id == series.id,
               ReadProgress.user_id == user.id,
               ReadProgress.completed == True)  # noqa: E712
    ) or 0
    in_progress = db.scalar(
        select(func.count(ReadProgress.id))
        .join(Book, Book.id == ReadProgress.book_id)
        .where(Book.series_id == series.id,
               ReadProgress.user_id == user.id,
               ReadProgress.completed == False)  # noqa: E712
    ) or 0
    d = {
        "id": series.id,
        "library_id": series.library_id,
        "name": series.name,
        "book_count": total,
        "read_count": read_cnt,
        "in_progress_count": in_progress,
        "has_thumb": True,
        "created_at": _iso(series.created_at),
        "updated_at": _iso(series.updated_at),
    }
    if with_tags:
        d["tags"] = series_tags(db, series.id)
    return d
