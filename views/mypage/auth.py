import streamlit as st
from supabase import Client
from database import get_supabase_admin_client, get_supabase_client


# OAuth 인증 후 리다이렉트 주소 설정
def _get_redirect_url() -> str:
    default_url = "http://localhost:8501"
    try:
        if "supabase" in st.secrets:
            return st.secrets["supabase"].get("SUPABASE_REDIRECT_URL", default_url)
        return st.secrets.get("SUPABASE_REDIRECT_URL", default_url)
    except Exception:
        return default_url


# OAuth 제공자 로그인 URL 설정
def get_oauth_login_url(supabase: Client, provider: str) -> str | None:
    try:
        res = supabase.auth.sign_in_with_oauth(
            {
                "provider": provider,
                "options": {"redirect_to": _get_redirect_url()},
            }
        )
        return res.url
    except Exception as e:
        st.error(f"{provider} 로그인 URL 생성 중 오류 발생: {e}")
        return None


def handle_oauth_callback(supabase: Client | None = None):
    query_params = st.query_params

    if "code" in query_params and st.session_state.get("user") is None:
        auth_code = query_params["code"]

        try:
            # GitHub OAuth 인증 코드 교환
            res = supabase.auth.exchange_code_for_session(
                {"auth_code": auth_code}
            )
            user = res.user

            if user is None:
                st.error("OAuth 사용자 정보를 가져오지 못했습니다.")
                return

            # 데이터베이스 전용 클라이언트로 사용자 정보 저장
            admin_supabase = get_supabase_admin_client()

            metadata = getattr(user, "user_metadata", {}) or {}

            username = (
                metadata.get("user_name")
                or metadata.get("preferred_username")
                or metadata.get("full_name")
                or metadata.get("name")
                or getattr(user, "email", None)
                or str(user.id)
            )

            admin_supabase.table("users").upsert(
                {
                    "id": str(user.id),
                    "username": username,
                },
                on_conflict="id",
            ).execute()

            # 로그인 상태 저장
            st.session_state.user = user
            st.session_state.user_id = str(user.id)
            st.session_state.logged_in = True
            st.session_state.current_menu = "홈"

            # OAuth 인증 코드 제거 후 화면 갱신
            st.query_params.clear()
            st.rerun()

        except Exception as e:
            st.error(f"OAuth 로그인 또는 사용자 정보 저장 실패: {e}")



# 로그아웃
def logout_user(supabase: Client) -> None:
    try:
        supabase.auth.sign_out()

    except Exception as e:
        st.warning(f"로그아웃 중 알림: {e}")

    finally:
        st.session_state.user = None
        st.session_state.user_id = None
        st.session_state.logged_in = False
        st.session_state.current_menu = "홈"

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
        supabase = get_supabase_client()

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
        supabase = get_supabase_client()
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