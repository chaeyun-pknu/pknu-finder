import secrets
import time

import streamlit as st

from database import create_auth_client, get_supabase_admin_client


# OAuth 인증 후 리다이렉트 주소 설정
def _get_redirect_url() -> str:
    default_url = "http://localhost:8501"
    try:
        if "supabase" in st.secrets:
            return st.secrets["supabase"].get("SUPABASE_REDIRECT_URL", default_url)
        return st.secrets.get("SUPABASE_REDIRECT_URL", default_url)
    except Exception:
        return default_url


_FLOW_TTL_SEC = 60 * 60
@st.cache_resource
def _flow_store() -> dict:
    """flow_key -> (client, login_url, 생성 시각). 서버 프로세스 메모리에 보관."""
    return {}


def _prune_flows(store: dict) -> None:
    now = time.time()
    for key, (_, _, created) in list(store.items()):
        if now - created > _FLOW_TTL_SEC:
            store.pop(key, None)


def _build_redirect_url(flow_key: str) -> str:
    base = _get_redirect_url()
    sep = "&" if "?" in base else "?"
    return f"{base}{sep}flow={flow_key}"


# OAuth 제공자 로그인 URL 설정
def get_oauth_login_url(provider: str) -> str | None:
    try:
        store = _flow_store()
        flows = st.session_state.get("oauth_flows") or {}

        # 같은 세션의 rerun에서는 기존 링크를 재사용
        entry = store.get(flows.get(provider))
        if entry and time.time() - entry[2] < _FLOW_TTL_SEC:
            return entry[1]

        _prune_flows(store)
        flow_key = secrets.token_urlsafe(16)
        client = create_auth_client()
        res = client.auth.sign_in_with_oauth(
            {
                "provider": provider,
                "options": {"redirect_to": _build_redirect_url(flow_key)},
            }
        )
        store[flow_key] = (client, res.url, time.time())
        flows[provider] = flow_key
        st.session_state["oauth_flows"] = flows
        return res.url
    except Exception as e:
        st.error(f"{provider} 로그인 URL 생성 중 오류 발생: {e}")
        return None


def handle_oauth_callback() -> None:
    if st.session_state.get("user") is not None:
        return

    params = st.query_params
    code = params.get("code")
    flow_key = params.get("flow")
    error = params.get("error_description") or params.get("error")

    if not code and not error:
        return

    # code는 일회용이다. rerun 때마다 재제출되지 않도록 URL에서 먼저 지운다.
    st.query_params.clear()

    if error:
        st.error(f"소셜 로그인 실패: {error}")
        return

    entry = _flow_store().pop(flow_key, None) if flow_key else None
    if not entry or time.time() - entry[2] > _FLOW_TTL_SEC:
        st.error(
            "로그인 흐름 정보를 찾지 못했습니다."
            "또는 Supabase가 redirect URL의 flow 파라미터를 전달하지 않음) "
            "다시 시도해 주세요. 계속되면 Supabase > Authentication > URL Configuration > "
            "Redirect URLs에 이 앱 주소(끝에 /** 포함)가 등록되어 있는지 확인하세요."
        )
        return
    client = entry[0]

    # 1) code -> session 교환 (verifier는 이 client가 기억하고 있다)
    try:
        res = client.auth.exchange_code_for_session({"auth_code": code})
    except Exception as e:
        st.error(f"OAuth 코드 교환 실패: {e}")
        return

    if res.user is None:
        st.error("OAuth 사용자 정보를 가져오지 못했습니다.")
        return

    # 2) public.users 저장 + 로그인 상태 설정 (교환 실패와 저장 실패를 구분해서 표시)
    try:
        _save_auth_user(res.user)
    except Exception as e:
        st.error(f"사용자 정보 저장 실패 (public.users 테이블/제약조건 확인): {e}")
        return

    st.rerun()


# 로그아웃
def logout_user() -> None:
    # 로그인 상태는 이 브라우저 세션(st.session_state)에만 있다.
    st.session_state.user = None
    st.session_state.user_id = None
    st.session_state.logged_in = False
    st.session_state.current_menu = "홈"
    st.session_state.pop("oauth_flows", None)
    st.rerun()


# 로그인 유저 정보 불러오기
def get_current_user_profile() -> dict | None:
    user = st.session_state.get("user")

    if not user:
        return None

    metadata = getattr(user, "user_metadata", {}) or {}

    return {
        "id": user.id,
        "email": getattr(user, "email", "") or "",
        "nickname": (
            metadata.get("user_name")
            or metadata.get("preferred_username")
            or metadata.get("full_name")
            or getattr(user, "email", "")
        ),
        "avatar_url": metadata.get("avatar_url") or metadata.get("picture", ""),
        "github_url": metadata.get("preferred_username", ""),
    }


