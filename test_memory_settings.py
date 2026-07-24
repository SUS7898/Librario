import os, sys, tempfile, shutil
from pathlib import Path
tmp=Path(tempfile.mkdtemp())
os.environ.update(DATA_DIR=str(tmp), SCAN_ON_STARTUP="false", SCHEDULER_ENABLED="false", SECRET_KEY="x"*40)
sys.path.insert(0,"/home/claude/mangaduck/backend")
from fastapi.testclient import TestClient
from app.main import app
ok=fail=0
def check(n,c):
    global ok,fail
    if c: ok+=1; print(f"  ✅ {n}")
    else: fail+=1; print(f"  ❌ {n}")
with TestClient(app) as c:
    c.post("/api/auth/setup", json={"username":"a","password":"pass1234"})
    r=c.get("/api/memory"); j=r.json()
    check("메모리 설정 조회", r.status_code==200 and "cache_mb" in j)
    check("시스템 RAM 감지", j.get("system_ram_mb") is None or j["system_ram_mb"]>0)
    r=c.put("/api/memory", json={"cache_mb":512,"mmap_mb":2048,"home_cache_sec":60})
    j=r.json()
    check("설정 저장", j["cache_mb"]==512 and j["mmap_mb"]==2048)
    check("즉시 적용", j["applied"]["cache_mb"]==512)
    # 새 연결에서 PRAGMA 가 실제로 반영되는지
    from app.database import engine
    with engine.connect() as conn:
        cs=conn.exec_driver_sql("PRAGMA cache_size").scalar()
        mm=conn.exec_driver_sql("PRAGMA mmap_size").scalar()
    check(f"PRAGMA cache_size 반영 ({cs})", int(cs)==-512000)
    # SQLite 는 mmap_size 를 페이지 크기 배수로 내림 조정한다
    want=2048*1024*1024
    check(f"PRAGMA mmap_size 반영 ({mm})", 0 < want-int(mm) <= 1024*1024 or int(mm)==want)
    r=c.put("/api/memory", json={"cache_mb":99999})
    check("범위 초과는 상한으로 보정", r.json()["cache_mb"]==4096)
    check("DB 정상 동작", c.get("/api/libraries").status_code==200)
print(f"\n결과: {ok} 통과 / {fail} 실패")
shutil.rmtree(tmp, ignore_errors=True)
sys.exit(1 if fail else 0)
