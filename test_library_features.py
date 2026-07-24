import os,sys,tempfile,shutil,zipfile,io,json
from pathlib import Path
from PIL import Image
tmp=Path(tempfile.mkdtemp())
a=tmp/"A"/"보관소"/"판타지"/"내소설"; a.mkdir(parents=True)
b=tmp/"B"/"만화"/"작품1"; b.mkdir(parents=True)
def cbz(p):
    with zipfile.ZipFile(p,"w") as z:
        bb=io.BytesIO(); Image.new("RGB",(300,420),(9,9,9)).save(bb,"JPEG"); z.writestr("1.jpg", bb.getvalue())
cbz(a/"1권.cbz"); cbz(b/"1화.cbz")
os.environ.update(DATA_DIR=str(tmp/"data"),SCAN_ON_STARTUP="false",SCHEDULER_ENABLED="false",SECRET_KEY="x"*40)
sys.path.insert(0,"/home/claude/mangaduck/backend")
from fastapi.testclient import TestClient
from app.main import app
from app import scanner
ok=fail=0
def check(n,c):
    global ok,fail
    if c: ok+=1; print(f"  ✅ {n}")
    else: fail+=1; print(f"  ❌ {n}")
with TestClient(app) as c:
    c.post("/api/auth/setup", json={"username":"a","password":"pass1234"})
    # 여러 경로
    r=c.post("/api/libraries", json={"name":"통합","path":str(tmp/"A"),
                                     "extra_paths":[str(tmp/"B")],"restricted":False})
    lid=r.json()["id"]
    check("추가 경로 저장", r.json()["extra_paths"]==[str(tmp/"B")])
    check("roots 2개", len(r.json()["roots"])==2)
    scanner.scan_library(lid, deep=True)
    items=c.get("/api/books", params={"library":lid}).json()["items"]
    check("두 경로 모두 스캔", len(items)==2)
    # 태그 제외
    r=c.put("/api/scan/tag-rules", json={"exclude_folders":["보관소"]})
    check("제외 폴더 저장", "보관소" in r.json()["exclude_folders"])
    scanner.scan_library(lid, deep=True)
    tags={t["name"] for it in c.get("/api/books", params={"library":lid}).json()["items"] for t in it["tags"]}
    check("보관소 태그 사라짐", "보관소" not in tags)
    check("판타지 태그는 유지", "판타지" in tags)
    # 라이브러리별 설정
    r=c.patch(f"/api/libraries/{lid}", json={"settings":{"schedule":{"mode":"custom",
        "quick_enabled":True,"quick_every_hours":3,"deep_enabled":False,"deep_at":"04:00"}}})
    check("라이브러리 설정 저장", r.json()["settings"]["schedule"]["quick_every_hours"]==3)
    # 대기열
    scanner.enqueue_scan(lid,"통합",False); scanner.enqueue_scan(999,"가짜",False)
    q=c.get("/api/libraries/queue").json()
    check("대기열 조회", len(q["queue"])>=1)
    r=c.put("/api/libraries/queue/order", json={"ids":[999,lid]})
    ids=[x["library_id"] for x in r.json()["queue"]]
    check("대기열 순서 변경", ids[0]==999)
    r=c.delete(f"/api/libraries/queue/999")
    check("대기열 개별 취소", all(x["library_id"]!=999 for x in r.json()["queue"]))
    r=c.post("/api/libraries/queue/clear")
    check("대기열 비우기", r.json()["queue"]==[])
print(f"\n결과: {ok} 통과 / {fail} 실패")
shutil.rmtree(tmp,ignore_errors=True)
sys.exit(1 if fail else 0)
