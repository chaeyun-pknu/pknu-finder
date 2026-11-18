import streamlit as st

def load_css(css_path):
    if not css_path.exists():
        st.error(f"CSS 파일을 찾을 수 없습니다: {css_path}")
        return

    with open(css_path, "r", encoding="utf-8") as file:
        st.markdown(
            f"<style>{file.read()}</style>",
            unsafe_allow_html=True
        )