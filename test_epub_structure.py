# -*- coding: utf-8 -*-
"""실제 EPUB 파일로 목차/삽화 API 및 스캔 사전분석 검증."""
import os, sys, shutil, tempfile
from pathlib import Path

SRC = "/mnt/user-data/uploads/나_혼자만_솔플러_1-385__예신하루.epub"
tmp = Path(tempfile.mkdtemp(prefix="librario_epub_"))
lib = tmp/"lib"/"소설"; lib.mkdir(parents=True)
shutil.copy(SRC, lib/"나 혼자만 솔플러.epub")

os.environ.update(DATA_DIR=str(tmp/"data"), SCAN_ON_STARTUP="false",
                  SCHEDULER_ENABLED="false",
                  SECRET_KEY="test-secret-key-that-is-long-enough-32b")
sys.path.insert(0, str(Path("/home/claude/mangaduck/backend")))
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
    lid = c.post("/api/libraries", json={"name":"소설","path":str(tmp/"lib"),"restricted":False}).json()["id"]
    scanner.scan_library(lid, deep=True)   # 라이브러리 생성 시 자동 스캔이 이미 돌므로 deep 으로 확인
    check("스캔 오류 없음", scanner.scan_status.get("error") is None)
    check("EPUB 사전분석 수행됨", int(scanner.scan_status.get("epub_indexed",0)) >= 1)

    b = c.get("/api/books", params={"library":lid}).json()["items"][0]
    bid = b["id"]

    r = c.get(f"/api/books/{bid}/toc"); j = r.json()
    check("목차 API 200", r.status_code==200)
    check("사전분석 플래그", j["indexed"] is True)
    check("챕터 387개", len(j["chapters"])==387)
    titles=[ch["title"] for ch in j["chapters"]]
    check("실제 챕터 제목 추출", "1. 시련의 탑" in titles and "0. 프롤로그" in titles)
    check("챕터에 href 포함", all("href" in ch for ch in j["chapters"][:5]))

    r = c.get(f"/api/books/{bid}/epub-images"); ij = r.json()
    check("삽화 API 200", r.status_code==200)
    check("삽화 1개(표지) 인식", len(ij["images"])==1)
    href = ij["images"][0]["href"]
    check("삽화에 이동할 챕터 정보", "chapter" in ij["images"][0])

    r = c.get(f"/api/books/{bid}/epub-asset", params={"href":href})
    check("삽화 바이트 전달", r.status_code==200 and r.headers["content-type"].startswith("image/"))
    check("삽화 크기 정상", len(r.content) > 100000)

    r = c.get(f"/api/books/{bid}/epub-asset", params={"href":"../../etc/passwd"})
    check("경로 탈출 차단", r.status_code in (400,404))

    # 챕터 단위 로딩 (대용량 EPUB 대응)
    r = c.get(f"/api/books/{bid}/chapter/2")
    cj = r.json()
    check("챕터 API 200", r.status_code==200)
    check("챕터 제목 반환", cj["title"]=="1. 시련의 탑")
    check("본문 HTML 포함", "<p>" in cj["html"] and len(cj["html"])>500)
    check("전체 파일보다 훨씬 작음", len(cj["html"]) < 100*1024)
    check("script 제거", "<script" not in cj["html"].lower())
    check("총 챕터 수 제공", cj["total"]==387)
    r = c.get(f"/api/books/{bid}/chapter/9999")
    check("범위 밖 챕터 404", r.status_code==404)

    # 스캔 옵션
    r = c.get("/api/scan/options")
    check("스캔 옵션 조회", r.status_code==200 and r.json()["epub_structure"] is True)
    r = c.put("/api/scan/options", json={"epub_structure": False})
    check("스캔 옵션 저장", r.json()["epub_structure"] is False)

print(f"\n결과: {ok} 통과 / {fail} 실패")
shutil.rmtree(tmp, ignore_errors=True)
sys.exit(1 if fail else 0)
