import streamlit as st
from DB.database import get_supabase_client
from views.mypage.auth import delete_user



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
    render_delete_account_section()  # 회원탈퇴 섹션

# 회원탈퇴 섹션 표시
def render_delete_account_section():
    st.divider()
    st.subheader("회원 탈퇴")

    st.warning(
        "회원 탈퇴 시 로그인이 비활성화됩니다.\n\n"
        "- 기존 게시글과 채팅 내역은 유지됩니다.\n"
        "- 작성자 이름은 '탈퇴한 유저'로 표시됩니다.\n"
        "- 기존 북마크는 삭제됩니다.\n"
        "- 탈퇴 후에는 기존 계정으로 로그인할 수 없습니다."
    )

    confirmed = st.checkbox(
        "회원 탈퇴 내용을 확인했으며, 탈퇴에 동의합니다."
    )

    if st.button(
        "회원 탈퇴",
        type="primary",
        disabled=not confirmed,
        use_container_width=False,
    ):
        user_id = st.session_state.get("user_id")

        if not user_id:
            st.error("로그인 정보를 확인할 수 없습니다.")
            return

        try:
            delete_user(user_id)

            # Streamlit 로그인 상태 초기화
            st.session_state["logged_in"] = False
            st.session_state["user_id"] = None
            st.session_state["user"] = None
            st.session_state["current_menu"] = "홈"

            # 인증 클라이언트 세션 정보 제거
            st.session_state.pop("_supabase_auth_client", None)

            st.success("회원 탈퇴가 완료되었습니다.")
            st.rerun()

        except Exception as e:
            st.error(f"회원 탈퇴 처리에 실패했습니다: {e}")   