import streamlit as st


def render_search():

    st.title("분실물 / 습득물 검색")

    # 1. 검색 유형 선택
    search_type = st.radio(
        "검색 유형을 선택하세요.",
        ["전체", "분실물", "습득물"],
        horizontal=True,
        key="search_type"
    )

    # 2. 검색창과 검색 버튼
    col1, col2 = st.columns([5, 1])

    with col1:
        keyword = st.text_input(
            "검색어",
            placeholder="물품명 또는 장소를 입력하세요.",
            label_visibility="collapsed",
            key="search_input"
        )

    with col2:
        search_clicked = st.button(
            "검색",
            use_container_width=True
        )

    # 3. 검색 버튼 클릭 이벤트
    if search_clicked:

        keyword = keyword.strip() #공백 제거

        if not keyword:
            st.warning("검색어를 입력해 주세요.")
        else:
            # 검색 유형과 검색어 딕셔너리 형태로 저장
            search_request = {
                "type": search_type,
                "keyword": keyword
            }

            st.session_state["search_request"] = search_request #화면이 다시 실행되어도 데이터를 유지하기 위해

            st.success(
                f"{search_type} 검색: {keyword}"
            )

            return search_request

    return None