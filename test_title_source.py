import os,sys,tempfile,shutil,zipfile
from pathlib import Path
tmp=Path(tempfile.mkdtemp()); lib=tmp/"lib"/"소설"; lib.mkdir(parents=True)
def epub(p, inner_title):
    with zipfile.ZipFile(p,"w") as z:
        z.writestr("mimetype","application/epub+zip")
        z.writestr("META-INF/container.xml",'<?xml version="1.0"?><container xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles><rootfile full-path="OEBPS/c.opf"/></rootfiles></container>')
        z.writestr("OEBPS/t.html","<html><body><p>본문</p></body></html>")
        z.writestr("OEBPS/c.opf",f'<?xml version="1.0"?><package xmlns="http://www.idpf.org/2007/opf"><metadata xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:title>{inner_title}</dc:title></metadata><manifest><item id="a" href="t.html" media-type="application/xhtml+xml"/></manifest><spine><itemref idref="a"/></spine></package>')
# 파일명은 일관되지만 내장 제목은 뒤죽박죽 (사용자 상황 재현)
for n,inner in [("01","제목 1"),("02","제목. 2"),("03","제목. 3"),("10","제목 10")]:
    epub(lib/f"제목 {n}권.epub", inner)
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
    lid=c.post("/api/libraries", json={"name":"소설","path":str(tmp/"lib"),"restricted":False}).json()["id"]
    scanner.scan_library(lid, deep=True)
    sid=c.get("/api/series", params={"library":lid}).json()["items"][0]["id"]
    titles=[b["title"] for b in c.get(f"/api/series/{sid}").json()["books"]]
    print("   기본(내장 우선):", titles)
    check("내장 제목이 쓰여 뒤죽박죽", any("." in t for t in titles))
    # 파일명 우선으로 전환 후 재적용
    c.put("/api/scan/tag-rules", json={"title_source":"filename"})
    r=c.post(f"/api/libraries/{lid}/reapply")
    check("재적용 실행", r.status_code==200 and r.json()["books"]==4)
    titles=[b["title"] for b in c.get(f"/api/series/{sid}").json()["books"]]
    print("   파일명 우선:", titles)
    check("파일명 기준 제목", all(t.startswith("제목") and "." not in t for t in titles))
    check("자연 정렬 (1,2,3,10)", titles==sorted(titles, key=lambda t:int(''.join(ch for ch in t if ch.isdigit()) or 0)))
print(f"\n결과: {ok} 통과 / {fail} 실패")
shutil.rmtree(tmp,ignore_errors=True)
sys.exit(1 if fail else 0)
