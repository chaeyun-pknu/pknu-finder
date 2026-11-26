import streamlit as st
from datetime import datetime
from pathlib import Path
from html import escape

from DB.database import get_supabase_client, clear_supabase_client
from views.common.util import *
from views.mypage.auth import delete_user


# --------------------------------------------------
# CSS 불러오기
# --------------------------------------------------
css_path = Path(__file__).parent / "mypage.css"
ITEMS_PER_PAGE = 6

# --------------------------------------------------
# 공통 함수
# --------------------------------------------------

def format_date(value):
    if not value:
        return "-"

    try:
        if isinstance(value, str):
            value = datetime.fromisoformat(
                value.replace("Z", "+00:00")
            )

        return value.strftime("%Y.%m.%d")

    except Exception:
        return str(value)[:10]


def get_current_user(supabase):
    try:
        return supabase.auth.get_user().user
    except Exception:
        return None

# --------------------------------------------------
# 마이페이지 메인
# --------------------------------------------------

def render_mypage():
    load_css(css_path)

    with st.container(key="mypage_page"):
        st.markdown("**:blue[PKNU FINDER]**")
        st.title("마이페이지")
        st.caption("PKNU Finder에서의 나의 활동을 확인해 보세요.")

        user_id = st.session_state.get("user_id")

        if not st.session_state.get("logged_in") or not user_id:
            st.warning("마이페이지를 이용하려면 먼저 로그인해주세요.")
            return

        supabase = get_supabase_client()
        auth_user = get_current_user(supabase)

        # 사용자 정보 조회
        try:
            response = (
                supabase.table("users")
                .select("*")
                .eq("id", str(user_id))
                .maybe_single()
                .execute()
            )

            profile = response.data or {}

        except Exception as e:
            print(f"프로필 조회 오류: {e}")
            profile = {}

        session_user = st.session_state.get("user") or {}

        if isinstance(session_user, dict):
            session_username = session_user.get("username")
        else:
            session_username = getattr(
                session_user, "username", None
            )

        username = (
            profile.get("username")
            or session_username
            or "PKNU 사용자"
        )

        email = getattr(auth_user, "email", None) or "-"
        signup_date = format_date(profile.get("created_at"))

        bookmark_page_key = f"mypage_bookmarks_page_{user_id}"
        my_items_page_key = f"mypage_my_items_page_{user_id}"

        # 각 목록의 현재 페이지와 대표 사진만 조회합니다.
        bookmark_query = (
            supabase.table("bookmarks")
            .select(f"id,lost_items!inner({ITEM_CARD_FIELDS})", count="exact")
            .eq("user_id", str(user_id))
            .order("id", desc=True)
            .order("id", foreign_table="lost_items.lost_item_images")
            .limit(1, foreign_table="lost_items.lost_item_images")
        )
        my_items_query = newest_items_query(supabase).eq("user_id", str(user_id))

        bookmark_rows, bookmark_count, bookmark_error = load_item_page(
            bookmark_query, bookmark_page_key, page_size=ITEMS_PER_PAGE
        )
        my_items, item_count, my_items_error = load_item_page(
            my_items_query, my_items_page_key, page_size=ITEMS_PER_PAGE
        )

        render_profile(
            username=username,
            email=email,
            bookmark_count=bookmark_count,
            item_count=item_count,
            signup_date=signup_date,
        )

        bookmarked_items = [row["lost_items"] for row in bookmark_rows]
        render_paginated_item_cards(
            supabase,
            bookmarked_items,
            bookmark_count,
            bookmark_error,
            page_key=bookmark_page_key,
            page_size=ITEMS_PER_PAGE,
            section_key="mypage_bookmarks",
            title="🤍 내가 북마크한 게시글",
            empty_message="아직 북마크한 게시글이 없습니다.",
            bookmark_ids={item["id"] for item in bookmarked_items},
        )
        render_paginated_item_cards(
            supabase,
            my_items,
            item_count,
            my_items_error,
            page_key=my_items_page_key,
            page_size=ITEMS_PER_PAGE,
            section_key="mypage_my_items",
            title="📝 내가 등록한 게시글",
            empty_message="아직 등록한 게시글이 없습니다.",
        )

        # 회원 탈퇴
        render_delete_account_section()


# --------------------------------------------------
# 프로필 + 통계
# --------------------------------------------------

def render_profile(
    username,
    email,
    bookmark_count,
    item_count,
    signup_date,
):
    bookmark_label = f"{bookmark_count}개" if bookmark_count is not None else "-"
    item_label = f"{item_count}개" if item_count is not None else "-"

    with st.container(key="mypage_profile", border=True):
        avatar_col, info_col = st.columns([1, 5])

        with avatar_col:
            st.markdown(
                '<div class="mypage-avatar">●</div>',
                unsafe_allow_html=True
            )

        with info_col:
            st.markdown(
                f"""
                <div class="mypage-name">
                    {escape(str(username))}
                </div>
                <div class="mypage-email">
                    {escape(str(email))}
                </div>
                """,
                unsafe_allow_html=True
            )

        st.divider()

        stat1, stat2, stat3 = st.columns(3)

        with stat1:
            st.markdown(
                f"""
                <div class="mypage-stat">
                    <div class="mypage-stat-label">
                        🤍 북마크한 게시글
                    </div>
                    <div class="mypage-stat-value">
                        {bookmark_label}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        with stat2:
            st.markdown(
                f"""
                <div class="mypage-stat">
                    <div class="mypage-stat-label">
                        📝 등록한 게시글
                    </div>
                    <div class="mypage-stat-value">
                        {item_label}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        with stat3:
            st.markdown(
                f"""
                <div class="mypage-stat">
                    <div class="mypage-stat-label">
                        📅 가입일
                    </div>
                    <div class="mypage-stat-value">
                        {escape(str(signup_date))}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )


# --------------------------------------------------
# 회원 탈퇴
# --------------------------------------------------

def render_delete_account_section():
    with st.container(key="mypage_delete", border=True):
        st.subheader("회원 탈퇴")

        st.warning(
            "회원 탈퇴 시 로그인이 비활성화됩니다.\n\n"
            "- 기존 게시글과 채팅 내역은 유지됩니다.\n"
            "- 작성자 이름은 '탈퇴한 유저'로 표시됩니다.\n"
            "- 기존 북마크는 삭제됩니다.\n"
            "- 탈퇴 후에는 기존 계정으로 로그인할 수 없습니다."
        )

        confirmed = st.checkbox(
            "회원 탈퇴 내용을 확인했으며, 탈퇴에 동의합니다.",
            key="mypage_delete_confirm",
        )

        if st.button(
            "회원 탈퇴",
            type="primary",
            disabled=not confirmed,
            width="content",
            key="mypage_delete_account",
        ):
            user_id = st.session_state.get("user_id")

            if not user_id:
                st.error("로그인 정보를 확인할 수 없습니다.")
                return

            try:
                delete_user(user_id)

                st.session_state["logged_in"] = False
                st.session_state["user_id"] = None
                st.session_state["user"] = None
                st.session_state["current_menu"] = "홈"

                clear_supabase_client()
                st.session_state.pop("supabase_access_token", None)
                st.session_state.pop("supabase_refresh_token", None)

                st.success("회원 탈퇴가 완료되었습니다.")
                st.rerun()

            except Exception as e:
                st.error(f"회원 탈퇴 처리에 실패했습니다: {e}")
