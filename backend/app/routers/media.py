# -*- coding: utf-8 -*-
import os
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response, FileResponse, PlainTextResponse
from sqlalchemy.orm import Session

from .. import security, formats
from ..database import get_db
from ..models import User, Book

router = APIRouter(prefix="/api", tags=["media"])


def _require_book(db, user, book_id) -> Book:
    book = db.get(Book, book_id)
    if not book or book.library_id not in set(security.accessible_library_ids(db, user)):
        raise HTTPException(status_code=404, detail="책을 찾을 수 없습니다.")
    return book


@router.get("/books/{book_id}/pages/{index}")
def comic_page(book_id: int, index: int,
               user: User = Depends(security.get_current_user), db: Session = Depends(get_db)):
    """만화(cbz/zip) 페이지 이미지. index 는 0-based."""
    book = _require_book(db, user, book_id)
    if book.fmt not in ("cbz", "zip"):
        raise HTTPException(status_code=400, detail="이미지 페이지가 없는 형식입니다.")
    res = formats.read_comic_page(book.path, index)
    if res is None:
        raise HTTPException(status_code=404, detail="페이지를 찾을 수 없습니다.")
    data, ctype = res
    return Response(content=data, media_type=ctype,
                    headers={"Cache-Control": "public, max-age=86400"})


_FILE_MIME = {
    "epub": "application/epub+zip",
    "pdf": "application/pdf",
    "txt": "text/plain; charset=utf-8",
    "cbz": "application/vnd.comicbook+zip",
    "zip": "application/zip",
}


@router.get("/books/{book_id}/file")
def raw_file(book_id: int, user: User = Depends(security.get_current_user),
             db: Session = Depends(get_db)):
    """EPUB/PDF 등 원본 파일 스트리밍 (FileResponse 가 Range 요청 처리 → 대용량/탐색 지원)."""
    book = _require_book(db, user, book_id)
    if not os.path.exists(book.path):
        raise HTTPException(status_code=404, detail="파일이 존재하지 않습니다.")
    media = _FILE_MIME.get(book.fmt, "application/octet-stream")
    filename = os.path.basename(book.path)
    return FileResponse(
        book.path, media_type=media, filename=filename,
        headers={"Cache-Control": "private, max-age=3600",
                 "Accept-Ranges": "bytes"},
    )


@router.get("/books/{book_id}/content")
def text_content(book_id: int, user: User = Depends(security.get_current_user),
                 db: Session = Depends(get_db)):
    """TXT 파일을 UTF-8 로 디코딩해서 반환 (인코딩 자동감지)."""
    book = _require_book(db, user, book_id)
    if book.fmt != "txt":
        raise HTTPException(status_code=400, detail="텍스트 형식이 아닙니다.")
    text = formats.read_text_file(book.path)
    return PlainTextResponse(text, headers={"Cache-Control": "private, max-age=3600"})


@router.get("/books/{book_id}/download")
def download(book_id: int, user: User = Depends(security.get_current_user),
             db: Session = Depends(get_db)):
    book = _require_book(db, user, book_id)
    if not os.path.exists(book.path):
        raise HTTPException(status_code=404, detail="파일이 존재하지 않습니다.")
    return FileResponse(book.path, filename=os.path.basename(book.path),
                        media_type="application/octet-stream")
