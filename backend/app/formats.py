# -*- coding: utf-8 -*-
"""
파일 형식별 처리:
 - 만화(cbz/zip): 페이지 목록/추출/표지
 - EPUB: 메타데이터 + '느슨한' 표지 추출 (Komga가 못 잡는 것도 최대한 인식)
 - PDF: 페이지수 + 표지 (PyMuPDF)
 - TXT: 인코딩 자동감지 디코딩
 - ComicInfo.xml 파싱
"""
import os
import re
import posixpath
import xml.etree.ElementTree as ET
from zipfile import ZipFile, BadZipFile
from typing import List, Optional, Tuple, Dict

IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".jfif", ".avif")
MIME_BY_EXT = {
    ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".jfif": "image/jpeg",
    ".png": "image/png", ".gif": "image/gif", ".webp": "image/webp",
    ".bmp": "image/bmp", ".avif": "image/avif",
}


def natural_key(s: str):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", s)]


def ext_of(name: str) -> str:
    return os.path.splitext(name)[1].lower()


def fmt_of(path: str) -> str:
    e = ext_of(path)
    return e[1:] if e else ""


# ---------------------------------------------------------------------------
# 만화 (cbz / zip)
# ---------------------------------------------------------------------------
def _is_page_entry(name: str) -> bool:
    if name.endswith("/"):
        return False
    low = name.lower()
    if "__macosx" in low or low.endswith("comicinfo.xml"):
        return False
    if os.path.basename(low).startswith("."):
        return False
    return ext_of(name) in IMAGE_EXTS


def list_comic_pages(path: str) -> List[str]:
    try:
        with ZipFile(path, "r") as z:
            names = [n for n in z.namelist() if _is_page_entry(n)]
    except (BadZipFile, OSError):
        return []
    names.sort(key=natural_key)
    return names


def read_comic_page(path: str, index: int) -> Optional[Tuple[bytes, str]]:
    pages = list_comic_pages(path)
    if index < 0 or index >= len(pages):
        return None
    name = pages[index]
    try:
        with ZipFile(path, "r") as z:
            data = z.read(name)
    except (BadZipFile, OSError, KeyError):
        return None
    return data, MIME_BY_EXT.get(ext_of(name), "application/octet-stream")


def comic_cover_bytes(path: str) -> Optional[bytes]:
    res = read_comic_page(path, 0)
    return res[0] if res else None


def read_comicinfo(path: str) -> Dict[str, str]:
    """cbz/zip 내부 ComicInfo.xml 을 파싱하여 dict 반환 (없으면 빈 dict)."""
    try:
        with ZipFile(path, "r") as z:
            target = None
            for n in z.namelist():
                if n.lower().endswith("comicinfo.xml"):
                    target = n
                    break
            if not target:
                return {}
            raw = z.read(target)
    except (BadZipFile, OSError, KeyError):
        return {}
    try:
        root = ET.fromstring(raw)
    except ET.ParseError:
        return {}
    out = {}
    for child in root:
        tag = child.tag.split("}", 1)[-1]
        if child.text and child.text.strip():
            out[tag] = child.text.strip()
    return out


# ---------------------------------------------------------------------------
# EPUB (느슨한 표지/메타 추출)
# ---------------------------------------------------------------------------
def _local(tag: str) -> str:
    return tag.split("}", 1)[-1].lower()


def _epub_opf_path(z: ZipFile) -> Optional[str]:
    try:
        root = ET.fromstring(z.read("META-INF/container.xml"))
        for el in root.iter():
            if _local(el.tag) == "rootfile":
                fp = el.get("full-path")
                if fp:
                    return fp
    except (KeyError, ET.ParseError, OSError):
        pass
    for n in z.namelist():  # 폴백: 아무 opf
        if n.lower().endswith(".opf"):
            return n
    return None


def _first_image_in_zip(z: ZipFile) -> Optional[str]:
    imgs = [n for n in z.namelist() if ext_of(n) in IMAGE_EXTS and "__macosx" not in n.lower()]
    imgs.sort(key=natural_key)
    return imgs[0] if imgs else None


