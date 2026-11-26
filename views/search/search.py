import streamlit as st
from pathlib import Path

from views.search.search_service import search_items
from DB.database import get_supabase_client
from views.register.detail import (
    get_item_images,
    get_signed_image_url,
)
from views.common.util import AREA_LOCATIONS, ALL_LOCATIONS


# ==========================================
# CSS 불러오기
# ==========================================

def load_search_css():
    css_path = Path(__file__).parent / "search.css"

    try:
        with open(css_path, encoding="utf-8") as css_file:
            st.markdown(
                f"<style>{css_file.read()}</style>",
                unsafe_allow_html=True
            )
    except FileNotFoundError:
        st.warning("search.css 파일을 찾을 수 없습니다.")


# ==========================================
# 검색 필터 옵션
# ==========================================

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

# 페이지당 게시글 수
PAGE_SIZE = 9

# 페이지 번호 최대 표시 개수
PAGE_NUMBER_COUNT = 5


# ==========================================
# 검색 조건 초기화
# ==========================================

def clear_search_filters():
    st.session_state["search_input"] = ""
    st.session_state["search_type"] = "전체"
    st.session_state["search_category"] = "전체"
    st.session_state["search_area"] = "전체"
    st.session_state["search_location"] = "전체"
    st.session_state["search_date_range"] = ()

    st.session_state["search_page"] = 1
    st.session_state["search_page_selector"] = 1

    st.session_state.pop("search_results", None)
    st.session_state.pop("search_total_count", None)
    st.session_state.pop("search_request", None)


# 구역 변경 시 세부 장소 초기화
def reset_search_location():
    st.session_state["search_location"] = "전체"


# 페이지 번호 라디오 변경 시 현재 페이지 갱신
def update_page():
    st.session_state["search_page"] = st.session_state[
        "search_page_selector"
    ]


# ==========================================
# 검색 화면
# ==========================================

