import streamlit as st

from DB.database import get_supabase_client


def get_current_user_id():
    user_id = st.session_state.get("user_id")

    if not user_id:
        return None

    return str(user_id)

# ============================================
# 북마크 등록
# ============================================
def register_bookmark(item_id: int) -> tuple[bool, str]:
    user_id = get_current_user_id()

    if not user_id:
        return False, "로그인이 필요합니다."

    try:
        supabase = get_supabase_client()

        # 이미 등록된 북마크인지 확인
        existing = (
            supabase.table("bookmarks")
            .select("id")
            .eq("user_id", user_id)
            .eq("item_id", item_id)
            .execute()
        )

        if existing.data:
            return False, "이미 북마크에 등록된 게시글입니다."

        # 북마크 등록
        supabase.table("bookmarks").insert({
            "user_id": user_id,
            "item_id": item_id,
        }).execute()

        return True, "북마크에 추가했습니다."

    except Exception as e:
        print(f"북마크 등록 오류: {e}")
        return False, "북마크 등록에 실패했습니다."


# ============================================
# 북마크 삭제
# ============================================
def delete_bookmark(item_id: int) -> bool:
    user_id = get_current_user_id()

    if not user_id:
        return False

    try:
        supabase = get_supabase_client()

        supabase.table("bookmarks") \
            .delete() \
            .eq("user_id", user_id) \
            .eq("item_id", item_id) \
            .execute()

        return True

    except Exception as e:
        print(f"북마크 삭제 오류: {e}")
        return False

# ============================================
# 북마크 확인
# ============================================
def is_bookmarked(item_id: int) -> bool:
    user_id = get_current_user_id()

    if not user_id:
        return False

    try:
        supabase = get_supabase_client()

        response = (
            supabase.table("bookmarks")
            .select("id")
            .eq("user_id", user_id)
            .eq("item_id", item_id)
            .limit(1)
            .execute()
        )

        return bool(response.data)

    except Exception as e:
        print(f"북마크 확인 오류: {e}")
        return False

# ============================================
# 북마크 목록 조회
# ============================================
def get_bookmarks():
    user_id = get_current_user_id()

    if not user_id:
        return []

    try:
        supabase = get_supabase_client()

        response = (
            supabase.table("bookmarks")
            .select("*")
            .eq("user_id", user_id)
            .order("id", desc=True)
            .execute()
        )

        return response.data or []

    except Exception as e:
        print(f"북마크 목록 조회 오류: {e}")
        return []
