import streamlit as st
from pathlib import Path
from datetime import datetime, timedelta, timezone
from views.common.util import *
from DB.database import get_supabase_client


# --------------------------------------------------
# CSS 불러오기
# --------------------------------------------------
css_path = Path(__file__).parent / "home.css"
ITEMS_PER_PAGE = 6

# --------------------------------------------------
# 홈 화면
# --------------------------------------------------

def render_home() -> None:
    load_css(css_path)

    # 메인 소개 영역
    st.markdown(
        """
        <div class="home-hero">
            <h1 class="home-title">PKNU Finder</h1>
            <p class="home-subtitle">
                부경대학교 학생들을 위한 분실물 찾기 서비스
            </p>
            <p class="home-description">
                잃어버린 물건을 찾고, 습득한 물건의 주인을 찾아주세요.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()
    render_recent_items()


# --------------------------------------------------
# 최근 등록된 게시글
# --------------------------------------------------

def render_recent_items():
    user_id = st.session_state.get("user_id")
    page_key = f"home_recent_items_page_{user_id}"
    bookmark_ids = set()

    try:
        supabase = get_supabase_client()
        one_week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
        query = newest_items_query(supabase).gte("created_at", one_week_ago)
        items, total, load_error = load_item_page(query, page_key, page_size=ITEMS_PER_PAGE)

        if items and st.session_state.get("logged_in") and user_id:
            bookmark_response = (
                supabase.table("bookmarks")
                .select("item_id")
                .eq("user_id", str(user_id))
                .in_("item_id", [item["id"] for item in items])
                .execute()
            )
            bookmark_ids = {row["item_id"] for row in (bookmark_response.data or [])}

    except Exception as exc:
        print(f"최근 게시글 조회 오류: {exc}")
        st.error("최근 게시글을 불러오는 중 오류가 발생했습니다.")
        return

    render_paginated_item_cards(
        supabase,
        items,
        total,
        load_error,
        page_key=page_key,
        page_size=ITEMS_PER_PAGE,
        section_key="home_recent_items",
        title="⏱ 최근 등록된 게시글",
        description="최근 7일 이내 등록된 분실물 및 습득물입니다.",
        empty_message="최근 7일 동안 등록된 게시글이 없습니다.",
        bookmark_ids=bookmark_ids,
    )
