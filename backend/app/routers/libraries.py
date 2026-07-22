# -*- coding: utf-8 -*-
import os
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from .. import security, schemas, scanner
from ..database import get_db
from ..models import User, Library, Series, Book

router = APIRouter(prefix="/api/libraries", tags=["libraries"])


def _lib_dict(db: Session, lib: Library):
    series_cnt = db.scalar(select(func.count(Series.id)).where(Series.library_id == lib.id)) or 0
    book_cnt = db.scalar(select(func.count(Book.id)).where(Book.library_id == lib.id)) or 0
    return {
        "id": lib.id,
        "name": lib.name,
        "path": lib.path,
        "restricted": lib.restricted,
        "series_count": series_cnt,
        "book_count": book_cnt,
    }


@router.get("")
def list_libraries(user: User = Depends(security.get_current_user), db: Session = Depends(get_db)):
    ids = set(security.accessible_library_ids(db, user))
    libs = db.scalars(select(Library).order_by(Library.name)).all()
    return [_lib_dict(db, l) for l in libs if l.id in ids]


@router.post("")
def create_library(body: schemas.LibraryCreateIn, _: User = Depends(security.require_admin),
                   db: Session = Depends(get_db)):
    path = body.path.rstrip("/") or "/"
    if not os.path.isdir(path):
        raise HTTPException(status_code=400, detail=f"폴더가 존재하지 않습니다: {path}")
    if db.scalar(select(Library).where(Library.path == path)):
        raise HTTPException(status_code=400, detail="이미 등록된 경로입니다.")
    lib = Library(name=body.name.strip() or os.path.basename(path), path=path,
                  restricted=body.restricted)
    db.add(lib)
    db.commit()
    db.refresh(lib)
    scanner.scan_library_async(lib.id)
    return _lib_dict(db, lib)


@router.patch("/{library_id}")
def update_library(library_id: int, body: schemas.LibraryUpdateIn,
                   _: User = Depends(security.require_admin), db: Session = Depends(get_db)):
    lib = db.get(Library, library_id)
    if not lib:
        raise HTTPException(status_code=404, detail="라이브러리를 찾을 수 없습니다.")
    if body.name is not None:
        lib.name = body.name.strip()
    if body.restricted is not None:
        lib.restricted = body.restricted
    db.commit()
    db.refresh(lib)
    return _lib_dict(db, lib)


@router.delete("/{library_id}")
def delete_library(library_id: int, _: User = Depends(security.require_admin),
                   db: Session = Depends(get_db)):
    lib = db.get(Library, library_id)
    if not lib:
        raise HTTPException(status_code=404, detail="라이브러리를 찾을 수 없습니다.")
    db.delete(lib)  # cascade 로 series/book/tag 링크 정리
    db.commit()
    return {"ok": True}


@router.post("/{library_id}/scan")
def scan_one(library_id: int, deep: bool = False,
             _: User = Depends(security.require_admin), db: Session = Depends(get_db)):
    lib = db.get(Library, library_id)
    if not lib:
        raise HTTPException(status_code=404, detail="라이브러리를 찾을 수 없습니다.")
    started = scanner.scan_library_async(library_id, deep=deep)
    if not started:
        raise HTTPException(status_code=409, detail="이미 스캔이 진행 중입니다.")
    kind = "심층 스캔" if deep else "스캔"
    return {"ok": True, "message": f"{kind}을 시작했습니다.", "deep": deep}


@router.post("/scan-all")
def scan_all(deep: bool = False, _: User = Depends(security.require_admin)):
    started = scanner.scan_all_async(deep=deep)
    if not started:
        raise HTTPException(status_code=409, detail="이미 스캔이 진행 중입니다.")
    kind = "전체 심층 스캔" if deep else "전체 스캔"
    return {"ok": True, "message": f"{kind}을 시작했습니다.", "deep": deep}


@router.get("/scan-status")
def scan_status(_: User = Depends(security.get_current_user)):
    return dict(scanner.scan_status)
