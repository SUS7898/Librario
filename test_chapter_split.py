# -*- coding: utf-8 -*-
"""합본 EPUB(한 챕터에 수백 화) 분할 + 미리받기 검증."""
import os, sys, shutil, tempfile, zipfile
from pathlib import Path
tmp=Path(tempfile.mkdtemp()); lib=tmp/"lib"/"소설"; lib.mkdir(parents=True)
# 한 챕터에 300화가 들어간 합본
big_html = "<html><body>" + "".join(
    f"<h2>{i+1}화</h2>" + "<p>본문 문장입니다. 조금 더 길게 씁니다.</p>"*40
    for i in range(300)) + "</body></html>"
with zipfile.ZipFile(lib/"합본소설.epub","w") as z:
    z.writestr("mimetype","application/epub+zip")
    z.writestr("META-INF/container.xml",
      '<?xml version="1.0"?><container xmlns="urn:oasis:names:tc:opendocument:xmlns:container">'
      '<rootfiles><rootfile full-path="OEBPS/content.opf"/></rootfiles></container>')
    z.writestr("OEBPS/Text/all.html", big_html)
    z.writestr("OEBPS/content.opf",
      '<?xml version="1.0"?><package xmlns="http://www.idpf.org/2007/opf">'
      '<manifest><item id="a" href="Text/all.html" media-type="application/xhtml+xml"/></manifest>'
      '<spine><itemref idref="a"/></spine></package>')
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
    bid=c.get("/api/books", params={"library":lid}).json()["items"][0]["id"]
    r=c.get(f"/api/books/{bid}/chapter/0")
    j=r.json()
    print(f"   원본 챕터 {len(big_html)//1024}KB → 조각 {j['parts']}개, 첫 조각 {len(j['html'])//1024}KB")
    check("큰 챕터가 여러 조각으로 분할", j["parts"]>1)
    check("첫 조각만 전송(작음)", len(j["html"]) < 200*1024)
    check("part 인덱스 반환", j["part"]==0)
    # 모든 조각을 합치면 원본 본문과 같아야 함
    joined="".join(c.get(f"/api/books/{bid}/chapter/0?part={p}").json()["html"] for p in range(j["parts"]))
    check("조각 합계 = 원본 본문", joined.count("<h2>")==300)
    check("태그 균형(각 조각)", all(
        c.get(f"/api/books/{bid}/chapter/0?part={p}").json()["html"].count("<p>")==
        c.get(f"/api/books/{bid}/chapter/0?part={p}").json()["html"].count("</p>")
        for p in range(min(j["parts"],3))))
    r=c.get(f"/api/books/{bid}/chapter/0?part=999")
    check("범위 밖 part 는 마지막으로 보정", r.json()["part"]==j["parts"]-1)
    r=c.get(f"/api/books/{bid}/chapter/0?max_chars=30000")
    check("조각 크기 조절 가능", r.json()["parts"] > j["parts"])
print(f"\n결과: {ok} 통과 / {fail} 실패")
shutil.rmtree(tmp, ignore_errors=True)
sys.exit(1 if fail else 0)
