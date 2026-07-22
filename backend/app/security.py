# -*- coding: utf-8 -*-
import hashlib
import hmac
import os
import base64
import datetime as dt
from typing import Optional

import jwt
from fastapi import Depends, HTTPException, status, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from . import config
from .database import get_db
from .models import User

ALGO = "HS256"
_PBKDF2_ROUNDS = 200_000


# ---------------------------------------------------------------------------
# 비밀번호 해싱 (표준 라이브러리 PBKDF2 - 외부 의존성 없음)
# ---------------------------------------------------------------------------
def hash_password(password: str) -> str:
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _PBKDF2_ROUNDS)
    return "pbkdf2_sha256${}${}${}".format(
        _PBKDF2_ROUNDS,
        base64.b64encode(salt).decode(),
        base64.b64encode(dk).decode(),
    )


def verify_password(password: str, stored: str) -> bool:
    try:
        algo, rounds, b64salt, b64hash = stored.split("$")
        if algo != "pbkdf2_sha256":
            return False
        salt = base64.b64decode(b64salt)
        expected = base64.b64decode(b64hash)
        dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, int(rounds))
        return hmac.compare_digest(dk, expected)
    except Exception:
        return False


# ---------------------------------------------------------------------------
# JWT
# ---------------------------------------------------------------------------
def create_access_token(user_id: int, expires_minutes: Optional[int] = None) -> str:
    now = dt.datetime.utcnow()
    minutes = expires_minutes if expires_minutes is not None else config.ACCESS_TOKEN_EXPIRE_MINUTES
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + dt.timedelta(minutes=minutes),
    }
    return jwt.encode(payload, config.get_secret_key(), algorithm=ALGO)


def _decode(token: str) -> Optional[int]:
    try:
        data = jwt.decode(token, config.get_secret_key(), algorithms=[ALGO])
        return int(data.get("sub"))
    except Exception:
        return None


def _extract_token(request: Request) -> Optional[str]:
    # 1) Authorization: Bearer xxx  (네이티브 앱)
    auth = request.headers.get("Authorization", "")
    if auth.lower().startswith("bearer "):
        return auth[7:].strip()
    # 2) 쿠키 (웹앱 - img/epub.js/pdf.js 가 자동 전송)
    tok = request.cookies.get("access_token")
    if tok:
        return tok
    # 3) 쿼리 파라미터 (예외적 상황)
    tok = request.query_params.get("token")
    if tok:
        return tok
    return None


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = _extract_token(request)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="인증이 필요합니다.")
    uid = _decode(token)
    if uid is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="토큰이 유효하지 않습니다.")
    user = db.get(User, uid)
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="비활성 사용자입니다.")
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="관리자 권한이 필요합니다.")
    return user


# ---------------------------------------------------------------------------
# 접근 가능한 라이브러리 계산
# ---------------------------------------------------------------------------
def accessible_library_ids(db: Session, user: User):
    from .models import Library
    if user.is_admin:
        return [l.id for l in db.scalars(select(Library)).all()]
    ids = set()
    for lib in db.scalars(select(Library)).all():
        if not lib.restricted:
            ids.add(lib.id)
    for lib in user.granted_libraries:
        ids.add(lib.id)
    return list(ids)


def can_access_library(db: Session, user: User, library_id: int) -> bool:
    return library_id in set(accessible_library_ids(db, user))
