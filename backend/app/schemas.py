# -*- coding: utf-8 -*-
from typing import List, Optional
from pydantic import BaseModel, Field


from typing import Any


# ---- 요청 바디 ----
class SetupIn(BaseModel):
    username: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=4, max_length=200)
    remember: bool = True


class LoginIn(BaseModel):
    username: str
    password: str
    remember: bool = True  # 로그인 유지(자동 로그인)


class UserCreateIn(BaseModel):
    username: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=4, max_length=200)
    role: str = "user"  # admin | user
    library_ids: List[int] = []  # 접근 허용할 제한 라이브러리들


class UserUpdateIn(BaseModel):
    password: Optional[str] = Field(default=None, min_length=4, max_length=200)
    role: Optional[str] = None
    is_active: Optional[bool] = None
    library_ids: Optional[List[int]] = None


class LibraryCreateIn(BaseModel):
    name: str
    path: str
    restricted: bool = False
    private: Optional[bool] = None
    extra_paths: Optional[List[str]] = None
    settings: Optional[dict] = None


class LibraryUpdateIn(BaseModel):
    name: Optional[str] = None
    restricted: Optional[bool] = None
    private: Optional[bool] = None
    extra_paths: Optional[List[str]] = None
    settings: Optional[dict] = None


class TagsSetIn(BaseModel):
    tags: List[str]  # 수동 태그 전체를 이 목록으로 교체


class TagAddIn(BaseModel):
    tag: str


class RatingIn(BaseModel):
    value: int = Field(ge=0, le=5)  # 0 이면 평점 제거


class ProgressIn(BaseModel):
    page: Optional[int] = None
    position: Optional[str] = None
    completed: Optional[bool] = None


class ScheduleIn(BaseModel):
    quick_enabled: Optional[bool] = None
    quick_every_hours: Optional[int] = Field(default=None, ge=1, le=720)
    deep_enabled: Optional[bool] = None
    deep_every_days: Optional[int] = Field(default=None, ge=1, le=365)
    deep_at: Optional[str] = None  # "HH:MM"


class TagRulesIn(BaseModel):
    enabled: Optional[bool] = None
    bracket_tags: Optional[bool] = None
    keywords: Optional[List[dict]] = None  # [{"match":..,"tag":..}]
    regex: Optional[List[dict]] = None     # [{"pattern":..,"tag":..,"group":..}]
    author_marker: Optional[bool] = None
    chapter_range: Optional[bool] = None
    chapter_range_tag: Optional[bool] = None
    clean_title: Optional[bool] = None
    exclude_folders: Optional[List[str]] = None


class MetadataApplyIn(BaseModel):
    provider: str
    external_id: Any
    fields: List[str] = ["description", "author", "tags", "publisher", "language"]
    replace_cover: bool = False


class LibraryOrderIn(BaseModel):
    ids: List[int]


class ScanOptionsIn(BaseModel):
    thumbnails: Optional[bool] = None
    page_count: Optional[bool] = None
    metadata: Optional[bool] = None
    filename_tags: Optional[bool] = None
    epub_structure: Optional[bool] = None


class ThreadsIn(BaseModel):
    read_threads: Optional[int] = None
    scan_workers: Optional[int] = None


class IdsIn(BaseModel):
    ids: List[int]


class MemoryIn(BaseModel):
    cache_mb: Optional[int] = None
    mmap_mb: Optional[int] = None
    home_cache_sec: Optional[int] = None
