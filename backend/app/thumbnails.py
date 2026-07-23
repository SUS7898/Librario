# -*- coding: utf-8 -*-
import io
import os
from pathlib import Path
from typing import Optional

from . import config, formats

try:
    from PIL import Image
    _HAS_PIL = True
except Exception:
    _HAS_PIL = False


def book_thumb_path(book_id: int) -> Path:
    return config.THUMB_DIR / f"book_{book_id}.jpg"


def series_thumb_path(series_id: int) -> Path:
    return config.THUMB_DIR / f"series_{series_id}.jpg"


def _resize_to_jpeg(raw: bytes) -> Optional[bytes]:
    if not _HAS_PIL:
        return None
    try:
        im = Image.open(io.BytesIO(raw))
        im.load()
    except Exception:
        return None
    try:
        if im.mode not in ("RGB", "L"):
            im = im.convert("RGB")
        w, h = im.size
        if w > config.THUMB_WIDTH:
            ratio = config.THUMB_WIDTH / float(w)
            im = im.resize((config.THUMB_WIDTH, max(1, int(h * ratio))), Image.LANCZOS)
        out = io.BytesIO()
        im.save(out, format="JPEG", quality=config.THUMB_QUALITY, optimize=True)
        return out.getvalue()
    except Exception:
        return None


def _placeholder_jpeg(title: str) -> Optional[bytes]:
    """표지를 못 만든 경우(주로 TXT) 제목을 그려 넣은 커버 생성."""
    if not _HAS_PIL:
        return None
    try:
        from PIL import ImageDraw, ImageFont
        W, H = config.THUMB_WIDTH, int(config.THUMB_WIDTH * 1.4)
        # 제목 해시로 배경색 결정
        hue = sum(ord(c) for c in (title or "?")) % 360
        r, g, b = _hsv_to_rgb(hue / 360.0, 0.35, 0.55)
        im = Image.new("RGB", (W, H), (r, g, b))
        d = ImageDraw.Draw(im)
        try:
            font = ImageFont.load_default()
        except Exception:
            font = None
        text = (title or "TXT")[:40]
        # 단순 줄바꿈
        lines, cur = [], ""
        for ch in text:
            cur += ch
            if len(cur) >= 12:
                lines.append(cur)
                cur = ""
        if cur:
            lines.append(cur)
        y = H // 2 - (len(lines) * 14) // 2
        for ln in lines[:6]:
            d.text((14, y), ln, fill=(255, 255, 255), font=font)
            y += 16
        out = io.BytesIO()
        im.save(out, format="JPEG", quality=config.THUMB_QUALITY)
        return out.getvalue()
    except Exception:
        return None


def _hsv_to_rgb(h, s, v):
    import colorsys
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return int(r * 255), int(g * 255), int(b * 255)


def raw_cover_for_book(path: str, fmt: str) -> Optional[bytes]:
    fmt = fmt.lower()
    if fmt in ("cbz", "zip"):
        return formats.comic_cover_bytes(path)
    if fmt == "epub":
        info = formats.epub_info(path)
        return info.get("cover_bytes")  # type: ignore
    if fmt == "pdf":
        return formats.pdf_cover_bytes(path)
    return None


def render_thumb_jpeg(path: str, fmt: str, title: str = "") -> Optional[bytes]:
    """표지를 추출·리사이즈해 JPEG 바이트를 만든다 (무거운 작업, 병렬 처리 가능).
    book_id 가 필요 없으므로 워커 스레드에서 미리 실행할 수 있다."""
    raw = raw_cover_for_book(path, fmt)
    jpeg = _resize_to_jpeg(raw) if raw else None
    if jpeg is None:
        jpeg = _placeholder_jpeg(title)
    return jpeg


def write_thumb_jpeg(book_id: int, jpeg: Optional[bytes]) -> bool:
    """미리 만들어 둔 JPEG 를 book_id 경로에 기록 (가벼운 작업)."""
    if not jpeg:
        return False
    try:
        dst = book_thumb_path(book_id)
        dst.parent.mkdir(parents=True, exist_ok=True)
        with open(dst, "wb") as f:
            f.write(jpeg)
        return True
    except OSError:
        return False


