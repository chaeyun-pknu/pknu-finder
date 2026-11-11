import streamlit as st
from DB.database import get_supabase_client
from io import BytesIO
from PIL import Image, ImageOps

#=========================
# 북마크 등록
#=========================
def register_bookmark(item_id: int) -> tuple[bool, str]:

    # 게시글 ID 유효성 검사
    if isinstance(item_id, bool) or not isinstance(item_id, int) or item_id <= 0:
        return False, "올바르지 않은 게시글 ID입니다."

    try:
        supabase = get_supabase_client()

        # 현재 로그인한 사용자 확인
        user_response = supabase.auth.get_user()
        current_user = user_response.user

        if current_user is None:
            return False, "로그인이 필요합니다."

        # 북마크 등록
        supabase.table("bookmarks").insert({"user_id": str(current_user.id), "item_id": item_id}).execute()
        return True, "북마크에 추가했습니다."

    except Exception as e:
        # UNIQUE 제약조건에 의한 중복 등록 확인
        if getattr(e, "code", None) == "23505":
            return False, "이미 북마크에 추가된 게시글입니다."

        print(f"북마크 등록 오류: {e}")
        return False, "북마크 등록 중 오류가 발생했습니다."

#=========================
# 북마크 삭제
#=========================
def delete_bookmark(item_id: int) -> tuple[bool, str]:

    # 게시글 ID 유효성 검사
    if isinstance(item_id, bool) or not isinstance(item_id, int) or item_id <= 0:
        return False, "올바르지 않은 게시글 ID입니다."

    try:
        supabase = get_supabase_client()

        # 현재 로그인한 사용자 확인
        user_response = supabase.auth.get_user()
        current_user = user_response.user

        if current_user is None:
            return False, "로그인이 필요합니다."

        # 북마크 삭제
        supabase.table("bookmarks").delete().eq("user_id", str(current_user.id)).eq("item_id", item_id).execute()
        return True, "북마크에서 삭제했습니다."

    except Exception as e:
        print(f"북마크 삭제 오류: {e}")
        return False, "북마크 삭제 중 오류가 발생했습니다."

#=========================
# 북마크 랜더링
#=========================
def render_bookmarks():

    st.subheader("내가 북마크한 게시글")

    try:
        supabase = get_supabase_client()

        # 현재 로그인 사용자 확인
        user_response = supabase.auth.get_user()
        current_user = user_response.user

        if current_user is None:
            st.warning("로그인이 필요합니다.")
            return

        # 1. 현재 사용자의 북마크 목록 조회
        bookmark_response = (
            supabase.table("bookmarks")
            .select("item_id")
            .eq("user_id", str(current_user.id))
            .order("id", desc=True)
            .execute()
        )

        bookmarks = bookmark_response.data or []

        if not bookmarks:
            st.info("아직 북마크한 게시글이 없습니다.")
            return

        item_ids = [bookmark["item_id"] for bookmark in bookmarks]

        # 2. 북마크한 게시글 정보 조회
        item_response = (
            supabase.table("lost_items")
            .select("*")
            .in_("id", item_ids)
            .execute()
        )

        items = item_response.data or []
        item_map = {item["id"]: item for item in items}

        # 3. 게시글 이미지 조회
        image_response = (
            supabase.table("lost_item_images")
            .select("lost_item_id, image_path, created_at")
            .in_("lost_item_id", item_ids)
            .order("created_at")
            .execute()
        )

        images = image_response.data or []

        # 게시글별 대표 이미지 저장
        image_map = {}

        for image in images:
            item_id = image["lost_item_id"]

            if item_id not in image_map:
                image_map[item_id] = image["image_path"]

        # 4. 북마크 목록 출력
        cols = st.columns(3)

        for index, item_id in enumerate(item_ids):
            item = item_map.get(item_id)

            if item is None:
                continue

            title = item.get("title") or "제목 없음"
            status = item.get("status") or "미분류"
            category = item.get("category") or "미입력"
            location = item.get("location") or "장소 미입력"
            lost_date = item.get("lost_date") or "날짜 미입력"

            # 3개씩 한 줄에 배치
            with cols[index % 3]:
                with st.container(border=True):

                    # 이미지
                    image_path = image_map.get(item_id)

                    if image_path:
                        try:
                            image_data = (
                                supabase.storage
                                .from_("lost-item-images")
                                .download(image_path)
                            )

                            original_image = Image.open(
                                BytesIO(image_data)
                            ).convert("RGB")

                            thumbnail = ImageOps.fit(
                                original_image,
                                (200, 200),
                                method=Image.Resampling.LANCZOS,
                                centering=(0.5, 0.5)
                            )

                            st.image(thumbnail, width="stretch")

                        except Exception as e:
                            print(f"이미지 로드 오류: {e}")
                            st.warning("이미지를 불러오는 중 오류가 발생했습니다.")

                    # 제목
                    st.markdown(f"**{title}**")

                    # 게시글 정보
                    st.caption(f"📁 {status} · {category}")
                    st.caption(f"📍 {location}")
                    st.caption(f"📅 {lost_date}")

                    # 상세보기 / 북마크 삭제 버튼
                    detail_col, bookmark_col = st.columns([1, 1])

                    with detail_col:
                        if st.button(
                            "상세보기",
                            key=f"detail_{item_id}",
                            width="stretch"
                        ):
                            #st.session_state["selected_item_id"] = item_id
                            #st.session_state["current_menu"] = "게시글 상세보기"
                            #st.rerun()
                            st.toast("상세보기 기능은 준비 중입니다.")

                    with bookmark_col:
                        if st.button(
                            "북마크 삭제",
                            key=f"remove_bookmark_{item_id}",
                            help="북마크 삭제",
                            width="stretch"
                        ):
                            try:
                                (
                                    supabase.table("bookmarks")
                                    .delete()
                                    .eq("user_id", str(current_user.id))
                                    .eq("item_id", item_id)
                                    .execute()
                                )

                                st.toast("북마크를 삭제했습니다.")
                                st.rerun()

                            except Exception as e:
                                print(f"북마크 삭제 오류: {e}")
                                st.error("북마크 삭제에 실패했습니다.")

    except Exception as e:
        print(f"북마크 조회 오류: {e}")
        st.error("북마크를 불러오는 중 오류가 발생했습니다.")