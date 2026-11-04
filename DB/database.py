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

#===================================
#Supabase 클라이언트 생성 및 초기화
#==================================

# Supabase URL 및 키를 환경변수 또는 secrets.toml에서 가져오는 헬퍼 함수
def _get_secret(name: str) -> Optional[str]:
    """st.secrets[supabase] 섹션 -> st.secrets 최상위 -> 환경변수 순서로 조회."""
    try:
        section = st.secrets.get("supabase")
        if section and section.get(name):
            return section.get(name)
        if st.secrets.get(name):
            return st.secrets.get(name)
    except Exception:
        pass
    return os.getenv(name)


def get_supabase_url() -> str:
    url = _get_secret("SUPABASE_URL")
    if not url:
        raise DatabaseConfigurationError("SUPABASE_URL이 설정되지 않았습니다.")
    return url.rstrip("/")


# 일반 Supabase 클라이언트 생성
def get_supabase_client() -> Client:
    try:
        client = create_client(get_supabase_url(), _get_secret("SUPABASE_ANON_KEY"),)

        access_token = st.session_state.get("supabase_access_token")
        refresh_token = st.session_state.get("supabase_refresh_token")

        if not access_token or not refresh_token:
            raise DatabaseOperationError(
                "로그인 세션이 없습니다. 다시 로그인해 주세요."
            )

        # 사용자 인증 세션 적용
        session_response = client.auth.set_session(access_token, refresh_token)

        # 갱신된 토큰 저장
        if session_response and session_response.session:
            st.session_state["supabase_access_token"] = (
                session_response.session.access_token
            )
            st.session_state["supabase_refresh_token"] = (
                session_response.session.refresh_token
            )

        # 실제 인증 사용자 확인
        auth_response = client.auth.get_user()

        if not auth_response.user:
            raise DatabaseOperationError(
                "사용자 인증 정보를 확인할 수 없습니다."
            )

        # 현재 로그인 사용자 ID와 인증 사용자 ID 비교
        session_user_id = st.session_state.get("user_id")

        if str(auth_response.user.id) != str(session_user_id):
            raise DatabaseOperationError(
                "로그인 사용자 정보가 일치하지 않습니다."
            )

        return client

    except DatabaseOperationError:
        raise

    except Exception as exc:
        raise DatabaseOperationError(
            f"Supabase 클라이언트 생성 또는 인증 실패: {exc}"
        ) from exc

# 관리자용 Supabase 클라이언트 생성 및 캐싱
@st.cache_resource
def get_supabase_admin_client() -> Client:
    supabase_url = _get_secret("SUPABASE_URL")
    service_key = _get_secret("SUPABASE_SERVICE_ROLE_KEY")

    if not supabase_url or not service_key:
        raise DatabaseConfigurationError("Supabase URL 또는 SERVICE ROLE KEY가 설정되지 않았습니다.")
    try:
        return create_client(supabase_url, service_key)
    except Exception as exc:
        raise DatabaseConfigurationError(f"Supabase 관리자 클라이언트 생성 실패: {exc}") from exc

# 로그인/회원가입 클라이언트 생성
def create_auth_client() -> Client:
    key = _get_secret("SUPABASE_ANON_KEY")
    if not key:
        raise DatabaseConfigurationError(
            "SUPABASE_ANON_KEY가 설정되지 않았습니다. .streamlit/secrets.toml을 확인해 주세요."
        )
    try:
        return create_client(get_supabase_url(), key)
    except Exception as exc:
        raise DatabaseConfigurationError(f"Supabase 인증 클라이언트 생성 실패: {exc}") from exc

#===========================
# Supabase 연결 테스트 및 초기화
#===========================
def init_db() -> None:
    try:
        # 로그인 전에도 Supabase 설정을 확인할 수 있도록
        # 사용자 인증 세션이 필요 없는 클라이언트 생성
        create_auth_client()

    except Exception as exc:
        raise DatabaseOperationError(
            f"Supabase 초기화 실패: {exc}"
        ) from exc

#=========================
# 사용자 정보 조회
#========================

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
