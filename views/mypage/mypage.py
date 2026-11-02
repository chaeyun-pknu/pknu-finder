import streamlit as st
from DB.database import get_supabase_client



def render_mypage() -> None:
    st.title("마이페이지")
    st.caption("개인 설정 및 북마크를 확인할 수 있습니다.")

    logged_in = st.session_state.get("logged_in", False)
    user_id = st.session_state.get("user_id")

    if not logged_in or user_id is None:
        st.warning("마이페이지를 이용하려면 먼저 로그인해주세요.")
        return

    st.success("로그인 상태입니다.")
    st.write(f"**사용자 ID: {user_id}님**")

    st.divider()
    st.subheader("북마크")
    st.info("북마크 기능은 준비 중입니다.")
    st.divider()
    st.subheader("계정 관리")
    st.info("회원 정보 수정 및 회원 탈퇴 기능 추가 예정")