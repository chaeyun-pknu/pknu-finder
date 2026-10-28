import streamlit as st
from database import get_connection
# from views.register/search.register/search import show_recent_items #최근 게시글 불러오기 함수

def render_home() -> None:
    st.markdown(
            """
            <div style="text-align: center; padding: 35px 0 25px 0;">
                <h1 style="font-size: 3rem; margin-bottom: 8px;">
                    PKNU Finder
                </h1>
                <p style="font-size: 1.05rem; color: #808080; margin-top: 0;">
                    부경대학교 학생들을 위한 분실물 찾기 서비스
                </p>
                <p style="font-size: 0.95rem; color: #999999;">
                    잃어버린 물건을 찾고, 습득한 물건의 주인을 찾아주세요.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.divider()
    st.subheader("최근 등록된 게시글")
    # show_recent_items() 
