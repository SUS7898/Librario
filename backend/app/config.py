# -*- coding: utf-8 -*-
"""전역 설정. 환경변수로 대부분 제어할 수 있습니다."""
import os
import secrets
from pathlib import Path

# 앱 이름 (컨테이너/이미지/표시 이름)
APP_NAME = os.environ.get("APP_NAME", "Librario")
APP_VERSION = "1.1.0"


def _bool(name: str, default: bool = False) -> bool:
    v = os.environ.get(name)
    if v is None:
        return default
    return v.strip().lower() in ("1", "true", "yes", "on", "y")


def _int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, str(default)))
    except (TypeError, ValueError):
        return default


# ---- 경로 ----
# /data 아래에 config(DB), thumbnails 캐시가 생성됩니다.
DATA_DIR = Path(os.environ.get("DATA_DIR", "/data")).resolve()
CONFIG_DIR = DATA_DIR / "config"
THUMB_DIR = DATA_DIR / "thumbnails"
def _default_db_path() -> str:
    new = CONFIG_DIR / "librario.db"
    legacy = CONFIG_DIR / "mangaduck.db"
    # 예전 이름의 DB 가 이미 있으면 그대로 사용(마이그레이션 불필요)
    if not new.exists() and legacy.exists():
        return str(legacy)
    return str(new)


DB_PATH = os.environ.get("DB_PATH", _default_db_path())

# ---- 인증 ----
# SECRET_KEY 미지정 시 최초 실행에 자동 생성되어 config/secret.key 에 저장됩니다.
_SECRET_ENV = os.environ.get("SECRET_KEY", "").strip()
ACCESS_TOKEN_EXPIRE_MINUTES = _int("ACCESS_TOKEN_EXPIRE_MINUTES", 60 * 24 * 30)  # 30일
# HTTPS 로 외부 노출할 때만 True (LAN/HTTP 사용 시 False 유지)
COOKIE_SECURE = _bool("COOKIE_SECURE", False)

# ---- 썸네일 ----
THUMB_WIDTH = _int("THUMB_WIDTH", 420)
THUMB_QUALITY = _int("THUMB_QUALITY", 82)

# ---- 라이브러리 시딩 ----
# 최초 실행 시 자동 생성할 라이브러리.
#   "이름::/경로;이름2::/경로2"  또는  "/경로;/경로2"  형식
# 컨테이너 안 경로 기준(도커 볼륨 매핑 후 경로)으로 적어야 합니다.
SEED_LIBRARIES = os.environ.get("SEED_LIBRARIES", "").strip()

# ---- 폴더 탐색기(라이브러리 추가 GUI)가 보여줄 최상위 경로 ----
# 지정하지 않으면 컨테이너 "/" 아래에서 시스템 폴더를 제외한 마운트만 자동 노출합니다.
#   예) BROWSE_ROOTS="/Comic;/Novel;/Book"
BROWSE_ROOTS = os.environ.get("BROWSE_ROOTS", "").strip()
_SYS_DIRS = {"app", "bin", "boot", "dev", "etc", "home", "lib", "lib32", "lib64",
             "libx32", "media", "mnt", "opt", "proc", "root", "run", "sbin",
             "srv", "sys", "tmp", "usr", "var", "data"}


def get_browse_roots():
    """폴더 탐색기의 시작 루트 목록(절대경로)."""
    roots = []
    if BROWSE_ROOTS:
        for chunk in BROWSE_ROOTS.replace(",", ";").split(";"):
            c = chunk.strip().rstrip("/")
            if c and os.path.isdir(c) and c not in roots:
                roots.append(c)
    if not roots:
        try:
            for name in sorted(os.listdir("/")):
                if name in _SYS_DIRS or name.startswith("."):
                    continue
                p = "/" + name
                if os.path.isdir(p) and not os.path.islink(p):
                    roots.append(p)
        except OSError:
            pass
    return roots


# 로그인 유지(remember me)를 끈 경우의 짧은 만료 (분)
SESSION_TOKEN_EXPIRE_MINUTES = _int("SESSION_TOKEN_EXPIRE_MINUTES", 60 * 24)  # 1일

# ---- 스캔 ----
SCAN_ON_STARTUP = _bool("SCAN_ON_STARTUP", True)
# 스캔 시 표지/페이지수 계산 대상 파일 형식
SUPPORTED_EXTS = {".cbz", ".zip", ".pdf", ".epub", ".txt"}
# 파일명에서 정규식/키워드로 태그 추출 (ComicInfo.xml 이 없어도 동작)
FILENAME_TAGS = _bool("FILENAME_TAGS", True)

# ---- 예약 스캔 스케줄러 ----
# 백그라운드 스케줄러 스레드 활성화 (실제 주기는 DB 설정에 저장)
SCHEDULER_ENABLED = _bool("SCHEDULER_ENABLED", True)
SCHEDULER_TICK_SECONDS = _int("SCHEDULER_TICK_SECONDS", 60)

# ---- 외부 메타데이터 ----
# 인터넷에서 메타데이터(줄거리/표지/태그)를 가져오는 기능 (NAS 인터넷 연결 필요)
METADATA_ENABLED = _bool("METADATA_ENABLED", True)
METADATA_TIMEOUT = _int("METADATA_TIMEOUT", 8)  # 초


def get_secret_key() -> str:
    if _SECRET_ENV:
        return _SECRET_ENV
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    key_file = CONFIG_DIR / "secret.key"
    if key_file.exists():
        return key_file.read_text(encoding="utf-8").strip()
    key = secrets.token_urlsafe(48)
    key_file.write_text(key, encoding="utf-8")
    try:
        os.chmod(key_file, 0o600)
    except OSError:
        pass
    return key


def ensure_dirs():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    THUMB_DIR.mkdir(parents=True, exist_ok=True)


def parse_seed_libraries():
    """SEED_LIBRARIES 문자열을 (name, path) 리스트로 파싱."""
    out = []
    if not SEED_LIBRARIES:
        return out
    for chunk in SEED_LIBRARIES.split(";"):
        chunk = chunk.strip()
        if not chunk:
            continue
        if "::" in chunk:
            name, path = chunk.split("::", 1)
            name, path = name.strip(), path.strip()
        else:
            path = chunk
            name = os.path.basename(path.rstrip("/")) or path
        if path:
            out.append((name, path))
    return out


# ---- 스캔 병렬 처리 ----
# 0 또는 미지정이면 CPU 코어 수에 맞춰 자동 결정 (I/O 대기가 많아 코어수+2 까지 허용)
SCAN_WORKERS = _int("SCAN_WORKERS", 0)


def scan_workers() -> int:
    if SCAN_WORKERS and SCAN_WORKERS > 0:
        return min(16, SCAN_WORKERS)
    try:
        n = os.cpu_count() or 2
    except Exception:
        n = 2
    return max(2, min(8, n + 1))


# ---- DB 커넥션 풀 ----
# 표지/이미지 스트리밍이 동시에 많이 일어나므로 기본값(5+10)으로는 부족하다.
# SQLite 는 연결 비용이 낮아 넉넉하게 잡아도 된다.
DB_POOL_SIZE = _int("DB_POOL_SIZE", 20)
DB_MAX_OVERFLOW = _int("DB_MAX_OVERFLOW", 60)
DB_POOL_TIMEOUT = _int("DB_POOL_TIMEOUT", 20)
