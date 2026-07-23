# -*- coding: utf-8 -*-
"""예약 스캔 스케줄러.

백그라운드 데몬 스레드가 주기적으로 깨어나 DB 에 저장된 스케줄을 확인하고
- 빠른(증분) 스캔
- 심층 스캔
을 조건에 맞으면 실행합니다.  스케줄은 관리 화면에서 변경합니다.
"""
import time
import threading
import datetime as dt

from . import config, scanner, settings_store
from .database import SessionLocal
from .models import utcnow

_thread = None
_stop = threading.Event()


def _parse_hhmm(s: str):
    try:
        h, m = s.split(":")
        return int(h), int(m)
    except Exception:
        return 4, 0


def _quick_due(cfg: dict, last) -> bool:
    if not cfg.get("quick_enabled"):
        return False
    hours = max(1, int(cfg.get("quick_every_hours", 6)))
    if last is None:
        return True
    return (utcnow() - last) >= dt.timedelta(hours=hours)


def _deep_due(cfg: dict, last) -> bool:
    if not cfg.get("deep_enabled"):
        return False
    days = max(1, int(cfg.get("deep_every_days", 7)))
    if last is not None and (utcnow() - last) < dt.timedelta(days=days):
        return False
    # 설정 시각 이후에만 실행 (컨테이너 로컬 시간 기준)
    h, m = _parse_hhmm(cfg.get("deep_at", "04:00"))
    now_local = dt.datetime.now()
    return (now_local.hour, now_local.minute) >= (h, m)


def _optimize_due(cfg, last_iso) -> bool:
    if not cfg.get("optimize_enabled", True):
        return False
    days = int(cfg.get("optimize_every_days", 7) or 7)
    if not last_iso:
        return True
    try:
        last = dt.datetime.fromisoformat(last_iso)
    except (TypeError, ValueError):
        return True
    return (dt.datetime.utcnow() - last).total_seconds() >= days * 86400


def _tick():
    db = SessionLocal()
    try:
        cfg = settings_store.get_scan_schedule(db)
        last_quick = settings_store.get_last_run(db, "quick")
        last_deep = settings_store.get_last_run(db, "deep")
    finally:
        db.close()

    if scanner.scan_status.get("running"):
        return

    # 심층이 우선 (심층은 증분을 포함)
    if _deep_due(cfg, last_deep):
        print("[scheduler] 심층 예약 스캔 시작", flush=True)
        scanner.scan_all(deep=True)
        return
    if _quick_due(cfg, last_quick):
        print("[scheduler] 빠른 예약 스캔 시작", flush=True)
        scanner.scan_all(deep=False)
        return

    # 스캔이 없을 때만 DB 최적화 (VACUUM 은 잠금을 잡으므로)
    db = SessionLocal()
    try:
        last_opt = settings_store.get_json(db, "last_db_optimize", None)
        if _optimize_due(cfg, last_opt):
            print("[scheduler] DB 최적화 시작", flush=True)
            from .database import optimize_db
            r = optimize_db(full=True)
            settings_store.set_json(db, "last_db_optimize", dt.datetime.utcnow().isoformat())
            print(f"[scheduler] DB 최적화 완료 {r.get('steps')} 확보 {r.get('freed')}바이트", flush=True)
    except Exception as e:
        print(f"[scheduler] DB 최적화 실패: {e}", flush=True)
    finally:
        db.close()


def _loop():
    # 시작 직후 잠깐 대기 (기동 스캔과 겹치지 않도록)
    _stop.wait(30)
    while not _stop.is_set():
        try:
            _tick()
        except Exception as e:  # noqa
            print(f"[scheduler] 오류: {e}", flush=True)
        _stop.wait(config.SCHEDULER_TICK_SECONDS)


def start():
    global _thread
    if not config.SCHEDULER_ENABLED:
        return
    if _thread and _thread.is_alive():
        return
    _stop.clear()
    _thread = threading.Thread(target=_loop, daemon=True, name="scheduler")
    _thread.start()
    print("[scheduler] 예약 스캔 스케줄러 시작", flush=True)


def stop():
    _stop.set()
