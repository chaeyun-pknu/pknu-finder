"""
Supabase 접속 설정을 관리하는 모듈.
필수 설정(.streamlit/secrets.toml):
    SUPABASE_URL = "https://<project-ref>.supabase.co"
    SUPABASE_SERVICE_ROLE_KEY = "<server-secret-key>"
    SUPABASE_ANON_KEY = "<anon-public-key>"
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


# 사용자별 클라이언트는 st.cache_resource > Streamlit 세션에 저장으로 변경.
_CLIENT_KEY = "_supabase_user_client"
_CLIENT_USER_KEY = "_supabase_client_user_id"
_CLIENT_TOKEN_KEY = "_supabase_client_refresh_token"


def clear_supabase_client() -> None:
    """로그아웃/탈퇴/사용자 변경 시 인증 클라이언트 캐시를 비움."""
    st.session_state.pop(_CLIENT_KEY, None)
    st.session_state.pop(_CLIENT_USER_KEY, None)
    st.session_state.pop(_CLIENT_TOKEN_KEY, None)


def _store_auth_session(session: Any) -> None:
    """Supabase가 갱신한 access/refresh token을 Streamlit 세션과 동기화함."""
    if session is None:
        raise DatabaseOperationError("인증 세션을 확인할 수 없습니다. 다시 로그인해 주세요.")
    st.session_state["supabase_access_token"] = session.access_token
    st.session_state["supabase_refresh_token"] = session.refresh_token


def _authenticate_client(client: Client, access_token: str, refresh_token: str, expected_user_id: str) -> None:
    """새 클라이언트의 인증 세션을 복원하고 사용자를 1회 검증합니다."""
    result = client.auth.set_session(access_token, refresh_token)
    session = getattr(result, "session", None)

    if session is None:
        raise DatabaseOperationError("인증 세션을 확인할 수 없습니다. 다시 로그인해 주세요.")


    # 사용자 식별은 인증 서버의 get_user() 응답으로 확인.
    auth_response = client.auth.get_user()
    user = getattr(auth_response, "user", None)
    if user is None or str(user.id) != expected_user_id:
        raise DatabaseOperationError("로그인 사용자 정보가 일치하지 않습니다.")
    _store_auth_session(session)


def get_supabase_client() -> Client:
    """
    인증 확인은 클라이언트 최초 생성 시 수행하고, 이후 호출에는 재사용합니다.
    get_session()은 로컬 세션을 읽고 토큰 만료 시 필요에 따라 갱신합니다.
    """
    access_token = st.session_state.get("supabase_access_token")
    refresh_token = st.session_state.get("supabase_refresh_token")
    user_id = st.session_state.get("user_id")

    if not access_token or not refresh_token or not user_id:
        clear_supabase_client()
        raise DatabaseOperationError("로그인 세션이 없습니다. 다시 로그인해 주세요.")

    try:
        client = st.session_state.get(_CLIENT_KEY)
        cached_user_id = st.session_state.get(_CLIENT_USER_KEY)

        # 사용자 교체 또는 Streamlit 세션 복원 시 인증 클라이언트를 새로 구성합니다.
        if (client is None or cached_user_id != str(user_id) or
                st.session_state.get(_CLIENT_TOKEN_KEY) != refresh_token):
            clear_supabase_client()
            key = _get_secret("SUPABASE_ANON_KEY")
            if not key:
                raise DatabaseConfigurationError("SUPABASE_ANON_KEY가 설정되지 않았습니다.")
            client = create_client(get_supabase_url(), key)
            _authenticate_client(client, access_token, refresh_token, str(user_id))
            st.session_state[_CLIENT_KEY] = client
            st.session_state[_CLIENT_USER_KEY] = str(user_id)
            st.session_state[_CLIENT_TOKEN_KEY] = st.session_state["supabase_refresh_token"]
            return client

        # 인증 클라이언트 내부의 세션이 만료되면 SDK가 필요할 때 토큰을 갱신합니다.
        # 재호출마다 set_session()/get_user()를 실행하지 않습니다.
        session = client.auth.get_session()
        if session is None:
            clear_supabase_client()
            raise DatabaseOperationError("인증 세션이 만료되었습니다. 다시 로그인해 주세요.")

        # 외부에서 토큰이 변경된 경우 이전 인증 상태를 재사용하지 않습니다.
        if (session.access_token != access_token or
                session.refresh_token != refresh_token):
            # SDK의 자동 갱신인 경우 최신 토큰을 저장합니다. 세션 user가 현재 사용자와
            # 다르거나 유효하지 않다면 재인증하도록 클라이언트를 폐기합니다.
            session_user = getattr(session, "user", None)
            if session_user is None or str(session_user.id) != str(user_id):
                clear_supabase_client()
                raise DatabaseOperationError("로그인 사용자 정보가 일치하지 않습니다.")
            _store_auth_session(session)
            st.session_state[_CLIENT_TOKEN_KEY] = session.refresh_token
        return client

    except (DatabaseOperationError, DatabaseConfigurationError):
        raise
    except Exception as exc:
        clear_supabase_client()
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
    """Supabase DB 연결 상태를 확인합니다."""
    client = create_auth_client()

    try:
        (
            client.table("lost_items")
            .select("id")
            .limit(0)
            .execute()
        )

    except Exception as exc:
        raise DatabaseOperationError(
            "Supabase 연결 확인 실패: "
            "lost_items 테이블의 접근 권한, "
            "테이블 이름 또는 네트워크 연결을 "
            "확인해 주세요."
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
