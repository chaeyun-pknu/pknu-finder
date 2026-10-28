import streamlit as st

st.set_page_config(
    page_title="PKNU Finder",
    page_icon=r"docs\images\pknulogo.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 데이터베이스 관련 함수
from database import (
    DatabaseConfigurationError,
    DatabaseOperationError,
    get_username,
    init_db,
)

# 로그인 및 회원가입
from views.mypage.user import check_login, create_user

# 각 화면 연결
from views.home.home import render_home
from views.register.register import render_register

# 다른 기능은 팀원이 구현한 후 연결
# from views.search.search import render_search
# from views.chat.chat import render_chat
# from views.mypage.mypage import render_mypage


# ==========================================
# 메뉴
# ==========================================

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
        "current_menu": "홈",
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

    login_tab, signup_tab = st.tabs(
        ["로그인", "회원가입"]
    )

    # --------------------------------------
    # 로그인
    # --------------------------------------
    with login_tab:

        st.subheader("로그인")

        with st.form("login_form"):

            login_username = st.text_input(
                "아이디",
                key="login_username"
            )

            login_password = st.text_input(
                "비밀번호",
                type="password",
                key="login_password"
            )

            login_submitted = st.form_submit_button(
                "로그인",
                type="primary"
            )

        if login_submitted:

            login_username = login_username.strip()

            if not login_username or not login_password:

                st.warning(
                    "아이디와 비밀번호를 모두 입력해주세요."
                )

            else:

                try:
                    user_id = check_login(
                        login_username,
                        login_password
                    )

                except Exception as exc:

                    st.error(
                        "로그인에 실패했습니다. "
                        "Supabase 설정과 users 테이블을 확인해주세요."
                    )

                    st.caption(f"오류 내용: {exc}")

                else:

                    if user_id is None:

                        st.error(
                            "아이디 또는 비밀번호가 올바르지 않습니다."
                        )

                    else:

                        st.session_state.logged_in = True
                        st.session_state.user_id = user_id
                        st.session_state.current_menu = "홈"

                        st.rerun()

    # --------------------------------------
    # 회원가입
    # --------------------------------------
    with signup_tab:

        st.subheader("회원가입")

        with st.form("signup_form"):

            signup_username = st.text_input(
                "사용할 아이디",
                key="signup_username"
            )

            signup_password = st.text_input(
                "사용할 비밀번호",
                type="password",
                key="signup_password"
            )

            signup_password_confirm = st.text_input(
                "비밀번호 확인",
                type="password",
                key="signup_password_confirm"
            )

            signup_submitted = st.form_submit_button(
                "회원가입"
            )

        if signup_submitted:

            signup_username = signup_username.strip()

            if (
                not signup_username
                or not signup_password
                or not signup_password_confirm
            ):

                st.warning(
                    "모든 항목을 입력해주세요."
                )

            elif signup_password != signup_password_confirm:

                st.error(
                    "비밀번호가 일치하지 않습니다."
                )

            else:

                try:
                    created = create_user(
                        signup_username,
                        signup_password
                    )

                except Exception as exc:

                    st.error(
                        "회원가입에 실패했습니다. "
                        "Supabase 설정과 users 테이블을 확인해주세요."
                    )

                    st.exception(exc)

                else:

                    if created:

                        st.success(
                            "회원가입이 완료되었습니다. "
                            "로그인 탭에서 로그인해주세요."
                        )

                    else:

                        st.error(
                            "이미 사용 중인 아이디이거나 "
                            "회원가입을 완료하지 못했습니다."
                        )


# ==========================================
# 로그아웃
# ==========================================

def logout() -> None:

    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.current_menu = "홈"

    for key in (
        "login_username",
        "login_password",
        "signup_username",
        "signup_password",
        "signup_password_confirm",
    ):
        st.session_state.pop(key, None)

    st.rerun()


# ==========================================
# 메뉴별 화면 실행
# ==========================================

def render_selected_page(menu: str) -> None:

    # 홈 화면
    if menu == "홈":

        render_home()

    # 마이페이지
    elif menu == "마이페이지":

        st.title("마이페이지")
        st.info("마이페이지는 준비 중입니다.")

        # render_mypage()

    # 검색 화면
    elif menu == "분실물/습득물 검색":

        st.title("분실물/습득물 검색")
        st.info("검색 화면은 준비 중입니다.")

        # render_search()

    # 등록 화면
    elif menu == "분실물/습득물 등록":

        # 사용자님이 구현한 등록 UI 실행
        render_register()

    # 채팅 화면
    elif menu == "채팅":

        st.title("채팅")
        st.info("채팅 화면은 준비 중입니다.")

        # render_chat()

    else:

        st.warning(
            "선택한 메뉴를 찾을 수 없습니다."
        )


# ==========================================
# 로그인 후 메인 화면
# ==========================================

def render_app() -> None:

    st.sidebar.title("PKNU Finder")
    st.sidebar.markdown("---")

    current_menu = st.session_state.get(
        "current_menu",
        "홈"
    )

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

    # 로그인 사용자 정보
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

    if st.sidebar.button(
        "로그아웃",
        use_container_width=True
    ):
        logout()

    # 선택한 메뉴 실행
    render_selected_page(selected_menu)


# ==========================================
# 프로그램 시작
# ==========================================

def main() -> None:

    initialize_session_state()

    # Supabase 연결 확인
    try:
        init_db()

    except DatabaseConfigurationError as exc:

        st.error(
            "Supabase 연결 설정이 필요합니다."
        )

        st.code(str(exc))

        st.info(
            ".streamlit/secrets.toml에 "
            "SUPABASE_URL과 "
            "SUPABASE_SERVICE_ROLE_KEY를 설정해주세요."
        )

        st.stop()

    except DatabaseOperationError as exc:

        st.error(
            "Supabase 데이터베이스를 확인하지 못했습니다."
        )

        st.code(str(exc))

        st.info(
            "supabase_schema.sql을 Supabase SQL Editor에서 "
            "실행했는지, 필수 테이블 이름과 권한이 "
            "올바른지 확인해주세요."
        )

        st.stop()

    except Exception as exc:

        st.error(
            "Supabase 초기화 중 오류가 발생했습니다."
        )

        st.code(str(exc))

        st.stop()

    # 로그인 여부에 따라 화면 구분
    if st.session_state.logged_in:

        render_app()

    else:

        render_auth_page()


if __name__ == "__main__":
    main()