# 사용자를 public.users 테이블에 저장
def _save_auth_user(user, username: str | None = None) -> None:
    admin_supabase = get_supabase_admin_client()
    metadata = getattr(user, "user_metadata", {}) or {}

    email = getattr(user, "email", None) or ""

    display_name = (
        username
        or metadata.get("user_name")
        or metadata.get("preferred_username")
        or metadata.get("full_name")
        or metadata.get("name")
        or email
        or str(user.id)
    )

    admin_supabase.table("users").upsert(
        {
            "id": str(user.id),
            "username": display_name,
        },
        on_conflict="id",
    ).execute()

    st.session_state.user = user
    st.session_state.user_id = str(user.id)
    st.session_state.logged_in = True
    st.session_state.current_menu = "홈"


# 이메일로 로그인
def login_with_email(email: str, password: str) -> bool:
    try:
        supabase = create_auth_client()

        res = supabase.auth.sign_in_with_password(
            {
                "email": email.strip(),
                "password": password,
            }
        )

        if not res.user:
            st.error("사용자 정보를 가져오지 못했습니다.")
            return False

        _save_auth_user(res.user)
        return True

    except Exception:
        st.error(
            "로그인에 실패했습니다. 이메일과 비밀번호를 확인해 주세요."
        )
        return False


# email로 회원가입
def signup_with_email(
    email: str,
    password: str,
    username: str,
) -> bool:
    try:
        supabase = create_auth_client()
        res = supabase.auth.sign_up(
            {
                "email": email.strip(),
                "password": password,
                "options": {
                    "data": {
                        "username": username.strip(),
                        "full_name": username.strip(),
                    }
                },
            }
        )

        if not res.session or not res.user:
            st.success(
                "회원가입 요청이 완료되었습니다. "
            )
            return True

        _save_auth_user(res.user, username.strip())
        st.success("회원가입 및 로그인이 완료되었습니다.")
        return True

    except Exception:
        st.error(
            "회원가입에 실패했습니다. 이메일 형식과 비밀번호를 "
            "확인하거나 이미 가입된 계정인지 확인해 주세요."
            "비밀번호는 6자리 이상, 문자와 숫자를 포함해야 합니다."
        )
        return False

def render_email_auth_form() -> None:
    st.markdown("---")
    st.subheader("이메일로 로그인")

    login_tab, signup_tab = st.tabs(["로그인", "회원가입"])

    with login_tab:
        with st.form("email_login_form"):
            email = st.text_input(
                "이메일",
                placeholder="example@domain.com",
                key="email_login_email",
            )
            password = st.text_input(
                "비밀번호",
                type="password",
                key="email_login_password",
            )
            submitted = st.form_submit_button(
                "로그인",
                use_container_width=True,
                type="primary",
            )

        if submitted:
            if not email.strip() or not password:
                st.warning("이메일과 비밀번호를 입력해 주세요.")
            elif login_with_email(email, password):
                st.rerun()

    with signup_tab:
        with st.form("email_signup_form"):
            username = st.text_input(
                "닉네임",
                placeholder="사용할 닉네임",
                key="email_signup_username",
            )
            email = st.text_input(
                "이메일",
                placeholder="example@domain.com",
                key="email_signup_email",
            )
            password = st.text_input(
                "비밀번호 (6자 이상)",
                type="password",
                key="email_signup_password",
            )
            password_confirm = st.text_input(
                "비밀번호 확인",
                type="password",
                key="email_signup_password_confirm",
            )
            submitted = st.form_submit_button(
                "회원가입",
                use_container_width=True,
                type="primary",
            )

        if submitted:
            if not username.strip() or not email.strip():
                st.warning("닉네임과 이메일을 입력해 주세요.")
            elif len(password) < 6:
                st.warning("비밀번호는 6자 이상 입력해 주세요.")
            elif password != password_confirm:
                st.warning("비밀번호가 일치하지 않습니다.")
            else:
                if signup_with_email(email, password, username):
                    st.rerun()

"""
# 회원 탈퇴
def delete_user(user_id: int | str) -> bool:
    if user_id is None or (isinstance(user_id, str) and not user_id.strip()):
        raise ValueError("유효한 사용자 ID가 필요합니다.")

    try:
        response = (
            get_supabase_client()
            .table("users")
            .delete()
            .eq("id", user_id)
            .execute()
        )
    except Exception as exc:
        raise DatabaseOperationError(
            "회원 탈퇴에 실패했습니다. Supabase 연결과 테이블 설정을 확인해주세요."
        ) from exc

    return bool(response.data)
    """