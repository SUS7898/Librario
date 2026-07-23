# -*- coding: utf-8 -*-
import os, sys, shutil, tempfile, zipfile, io
from pathlib import Path
tmp = Path(tempfile.mkdtemp()); lib = tmp/"lib"/"소설"; lib.mkdir(parents=True)
# 사용자 실제 파일명 형식 (txt 와 epub 둘 다)
(lib/"내 마법도서관이 살아있다 1-99 @릿테.txt").write_text("본문"*200, encoding="utf-8")
(lib/"어떤 웹소설 1-250 @다른작가.txt").write_text("본문"*200, encoding="utf-8")
os.environ.update(DATA_DIR=str(tmp/"data"), SCAN_ON_STARTUP="false",
                  SCHEDULER_ENABLED="false", SECRET_KEY="x"*40)
sys.path.insert(0, "/home/claude/mangaduck/backend")
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
    lid=c.post("/api/libraries", json={"name":"소설","path":str(tmp/"lib"),"restricted":False}).json()["id"]
    scanner.scan_library(lid, deep=True)
    items=c.get("/api/books", params={"library":lid}).json()["items"]
    b=[x for x in items if "마법도서관" in x["title"]][0]
    print("   제목:", b["title"], "| 작가:", b["author"], "| 태그:", [t["name"] for t in b["tags"]])
    tn={t["name"] for t in b["tags"]}
    check("제목에서 1-99/@릿테 제거", b["title"]=="내 마법도서관이 살아있다")
    check("작가 = 릿테", b["author"]=="릿테")
    check("작가 태그", "릿테" in tn)
    check("화수 태그는 기본적으로 없음", "1-99화" not in tn and "연재분" not in tn)
    # 작가로 검색/필터
    r=c.get("/api/books", params={"library":lid,"tag":"릿테"})
    check("작가 태그로 검색", r.json()["total"]==1)
    r=c.get("/api/books", params={"library":lid,"search":"릿테"})
    check("작가명 검색(author 필드)", r.json()["total"]>=1)
    r=c.get("/api/tags", params={"library":lid})
    names={t["name"] for t in r.json()["tags"]}
    check("태그 목록에 작가 노출", "릿테" in names and "다른작가" in names)
print(f"\n결과: {ok} 통과 / {fail} 실패")
shutil.rmtree(tmp, ignore_errors=True)
sys.exit(1 if fail else 0)
