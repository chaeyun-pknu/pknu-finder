import streamlit as st
from datetime import datetime
from pathlib import Path
from html import escape

from postgrest.exceptions import APIError
from DB.database import get_supabase_client, clear_supabase_client
from views.common.item_card import render_item_card
from views.common.util import *
from views.mypage.bookmark import get_bookmarks
from views.mypage.auth import delete_user


# --------------------------------------------------
# CSS 불러오기
# --------------------------------------------------
css_path = Path(__file__).parent / "mypage.css"
ITEMS_PER_PAGE = 6
ITEM_CARD_FIELDS = "id,title,status,category,location,lost_date,lost_item_images(image_path)"

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
        my_items_query = (
            supabase.table("lost_items")
            .select(ITEM_CARD_FIELDS, count="exact")
            .eq("user_id", str(user_id))
            .order("created_at", desc=True)
            .order("id", desc=True)
            .order("id", foreign_table="lost_item_images")
            .limit(1, foreign_table="lost_item_images")
        )

        bookmark_rows, bookmark_count, bookmark_error = load_item_page(
            bookmark_query, bookmark_page_key
        )
        my_items, item_count, my_items_error = load_item_page(
            my_items_query, my_items_page_key
        )

        render_profile(
            username=username,
            email=email,
            bookmark_count=bookmark_count,
            item_count=item_count,
            signup_date=signup_date,
        )

        render_item_section(
            supabase,
            [row["lost_items"] for row in bookmark_rows],
            bookmark_count,
            bookmark_error,
            page_key=bookmark_page_key,
            section_key="mypage_bookmarks",
            title="🤍 내가 북마크한 게시글",
            empty_message="아직 북마크한 게시글이 없습니다.",
            is_bookmark_list=True,
        )
        render_item_section(
            supabase,
            my_items,
            item_count,
            my_items_error,
            page_key=my_items_page_key,
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
# 게시글 목록 및 페이지 이동
# --------------------------------------------------

def load_item_page(query, page_key):
    """삭제로 현재 페이지가 사라졌다면 남아 있는 마지막 페이지를 조회합니다."""
    requested_page = page = st.session_state.get(page_key, 1)

    try:
        for _ in range(3):
            start = (page - 1) * ITEMS_PER_PAGE
            try:
                response = query.range(start, start + ITEMS_PER_PAGE - 1).execute()
            except APIError as exc:
                if exc.code != "PGRST103" or page == 1:
                    raise
                page = 1
                continue

            total = response.count
            last_page = max(1, (total + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)
            requested_page = min(requested_page, last_page)
            if page == requested_page:
                st.session_state[page_key] = page
                return response.data or [], total, False

            page = requested_page

        raise RuntimeError("페이지 조회 중 게시글 목록이 변경되었습니다.")

    except Exception as exc:
        print(f"마이페이지 게시글 조회 오류 ({page_key}): {exc}")
        return [], None, True


def render_item_section(
    supabase,
    items,
    total,
    load_error,
    *,
    page_key,
    section_key,
    title,
    empty_message,
    is_bookmark_list=False,
):
    with st.container(key=section_key, border=True):
        with st.container(
            horizontal=True, horizontal_alignment="distribute", vertical_alignment="center"
        ):
            st.subheader(title)

        if load_error:
            st.error("게시글을 불러오지 못했습니다. 다시 시도해 주세요.")
            return

        if not items:
            st.info(empty_message)
            return

        for start in range(0, len(items), 2):
            for column, item in zip(st.columns(2), items[start:start + 2]):
                images = item.get("lost_item_images") or []
                with column:
                    render_item_card(
                        supabase=supabase,
                        item=item,
                        image_path=images[0]["image_path"] if images else None,
                        is_bookmarked=is_bookmark_list,
                        show_bookmark_button=is_bookmark_list,
                        key_prefix=section_key,
                    )

        render_pagination(page_key, section_key, total)


def render_pagination(page_key, section_key, total):
    page_count = (total + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
    if page_count <= 1:
        return

    page = st.session_state[page_key]
    first_item = (page - 1) * ITEMS_PER_PAGE + 1
    last_item = min(page * ITEMS_PER_PAGE, total)
    first_page_number = max(1, min(page - 2, page_count - 4))
    last_page_number = min(page_count, first_page_number + 4)
    set_page = st.session_state.__setitem__

    with st.container(key=f"{section_key}_pagination"):
        range_column, button_column, _ = st.columns(
            [1, 3, 1], gap="small", vertical_alignment="center"
        )
        with range_column:
            st.caption(f"{first_item}–{last_item} / {total}개")
        with button_column, st.container(
            horizontal=True, horizontal_alignment="center", gap="xsmall"
        ):
            st.button(
                "‹ 이전",
                key=f"{page_key}_prev",
                disabled=page == 1,
                on_click=set_page,
                args=(page_key, page - 1),
            )
            for number in range(first_page_number, last_page_number + 1):
                st.button(
                    str(number),
                    key=f"{page_key}_number_{number}",
                    type="primary" if number == page else "secondary",
                    on_click=set_page,
                    args=(page_key, number),
                )
            st.button(
                "다음 ›",
                key=f"{page_key}_next",
                disabled=page == page_count,
                on_click=set_page,
                args=(page_key, page + 1),
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