def render_search():

    load_search_css()

    st.title("분실물 / 습득물 검색")

    # 페이지 번호 초기화
    if "search_page" not in st.session_state:
        st.session_state["search_page"] = 1

    # ==========================================
    # 1. 검색 유형 선택
    # ==========================================

    search_type = st.radio(
        "검색 유형을 선택하세요.",
        ["전체", "분실물", "습득물"],
        horizontal=True,
        key="search_type"
    )

    # ==========================================
    # 2. 검색창과 검색 버튼
    # ==========================================

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

    # ==========================================
    # 3. 검색 조건 필터
    # ==========================================

    with st.expander("검색 조건 필터"):

        category = st.selectbox(
            "카테고리",
            ITEM_CATEGORIES,
            key="search_category"
        )

        with st.container(border=True):

            st.markdown("### 장소 필터")
            st.caption("1단계 · 구역 선택")

            area_options = ["전체"] + list(AREA_LOCATIONS.keys())

            selected_area = st.radio(
                "구역 선택",
                area_options,
                horizontal=True,
                label_visibility="collapsed",
                key="search_area",
                on_change=reset_search_location
            )

            st.divider()
            st.caption("2단계 · 세부 장소 선택")

            if selected_area == "전체":
                location_options = ["전체", *ALL_LOCATIONS]
            else:
                location_options = [
                    "전체",
                    *AREA_LOCATIONS[selected_area]
                ]

            selected_location = st.selectbox(
                "세부 장소 선택",
                location_options,
                key="search_location",
                label_visibility="collapsed"
            )

        date_range = st.date_input(
            "날짜 범위",
            value=(),
            key="search_date_range",
            help="시작 날짜와 종료 날짜를 선택하세요."
        )

    # ==========================================
    # 4. 날짜 범위 처리
    # ==========================================

    start_date = None
    end_date = None

    if len(date_range) == 2:
        start_date, end_date = date_range
    elif len(date_range) == 1:
        start_date = date_range[0]

    # ==========================================
    # 5. 검색 조건 초기화 버튼
    # ==========================================

    st.button(
        "검색 조건 초기화",
        on_click=clear_search_filters
    )

    # ==========================================
    # 6. 검색 실행
    # ==========================================

    # 최초 진입 시 전체 게시글 조회
    # 검색 버튼을 누르면 현재 조건으로 1페이지부터 조회
    should_search = (
        search_clicked
        or "search_request" not in st.session_state
    )

    if should_search:

        # 새 검색을 시작하므로 이전 결과 제거
        st.session_state.pop("search_results", None)
        st.session_state.pop("search_total_count", None)

        # 날짜 범위 검사
        if (
            start_date is not None
            and end_date is not None
            and start_date > end_date
        ):
            # 잘못된 날짜 조건으로 이전 요청이 실행되지 않도록 제거
            st.session_state.pop("search_request", None)

            st.warning("시작 날짜는 종료 날짜보다 늦을 수 없습니다.")

        else:
            st.session_state["search_page"] = 1
            st.session_state["search_page_selector"] = 1

            st.session_state["search_request"] = {
                "type": search_type,
                "keyword": (keyword or "").strip(),
                "category": category,
                "area": selected_area,
                "location": selected_location,
                "start_date": start_date,
                "end_date": end_date
            }

    # ==========================================
    # 7. 현재 페이지 게시글 조회
    # ==========================================

    if "search_request" in st.session_state:

        request = st.session_state["search_request"]
        current_page = st.session_state["search_page"]

        try:
            results, total_count = search_items(
                keyword=request["keyword"],
                search_type=request["type"],
                category=request["category"],
                area=request["area"],
                location=request["location"],
                start_date=request["start_date"],
                end_date=request["end_date"],
                page=current_page,
                page_size=PAGE_SIZE
            )

            st.session_state["search_results"] = results
            st.session_state["search_total_count"] = total_count

        except Exception as e:
            print(f"검색 오류: {e}")
            st.error(
                "검색 중 문제가 발생했습니다. "
                "잠시 후 다시 시도해 주세요."
            )
            return

    # ==========================================
    # 8. 검색 결과 표시
    # ==========================================

    if "search_results" in st.session_state:

        results = st.session_state["search_results"]
        total_count = st.session_state.get("search_total_count", 0)

        st.subheader("검색 결과")
        st.caption(f"총 {total_count}개의 게시글")

        if not results:
            st.info("검색 결과가 없습니다.")

        else:
            supabase = get_supabase_client()

            # 세로 목록형 게시글 카드
            for item in results:

                with st.container(border=True):

                    image_col, info_col, button_col = st.columns(
                        [1, 5, 1],
                        vertical_alignment="center"
                    )

                    # 게시글 이미지
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
                                        width=150
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

                        st.markdown(
                            f"**{item.get('title', '제목 없음')}**"
                        )

                        st.caption(
                            f"{item.get('status', '정보 없음')} · "
                            f"{item.get('category', '정보 없음')}"
                        )

                        st.write(
                            f"장소: {item.get('location', '정보 없음')}  "
                            f"| 날짜: {item.get('lost_date', '정보 없음')}"
                        )

                        description = (
                            item.get("description") or "설명 없음"
                        )
                        st.write(description)

                    # 상세보기 버튼을 우측 끝에 배치
                    with button_col:

                        if st.button(
                            "상세보기",
                            key=f"search_detail_{item['id']}",
                            use_container_width=True
                        ):
                            st.session_state["selected_item_id"] = item["id"]
                            st.session_state["previous_menu"] = (
                                "분실물/습득물 검색"
                            )
                            st.session_state["current_menu"] = (
                                "게시글 상세보기"
                            )
                            st.rerun()

        # ==========================================
        # 9. 페이지 번호 표시
        # ==========================================

        total_pages = max(
            1,
            (total_count + PAGE_SIZE - 1) // PAGE_SIZE
        )

        if total_pages > 1:

            st.divider()

            current_page = st.session_state["search_page"]

            # 현재 페이지 기준 최대 5개 번호 표시
            start_page = max(
                1,
                current_page - PAGE_NUMBER_COUNT // 2
            )

            end_page = min(
                total_pages,
                start_page + PAGE_NUMBER_COUNT - 1
            )

            start_page = max(
                1,
                end_page - PAGE_NUMBER_COUNT + 1
            )

            page_numbers = list(
                range(start_page, end_page + 1)
            )

            # 페이지 선택값이 현재 표시 범위를 벗어나면 보정
            if (
                st.session_state.get("search_page_selector")
                not in page_numbers
            ):
                st.session_state["search_page_selector"] = current_page

            pagination_cols = st.columns([1, 1, 3, 1, 1])

            # 이전 버튼
            with pagination_cols[1]:
                if st.button(
                    "‹ 이전",
                    key="search_previous_page",
                    disabled=current_page <= 1,
                    use_container_width=True
                ):
                    st.session_state["search_page"] = current_page - 1
                    st.session_state["search_page_selector"] = current_page - 1
                    st.rerun()

            # 페이지 번호: 가운데 열에 배치
            with pagination_cols[2]:
                with st.container(key="search-pagination"):
                    st.radio(
                        "페이지 선택",
                        options=page_numbers,
                        index=page_numbers.index(current_page),
                        horizontal=True,
                        label_visibility="collapsed",
                        key="search_page_selector",
                        on_change=update_page
                    )

            # 다음 버튼
            with pagination_cols[3]:
                if st.button(
                    "다음 ›",
                    key="search_next_page",
                    disabled=current_page >= total_pages,
                    use_container_width=True
                ):
                    st.session_state["search_page"] = current_page + 1
                    st.session_state["search_page_selector"] = current_page + 1
                    st.rerun()