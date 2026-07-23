# -*- coding: utf-8 -*-
import os
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from .. import security, schemas, scanner, config
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
        "sort_order": lib.sort_order or 0,
        "series_count": series_cnt,
        "book_count": book_cnt,
    }


@router.get("")
def list_libraries(user: User = Depends(security.get_current_user), db: Session = Depends(get_db)):
    ids = set(security.accessible_library_ids(db, user))
    libs = db.scalars(select(Library).order_by(Library.sort_order, Library.name)).all()
    return [_lib_dict(db, l) for l in libs if l.id in ids]


@router.post("")
def create_library(body: schemas.LibraryCreateIn, _: User = Depends(security.require_admin),
                   db: Session = Depends(get_db)):
    path = body.path.rstrip("/") or "/"
    if not os.path.isdir(path):
        raise HTTPException(status_code=400, detail=f"폴더가 존재하지 않습니다: {path}")
    if db.scalar(select(Library).where(Library.path == path)):
        raise HTTPException(status_code=400, detail="이미 등록된 경로입니다.")
    max_order = db.scalar(select(func.max(Library.sort_order))) or 0
    lib = Library(name=body.name.strip() or os.path.basename(path), path=path,
                  restricted=body.restricted, sort_order=max_order + 1)
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


@router.put("/order")
def reorder_libraries(body: schemas.LibraryOrderIn, _: User = Depends(security.require_admin),
                      db: Session = Depends(get_db)):
    """전달된 id 순서대로 표시 순서를 다시 매깁니다."""
    for idx, lib_id in enumerate(body.ids):
        lib = db.get(Library, lib_id)
        if lib:
            lib.sort_order = idx
    db.commit()
    libs = db.scalars(select(Library).order_by(Library.sort_order, Library.name)).all()
    return [_lib_dict(db, l) for l in libs]


@router.post("/scan-cancel")
def scan_cancel(_: User = Depends(security.require_admin)):
    if not scanner.scan_status.get("running"):
        return {"ok": False, "message": "진행 중인 스캔이 없습니다."}
    scanner.request_cancel()
    return {"ok": True, "message": "스캔 취소를 요청했습니다. 곧 중단됩니다."}


@router.get("/scan-status")
def scan_status(_: User = Depends(security.get_current_user)):
    return dict(scanner.scan_status)


def _within_roots(real_path, roots):
    for r in roots:
        rr = os.path.realpath(r)
        if real_path == rr or real_path.startswith(rr + os.sep):
            return True
    return False


@router.get("/browse")
def browse_folders(path: str = "", _: User = Depends(security.require_admin)):
    """라이브러리 추가용 폴더 탐색기. path 가 비면 루트 목록을 반환."""
    roots = config.get_browse_roots()
    # 루트 목록
    if not path:
        entries = [{"name": os.path.basename(r) or r, "path": r} for r in roots]
        return {"path": "", "parent": None, "is_root": True, "entries": entries}
    # 경로 정규화 + 허용 루트 안에 있는지 확인 (상위 탈출 방지)
    real = os.path.realpath(path)
    if not _within_roots(real, roots):
        raise HTTPException(status_code=400, detail="접근이 허용되지 않은 경로입니다.")
    if not os.path.isdir(real):
        raise HTTPException(status_code=404, detail="폴더가 존재하지 않습니다.")
    entries = []
    try:
        for name in sorted(os.listdir(real), key=lambda s: s.lower()):
            if name.startswith("."):
                continue
            full = os.path.join(real, name)
            if os.path.isdir(full) and not os.path.islink(full):
                entries.append({"name": name, "path": full})
    except OSError as e:
        raise HTTPException(status_code=400, detail=f"폴더를 읽을 수 없습니다: {e}")
    # 상위 폴더 계산: 현재가 루트면 루트목록("")으로, 아니면 부모(루트 안이면)
    is_a_root = any(real == os.path.realpath(r) for r in roots)
    if is_a_root:
        parent = ""
    else:
        parentdir = os.path.dirname(real)
        parent = parentdir if _within_roots(parentdir, roots) else ""
    return {"path": real, "parent": parent, "is_root": False, "entries": entries}
