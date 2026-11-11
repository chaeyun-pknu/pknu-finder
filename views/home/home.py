import streamlit as st
from pathlib import Path
from datetime import datetime, timedelta, timezone

from DB.database import get_supabase_client
from views.common.item_card import render_item_card


# --------------------------------------------------
# CSS 불러오기
# --------------------------------------------------

def load_home_css():
    css_path = Path(__file__).parent / "home.css"

    if css_path.exists():
        with open(css_path, "r", encoding="utf-8") as file:
            st.markdown(
                f"<style>{file.read()}</style>",
                unsafe_allow_html=True
            )


# --------------------------------------------------
# 홈 화면
# --------------------------------------------------

def render_home() -> None:
    load_home_css()

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
    with st.container(key="home_recent_items"):
        st.subheader("⏱ 최근 등록된 게시글")
        st.caption("최근 7일 이내 등록된 분실물 및 습득물입니다.")

        try:
            supabase = get_supabase_client()

            # 최근 7일 기준
            one_week_ago = (
                datetime.now(timezone.utc) - timedelta(days=7)
            ).isoformat()

            # 최근 게시글 조회
            item_response = (
                supabase.table("lost_items")
                .select("*")
                .gte("created_at", one_week_ago)
                .order("created_at", desc=True)
                .limit(9)
                .execute()
            )

            items = item_response.data or []

            if not items:
                st.info("최근 7일 동안 등록된 게시글이 없습니다.")
                return

            item_ids = [item["id"] for item in items]

            # 게시글 이미지 경로 조회
            image_response = (
                supabase.table("lost_item_images")
                .select("lost_item_id, image_path, created_at")
                .in_("lost_item_id", item_ids)
                .order("created_at")
                .execute()
            )

            image_map = {}

            for image in image_response.data or []:
                item_id = image["lost_item_id"]

                # 게시글별 첫 번째 이미지 사용
                if item_id not in image_map:
                    image_map[item_id] = image["image_path"]

            # 로그인 사용자 북마크 조회
            user_id = st.session_state.get("user_id")
            bookmark_ids = set()

            if st.session_state.get("logged_in") and user_id:
                bookmark_response = (
                    supabase.table("bookmarks")
                    .select("item_id")
                    .eq("user_id", str(user_id))
                    .in_("item_id", item_ids)
                    .execute()
                )

                bookmark_ids = {
                    row["item_id"]
                    for row in (bookmark_response.data or [])
                }

            # 게시글 카드 출력
            cols = st.columns(3)

            for index, item in enumerate(items):
                item_id = item["id"]

                with cols[index % 3]:
                    render_item_card(
                        supabase=supabase,
                        item=item,
                        image_path=image_map.get(item_id),
                        is_bookmarked=item_id in bookmark_ids,
                        show_bookmark_button=True,
                        key_prefix="home",
                    )

        except Exception as e:
            print(f"최근 게시글 조회 오류: {e}")
            st.error("최근 게시글을 불러오는 중 오류가 발생했습니다.")
