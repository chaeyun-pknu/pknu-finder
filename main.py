import streamlit as st
from database import init_db, get_username
from views.mypage.user import create_user, check_login
# from views.mypage.mypage import render_mypage
# from views.home.home import render_home  # 홈 화면 임포트
# from views.search.search import render_search
# from views.chat.chat import render_chat
# from views.register.register import render_register

# 데이터베이스 초기화
init_db()

# 페이지 기본 설정
st.set_page_config(
    page_title="PKNU Finder",
    page_icon="images/pknulogo.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 세션 상태 초기화
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "current_menu" not in st.session_state:
    st.session_state.current_menu = "홈"


# 초기 접속 시 로그인/회원가입 화면 렌더링

def render_auth_page():
    st.title("PKNU Finder 로그인 / 회원가입")

    tab_login, tab_signup = st.tabs(["로그인", "회원가입"])

    with tab_login:
        st.subheader("로그인")
        login_username = st.text_input("아이디", key="login_username")
        login_password = st.text_input("비밀번호", type="password", key="login_password")
        
        if st.button("로그인", type="primary"):
            if login_username and login_password:
                user_id = check_login(login_username, login_password)
                if user_id:
                    st.session_state.logged_in = True
                    st.session_state.user_id = user_id
                    st.session_state.current_menu = "홈"  # 로그인 직후 홈으로 설정
                    st.success(f"환영합니다, {login_username}님!")
                    st.rerun()
                else:
                    st.error("아이디 또는 비밀번호가 올바르지 않습니다.")
            else:
                st.warning("아이디와 비밀번호를 모두 입력해주세요.")

    with tab_signup:
        st.subheader("회원가입")
        signup_username = st.text_input("사용할 아이디", key="signup_username")
        signup_password = st.text_input("사용할 비밀번호", type="password", key="signup_password")
        signup_password_confirm = st.text_input("비밀번호 확인", type="password", key="signup_password_confirm")

        if st.button("회원가입 하기"):
            if signup_username and signup_password:
                if signup_password != signup_password_confirm:
                    st.error("비밀번호가 일치하지 않습니다.")
                else:
                    success = create_user(signup_username, signup_password)
                    if success:
                        st.success("회원가입이 완료되었습니다! 로그인 탭에서 로그인해주세요.")
                    else:
                        st.error("이미 존재하는 아이디입니다.")
            else:
                st.warning("모든 항목을 입력해주세요.")


def main():
    # 로그인이 되어있지 않은 경우 로그인/회원가입 화면 표시
    if not st.session_state.logged_in:
        render_auth_page()
        return


    #사이드바

    st.sidebar.title("PKNU Finder")
    st.sidebar.markdown("---")

    # 메뉴 목록
    menu_options = ["홈", "분실물/습득물 검색", "분실물/습득물 등록", "채팅", "마이페이지"]
    
    # 현재 선택된 메뉴가 세션 상태에 없으면 기본값으로 "홈" 설정
    if st.session_state.current_menu not in menu_options:
        st.session_state.current_menu = "홈"
    default_index = menu_options.index(st.session_state.current_menu)

    menu = st.sidebar.radio(
        "메뉴 선택", 
        menu_options,
        index=default_index
    )
    
    # 메뉴 선택 변경 >  세션 상태 업데이트 > 페이지 새로고침
    if menu != st.session_state.current_menu:
        st.session_state.current_menu = menu
        st.rerun()

    st.sidebar.markdown("---")

    # 접속 계정 표시
    current_username = get_username(st.session_state.user_id)
    st.sidebar.text(f"접속 계정: {current_username}님")

    # 로그아웃 버튼
    if st.sidebar.button("로그아웃", type="secondary", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.user_id = None
        st.session_state.current_menu = "홈"
        st.success("로그아웃되었습니다.")
        st.rerun()

    # 메뉴 선택에 따른 화면 라우팅
    if st.session_state.current_menu == "홈":
        st.title("홈화면")
        st.write("홈화면 개발 예정")  # << 임시 화면 출력용 코드
        # render_home()  # views/home/home.py 함수 호출 << 추후 코드 작성 후 주석 제거 바람

    elif st.session_state.current_menu == "분실물/습득물 검색":
        st.title("분실물/습득물 검색")
        st.write("분실물 검색 화면 개발 예정") # << 임시 화면 출력용 코드
        # render_search() << 추후 코드 작성 후 주석 제거 바람

    elif st.session_state.current_menu == "분실물/습득물 등록":
        st.title("분실물/습득물 등록")
        st.write("분실물 등록 화면 개발 예정") # << 임시 화면 출력용 코드
        # render_register() << 추후 코드 작성 후 주석 제거 바람

    elif st.session_state.current_menu == "채팅":
        st.title("채팅")
        st.write("채팅 화면 개발 예정") # << 임시 화면 출력용 코드
        # render_chat() << 추후 코드 작성 후 주석 제거 바람

    elif st.session_state.current_menu == "마이페이지":
        st.title("마이페이지")
        st.write("마이페이지 화면 개발 예정") # << 임시 화면 출력용 코드
        #render_mypage() << 추후 코드 작성 후 주석 제거 바람


if __name__ == "__main__":
    main()