import streamlit as st
from pathlib import Path
from html import escape

from views.mypage.bookmark import (
    register_bookmark,
    delete_bookmark,
)

# ============================================
# CSS 불러오기
# ============================================
def load_item_card_css():
    css_path = Path(__file__).parent / "item_card.css"

    if css_path.exists():
        with open(css_path, "r", encoding="utf-8") as f:
            st.markdown(
                f"<style>{f.read()}</style>",
                unsafe_allow_html=True,
            )

# ===========================================
# 게시글 카드 렌더링
# ===========================================
def get_item_image_url(supabase, image_path):
    if not image_path:
        return None

    try:
        response = (
            supabase.storage
            .from_("lost-item-images")
            .create_signed_url(image_path, 3600)
        )

        return (
            response.get("signedURL")
            or response.get("signedUrl")
        )

    except Exception as e:
        print(f"이미지 로드 오류: {e}")
        return None

# ===========================================
# 게시글 날짜 포맷팅
# ===========================================
def format_item_date(value):
    if not value:
        return "날짜 미입력"

    return str(value)[:10]

# ===========================================
# 게시글 카드 렌더링
# ===========================================
def render_item_card(
    supabase,
    item,
    image_path=None,
    is_bookmarked=False,
    show_bookmark_button=True,
    key_prefix="item",
):
    """
    Args:
        supabase: Supabase 클라이언트
        item: 게시글 데이터
        image_path: 게시글 이미지 경로
        is_bookmarked: 현재 사용자의 북마크 여부
        show_bookmark_button: 북마크 버튼 표시 여부
        key_prefix: Streamlit 버튼 및 컨테이너 고유 키 구분
    """

    load_item_card_css()

    item_id = item["id"]

    title = item.get("title")
    status = item.get("status")
    category = item.get("category")
    location = item.get("location")
    lost_date = format_item_date(item.get("lost_date"))

    image_url = get_item_image_url(supabase, image_path)

    with st.container(
        key=f"{key_prefix}_item_card_{item_id}",
        border=True,
    ):
        # 이미지
        if image_url:
            st.markdown(
                f"""
                <div class="item-card-image-wrapper">
                    <img
                        src="{escape(image_url, quote=True)}"
                        class="item-card-image"
                        alt="게시글 이미지"
                    >
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                """
                <div class="item-card-no-image">
                    🖼️
                </div>
                """,
                unsafe_allow_html=True,
            )

        # 제목
        st.markdown(
            f"""
            <div class="item-card-title">
                {escape(str(title))}
            </div>
            """,
            unsafe_allow_html=True,
        )

        # 등록 유형 및 카테고리
        st.markdown(
            f"""
            <div class="item-card-tags">
                <span class="item-card-tag">
                    {escape(str(status))}
                </span>
                <span class="item-card-tag">
                    {escape(str(category))}
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # 장소
        st.markdown(
            f"""
            <div class="item-card-info">
                📍 {escape(str(location))}
            </div>
            """,
            unsafe_allow_html=True,
        )

        # 날짜
        st.markdown(
            f"""
            <div class="item-card-info">
                📅 {escape(lost_date)}
            </div>
            """,
            unsafe_allow_html=True,
        )

        # 버튼
        if show_bookmark_button:
            detail_col, bookmark_col = st.columns(2)
        else:
            detail_col = st.container()
            bookmark_col = None

        with detail_col:
            if st.button(
                "상세보기",
                key=f"{key_prefix}_detail_{item_id}",
                width="stretch",
            ):
                st.session_state["selected_item_id"] = item_id
                st.session_state["previous_menu"] = st.session_state.get("current_menu", "홈")
                st.session_state["current_menu"] = "게시글 상세보기"
                st.rerun()

        if show_bookmark_button:
            with bookmark_col:
                button_label = (
                    "❤️ 북마크 해제"
                    if is_bookmarked
                    else "🤍 북마크"
                )

                if st.button(
                    button_label,
                    key=f"{key_prefix}_bookmark_{item_id}",
                    width="stretch",
                ):
                    user_id = st.session_state.get("user_id")

                    if not user_id or not st.session_state.get("logged_in"):
                        st.warning("로그인이 필요합니다.")
                        return

                    if is_bookmarked:
                        success = delete_bookmark(item_id)

                        if success:
                            st.toast("북마크를 해제했습니다.")
                        else:
                            st.error("북마크 해제에 실패했습니다.")

                    else:
                        success, message = register_bookmark(item_id)

                        if success:
                            st.toast(message)
                        else:
                            st.error(message)

                    st.rerun()
