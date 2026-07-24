import os,sys,tempfile,shutil,zipfile,io
from pathlib import Path
from PIL import Image
tmp=Path(tempfile.mkdtemp()); lib=tmp/"lib"
(lib/"판타지"/"작품A").mkdir(parents=True); (lib/"로맨스"/"작품B").mkdir(parents=True)
def cbz(p):
    with zipfile.ZipFile(p,"w") as z:
        b=io.BytesIO(); Image.new("RGB",(200,300),(5,5,5)).save(b,"JPEG"); z.writestr("1.jpg",b.getvalue())
cbz(lib/"판타지"/"작품A"/"1.cbz")
(lib/"로맨스"/"작품B"/"1.txt").write_text("본문"*100, encoding="utf-8")
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
    lid=c.post("/api/libraries", json={"name":"t","path":str(lib),"restricted":False}).json()["id"]
    scanner.scan_library(lid, deep=True)
    bid=c.get("/api/books", params={"library":lid,"search":"1"}).json()["items"][0]["id"]
    for t in ["완결","추천"]: c.post(f"/api/books/{bid}/tags", json={"tag":t})
    check("형식 단일 필터", c.get("/api/books", params={"fmt":"txt"}).json()["total"]==1)
    check("형식 다중 필터", c.get("/api/books", params={"fmt":"txt,cbz"}).json()["total"]==2)
    r=c.get("/api/books", params={"tags":"완결"})
    check("태그 1개", r.json()["total"]>=1)
    r=c.get("/api/books", params={"tags":"완결,추천"})
    check("태그 2개 모두 가진 것만(AND)", r.json()["total"]==1)
    r=c.get("/api/books", params={"tags":"완결,없는태그"})
    check("하나라도 없으면 제외", r.json()["total"]==0)
    r=c.get("/api/series", params={"tags":"완결"})
    check("시리즈 다중 태그", r.json()["total"]>=1)
    r=c.get("/api/series", params={"fmt":"txt"})
    check("시리즈 형식 필터", r.json()["total"]==1)
print(f"\n결과: {ok} 통과 / {fail} 실패")
shutil.rmtree(tmp,ignore_errors=True)
sys.exit(1 if fail else 0)