def generate_book_thumbnail(book_id: int, path: str, fmt: str, title: str = "") -> bool:
    """성공 시 True. 표지를 못 얻으면 TXT 등은 플레이스홀더 생성."""
    raw = raw_cover_for_book(path, fmt)
    jpeg = _resize_to_jpeg(raw) if raw else None
    if jpeg is None:
        jpeg = _placeholder_jpeg(title)
    if jpeg is None:
        return False
    try:
        dst = book_thumb_path(book_id)
        dst.parent.mkdir(parents=True, exist_ok=True)
        with open(dst, "wb") as f:
            f.write(jpeg)
        return True
    except OSError:
        return False


def save_cover_from_bytes(book_id: int, raw: bytes) -> bool:
    """외부에서 내려받은 표지 이미지를 리사이즈해서 저장 (메타데이터 표지 교체용)."""
    jpeg = _resize_to_jpeg(raw) if raw else None
    if jpeg is None:
        return False
    try:
        dst = book_thumb_path(book_id)
        dst.parent.mkdir(parents=True, exist_ok=True)
        with open(dst, "wb") as f:
            f.write(jpeg)
        return True
    except OSError:
        return False


def link_series_thumbnail(series_id: int, book_id: int) -> bool:
    src = book_thumb_path(book_id)
    if not src.exists():
        return False
    try:
        dst = series_thumb_path(series_id)
        with open(src, "rb") as fi, open(dst, "wb") as fo:
            fo.write(fi.read())
        return True
    except OSError:
        return False


def delete_book_thumbnail(book_id: int):
    for p in (book_thumb_path(book_id),):
        try:
            if p.exists():
                os.remove(p)
        except OSError:
            pass


# ---------------------------------------------------------------------------
# EPUB 삽화 썸네일 — 스캔 때 미리 만들어 두면 삽화 목록이 즉시 뜬다.
# 원본(수 MB)을 그대로 내려받지 않아 모바일에서 특히 유리하다.
# ---------------------------------------------------------------------------
import hashlib


def epub_img_thumb_path(book_id: int, href: str) -> Path:
    key = hashlib.sha1(href.encode("utf-8", "replace")).hexdigest()[:16]
    return config.THUMB_DIR / "epub" / str(book_id) / f"{key}.jpg"


def _resize_small(raw: bytes, box=(220, 300)) -> Optional[bytes]:
    try:
        from PIL import Image
        im = Image.open(io.BytesIO(raw))
        im.load()
        if im.mode not in ("RGB", "L"):
            im = im.convert("RGB")
        im.thumbnail(box, Image.LANCZOS)
        out = io.BytesIO()
        im.save(out, "JPEG", quality=78, optimize=True)
        return out.getvalue()
    except Exception:
        return None


def build_epub_image_thumbs(book_id: int, path: str, images, limit: int = 400) -> int:
    """삽화 썸네일을 미리 생성. 이미 있으면 건너뛴다. 생성 개수를 반환."""
    from . import formats
    made = 0
    for it in (images or [])[:limit]:
        href = it.get("href") if isinstance(it, dict) else None
        if not href:
            continue
        dst = epub_img_thumb_path(book_id, href)
        if dst.exists():
            continue
        got = formats.epub_asset_bytes(path, href)
        if not got:
            continue
        small = _resize_small(got[0])
        if not small:
            continue
        try:
            dst.parent.mkdir(parents=True, exist_ok=True)
            with open(dst, "wb") as f:
                f.write(small)
            made += 1
        except OSError:
            continue
    return made


def delete_epub_image_thumbs(book_id: int):
    import shutil as _sh
    d = config.THUMB_DIR / "epub" / str(book_id)
    if d.exists():
        try:
            _sh.rmtree(d)
        except OSError:
            pass
