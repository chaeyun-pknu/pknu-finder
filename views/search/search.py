import streamlit as st
from views.search.search_service import search_items


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
            placeholder="물품명, 장소 또는 카테고리를 입력하세요.",
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

        keyword = keyword.strip()

        if not keyword:
            st.warning("검색어를 입력해 주세요.")
            return

        # 검색 요청 저장
        st.session_state["search_request"] = {
            "type": search_type,
            "keyword": keyword
        }

        # 4. 실제 Supabase 검색 실행
        try:
            results = search_items(keyword, search_type)

            st.session_state["search_results"] = results

        except Exception as e:
            st.error(f"검색 중 오류가 발생했습니다: {e}")
            return

    # 5. 검색 결과 표시
    if "search_results" in st.session_state:

        results = st.session_state["search_results"]

        st.subheader("검색 결과")

        if not results:
            st.info("검색 결과가 없습니다.")

        else:
            st.success(f"총 {len(results)}개의 결과를 찾았습니다.")

            for item in results:
                with st.container(border=True):
                    st.subheader(item.get("title", "제목 없음"))

                    st.write(
                        f"분류: {item.get('status', '정보 없음')}"
                    )

                    st.write(
                        f"카테고리: {item.get('category', '정보 없음')}"
                    )

                    st.write(
                        f"분실 날짜: {item.get('lost_date', '정보 없음')}"
                    )

                    st.write(
                        item.get("description", "설명 없음")
                    )
