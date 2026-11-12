import streamlit as st
from views.search.search_service import search_items
from DB.database import get_supabase_client

from views.register.detail import (
    show_item_detail,
    get_item_images,
    get_signed_image_url
)


# ==========================================
# 검색 필터 옵션
# ==========================================

# 등록 화면의 ITEM_CATEGORIES와 동일하게 유지
ITEM_CATEGORIES = [
    "전체",
    "전자기기",
    "지갑·카드·신분증",
    "가방·파우치",
    "의류·액세서리",
    "학용품·서적",
    "생활용품·소지품",
    "기타",
]

# 장소 선택 옵션
# 등록 화면은 자유 입력이므로 실제 등록 장소에 맞게 조정 가능
ITEM_LOCATIONS = [
    "전체",
    "중앙도서관",
    "공학관",
    "인문사회관",
    "학생회관",
    "기숙사",
    "강의실",
    "식당",
    "운동장",
]


# ==========================================
# 검색 조건 초기화
# ==========================================

def clear_search_filters():

    st.session_state["search_input"] = ""
    st.session_state["search_type"] = "전체"
    st.session_state["search_category"] = "전체"
    st.session_state["search_location"] = "전체"
    st.session_state["search_date_range"] = ()

    st.session_state.pop("search_results", None)
    st.session_state.pop("search_request", None)


# ==========================================
# 검색 화면
# ==========================================

def render_search():

     # 상세 페이지 진입 여부 확인
    if st.session_state.get("selected_item_id"):

        if st.button("← 검색 결과로 돌아가기"):
            st.session_state.pop("selected_item_id")
            st.rerun()

        show_item_detail(
            st.session_state["selected_item_id"]
        )

        return

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

    # 3. 검색 조건 필터
    with st.expander("검색 조건 필터"):

        category = st.selectbox(
            "카테고리",
            ITEM_CATEGORIES,
            key="search_category"
        )

        location = st.selectbox(
            "장소",
            ITEM_LOCATIONS,
            key="search_location"
        )

        date_range = st.date_input(
            "날짜 범위",
            value=(),
            key="search_date_range",
            help="시작 날짜와 종료 날짜를 선택하세요."
        )

    # 4. 날짜 범위 처리
    start_date = None
    end_date = None

    if len(date_range) == 2:
        start_date, end_date = date_range

    elif len(date_range) == 1:
        start_date = date_range[0]

    # 5. 초기화 버튼
    st.button(
        "검색 조건 초기화",
        on_click=clear_search_filters
    )

    # 6. 검색 버튼 클릭 이벤트
    if search_clicked:

        # 이전 검색 결과 초기화
        st.session_state.pop("search_results", None)

        keyword = keyword.strip()

        # 검색 조건이 하나도 없는 경우
        if (
            not keyword
            and search_type == "전체"
            and category == "전체"
            and location == "전체"
            and start_date is None
            and end_date is None
        ):
            st.warning(
                "검색어나 검색 조건을 하나 이상 선택해 주세요."
            )

        # 날짜 범위 검사
        elif (
            start_date is not None
            and end_date is not None
            and start_date > end_date
        ):
            st.warning(
                "시작 날짜는 종료 날짜보다 늦을 수 없습니다."
            )

        else:

            # 검색 요청 저장
            st.session_state["search_request"] = {
                "type": search_type,
                "keyword": keyword,
                "category": category,
                "location": location,
                "start_date": start_date,
                "end_date": end_date
            }

            # 7. 실제 Supabase 검색 실행
            try:

                results = search_items(
                    keyword=keyword,
                    search_type=search_type,
                    category=category,
                    location=location,
                    start_date=start_date,
                    end_date=end_date
                )

                st.session_state["search_results"] = results

            except Exception as e:
                
                print(f"검색 오류: {e}")

                st.error(
                    "검색 중 문제가 발생했습니다. "
                    "잠시 후 다시 시도해 주세요."
                )

                return
            
    # 8. 검색 결과 표시
    if "search_results" in st.session_state:

        results = st.session_state["search_results"]

        st.subheader("검색 결과")

        if not results:
            st.info("검색 결과가 없습니다.")

        else:
            st.success(
                f"총 {len(results)}개의 결과를 찾았습니다."
            )

            supabase = get_supabase_client()

            for item in results:

                with st.container(border=True):

                    image_col, info_col = st.columns([1, 3])

                    # 이미지 표시
                    with image_col:

                        try:
                            image_paths = get_item_images(
                                item["id"],
                                supabase
                            )

                            if image_paths:
                                image_url = get_signed_image_url(
                                    supabase,
                                    image_paths[0]
                                )

                                if image_url:
                                    st.image(
                                        image_url,
                                        use_container_width=True
                                    )
                                else:
                                    st.caption("이미지 없음")

                            else:
                                st.caption("등록된 사진이 없습니다.")

                        except Exception as e:
                            print(f"이미지 조회 오류: {e}")
                            st.caption("이미지를 불러올 수 없습니다.")

                    # 게시글 정보
                    with info_col:

                        st.subheader(
                            item.get("title", "제목 없음")
                        )

                        st.write(
                            f"분류: {item.get('status', '정보 없음')}"
                        )

                        st.write(
                            f"카테고리: {item.get('category', '정보 없음')}"
                        )

                        st.write(
                            f"장소: {item.get('location', '정보 없음')}"
                        )

                        st.write(
                            f"날짜: {item.get('lost_date', '정보 없음')}"
                        )

                        st.write(
                            item.get("description", "설명 없음")
                        )

                        # 상세보기 버튼
                        if st.button(
                            "상세보기",
                            key=f"search_detail_{item['id']}"
                        ):
                            st.session_state["selected_item_id"] = item["id"]
                            st.rerun()