# -*- coding: utf-8 -*-
import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select

from . import config, scanner, scheduler
from .database import init_db, SessionLocal
from .models import Library
from .routers import auth, libraries, browse, media, manage

app = FastAPI(title=config.APP_NAME, version=config.APP_VERSION)

app.include_router(auth.router)
app.include_router(libraries.router)
app.include_router(browse.router)
app.include_router(media.router)
app.include_router(manage.router)

FRONTEND_DIR = Path(os.environ.get(
    "FRONTEND_DIR",
    str(Path(__file__).resolve().parent.parent.parent / "frontend")
)).resolve()


def _seed_libraries():
    seeds = config.parse_seed_libraries()
    if not seeds:
        return
    db = SessionLocal()
    try:
        for name, path in seeds:
            path = path.rstrip("/") or "/"
            if not os.path.isdir(path):
                print(f"[seed] 경로 없음, 건너뜀: {path}", flush=True)
                continue
            exists = db.scalar(select(Library).where(Library.path == path))
            if exists:
                continue
            restricted = ("r17" in name.lower() or "성인" in name or "adult" in name.lower())
            db.add(Library(name=name, path=path, restricted=restricted))
            print(f"[seed] 라이브러리 등록: {name} -> {path}", flush=True)
        db.commit()
    finally:
        db.close()


def apply_read_threads(n: int) -> int:
    """요청 처리(읽기)용 스레드 수 조정. 스캔 작업 스레드와 분리되어 있어
    스캔 중에도 페이지 로딩이 느려지지 않도록 한다."""
    try:
        import anyio.to_thread
        limiter = anyio.to_thread.current_default_thread_limiter()
        if n and n > 0:
            limiter.total_tokens = max(4, min(128, int(n)))
        return int(limiter.total_tokens)
    except Exception:
        return 0


@app.on_event("startup")
def _startup():
    config.ensure_dirs()
    init_db()
    _seed_libraries()
    if config.SCAN_ON_STARTUP:
        scanner.scan_all_async()
        print("[startup] 백그라운드 스캔 시작", flush=True)
    # 읽기 전용 스레드 풀 크기 반영
    try:
        from .database import SessionLocal as _S
        from . import settings_store as _ss
        _db = _S()
        try:
            _n = int((_ss.get_threads(_db) or {}).get("read_threads") or 0)
        finally:
            _db.close()
        if _n:
            print(f"[startup] 읽기 스레드 {apply_read_threads(_n)}개", flush=True)
    except Exception:
        pass
    scheduler.start()  # 예약 스캔 스케줄러


@app.on_event("shutdown")
def _shutdown():
    scheduler.stop()


@app.get("/api/health")
def health():
    return {"status": "ok", "version": app.version}


# ---- 정적 프론트엔드 (있을 경우) ----
if FRONTEND_DIR.exists():
    assets = FRONTEND_DIR / "assets"
    if assets.exists():
        app.mount("/assets", StaticFiles(directory=str(assets)), name="assets")

    @app.get("/manifest.webmanifest")
    def manifest():
        p = FRONTEND_DIR / "manifest.webmanifest"
        if p.exists():
            return FileResponse(str(p), media_type="application/manifest+json")
        return JSONResponse({"detail": "not found"}, status_code=404)

    @app.get("/sw.js")
    def service_worker():
        p = FRONTEND_DIR / "sw.js"
        if p.exists():
            return FileResponse(str(p), media_type="application/javascript")
        return JSONResponse({"detail": "not found"}, status_code=404)

    @app.get("/{full_path:path}")
    def spa(full_path: str, request: Request):
        # /api 로 시작하는데 여기까지 왔다면 실제로 없는 API → JSON 404 (index.html 반환 금지)
        if full_path.startswith("api/") or full_path == "api":
            return JSONResponse({"detail": "Not Found"}, status_code=404)
        # 나머지는 SPA index.html 반환.
        candidate = FRONTEND_DIR / full_path
        if full_path and candidate.is_file():
            return FileResponse(str(candidate))
        index = FRONTEND_DIR / "index.html"
        if index.exists():
            return FileResponse(str(index))
        return JSONResponse({"detail": "frontend not built"}, status_code=404)
