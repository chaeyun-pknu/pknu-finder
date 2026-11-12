import streamlit as st
from datetime import datetime
from pathlib import Path
from html import escape

from DB.database import get_supabase_client
from views.common.item_card import render_item_card
from views.mypage.bookmark import get_bookmarks
from views.mypage.auth import delete_user


# --------------------------------------------------
# CSS 불러오기
# --------------------------------------------------

def load_mypage_css():
    css_path = Path(__file__).parent / "mypage.css"

    if not css_path.exists():
        st.error(f"CSS 파일을 찾을 수 없습니다: {css_path}")
        return

    with open(css_path, "r", encoding="utf-8") as file:
        st.markdown(
            f"<style>{file.read()}</style>",
            unsafe_allow_html=True
        )


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

#--------------------------------------------------
# 게시글별 첫 번째 이미지 조회
#--------------------------------------------------
def get_item_images(supabase, item_ids):
    if not item_ids:
        return {}

    image_map = {}

    try:
        response = (
            supabase.table("lost_item_images")
            .select("*")
            .in_("lost_item_id", item_ids)
            .order("created_at")
            .execute()
        )

        for image in response.data or []:
            image_map.setdefault(
                image.get("lost_item_id"),
                image.get("image_path")
            )

    except Exception as e:
        print(f"게시글 이미지 조회 오류: {e}")

    return image_map


# --------------------------------------------------
# 마이페이지 메인
# --------------------------------------------------

def render_mypage():
    load_mypage_css()

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

        # 북마크 목록 조회
        bookmarks = get_bookmarks()

        # 내가 등록한 게시글 조회
        try:
            response = (
                supabase.table("lost_items")
                .select("*")
                .eq("user_id", str(user_id))
                .order("created_at", desc=True)
                .execute()
            )

            my_items = response.data or []

        except Exception as e:
            st.error(f"게시글 조회 오류: {e}")
            my_items = []

        # 프로필 및 통계
        render_profile(
            username=username,
            email=email,
            bookmark_count=len(bookmarks),
            item_count=len(my_items),
            signup_date=signup_date,
        )

        # 북마크 게시글
        render_bookmark_section(supabase, bookmarks)

        # 내가 등록한 게시글
        render_my_items_section(supabase, my_items)

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
                        {bookmark_count}개
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
                        {item_count}개
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
# 북마크 게시글
# --------------------------------------------------

def render_bookmark_section(supabase, bookmarks):
    with st.container(key="mypage_bookmarks", border=True):
        st.subheader("🤍 내가 북마크한 게시글")

        if not bookmarks:
            st.info("아직 북마크한 게시글이 없습니다.")
            return

        item_ids = list(dict.fromkeys(
            bookmark["item_id"]
            for bookmark in bookmarks
            if bookmark.get("item_id") is not None
        ))

        if not item_ids:
            st.info("북마크한 게시글이 없습니다.")
            return

        try:
            response = (
                supabase.table("lost_items")
                .select("*")
                .in_("id", item_ids)
                .execute()
            )

            items = response.data or []

        except Exception as e:
            st.error(f"게시글을 불러오지 못했습니다: {e}")
            return

        # 북마크 등록 순서 유지
        item_map = {
            item["id"]: item
            for item in items
        }

        ordered_items = [
            item_map[item_id]
            for item_id in item_ids
            if item_id in item_map
        ]

        if not ordered_items:
            st.info("북마크한 게시글이 없습니다.")
            return

        image_map = get_item_images(
            supabase,
            [item["id"] for item in ordered_items]
        )

        # 공통 게시글 카드 사용
        for start in range(0, min(len(ordered_items), 6), 2):
            cols = st.columns(2)

            for col, item in zip(
                cols,
                ordered_items[start:start + 2]
            ):
                with col:
                    render_item_card(
                        supabase=supabase,
                        item=item,
                        image_path=image_map.get(item["id"]),
                        is_bookmarked=True,
                        show_bookmark_button=True,
                        key_prefix="mypage_bookmark",
                    )

        if len(ordered_items) > 6:
            st.caption(
                f"최근 6개 게시글을 표시하고 있습니다. "
                f"전체 {len(ordered_items)}개"
            )


# --------------------------------------------------
# 내가 등록한 게시글
# --------------------------------------------------

def render_my_items_section(supabase, my_items):
    with st.container(key="mypage_my_items", border=True):
        st.subheader("📝 등록한 게시글")

        if not my_items:
            st.info("아직 등록한 게시글이 없습니다.")
            return

        display_items = my_items[:6]

        image_map = get_item_images(
            supabase,
            [item["id"] for item in display_items]
        )

        cols = st.columns(2)

        for index, item in enumerate(display_items):
            with cols[index % 2]:
                render_item_card(
                    supabase=supabase,
                    item=item,
                    image_path=image_map.get(item["id"]),
                    is_bookmarked=False,
                    show_bookmark_button=False,
                    key_prefix="mypage_my_items",
                )

        if len(my_items) > 6:
            st.caption(
                f"최근 6개 게시글을 표시하고 있습니다. "
                f"전체 {len(my_items)}개"
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

                st.session_state.pop("_supabase_auth_client", None)
                st.session_state.pop("supabase_access_token", None)
                st.session_state.pop("supabase_refresh_token", None)

                st.success("회원 탈퇴가 완료되었습니다.")
                st.rerun()

            except Exception as e:
                st.error(f"회원 탈퇴 처리에 실패했습니다: {e}")
