# -*- coding: utf-8 -*-
"""백엔드 전 기능 스모크 테스트. 샘플 라이브러리를 만들어 API 흐름을 검증."""
import io
import os
import sys
import tempfile
import zipfile
from pathlib import Path

from PIL import Image


def make_jpeg(color=(200, 80, 80), size=(300, 420)) -> bytes:
    im = Image.new("RGB", size, color)
    b = io.BytesIO()
    im.save(b, "JPEG")
    return b.getvalue()


def make_cbz(path: Path, pages=3, completed_title=False):
    ci = (
        '<?xml version="1.0"?>\n<ComicInfo>'
        '<Title>멋진 만화 1권</Title>'
        '<Genre>액션</Genre>'
        '<Tags>액션, 모험</Tags>'
        '<Writer>홍길동</Writer>'
        '</ComicInfo>'
    )
    with zipfile.ZipFile(path, "w") as z:
        for i in range(pages):
            z.writestr(f"{i+1:03d}.jpg", make_jpeg(color=(60 + i * 40, 100, 160)))
        z.writestr("ComicInfo.xml", ci)


def make_epub(path: Path):
    cover = make_jpeg(color=(70, 130, 180), size=(400, 560))
    container = (
        '<?xml version="1.0"?>\n'
        '<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">'
        '<rootfiles><rootfile full-path="OEBPS/content.opf" '
        'media-type="application/oebps-package+xml"/></rootfiles></container>'
    )
    opf = (
        '<?xml version="1.0"?>\n'
        '<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="id">'
        '<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">'
        '<dc:title>테스트 소설</dc:title>'
        '<dc:creator>김작가</dc:creator>'
        '<meta name="cover" content="cover-img"/>'
        '</metadata>'
        '<manifest>'
        '<item id="cover-img" href="images/cover.jpg" media-type="image/jpeg" properties="cover-image"/>'
        '<item id="ch1" href="ch1.xhtml" media-type="application/xhtml+xml"/>'
        '</manifest>'
        '<spine><itemref idref="ch1"/></spine>'
        '</package>'
    )
    ch1 = ('<?xml version="1.0"?>\n<html xmlns="http://www.w3.org/1999/xhtml"><head>'
           '<title>1장</title></head><body><h1>1장</h1><p>안녕하세요. 테스트 본문입니다.</p>'
           '</body></html>')
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        z.writestr("META-INF/container.xml", container)
        z.writestr("OEBPS/content.opf", opf)
        z.writestr("OEBPS/ch1.xhtml", ch1)
        z.writestr("OEBPS/images/cover.jpg", cover)


