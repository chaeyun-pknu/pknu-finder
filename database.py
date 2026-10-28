"""
Supabase 접속 설정을 관리하는 모듈.
필수 설정(.streamlit/secrets.toml):
    SUPABASE_URL = "https://<project-ref>.supabase.co"
    SUPABASE_SERVICE_ROLE_KEY = "<server-secret-key>"
"""

from __future__ import annotations
import hashlib
import os
from functools import lru_cache
from typing import Any

import streamlit as st
from supabase import Client, create_client


class DatabaseConfigurationError(RuntimeError):
    """Supabase 접속 설정이 없거나 잘못된 경우 발생합니다."""


class DatabaseOperationError(RuntimeError):
    """Supabase 요청이 실패한 경우 발생합니다."""


# 환경 변수 또는 Streamlit secrets에서 설정 값을 가져오는 함수
def _get_setting(name: str) -> str | None:
    try:
        value = st.secrets.get(name)
        if value:
            return str(value).strip()
    except (FileNotFoundError, RuntimeError, AttributeError):
        pass

    value = os.getenv(name)
    return value.strip() if value else None


# Supabase 클라이언트 생성 및 캐싱
@lru_cache(maxsize=1)
def get_supabase_client() -> Client:
    url = _get_setting("SUPABASE_URL")
    key = _get_setting("SUPABASE_SERVICE_ROLE_KEY")

    if not url:
        raise DatabaseConfigurationError(
            "SUPABASE_URL이 설정되지 않았습니다. "
            ".streamlit/secrets.toml을 확인해주세요."
        )

    if not key:
        raise DatabaseConfigurationError(
            "SUPABASE_SERVICE_ROLE_KEY가 설정되지 않았습니다. "
            ".streamlit/secrets.toml을 확인해주세요."
        )

    try:
        return create_client(url, key)
    except Exception as exc:
        raise DatabaseConfigurationError(
            "Supabase 클라이언트를 생성하지 못했습니다. "
            "프로젝트 URL과 서버용 키를 확인해주세요."
        ) from exc

# Supabase 클라이언트 반환 함수
def get_connection() -> Client:
    return get_supabase_client()


# 테이블 접근 확인 함수
def init_db() -> None:
    client = get_supabase_client()
    required_tables = ("users", "lost_items", "lost_item_images", "chats", "bookmarks")
    missing_tables: list[str] = []

    for table_name in required_tables:
        try:
            client.table(table_name).select("*").limit(1).execute()
        except Exception:
            missing_tables.append(table_name)

    if missing_tables:
        missing = ", ".join(missing_tables)
        raise DatabaseOperationError(
            f"Supabase 테이블을 조회할 수 없습니다: {missing}. "
            "테이블 존재 여부, RLS 정책, API 권한을 확인해주세요."
        )


# 비밀번호 해싱
def hash_password(password: str) -> str:
    if not isinstance(password, str):
        raise TypeError("password는 문자열이어야 합니다.")

    return hashlib.sha256(password.encode("utf-8")).hexdigest()


# 사용자 이름 조회
def get_username(user_id: int | str | None) -> str | None:
    if user_id is None:
        return None

    try:
        response: Any = (
            get_supabase_client()
            .table("users")
            .select("username")
            .eq("id", user_id)
            .limit(1)
            .execute()
        )
    except Exception as exc:
        raise DatabaseOperationError(
            f"사용자 이름 조회 실패: {exc}"
        ) from exc

    rows = response.data or []
    return rows[0].get("username") if rows else None
