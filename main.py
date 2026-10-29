import streamlit as st
from views.mypage.social_button import render_social_login_buttons

st.set_page_config(
    page_title="PKNU Finder",
    page_icon="docs\\images\\pknulogo.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

from database import (
    DatabaseConfigurationError,
    DatabaseOperationError,
    get_username,
    init_db,
)

from views.mypage.auth import (
    get_oauth_login_url,
    handle_oauth_callback,
    logout_user,
    get_current_user_profile,
    render_email_auth_form
)

# 각 폴더, 파일 별 ui 작업 후 render_home, render_search, render_register, render_chat, render_mypage를 import하여 사용. 주석 제거 바람
from views.home.home import render_home
#from views.search.search import render_search
#from views.register.register import render_register
#from views.chat.chat import render_chat
#from views.mypage.mypage import render_mypage


MENU_OPTIONS = [
    "홈",
    "분실물/습득물 검색",
    "분실물/습득물 등록",
    "채팅",
    "마이페이지",
]


def initialize_session_state() -> None:
    defaults = {
        "logged_in": False,
        "user_id": None,
        "user" : None,
        "current_menu": "홈",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def render_auth_page() -> None:
    st.title("PKNU Finder")
    st.caption("부경대학교 분실물·습득물 찾기 서비스")

    #Github, Google 로그인 URL 가져오기
    github_url = get_oauth_login_url("github")
    google_url = get_oauth_login_url("google")

    # 소셜 로그인 랜더링
    render_social_login_buttons(
        google_url=google_url,
        github_url=github_url,
    )

    #email 로그인 랜더링
    render_email_auth_form()
        
    st.markdown("---")

def logout() -> None:
    for key in (
        "email_login_email",
        "email_login_password",
        "email_signup_username",
        "email_signup_email",
        "email_signup_password",
        "email_signup_password_confirm",
    ):
        st.session_state.pop(key, None)

    logout_user()  # 세션 상태 초기화 후 st.rerun()

# 랜더링 함수들을 각 메뉴에 맞게 구현 후 주석 제거 바람
def render_selected_page(menu: str) -> None:
    if menu == "홈":
        render_home()
    elif menu == "마이페이지":
        st.title("마이페이지")
        st.info("마이페이지는 준비 중입니다.")
        #render_mypage()
    elif menu == "분실물/습득물 검색":
        st.title("분실물/습득물 검색")
        st.info("검색 화면은 준비 중입니다.")
        #render_search()
    elif menu == "분실물/습득물 등록":
        st.title("분실물/습득물 등록")
        st.info("등록 화면은 준비 중입니다.")
        #render_register()
    elif menu == "채팅":
        st.title("채팅")
        st.info("채팅 화면은 준비 중입니다.")
        #render_chat()
    else:
        st.warning("선택한 메뉴를 찾을 수 없습니다.")


def render_app() -> None:
    st.sidebar.title("PKNU Finder")
    st.sidebar.markdown("---")

    current_menu = st.session_state.get("current_menu", "홈")
    if current_menu not in MENU_OPTIONS:
        current_menu = "홈"
        st.session_state.current_menu = current_menu

    selected_menu = st.sidebar.radio(
        "메뉴 선택",
        MENU_OPTIONS,
        index=MENU_OPTIONS.index(current_menu),
        key="menu_radio",
    )
    st.session_state.current_menu = selected_menu

    st.sidebar.markdown("---")


    # 계정 이름 표시 (GitHub OAuth 유저 / DB 유저 통합)
    profile = get_current_user_profile()
    username = None
    
    if profile:
        username = profile.get("nickname")
    elif st.session_state.get("user_id"):
        try:
            username = get_username(st.session_state.user_id)
        except Exception:
            username = None

    st.sidebar.write(f"접속 계정: {username}님" if username else "접속 계정")
    if st.sidebar.button("로그아웃", use_container_width=True):
        logout()

    render_selected_page(selected_menu)


# DB 연결 확인은 10분에 한 번
@st.cache_resource(ttl=600, show_spinner=False)
def check_db_once() -> bool:
    init_db()
    return True


# 메인 함수 오류 확인 등
def main() -> None:
    initialize_session_state()
    try:
        check_db_once()
    except DatabaseConfigurationError as exc:
        st.error("Supabase 연결 설정이 필요합니다.")
        st.code(str(exc))
        st.info(
            ".streamlit/secrets.toml에 SUPABASE_URL과 "
            "SUPABASE_SERVICE_ROLE_KEY를 설정해주세요."
        )
        st.stop()
    except DatabaseOperationError as exc:
        st.error("Supabase 데이터베이스를 확인하지 못했습니다.")
        st.code(str(exc))
        st.info(
            "supabase_schema.sql을 Supabase SQL Editor에서 실행했는지, "
            "필수 테이블 이름과 권한이 올바른지 확인해주세요."
        )
        st.stop()
    except Exception as exc:
        st.error("Supabase 초기화 중 오류가 발생했습니다.")
        st.code(str(exc))
        st.stop()

    #OAuth 콜백 파라미터 체크 및 자동 로그인 세션 교환
    handle_oauth_callback()

    # 로그인 여부 확인
    if st.session_state.get("user") is not None:
        st.session_state.logged_in = True
    
    #로그인 여부에 따른 화면 랜더링
    if st.session_state.logged_in:
        render_app()
    else:
        render_auth_page()


if __name__ == "__main__":
    main()