def epub_info(path: str) -> Dict[str, Optional[object]]:
    """
    return: {"title": str|None, "author": str|None, "cover_bytes": bytes|None}
    표지 인식은 여러 단계 폴백으로 최대한 관대하게 시도한다.
    """
    result = {"title": None, "author": None, "cover_bytes": None,
              "language": None, "publisher": None, "description": None}
    try:
        with ZipFile(path, "r") as z:
            opf = _epub_opf_path(z)
            base = posixpath.dirname(opf) if opf else ""
            manifest = {}   # id -> {href, media, props}
            href_by_props = {}
            cover_meta_id = None
            title = None
            author = None
            language = None
            publisher = None
            description = None

            if opf:
                try:
                    root = ET.fromstring(z.read(opf))
                except (ET.ParseError, KeyError, OSError):
                    root = None
                if root is not None:
                    for el in root.iter():
                        ln = _local(el.tag)
                        if ln == "title" and title is None and el.text:
                            title = el.text.strip()
                        elif ln == "creator" and author is None and el.text:
                            author = el.text.strip()
                        elif ln == "language" and language is None and el.text:
                            language = el.text.strip()
                        elif ln == "publisher" and publisher is None and el.text:
                            publisher = el.text.strip()
                        elif ln == "description" and description is None and el.text:
                            description = el.text.strip()
                        elif ln == "meta":
                            # <meta name="cover" content="cover-id"/>
                            if (el.get("name") or "").lower() == "cover":
                                cover_meta_id = el.get("content")
                        elif ln == "item":
                            iid = el.get("id") or ""
                            href = el.get("href") or ""
                            media = (el.get("media-type") or "").lower()
                            props = (el.get("properties") or "").lower()
                            manifest[iid] = {"href": href, "media": media, "props": props}
                            if "cover-image" in props:
                                href_by_props = {"href": href}

            def _resolve(href: str) -> Optional[bytes]:
                if not href:
                    return None
                cand = posixpath.normpath(posixpath.join(base, href)) if base else href
                for name in (cand, href, cand.lstrip("/")):
                    try:
                        return z.read(name)
                    except (KeyError, OSError):
                        continue
                # 대소문자/경로 흔들림 대비 basename 매칭
                bn = posixpath.basename(href).lower()
                for n in z.namelist():
                    if posixpath.basename(n).lower() == bn:
                        try:
                            return z.read(n)
                        except (KeyError, OSError):
                            pass
                return None

            cover = None
            # 1) properties=cover-image
            if href_by_props.get("href"):
                cover = _resolve(href_by_props["href"])
            # 2) <meta name=cover content=id>
            if cover is None and cover_meta_id and cover_meta_id in manifest:
                cover = _resolve(manifest[cover_meta_id]["href"])
            # 3) id/href 에 'cover' 포함 + 이미지
            if cover is None:
                for it in manifest.values():
                    if it["media"].startswith("image") and "cover" in (it["href"].lower()):
                        cover = _resolve(it["href"])
                        if cover:
                            break
            if cover is None:
                for iid, it in manifest.items():
                    if it["media"].startswith("image") and "cover" in iid.lower():
                        cover = _resolve(it["href"])
                        if cover:
                            break
            # 4) manifest 상의 첫 이미지
            if cover is None:
                for it in manifest.values():
                    if it["media"].startswith("image"):
                        cover = _resolve(it["href"])
                        if cover:
                            break
            # 5) 최후: zip 내부 아무 이미지
            if cover is None:
                fn = _first_image_in_zip(z)
                if fn:
                    try:
                        cover = z.read(fn)
                    except (KeyError, OSError):
                        cover = None

            result["title"] = title
            result["author"] = author
            result["cover_bytes"] = cover
            result["language"] = language
            result["publisher"] = publisher
            result["description"] = description
    except (BadZipFile, OSError):
        pass
    return result


# ---------------------------------------------------------------------------
# PDF (PyMuPDF - 없으면 조용히 건너뜀)
# ---------------------------------------------------------------------------
def _load_fitz():
    try:
        import fitz  # PyMuPDF
        return fitz
    except Exception:
        try:
            import pymupdf as fitz  # noqa
            return fitz
        except Exception:
            return None


def pdf_page_count(path: str) -> Optional[int]:
    fitz = _load_fitz()
    if fitz is None:
        return None
    try:
        with fitz.open(path) as doc:
            return doc.page_count
    except Exception:
        return None


def pdf_cover_bytes(path: str, zoom: float = 1.4) -> Optional[bytes]:
    fitz = _load_fitz()
    if fitz is None:
        return None
    try:
        with fitz.open(path) as doc:
            if doc.page_count == 0:
                return None
            page = doc.load_page(0)
            pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
            return pix.tobytes("png")
    except Exception:
        return None


# ---------------------------------------------------------------------------
# TXT (인코딩 자동감지)
# ---------------------------------------------------------------------------
_TXT_ENCODINGS = ("utf-8-sig", "utf-8", "cp949", "euc-kr", "utf-16", "latin-1")


def read_text_file(path: str, limit_bytes: Optional[int] = None) -> str:
    try:
        with open(path, "rb") as f:
            raw = f.read() if limit_bytes is None else f.read(limit_bytes)
    except OSError:
        return ""
    for enc in _TXT_ENCODINGS:
        try:
            return raw.decode(enc)
        except (UnicodeDecodeError, LookupError):
            continue
    return raw.decode("utf-8", errors="replace")
