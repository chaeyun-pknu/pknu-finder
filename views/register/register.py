import streamlit as st
from database import get_connection


def render_register():
    st.title("분실물 / 습득물 등록")
    st.write("분실하거나 습득한 물품의 정보를 입력해주세요.")

    with st.form("register_form"):
        item_type = st.radio(
            "등록 유형",
            ["분실물", "습득물"],
            horizontal=True
        )

        item_name = st.text_input("물품명")

        category = st.selectbox(
            "카테고리",
            ["전자기기", "지갑", "의류", "가방", "기타"]
        )

        location = st.text_input("분실 / 습득 장소")

        item_date = st.date_input("분실 / 습득 날짜")

        description = st.text_area("상세 설명")

        image = st.file_uploader(
            "물품 사진",
            type=["jpg", "jpeg", "png"]
        )

        submitted = st.form_submit_button("등록하기")

    if submitted:
        if not item_name.strip() or not location.strip():
            st.warning("물품명과 장소를 입력해주세요.")
        else:
            st.success("입력 내용이 확인되었습니다. DB 저장 기능은 연결 예정입니다.")
