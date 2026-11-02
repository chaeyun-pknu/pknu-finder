import re
import secrets
import time
from datetime import datetime, timezone
import streamlit as st

from DB.database import create_auth_client, get_supabase_admin_client


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

# =========================
# OAuth 로그인
# =========================

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

    # code는 일회용. rerun 때마다 재제출되지 않도록 URL에서 지움.
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

    # code -> session 교환
    try:
        res = client.auth.exchange_code_for_session({"auth_code": code})
    except Exception as e:
        st.error(f"OAuth 코드 교환 실패: {e}")
        return

    if res.user is None:
        st.error("OAuth 사용자 정보를 가져오지 못했습니다.")
        return

    # public.users 저장 + 로그인 상태 설정
    try:
        _save_auth_user(res.user)
    except Exception as e:
        st.error(f"사용자 정보 저장 실패 (public.users 테이블/제약조건 확인): {e}")
        return

    st.rerun()

# =====================
# 사용자 정보
# =====================

# 로그인 후 Supabase Auth 사용자 정보를 public.users 테이블에 저장하고 세션 상태를 설정합니다.
def _save_auth_user(user, username: str | None = None) -> None:
    admin_supabase = get_supabase_admin_client()
    metadata = getattr(user, "user_metadata", {}) or {}
    email = getattr(user, "email", None) or ""

    display_name = (
        username
        or metadata.get("username")
        or metadata.get("user_name")
        or metadata.get("preferred_username")
        or metadata.get("full_name")
        or metadata.get("name")
        or email
        or str(user.id)
    )

    # 탈퇴 처리된 계정 회원가입 방지
    existing = (
        admin_supabase.table("users")
        .select("is_deleted")
        .eq("id", str(user.id))
        .limit(1)
        .execute()
    )
    if existing.data and existing.data[0].get("is_deleted"):
        raise ValueError("탈퇴 처리된 계정입니다.")

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


def get_current_user_profile() -> dict | None:
    """현재 로그인한 사용자의 프로필 정보를 반환합니다."""
    user = st.session_state.get("user")
    if not user:
        return None

    metadata = getattr(user, "user_metadata", {}) or {}

    return {
        "id": user.id,
        "email": getattr(user, "email", "") or "",
        "nickname": (
            metadata.get("username")
            or metadata.get("user_name")
            or metadata.get("preferred_username")
            or metadata.get("full_name")
            or getattr(user, "email", "")
        ),
        "avatar_url": metadata.get("avatar_url") or metadata.get("picture", ""),
        "github_url": metadata.get("preferred_username", ""),
    }

# ==========================
# 로그아웃 및 이메일 로그인
# ===========================

def logout_user() -> None:
    """현재 Streamlit 세션의 로그인 상태를 초기화합니다."""
    st.session_state.user = None
    st.session_state.user_id = None
    st.session_state.logged_in = False
    st.session_state.current_menu = "홈"
    st.session_state.pop("oauth_flows", None)
    st.rerun()


def login_with_email(email: str, password: str) -> bool:
    """이메일과 비밀번호로 로그인합니다."""
    try:
        supabase = create_auth_client()
        response = supabase.auth.sign_in_with_password(
            {
                "email": email.strip(),
                "password": password,
            }
        )

        if not response.user:
            st.error("사용자 정보를 가져오지 못했습니다.")
            return False

        _save_auth_user(response.user)
        return True

    except Exception:
        st.error("로그인에 실패했습니다. 이메일과 비밀번호를 확인해 주세요.")
        return False

# =======================
# 회원가입 유효성 검사
# =======================

# 비밀번호 유효성 검사: 영문과 숫자를 포함하여 6자리 이상
def validate_password(password: str) -> bool:
    pattern = r"^(?=.*[A-Za-z])(?=.*[0-9]).{6,}$"
    return bool(re.fullmatch(pattern, password))

# 닉네임 중복 여부 확인
def is_nickname_available(nickname: str) -> bool:
    normalized_nickname = nickname.strip()
    if not normalized_nickname:
        return False

    admin_supabase = get_supabase_admin_client()
    response = (
        admin_supabase.table("users")
        .select("id")
        .ilike("username", normalized_nickname)
        .limit(1)
        .execute()
    )
    return not bool(response.data)


# 회원가입 입력값 유효성 검사
def validate_signup_inputs(
    email: str,
    password: str,
    password_confirm: str,
    nickname: str,
) -> list[str]:
    errors = []

    email = email.strip()
    nickname = nickname.strip()

    if not email:
        errors.append("이메일을 입력해주세요.")

    if not nickname:
        errors.append("닉네임을 입력해주세요.")

    if not validate_password(password):
        errors.append(
            "비밀번호는 영문과 숫자를 포함하여 6자리 이상이어야 합니다."
        )

    if password != password_confirm:
        errors.append("비밀번호가 일치하지 않습니다.")

    if nickname:
        try:
            if not is_nickname_available(nickname):
                errors.append("이미 사용 중인 닉네임입니다.")
        except Exception:
            errors.append("닉네임 중복 여부를 확인하지 못했습니다. 잠시 후 다시 시도해주세요.")

    return errors