def main():
    tmp = Path(tempfile.mkdtemp(prefix="mangaduck_test_"))
    data_dir = tmp / "data"
    lib_dir = tmp / "library"
    # 폴더 구조: library/판타지/현대 판타지/멋진 만화 (완)/vol1.cbz
    comic_folder = lib_dir / "판타지" / "현대 판타지" / "멋진 만화 (완)"
    comic_folder.mkdir(parents=True)
    make_cbz(comic_folder / "멋진 만화 1권.cbz", pages=3)

    novel_folder = lib_dir / "소설" / "판타지소설" / "테스트 소설"
    novel_folder.mkdir(parents=True)
    make_epub(novel_folder / "테스트 소설.epub")

    essay_folder = lib_dir / "에세이" / "글모음"
    essay_folder.mkdir(parents=True)
    (essay_folder / "나의 노트.txt").write_text("첫 줄\n둘째 줄\n" * 100, encoding="utf-8")

    os.environ["DATA_DIR"] = str(data_dir)
    os.environ["SCAN_ON_STARTUP"] = "false"
    os.environ["SECRET_KEY"] = "test-secret-key"

    sys.path.insert(0, str(Path(__file__).resolve().parent / "backend"))
    from fastapi.testclient import TestClient
    from app.main import app
    from app import scanner
    from app.database import SessionLocal
    from app.models import Library

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

    with TestClient(app) as client:
        print("== 인증 ==")
        r = client.get("/api/auth/status")
        check("status initialized=False", r.json().get("initialized") is False)

        r = client.post("/api/auth/setup", json={"username": "admin", "password": "pass1234"})
        check("setup 성공", r.status_code == 200 and "token" in r.json())
        check("첫 사용자 admin", r.json()["user"]["role"] == "admin")

        r = client.get("/api/auth/me")
        check("me (쿠키 인증)", r.status_code == 200 and r.json()["username"] == "admin")

        print("== 라이브러리 & 스캔 ==")
        r = client.post("/api/libraries", json={"name": "만화", "path": str(lib_dir),
                                                "restricted": False})
        check("라이브러리 생성", r.status_code == 200)
        lib_id = r.json()["id"]

        # 동기 스캔 실행 (라이브러리 생성 시 async 스캔이 이미 돌았을 수 있으므로 found 로 확인)
        scanner.scan_library(lib_id)
        check("스캔 파일 발견 3개", int(scanner.scan_status.get("found", 0)) >= 3)
        check("스캔 에러 없음", scanner.scan_status.get("error") is None)

        r = client.get("/api/libraries")
        libs = r.json()
        check("라이브러리 통계", libs[0]["book_count"] == 3)

        print("== 홈 ==")
        r = client.get("/api/home")
        h = r.json()
        check("최근 추가된 책 3권", len(h["recently_added_books"]) == 3)
        check("최근 업데이트 시리즈", len(h["recently_updated_series"]) >= 3)

        print("== 시리즈 ==")
        r = client.get("/api/series")
        s = r.json()
        check("시리즈 목록", s["total"] == 3)
        names = {x["name"] for x in s["items"]}
        check("시리즈명 정리('멋진 만화')", "멋진 만화" in names)

        # 시리즈 상세 + 태그 확인
        comic_series = next(x for x in s["items"] if x["name"] == "멋진 만화")
        r = client.get(f"/api/series/{comic_series['id']}")
        sd = r.json()
        check("시리즈 상세 책 목록", len(sd["books"]) == 1)
        tags = set(sd["tags"])
        check("경로 태그 '판타지'", "판타지" in tags)
        check("경로 태그 '현대 판타지'", "현대 판타지" in tags)
        check("ComicInfo 태그 '액션'", "액션" in tags)
        check("완결 태그 자동추가", "완결" in tags)

        book = sd["books"][0]
        book_id = book["id"]
        check("책 제목 ComicInfo Title", book["title"] == "멋진 만화 1권")
        check("페이지수 3", book["page_count"] == 3)
        check("작가 파싱", book["author"] == "홍길동")

        print("== 만화 뷰어 ==")
        r = client.get(f"/api/books/{book_id}/pages/0")
        check("페이지0 이미지", r.status_code == 200 and r.headers["content-type"].startswith("image"))
        r = client.get(f"/api/books/{book_id}/pages/99")
        check("범위 밖 페이지 404", r.status_code == 404)
        r = client.get(f"/api/books/{book_id}/thumbnail")
        check("책 썸네일", r.status_code == 200)
        r = client.get(f"/api/series/{comic_series['id']}/thumbnail")
        check("시리즈 썸네일", r.status_code == 200)

        print("== 태그 편집 ==")
        r = client.post(f"/api/books/{book_id}/tags", json={"tag": "명작"})
        check("태그 추가", any(t["name"] == "명작" for t in r.json()["tags"]))
        r = client.delete(f"/api/books/{book_id}/tags/명작")
        check("태그 삭제", not any(t["name"] == "명작" for t in r.json()["tags"]))
        r = client.get("/api/tags")
        check("태그 목록 집계", any(t["name"] == "액션" for t in r.json()["tags"]))
        r = client.get("/api/series?tag=액션")
        check("태그로 시리즈 검색", r.json()["total"] == 1)

        print("== 평점 & 진행률 ==")
        r = client.put(f"/api/books/{book_id}/rating", json={"value": 5})
        check("평점 5 저장", r.json()["my_rating"] == 5)
        r = client.put(f"/api/books/{book_id}/progress", json={"page": 1})
        check("진행률 page=1", r.json()["progress"]["page"] == 1)
        r = client.get("/api/home")
        check("이어보기 등장", len(r.json()["continue_reading"]) == 1)
        # 완독 처리
        r = client.put(f"/api/books/{book_id}/progress", json={"page": 2})
        check("마지막 페이지 자동 완독", r.json()["progress"]["completed"] is True)
        r = client.get("/api/home")
        check("완독 후 이어보기 사라짐", len(r.json()["continue_reading"]) == 0)

        print("== EPUB / TXT ==")
        r = client.get("/api/books?fmt=epub")
        epub_book = r.json()["items"][0]
        check("EPUB 제목 메타", epub_book["title"] == "테스트 소설")
        r = client.get(f"/api/books/{epub_book['id']}/thumbnail")
        check("EPUB 느슨한 표지 인식", r.status_code == 200 and int(r.headers.get("content-length", 0)) > 0)
        r = client.get(f"/api/books/{epub_book['id']}/file")
        check("EPUB 원본 파일 서빙", r.status_code == 200)

        r = client.get("/api/books?fmt=txt")
        txt_book = r.json()["items"][0]
        r = client.get(f"/api/books/{txt_book['id']}/content")
        check("TXT 내용 디코딩", r.status_code == 200 and "첫 줄" in r.text)
        r = client.get(f"/api/books/{txt_book['id']}/thumbnail")
        check("TXT 플레이스홀더 썸네일", r.status_code == 200)

        print("== 사용자 권한 ==")
        r = client.post("/api/auth/users", json={"username": "reader", "password": "pass1234",
                                                 "role": "user", "library_ids": []})
        check("일반 사용자 생성", r.status_code == 200)

        # 라이브러리를 제한으로 변경 후 일반 사용자 접근 차단 확인
        client.patch(f"/api/libraries/{lib_id}", json={"restricted": True})
        c2 = TestClient(app)
        r = c2.post("/api/auth/login", json={"username": "reader", "password": "pass1234"})
        check("일반 사용자 로그인", r.status_code == 200)
        r = c2.get("/api/series")
        check("제한 라이브러리 접근 차단", r.json()["total"] == 0)

    print(f"\n결과: {ok} 통과 / {fail} 실패")
    # 정리
    import shutil
    shutil.rmtree(tmp, ignore_errors=True)
    sys.exit(1 if fail else 0)


if __name__ == "__main__":
    main()
