# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from .. import config, security, schemas
from ..database import get_db
from ..models import User, Library

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _set_cookie(resp: Response, token: str, remember: bool = True):
    # remember=True → 브라우저를 닫아도 유지되는 지속 쿠키(자동 로그인)
    # remember=False → max_age 없이 세션 쿠키(브라우저 종료 시 만료)
    kwargs = dict(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        secure=config.COOKIE_SECURE,
        path="/",
    )
    if remember:
        kwargs["max_age"] = config.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    resp.set_cookie(**kwargs)


def _token_for(remember: bool):
    minutes = (config.ACCESS_TOKEN_EXPIRE_MINUTES if remember
               else config.SESSION_TOKEN_EXPIRE_MINUTES)
    return minutes


def _user_public(db: Session, u: User):
    return {
        "id": u.id,
        "username": u.username,
        "role": u.role,
        "is_active": u.is_active,
        "granted_library_ids": [l.id for l in u.granted_libraries],
    }


@router.get("/status")
def status(db: Session = Depends(get_db)):
    count = db.scalar(select(func.count(User.id))) or 0
    return {"initialized": count > 0}


@router.post("/setup")
def setup(body: schemas.SetupIn, resp: Response, db: Session = Depends(get_db)):
    count = db.scalar(select(func.count(User.id))) or 0
    if count > 0:
        raise HTTPException(status_code=400, detail="이미 초기화되었습니다.")
    user = User(
        username=body.username.strip(),
        password_hash=security.hash_password(body.password),
        role="admin",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = security.create_access_token(user.id, _token_for(body.remember))
    _set_cookie(resp, token, body.remember)
    return {"token": token, "user": _user_public(db, user)}


@router.post("/login")
def login(body: schemas.LoginIn, resp: Response, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.username == body.username.strip()))
    if not user or not security.verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="아이디 또는 비밀번호가 올바르지 않습니다.")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="비활성화된 계정입니다.")
    token = security.create_access_token(user.id, _token_for(body.remember))
    _set_cookie(resp, token, body.remember)
    return {"token": token, "user": _user_public(db, user)}


@router.post("/logout")
def logout(resp: Response):
    resp.delete_cookie("access_token", path="/")
    return {"ok": True}


@router.get("/me")
def me(user: User = Depends(security.get_current_user), db: Session = Depends(get_db)):
    return _user_public(db, user)


# -------------------- 사용자 관리 (관리자) --------------------
@router.get("/users")
def list_users(_: User = Depends(security.require_admin), db: Session = Depends(get_db)):
    users = db.scalars(select(User).order_by(User.id)).all()
    return [_user_public(db, u) for u in users]


@router.post("/users")
def create_user(body: schemas.UserCreateIn, _: User = Depends(security.require_admin),
                db: Session = Depends(get_db)):
    if db.scalar(select(User).where(User.username == body.username.strip())):
        raise HTTPException(status_code=400, detail="이미 존재하는 아이디입니다.")
    if body.role not in ("admin", "user"):
        raise HTTPException(status_code=400, detail="role 은 admin 또는 user 여야 합니다.")
    u = User(
        username=body.username.strip(),
        password_hash=security.hash_password(body.password),
        role=body.role,
        is_active=True,
    )
    if body.library_ids:
        libs = db.scalars(select(Library).where(Library.id.in_(body.library_ids))).all()
        u.granted_libraries = libs
    db.add(u)
    db.commit()
    db.refresh(u)
    return _user_public(db, u)


@router.patch("/users/{user_id}")
def update_user(user_id: int, body: schemas.UserUpdateIn,
                admin: User = Depends(security.require_admin), db: Session = Depends(get_db)):
    u = db.get(User, user_id)
    if not u:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    if body.password:
        u.password_hash = security.hash_password(body.password)
    if body.role in ("admin", "user"):
        # 마지막 관리자 강등 방지
        if u.role == "admin" and body.role == "user":
            admins = db.scalar(select(func.count(User.id)).where(User.role == "admin")) or 0
            if admins <= 1:
                raise HTTPException(status_code=400, detail="마지막 관리자는 강등할 수 없습니다.")
        u.role = body.role
    if body.is_active is not None:
        if not body.is_active and u.id == admin.id:
            raise HTTPException(status_code=400, detail="자기 자신은 비활성화할 수 없습니다.")
        u.is_active = body.is_active
    if body.library_ids is not None:
        libs = db.scalars(select(Library).where(Library.id.in_(body.library_ids))).all()
        u.granted_libraries = libs
    db.commit()
    db.refresh(u)
    return _user_public(db, u)


@router.delete("/users/{user_id}")
def delete_user(user_id: int, admin: User = Depends(security.require_admin),
                db: Session = Depends(get_db)):
    u = db.get(User, user_id)
    if not u:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    if u.id == admin.id:
        raise HTTPException(status_code=400, detail="자기 자신은 삭제할 수 없습니다.")
    db.delete(u)
    db.commit()
    return {"ok": True}
