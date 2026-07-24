# -*- coding: utf-8 -*-
"""초성검색 · 중복찾기 · 백업/복원 · 다음권 · 미독필터 테스트."""
import io, os, sys, shutil, tempfile, zipfile
from pathlib import Path
from PIL import Image

def jpg(c=(90,110,160)):
    b=io.BytesIO(); Image.new("RGB",(300,420),c).save(b,"JPEG"); return b.getvalue()

def cbz(p, pages=3):
    with zipfile.ZipFile(p,"w") as z:
        for i in range(pages): z.writestr(f"{i:03d}.jpg", jpg())

tmp=Path(tempfile.mkdtemp(prefix="librario_v12_"))
lib=tmp/"lib"; (lib/"나 혼자만 솔플러").mkdir(parents=True)
cbz(lib/"나 혼자만 솔플러"/"1권.cbz"); cbz(lib/"나 혼자만 솔플러"/"2권.cbz"); cbz(lib/"나 혼자만 솔플러"/"3권.cbz")
(lib/"던전 이야기").mkdir()
cbz(lib/"던전 이야기"/"단행본.cbz", pages=5)
# 중복: 다른 폴더에 같은 이름·같은 크기
(lib/"백업본").mkdir()
shutil.copy(lib/"나 혼자만 솔플러"/"1권.cbz", lib/"백업본"/"1권.cbz")

os.environ.update(DATA_DIR=str(tmp/"data"), SCAN_ON_STARTUP="false",
                  SCHEDULER_ENABLED="false", SECRET_KEY="x"*40)
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
    c.post("/api/auth/setup", json={"username":"admin","password":"pass1234"})
    lid=c.post("/api/libraries", json={"name":"만화","path":str(lib),"restricted":False}).json()["id"]
    scanner.scan_library(lid, deep=True)

    print("== 1. 초성 검색 ==")
    r=c.get("/api/series", params={"search":"ㄴㅎㅈㅁ"})
    check("시리즈 초성 검색 (ㄴㅎㅈㅁ → 나 혼자만 솔플러)",
          r.json()["total"]>=1 and any("나 혼자만" in x["name"] for x in r.json()["items"]))
    r=c.get("/api/series", params={"search":"ㄷㅈ"})
    check("부분 초성 검색 (ㄷㅈ → 던전 이야기)", any("던전" in x["name"] for x in r.json()["items"]))
    r=c.get("/api/series", params={"search":"ㅋㅋㅋㅋ"})
    check("없는 초성은 결과 없음", r.json()["total"]==0)
    r=c.get("/api/series", params={"search":"나 혼자만"})
    check("일반 검색도 그대로 동작", r.json()["total"]>=1)

    print("== 2. 중복 찾기 ==")
    r=c.get("/api/duplicates")
    j=r.json()
    check("중복 그룹 탐지", j["group_count"]>=1)
    grp=j["groups"][0]
    check("그룹에 2개 이상", len(grp)>=2)
    check("낭비 용량 계산", j["wasted"]>0)
    check("경로 정보 포함", all("path" in i for i in grp))
    dup_id=[i for i in grp if "백업본" in i["path"]][0]["id"]
    r=c.post("/api/duplicates/resolve", json={"ids":[dup_id]}, params={"permanent":"true"})
    check("중복 영구 삭제", r.status_code==200 and r.json()["count"]==1)
    check("삭제 후 중복 사라짐", c.get("/api/duplicates").json()["group_count"]==0)
    r=c.get("/api/duplicates", params={"mode":"title"})
    check("제목 기준 모드 동작", r.status_code==200 and "groups" in r.json())

    print("== 3. 다음 권 ==")
    books=c.get("/api/books", params={"library":lid,"sort":"title","order":"asc"}).json()["items"]
    solo=[b for b in books if "나 혼자만" in (b.get("series_name") or "")]
    b1=sorted(solo, key=lambda x:x["title"])[0]
    r=c.get(f"/api/books/{b1['id']}/next")
    check("다음 권 반환", r.json()["next"] is not None)
    last=sorted(solo, key=lambda x:x["title"])[-1]
    r=c.get(f"/api/books/{last['id']}/next")
    check("마지막 권은 next=None", r.json()["next"] is None)

    print("== 4. 미독 필터 ==")
    total=c.get("/api/books", params={"library":lid}).json()["total"]
    r=c.get("/api/books", params={"library":lid,"progress":"unread"})
    check("전부 미독", r.json()["total"]==total)
    c.put(f"/api/books/{b1['id']}/progress", json={"page":1})
    r=c.get("/api/books", params={"library":lid,"progress":"unread"})
    check("읽은 책은 미독에서 제외", r.json()["total"]==total-1)

    print("== 5. 백업 / 복원 ==")
    sid=c.get("/api/series", params={"library":lid}).json()["items"][0]["id"]
    c.put(f"/api/series/{sid}/rating", json={"value":5})
    c.post(f"/api/favorites/series/{sid}")
    c.put(f"/api/books/{b1['id']}/rating", json={"value":4})
    c.post(f"/api/books/{b1['id']}/tags", json={"tag":"내수동태그"})
    bk=c.get("/api/backup").json()
    check("백업 생성", bk["version"]==1 and bk["counts"]["ratings"]>=1)
    check("시리즈 별점 포함", bk["counts"]["series_ratings"]>=1)
    check("즐겨찾기 포함", bk["counts"]["favorites"]>=1)
    check("수동태그 포함", bk["counts"]["manual_tags"]>=1)
    check("진행률 포함", bk["counts"]["progress"]>=1)
    # 사용자 데이터를 지운 뒤 복원
    c.delete(f"/api/favorites/series/{sid}")
    c.put(f"/api/series/{sid}/rating", json={"value":0})
    c.put(f"/api/books/{b1['id']}/rating", json={"value":0})
    check("초기화 확인", c.get("/api/series", params={"library":lid}).json()["items"][0]["favorite"] is False)
    r=c.post("/api/restore", json=bk)
    check("복원 성공", r.status_code==200 and r.json()["applied"]["ratings"]>=1)
    s0=c.get("/api/series", params={"library":lid}).json()["items"][0]
    check("즐겨찾기 복원", s0["favorite"] is True)
    check("시리즈 별점 복원", s0["my_rating"]==5)
    bb=c.get(f"/api/books/{b1['id']}").json()
    check("책 별점 복원", bb["my_rating"]==4)
    check("수동태그 복원", any(t["name"]=="내수동태그" for t in bb["tags"]))
    r=c.post("/api/restore", json={"nope":1})
    check("잘못된 백업 거부", r.status_code==400)

print(f"\n결과: {ok} 통과 / {fail} 실패")
shutil.rmtree(tmp, ignore_errors=True)
sys.exit(1 if fail else 0)
