# -*- coding: utf-8 -*-
"""신규 기능 테스트: 휴지통/이동복구/심층스캔/파일명태그/새로고침/예약스캔/분석/자동로그인/메타파서."""
import io
import os
import sys
import shutil
import tempfile
import zipfile
from pathlib import Path

from PIL import Image


def make_jpeg(color=(180, 90, 90), size=(300, 420)) -> bytes:
    im = Image.new("RGB", size, color)
    b = io.BytesIO()
    im.save(b, "JPEG")
    return b.getvalue()


def make_cbz(path: Path, pages=3, comicinfo=True, title="제목"):
    with zipfile.ZipFile(path, "w") as z:
        for i in range(pages):
            z.writestr(f"{i+1:03d}.jpg", make_jpeg((60 + i * 30, 100, 150)))
        if comicinfo:
            z.writestr("ComicInfo.xml",
                       f'<?xml version="1.0"?><ComicInfo><Title>{title}</Title>'
                       '<Publisher>어떤출판사</Publisher><LanguageISO>ko</LanguageISO>'
                       '<Number>1</Number><Summary>줄거리 요약</Summary>'
                       '<Genre>액션</Genre></ComicInfo>')


def main():
    tmp = Path(tempfile.mkdtemp(prefix="librario_new_"))
    data_dir = tmp / "data"
    lib_dir = tmp / "lib"
    (lib_dir / "판타지").mkdir(parents=True)

    # 파일명 태그가 들어간 cbz (ComicInfo 없음 → 파일명에서 태그 추출 검증)
    fn_tag_file = lib_dir / "판타지" / "[스캔팀] 던전 이야기 1-050화 [완결].cbz"
    make_cbz(fn_tag_file, pages=3, comicinfo=False)

    # 이동/휴지통 테스트용 파일 (고유 제목으로 검색 가능하게)
    move_src = lib_dir / "판타지" / "이동테스트.cbz"
    make_cbz(move_src, pages=2, comicinfo=True, title="이동테스트책")

    os.environ["DATA_DIR"] = str(data_dir)
    os.environ["SCAN_ON_STARTUP"] = "false"
    os.environ["SCHEDULER_ENABLED"] = "false"
    os.environ["SECRET_KEY"] = "test-secret-key-that-is-long-enough-32b"

    sys.path.insert(0, str(Path(__file__).resolve().parent / "backend"))
    from fastapi.testclient import TestClient
    from app.main import app
    from app import scanner, metadata
    from app.database import SessionLocal
    from app.models import Book

    ok = 0
    fail = 0

    def check(name, cond):
        nonlocal ok, fail
        if cond:
            ok += 1
            print(f"  ✅ {name}")
        else:
            fail += 1
            print(f"  ❌ {name}")

    # -------- 오프라인: 메타데이터 파서 --------
    print("== 메타데이터 파서 (오프라인) ==")
    g = metadata.parse_google_item({
        "id": "abc", "volumeInfo": {
            "title": "구글북", "authors": ["작가A"], "description": "<p>설명</p>",
            "publisher": "펍", "publishedDate": "2019-05-01", "language": "ko",
            "categories": ["Fiction"], "imageLinks": {"thumbnail": "http://x/y.jpg"}}})
    check("google 파서 title/year/https표지",
          g["title"] == "구글북" and g["year"] == 2019
          and g["cover_url"].startswith("https://") and g["description"] == "설명")
    o = metadata.parse_openlib_doc({
        "key": "/works/OL1W", "title": "오픈북", "author_name": ["작가B"],
        "first_publish_year": 2001, "cover_i": 123, "subject": ["Magic"] * 30})
    check("openlib 파서 표지URL/태그15개제한",
          o["cover_url"].endswith("123-L.jpg") and len(o["tags"]) == 15)
    a = metadata.parse_anilist_media({
        "id": 5, "title": {"english": "Dungeon", "romaji": "Danjon"},
        "description": "줄거리<br>둘째줄", "genres": ["Action"],
        "tags": [{"name": "Magic", "rank": 80}, {"name": "Low", "rank": 10}],
        "coverImage": {"large": "https://c/large.jpg"}, "startDate": {"year": 2015}})
    check("anilist 파서 title/genre+고랭크태그/저랭크제외",
          a["title"] == "Dungeon" and "Action" in a["tags"]
          and "Magic" in a["tags"] and "Low" not in a["tags"])

    with TestClient(app) as client:
        # -------- 자동 로그인(remember) 쿠키 --------
        print("== 자동 로그인(로그인 유지) ==")
        r = client.post("/api/auth/setup",
                        json={"username": "admin", "password": "pass1234", "remember": True})
        check("setup 성공", r.status_code == 200)
        sc = r.headers.get("set-cookie", "")
        check("remember=True → 지속 쿠키(Max-Age 있음)", "max-age=" in sc.lower())

        r2 = client.post("/api/auth/login",
                         json={"username": "admin", "password": "pass1234", "remember": False})
        sc2 = r2.headers.get("set-cookie", "")
        check("remember=False → 세션 쿠키(Max-Age 없음)", "max-age=" not in sc2.lower())
        # 세션 쿠키라도 토큰 자체는 유효 → me 성공
        client.post("/api/auth/login",
                    json={"username": "admin", "password": "pass1234", "remember": True})

        # -------- 없는 API 는 index.html 이 아니라 404 --------
        print("== /api 404 처리 ==")
        r = client.get("/api/does-not-exist")
        check("없는 API → 404", r.status_code == 404)
        check("없는 API → JSON(detail)", r.headers.get("content-type", "").startswith("application/json"))

        # -------- 라이브러리 생성 + 스캔 --------
        print("== 스캔/파일명 태그 ==")
        r = client.post("/api/libraries", json={"name": "만화", "path": str(lib_dir),
                                                "restricted": False})
        lib_id = r.json()["id"]
        scanner.scan_library(lib_id)
        check("스캔 에러 없음", scanner.scan_status.get("error") is None)

        # 파일명 태그 검증
        r = client.get("/api/books", params={"library": lib_id, "search": "던전"})
        items = r.json()["items"]
        check("던전 책 검색됨", len(items) >= 1)
        dungeon = items[0]
        tagnames = {t["name"] for t in dungeon["tags"]}
        check("대괄호 태그 '스캔팀'", "스캔팀" in tagnames)
        check("키워드 태그 '완결'", "완결" in tagnames)
        check("정규식 태그 '연재분'(화수범위)", "연재분" in tagnames)
        check("바로 위 폴더는 시리즈(판타지)", dungeon["series_name"] == "판타지")

        # -------- 메타데이터 새로고침 --------
        print("== 메타데이터 새로고침 ==")
        # 이동테스트 책 찾기 (ComicInfo Title = '이동테스트책')
        r = client.get("/api/books", params={"library": lib_id, "search": "이동테스트책"})
        move_book = r.json()["items"][0]
        move_id = move_book["id"]
        # 수동 태그 + 평점 부여 (이동 후 유지되는지 확인용)
        client.post(f"/api/books/{move_id}/tags", json={"tag": "내태그"})
        client.put(f"/api/books/{move_id}/rating", json={"value": 4})
        r = client.post(f"/api/books/{move_id}/refresh")
        check("새로고침 성공", r.status_code == 200 and r.json()["ok"])
        check("ComicInfo publisher 반영", r.json()["book"]["publisher"] == "어떤출판사")
        check("ComicInfo 언어 반영", r.json()["book"]["language"] == "ko")
        check("ComicInfo Summary → description", r.json()["book"]["description"] == "줄거리 요약")

        # -------- 휴지통: 파일 삭제 --------
        print("== 휴지통(소프트 삭제) ==")
        os.remove(move_src)  # 파일 제거
        scanner.scan_library(lib_id)
        check("삭제 파일 → trashed 카운트", int(scanner.scan_status.get("trashed", 0)) >= 1)
        # 브라우즈에서 사라짐
        r = client.get("/api/books", params={"library": lib_id, "search": "이동테스트책"})
        check("휴지통 책은 목록에서 숨김", len(r.json()["items"]) == 0)
        # 휴지통 목록엔 있음
        r = client.get("/api/trash")
        trash_titles = [it["title"] for it in r.json()["items"]]
        check("휴지통 목록에 존재", any("이동테스트책" == t for t in trash_titles))
        check("휴지통 file_exists=False",
              all(not it["file_exists"] for it in r.json()["items"]))

        # -------- 휴지통: 이동 복구 (다른 경로에 동일 파일) --------
        print("== 이동 감지 → 자동 복구 ==")
        moved_dst = lib_dir / "판타지" / "옮겨진폴더"
        moved_dst.mkdir(parents=True, exist_ok=True)
        make_cbz(moved_dst / "이동테스트.cbz", pages=2, comicinfo=True,
                 title="이동테스트책")  # 동일 basename+동일 내용
        scanner.scan_library(lib_id)
        check("복구(restored) 카운트 ≥1", int(scanner.scan_status.get("restored", 0)) >= 1)
        r = client.get(f"/api/books/{move_id}")
        check("복구된 책 status=active", r.status_code == 200 and r.json()["status"] == "active")
        rtags = {t["name"] for t in r.json()["tags"]}
        check("이동 후 수동태그 '내태그' 유지", "내태그" in rtags)
        check("이동 후 평점 4 유지", r.json()["my_rating"] == 4)
        check("이동 후 새 시리즈(옮겨진폴더) 반영", r.json().get("series_name") == "옮겨진폴더")

        # -------- 휴지통 영구 삭제 & 비우기 --------
        print("== 휴지통 영구 삭제 ==")
        # 파일명태그 파일을 지워 휴지통에 하나 만들고 영구삭제
        os.remove(fn_tag_file)
        scanner.scan_library(lib_id)
        r = client.get("/api/trash")
        n_before = r.json()["total"]
        check("휴지통에 항목 존재", n_before >= 1)
        r = client.post("/api/trash/empty")
        check("휴지통 비우기 성공", r.status_code == 200 and r.json()["deleted"] >= 1)
        r = client.get("/api/trash")
        check("비운 후 휴지통 0", r.json()["total"] == 0)

        # -------- 심층 스캔 --------
        print("== 심층(deep) 스캔 ==")
        scanner.scan_library(lib_id, deep=True)  # 동기 실행으로 경쟁 상태 제거
        check("심층 스캔 모드 기록", scanner.scan_status.get("mode") == "deep")
        check("심층 스캔 에러 없음", scanner.scan_status.get("error") is None)

        # -------- 예약 스캔 스케줄 --------
        print("== 예약 스캔 스케줄 ==")
        r = client.get("/api/scan/schedule")
        check("스케줄 조회 기본값", r.status_code == 200 and "quick_enabled" in r.json())
        r = client.put("/api/scan/schedule", json={
            "quick_enabled": True, "quick_every_hours": 3,
            "deep_enabled": True, "deep_every_days": 5, "deep_at": "03:30"})
        check("스케줄 저장", r.json()["quick_every_hours"] == 3 and r.json()["deep_at"] == "03:30")
        r = client.put("/api/scan/schedule", json={"deep_at": "bad"})
        check("잘못된 deep_at 거부", r.status_code == 400)

        # -------- 태그 규칙 --------
        print("== 파일명 태그 규칙 ==")
        r = client.get("/api/scan/tag-rules")
        check("태그 규칙 조회", r.status_code == 200 and r.json().get("enabled") is True)
        r = client.put("/api/scan/tag-rules", json={
            "keywords": [{"match": "특별판", "tag": "특별판"}]})
        check("태그 규칙 저장", any(k["tag"] == "특별판" for k in r.json()["keywords"]))

        # -------- 메타데이터 공급자 목록/검색 --------
        print("== 외부 메타데이터 ==")
        r = client.get("/api/metadata/providers")
        pids = {p["id"] for p in r.json()["providers"]}
        check("공급자 3종 노출", {"google", "openlib", "anilist"} <= pids)
        r = client.get(f"/api/books/{move_id}/metadata/search",
                       params={"provider": "google", "query": "python"})
        # 오프라인이면 results=[] 지만 200 이어야 함
        check("메타 검색 200(오프라인 허용)", r.status_code == 200 and "results" in r.json())

        # -------- 분석 --------
        print("== 분석 ==")
        r = client.get("/api/analytics")
        j = r.json()
        check("분석 totals 구조", "totals" in j and "books" in j["totals"])
        check("분석 by_format 존재", isinstance(j["by_format"], list))
        check("분석 by_library 존재", any(l["id"] == lib_id for l in j["by_library"]))
        check("분석 저장용량 ≥0", j["totals"]["size"] >= 0)

    print(f"\n결과: {ok} 통과 / {fail} 실패")
    shutil.rmtree(tmp, ignore_errors=True)
    sys.exit(1 if fail else 0)


if __name__ == "__main__":
    main()
