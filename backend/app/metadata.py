# -*- coding: utf-8 -*-
"""외부 메타데이터 공급자.

인터넷에서 줄거리/표지/태그/작가 등을 가져옵니다. (NAS 의 인터넷 연결 필요)
- google  : Google Books  (책/전자책)  키 불필요
- openlib : Open Library  (책)          키 불필요
- anilist : AniList        (만화/웹툰)   키 불필요

모든 네트워크 오류는 조용히 처리하여 빈 결과를 반환합니다.
표준 라이브러리(urllib)만 사용하므로 추가 의존성이 없습니다.
"""
import json
import re
import urllib.request
import urllib.parse
from typing import List, Dict, Optional

from . import config

_UA = "Librario/1.1 (+self-hosted)"
_TAG_RE = re.compile(r"<[^>]+>")


def _strip_html(s: Optional[str]) -> Optional[str]:
    if not s:
        return None
    s = _TAG_RE.sub("", s)
    s = (s.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
           .replace("&quot;", '"').replace("&#039;", "'").replace("<br>", "\n"))
    return s.strip() or None


def _get_json(url: str, headers: Optional[dict] = None) -> Optional[object]:
    req = urllib.request.Request(url, headers={"User-Agent": _UA, **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=config.METADATA_TIMEOUT) as r:
            return json.loads(r.read().decode("utf-8", "replace"))
    except Exception:
        return None


def _post_json(url: str, payload: dict) -> Optional[object]:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data,
        headers={"User-Agent": _UA, "Content-Type": "application/json",
                 "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=config.METADATA_TIMEOUT) as r:
            return json.loads(r.read().decode("utf-8", "replace"))
    except Exception:
        return None


def download_image(url: str, max_bytes: int = 8 * 1024 * 1024) -> Optional[bytes]:
    if not url or not url.lower().startswith(("http://", "https://")):
        return None
    req = urllib.request.Request(url, headers={"User-Agent": _UA})
    try:
        with urllib.request.urlopen(req, timeout=config.METADATA_TIMEOUT) as r:
            return r.read(max_bytes + 1)[:max_bytes]
    except Exception:
        return None


# ---------------------------------------------------------------------------
# 파서 (순수 함수 → 오프라인 테스트 가능)
# ---------------------------------------------------------------------------
def parse_google_item(item: dict) -> Dict:
    vi = item.get("volumeInfo", {}) or {}
    links = vi.get("imageLinks", {}) or {}
    cover = links.get("thumbnail") or links.get("smallThumbnail")
    if cover:
        cover = cover.replace("http://", "https://").replace("&edge=curl", "")
    year = None
    pub = vi.get("publishedDate") or ""
    m = re.match(r"(\d{4})", pub)
    if m:
        year = int(m.group(1))
    return {
        "provider": "google",
        "id": item.get("id"),
        "title": vi.get("title"),
        "authors": vi.get("authors", []) or [],
        "description": _strip_html(vi.get("description")),
        "cover_url": cover,
        "tags": vi.get("categories", []) or [],
        "publisher": vi.get("publisher"),
        "language": vi.get("language"),
        "year": year,
    }


def parse_openlib_doc(doc: dict) -> Dict:
    cover_id = doc.get("cover_i")
    cover = f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg" if cover_id else None
    langs = doc.get("language") or []
    return {
        "provider": "openlib",
        "id": doc.get("key"),
        "title": doc.get("title"),
        "authors": doc.get("author_name", []) or [],
        "description": None,  # search 결과엔 없음 → apply 시 상세 조회
        "cover_url": cover,
        "tags": (doc.get("subject") or [])[:15],
        "publisher": (doc.get("publisher") or [None])[0] if doc.get("publisher") else None,
        "language": langs[0] if langs else None,
        "year": doc.get("first_publish_year"),
    }


def parse_anilist_media(m: dict) -> Dict:
    t = m.get("title", {}) or {}
    title = t.get("english") or t.get("romaji") or t.get("native")
    tags = list(m.get("genres", []) or [])
    for tg in (m.get("tags", []) or []):
        if isinstance(tg, dict) and tg.get("name") and (tg.get("rank") or 0) >= 60:
            tags.append(tg["name"])
    cover = (m.get("coverImage", {}) or {}).get("large")
    sd = m.get("startDate", {}) or {}
    return {
        "provider": "anilist",
        "id": m.get("id"),
        "title": title,
        "authors": [],
        "description": _strip_html(m.get("description")),
        "cover_url": cover,
        "tags": tags[:20],
        "publisher": None,
        "language": None,
        "year": sd.get("year"),
    }


# ---------------------------------------------------------------------------
# 공급자별 검색/상세
# ---------------------------------------------------------------------------
def _google_search(q: str) -> List[Dict]:
    url = ("https://www.googleapis.com/books/v1/volumes?q="
           + urllib.parse.quote(q) + "&maxResults=8")
    data = _get_json(url)
    if not isinstance(data, dict):
        return []
    return [parse_google_item(it) for it in data.get("items", []) if it.get("id")]


def _google_fetch(book_id: str) -> Optional[Dict]:
    data = _get_json("https://www.googleapis.com/books/v1/volumes/"
                     + urllib.parse.quote(book_id))
    if not isinstance(data, dict):
        return None
    return parse_google_item(data)


def _openlib_search(q: str) -> List[Dict]:
    url = ("https://openlibrary.org/search.json?limit=8&fields="
           "key,title,author_name,first_publish_year,cover_i,subject,language,publisher&q="
           + urllib.parse.quote(q))
    data = _get_json(url)
    if not isinstance(data, dict):
        return []
    return [parse_openlib_doc(d) for d in data.get("docs", []) if d.get("key")]


def _openlib_fetch(work_key: str) -> Optional[Dict]:
    key = work_key if work_key.startswith("/") else "/" + work_key
    data = _get_json("https://openlibrary.org" + key + ".json")
    if not isinstance(data, dict):
        return {"provider": "openlib", "id": work_key}
    desc = data.get("description")
    if isinstance(desc, dict):
        desc = desc.get("value")
    subjects = data.get("subjects") or []
    return {
        "provider": "openlib",
        "id": work_key,
        "title": data.get("title"),
        "authors": [],
        "description": _strip_html(desc) if isinstance(desc, str) else None,
        "cover_url": (f"https://covers.openlibrary.org/b/id/{data['covers'][0]}-L.jpg"
                      if data.get("covers") else None),
        "tags": subjects[:15],
        "publisher": None,
        "language": None,
        "year": None,
    }


_ANILIST_Q = """
query ($search: String, $id: Int) {
  Media(search: $search, id: $id, type: MANGA) {
    id
    title { romaji english native }
    description(asHtml: false)
    genres
    tags { name rank }
    coverImage { large }
    startDate { year }
  }
}
"""


def _anilist_search(q: str) -> List[Dict]:
    # AniList 은 페이지 검색과 단건 Media 를 함께 제공. 여기선 Page 로 목록화.
    page_q = """
    query ($search: String) {
      Page(perPage: 8) {
        media(search: $search, type: MANGA) {
          id title { romaji english native }
          description(asHtml: false) genres tags { name rank }
          coverImage { large } startDate { year }
        }
      }
    }"""
    data = _post_json("https://graphql.anilist.co",
                      {"query": page_q, "variables": {"search": q}})
    try:
        media = data["data"]["Page"]["media"]  # type: ignore
    except (TypeError, KeyError):
        return []
    return [parse_anilist_media(m) for m in media if m.get("id")]


def _anilist_fetch(media_id) -> Optional[Dict]:
    data = _post_json("https://graphql.anilist.co",
                      {"query": _ANILIST_Q, "variables": {"id": int(media_id)}})
    try:
        m = data["data"]["Media"]  # type: ignore
    except (TypeError, KeyError, ValueError):
        return None
    return parse_anilist_media(m)


PROVIDERS = {
    "google":  {"label": "Google Books", "kind": "book",
                "search": _google_search, "fetch": _google_fetch},
    "openlib": {"label": "Open Library", "kind": "book",
                "search": _openlib_search, "fetch": _openlib_fetch},
    "anilist": {"label": "AniList (만화)", "kind": "comic",
                "search": _anilist_search, "fetch": _anilist_fetch},
}


def list_providers() -> List[Dict]:
    return [{"id": pid, "label": p["label"], "kind": p["kind"]}
            for pid, p in PROVIDERS.items()]


def search(provider: str, query: str) -> List[Dict]:
    p = PROVIDERS.get(provider)
    if not p or not query.strip():
        return []
    try:
        return p["search"](query.strip()) or []
    except Exception:
        return []


def fetch(provider: str, external_id) -> Optional[Dict]:
    p = PROVIDERS.get(provider)
    if not p:
        return None
    try:
        return p["fetch"](external_id)
    except Exception:
        return None