# 회원가입 오류 메시지 처리
def _signup_error_message(error: Exception) -> str:
    message = str(error).lower()

    if any(
        marker in message
        for marker in (
            "already registered",
            "email_exists",
            "user_already_exists",
            "already been registered",
        )
    ):
        return "이미 가입된 이메일입니다."

    return (
        "회원가입에 실패했습니다. 이메일 형식과 비밀번호를 확인해 주세요. "
        f"(오류: {error})"
    )

# 이메일 회원가입 처리
def signup_with_email(
    email: str,
    password: str,
    username: str,
) -> bool:
    try:
        supabase = create_auth_client()
        nickname = username.strip()

        response = supabase.auth.sign_up(
            {
                "email": email.strip(),
                "password": password,
                "options": {
                    "data": {
                        "username": nickname,
                        "full_name": nickname,
                    }
                },
            }
        )

        # 이메일 인증이 활성화되어 있으면 session이 없는 상태로 반환될 수 있습니다.
        if not response.user:
            st.error("회원가입 결과를 확인할 수 없습니다.")
            return False

        if not response.session:
            st.success(
                "회원가입 요청이 완료되었습니다. 이메일 인증이 필요한 경우 "
                "메일함에서 인증을 완료한 후 로그인해 주세요."
            )
            return True

        _save_auth_user(response.user, nickname)
        st.success("회원가입 및 로그인이 완료되었습니다.")
        return True

    except Exception as e:
        st.error(_signup_error_message(e))
        return False

# ===============================
# 이메일 로그인 / 회원가입 화면
# ===============================

# 이메일 로그인 및 회원가입 폼 랜더링
def render_email_auth_form() -> None:
    st.markdown("---")
    st.subheader("이메일로 로그인")

    login_tab, signup_tab = st.tabs(["로그인", "회원가입"])

    with login_tab:
        with st.form("email_login_form"):
            login_email = st.text_input(
                "이메일",
                placeholder="example@domain.com",
                key="email_login_email",
            )
            login_password = st.text_input(
                "비밀번호",
                type="password",
                key="email_login_password",
            )
            login_submitted = st.form_submit_button(
                "로그인",
                use_container_width=True,
                type="primary",
            )

        if login_submitted:
            if not login_email.strip() or not login_password:
                st.warning("이메일과 비밀번호를 입력해 주세요.")
            elif login_with_email(login_email, login_password):
                st.rerun()

    with signup_tab:
        with st.form("email_signup_form"):
            signup_username = st.text_input(
                "닉네임",
                placeholder="사용할 닉네임",
                key="email_signup_username",
            )
            signup_email = st.text_input(
                "이메일",
                placeholder="example@domain.com",
                key="email_signup_email",
            )
            signup_password = st.text_input(
                "비밀번호",
                type="password",
                placeholder="영문과 숫자를 포함하여 6자 이상",
                key="email_signup_password",
            )
            signup_password_confirm = st.text_input(
                "비밀번호 확인",
                type="password",
                key="email_signup_password_confirm",
            )
            signup_submitted = st.form_submit_button(
                "회원가입",
                use_container_width=True,
                type="primary",
            )

        if signup_submitted:
            errors = validate_signup_inputs(
                signup_email,
                signup_password,
                signup_password_confirm,
                signup_username,
            )

            if errors:
                for error in errors:
                    st.error(error)
            else:
                if signup_with_email(
                    signup_email,
                    signup_password,
                    signup_username,
                ):
                    st.rerun()


# ===========
# 회원 탈퇴
# ===========
#1. 사용자 이름을 '탈퇴한 유저'로 변경
#2. 탈퇴 여부와 탈퇴 일시 저장
#3. 기존 북마크 삭제
#4. Supabase Auth 계정 Soft Delete
#게시글과 채팅 기록은 유지합니다.

def delete_user(user_id: str) -> None:
    if not user_id:
        raise ValueError("사용자 ID가 없습니다.")

    supabase = get_supabase_admin_client()

    # 사용자 프로필 탈퇴 유저로 변경
    supabase.table("users").update({
        "username": "탈퇴한 유저",
        "is_deleted": True,
        "deleted_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", user_id).execute()

    # 기존 북마크 삭제
    supabase.table("bookmarks").delete().eq(
        "user_id", user_id
    ).execute()

    # Supabase Auth 계정 Soft Delete
    supabase.auth.admin.delete_user(
        user_id,
        should_soft_delete=True,
    )