import streamlit as st
from DB.database import get_supabase_client


from views.common.item_card import render_item_card
from views.mypage.bookmark import get_bookmarks
from views.mypage.auth import delete_user

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
def render_mypage() -> None:
    st.title("마이페이지")
    st.caption("개인 설정 및 북마크를 확인할 수 있습니다.")

    logged_in = st.session_state.get("logged_in", False)
    user_id = st.session_state.get("user_id")

    if not logged_in or user_id is None:
        st.warning("마이페이지를 이용하려면 먼저 로그인해주세요.")
        return

    st.success("로그인 상태입니다.")
    st.write(f"**사용자 ID: {user_id}님**")

    st.divider()
    render_bookmark_section(supabase=get_supabase_client(), bookmarks=get_bookmarks())
    render_delete_account_section()

# --------------------------------------------------
# 북마크 게시글
# --------------------------------------------------
# 북마크 목록 조회
def render_bookmark_section(supabase, bookmarks):
    with st.container(key="mypage_bookmarks", border=True):
        st.subheader("♡ 내가 북마크한 게시글")

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
# 회원 탈퇴
# --------------------------------------------------
def render_delete_account_section():
    st.divider()
    st.subheader("회원 탈퇴")

    st.warning(
        "회원 탈퇴 시 로그인이 비활성화됩니다.\n\n"
        "- 기존 게시글과 채팅 내역은 유지됩니다.\n"
        "- 작성자 이름은 '탈퇴한 유저'로 표시됩니다.\n"
        "- 기존 북마크는 삭제됩니다.\n"
        "- 탈퇴 후에는 기존 계정으로 로그인할 수 없습니다."
    )

    confirmed = st.checkbox(
        "회원 탈퇴 내용을 확인했으며, 탈퇴에 동의합니다."
    )

    if st.button(
        "회원 탈퇴",
        type="primary",
        disabled=not confirmed,
        use_container_width=False,
    ):
        user_id = st.session_state.get("user_id")

        if not user_id:
            st.error("로그인 정보를 확인할 수 없습니다.")
            return

        try:
            delete_user(user_id)

            # Streamlit 로그인 상태 초기화
            st.session_state["logged_in"] = False
            st.session_state["user_id"] = None
            st.session_state["user"] = None
            st.session_state["current_menu"] = "홈"

            # 인증 클라이언트 세션 정보 제거
            st.session_state.pop("_supabase_auth_client", None)

            st.success("회원 탈퇴가 완료되었습니다.")
            st.rerun()

        except Exception as e:
            st.error(f"회원 탈퇴 처리에 실패했습니다: {e}")   