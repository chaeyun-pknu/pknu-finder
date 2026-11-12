import streamlit as st

from DB.database import (
    DatabaseConfigurationError,
    DatabaseOperationError,
    get_username,
    init_db,
)
from views.register.detail import show_item_detail

# 각 화면 연결
from views.home.home import render_home
from views.register.register import (
    render_register,
    clear_register_state,
)
from views.search.search import render_search
#from views.chat.chat import render_chat
from views.mypage.mypage import render_mypage

# 로그인 및 회원가입
from views.mypage.social_button import render_social_login_buttons
from views.mypage.auth import (
    get_oauth_login_url,
    handle_oauth_callback,
    logout_user,
    get_current_user_profile,
    render_email_auth_form,
)

#채팅 화면
from views.chat.chat import render_chat


st.set_page_config(
    page_title="PKNU Finder",
    page_icon="docs/images/pknufinderlogo.svg",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =======
# 메뉴
# =======

MENU_OPTIONS = [
    "홈",
    "분실물/습득물 검색",
    "분실물/습득물 등록",
    "채팅",
    "마이페이지",
]


# ==========================================
# 세션 상태 초기화
# ==========================================

def initialize_session_state() -> None:
    defaults = {
        "logged_in": False,
        "user_id": None,
        "user": None,
        "current_menu": "홈",
        "supabase_access_token": None,
        "supabase_refresh_token": None,
        "previous_menu": "홈",
        "selected_item_id": None,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# ==========================================
# 로그인 / 회원가입 화면
# ==========================================

def render_auth_page() -> None:
    st.title("PKNU Finder")
    st.caption("부경대학교 분실물·습득물 찾기 서비스")

    # Google / GitHub 로그인 URL 생성
    github_url = get_oauth_login_url("github")
    google_url = get_oauth_login_url("google")

    # 소셜 로그인 버튼
    render_social_login_buttons(
        google_url=google_url,
        github_url=github_url,
    )

    # 이메일 로그인 및 회원가입
    render_email_auth_form()

    st.markdown("---")


# ==========================================
# 로그아웃
# ==========================================

def logout() -> None:

    # 등록 화면의 임시 입력값 초기화
    clear_register_state()

    # 로그인 / 회원가입 입력값 초기화
    for key in (
        "email_login_email",
        "email_login_password",
        "email_signup_username",
        "email_signup_email",
        "email_signup_password",
        "email_signup_password_confirm",
    ):
        st.session_state.pop(key, None)

    # Supabase Auth 로그아웃
    logout_user()


# ==========================================
# 메뉴별 화면 실행
# ==========================================

def render_selected_page(menu: str) -> None:

    if menu == "홈":
        render_home()

    elif menu == "마이페이지":
        render_mypage()

    elif menu == "분실물/습득물 검색":
        render_search()

    elif menu == "분실물/습득물 등록":
        render_register()

    elif menu == "채팅":
        render_chat()

    elif menu == "게시글 상세보기":
        item_id = st.session_state.get("selected_item_id")

        if item_id is not None:
            show_item_detail(item_id)
        else:
            st.warning("상세보기할 게시글이 선택되지 않았습니다.")

    else:
        st.warning("선택한 메뉴를 찾을 수 없습니다.")
    


# ==========================================
# 로그인 후 메인 화면
# ==========================================

def render_app() -> None:
    
    # 사이드바 메뉴
    st.sidebar.title("PKNU Finder")
    st.sidebar.markdown("---")

    current_menu = st.session_state.get("current_menu", "홈")

    # 상세 페이지에서는 사이드바 메뉴를 표시하지 않고
    # 기존 메뉴 상태를 유지한다.
    if current_menu == "게시글 상세보기":
        if st.sidebar.button("← 이전 화면으로 돌아가기", width="stretch"):
            previous_menu = st.session_state.get(
                "previous_menu", "홈"
            )

            st.session_state.current_menu = previous_menu
            st.session_state.selected_item_id = None
            st.rerun()

    else:
        # 사이드바 메뉴
        st.sidebar.title("PKNU Finder")
        st.sidebar.markdown("---")

        selected_menu = st.sidebar.radio(
            "메뉴 선택",
            MENU_OPTIONS,
            index=MENU_OPTIONS.index(current_menu),
            key="menu_radio",
        )

        # 메뉴 변경 시 이전 메뉴 저장
        if selected_menu != current_menu:
            st.session_state.previous_menu = current_menu

        # 채팅 메뉴로 이동하면 채팅 목록 초기화
        if selected_menu == "채팅" and current_menu != "채팅":
            st.session_state.selected_room = None

        st.session_state.current_menu = selected_menu

        # 등록 화면에서 다른 메뉴로 이동하면 입력값 초기화
        if selected_menu != "분실물/습득물 등록":
            clear_register_state()

    st.sidebar.markdown("---")

    # 로그인 사용자 정보 표시
    profile = get_current_user_profile()
    username = None

    if profile:
        username = profile.get("nickname")

    elif st.session_state.get("user_id"):
        try:
            username = get_username(
                st.session_state.user_id
            )
        except Exception:
            username = None

    st.sidebar.write(
        f"접속 계정: {username}님"
        if username
        else "접속 계정"
    )

    # 로그아웃 버튼
    if st.sidebar.button("로그아웃", width="stretch"):
        logout()
        st.rerun()

    # 선택한 메뉴 실행
    render_selected_page(st.session_state.current_menu)



# ==========================================
# DB 연결 확인 (10분간 캐싱)
# ==========================================

@st.cache_resource(ttl=600, show_spinner=False)
def check_db_once() -> bool:
    init_db()
    return True


# ==========================================
# 프로그램 시작
# ==========================================

def main() -> None:

    initialize_session_state()

    # Supabase 연결 확인
    try:
        check_db_once()

    except DatabaseConfigurationError as exc:
        st.error("Supabase 연결 설정이 필요합니다.")
        st.code(str(exc))
        st.info(
            ".streamlit/secrets.toml의 "
            "Supabase 설정을 확인해주세요."
        )
        st.stop()

    except DatabaseOperationError as exc:
        st.error(
            "Supabase 데이터베이스를 확인하지 못했습니다."
        )
        st.code(str(exc))
        st.info(
            "Supabase 테이블 이름 및 "
            "접근 권한을 확인해주세요."
        )
        st.stop()

    except Exception as exc:
        st.error(
            "Supabase 초기화 중 오류가 발생했습니다."
        )
        st.code(str(exc))
        st.stop()

    # OAuth 로그인 인증 결과 처리
    handle_oauth_callback()

    if st.session_state.get("user") is not None:
        st.session_state.logged_in = True

    # 로그인 여부에 따른 화면 표시
    if st.session_state.logged_in:
        render_app()
    else:
        render_auth_page()


if __name__ == "__main__":
    main()
