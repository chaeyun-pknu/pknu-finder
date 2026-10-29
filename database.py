"""
Supabase 접속 설정을 관리하는 모듈.
필수 설정(.streamlit/secrets.toml):
    SUPABASE_URL = "https://<project-ref>.supabase.co"
    SUPABASE_SERVICE_ROLE_KEY = "<server-secret-key>"
"""

import os
from typing import Any, Optional, Dict
import streamlit as st
from supabase import Client, create_client


class DatabaseConfigurationError(RuntimeError):
    """Supabase 접속 설정이 없거나 잘못된 경우 발생합니다."""


class DatabaseOperationError(RuntimeError):
    """Supabase 요청이 실패한 경우 발생합니다."""

# Supabase 클라이언트 생성 및 캐싱
@st.cache_resource
def get_supabase_client() -> Client:
    supabase_url = None
    supabase_key = None

    # st.secrets 설정값 확인 (SUPABASE_SERVICE_ROLE_KEY 또는 SUPABASE_KEY 지원)
    if "supabase" in st.secrets:
        supabase_url = st.secrets["supabase"].get("SUPABASE_URL")
        supabase_key = (
            st.secrets["supabase"].get("SUPABASE_SERVICE_ROLE_KEY")
            or st.secrets["supabase"].get("SUPABASE_KEY")
            or st.secrets["supabase"].get("SUPABASE_ANON_KEY")
        )

    # st.secrets에 없으면 환경 변수 확인
    if not supabase_url:
        supabase_url = os.getenv("SUPABASE_URL")
    if not supabase_key:
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")

    if not supabase_url or not supabase_key:
        raise DatabaseConfigurationError(
            "Supabase URL 또는 API Key가 설정되지 않았습니다. "
            ".streamlit/secrets.toml 파일을 확인해 주세요."
        )

    try:
        return create_client(supabase_url, supabase_key)
    except Exception as exc:
        raise DatabaseConfigurationError(f"Supabase 클라이언트 생성 실패: {exc}") from exc


# Supabase 연결 테스트 및 초기화
def init_db() -> None:
    client = get_supabase_client()
    try:
        # 간단한 핑/쿼리로 테이블 접근 가능 여부 테스트
        _ = client.table("users").select("id").limit(1).execute()
    except Exception as exc:
        raise DatabaseOperationError(f"데이터베이스 연결 검증 실패: {exc}") from exc


# userid 기반 username 조회
def get_username(user_id: Any) -> Optional[str]:
    if not user_id:
        return None

    client = get_supabase_client()
    try:
        response = (
            client.table("users")
            .select("username")
            .eq("id", user_id)
            .maybe_single()
            .execute()
        )
        if response and response.data:
            return response.data.get("username")
        return None
    except Exception as exc:
        # DB 조회 실패 시 None 반환 혹은 예외 기록
        st.caption(f"사용자 정보 조회 중 오류: {exc}")
        return None


# userid 기반 사용자 정보 조회
def get_user_by_id(user_id: Any) -> Optional[Dict[str, Any]]:
    if not user_id:
        return None

    client = get_supabase_client()
    try:
        response = (
            client.table("users")
            .select("*")
            .eq("id", user_id)
            .maybe_single()
            .execute()
        )
        if response and response.data:
            return response.data
        return None
    except Exception as exc:
        st.caption(f"사용자 상세 조회 중 오류: {exc}")
        return None


# Supabase 관리 클라이언트 생성 및 캐싱
@st.cache_resource
def get_supabase_admin_client() -> Client:
    if "supabase" in st.secrets:
        supabase_url = st.secrets["supabase"].get("SUPABASE_URL")
        service_role_key = st.secrets["supabase"].get(
            "SUPABASE_SERVICE_ROLE_KEY"
        )
    else:
        supabase_url = os.getenv("SUPABASE_URL")
        service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not supabase_url or not service_role_key:
        raise DatabaseConfigurationError(
            "Supabase URL 또는 SERVICE_ROLE_KEY가 설정되지 않았습니다."
        )

    try:
        return create_client(supabase_url, service_role_key)
    except Exception as exc:
        raise DatabaseConfigurationError(
            f"Supabase 관리 클라이언트 생성 실패: {exc}"
        ) from exc
