import streamlit as st
from postgrest.exceptions import APIError
from DB.database import get_supabase_client
from pathlib import Path
from uuid import uuid4

def load_css(css_path):
    if not css_path.exists():
        st.error(f"CSS 파일을 찾을 수 없습니다: {css_path}")
        return

    with open(css_path, "r", encoding="utf-8") as file:
        st.markdown(
            f"<style>{file.read()}</style>",
            unsafe_allow_html=True
        )

# 부경대학교 대연캠퍼스 구역별 장소 목록
AREA_LOCATIONS = {
    "A구역": [
        "A11 대학본부",
        "A12 웅비관",
        "A13 누리관",
        "A15 향파관",
        "A17 워커하우스",
        "A21 미래관",
        "A22 디자인관",
        "A23 나래관",
        "A26 부산창업카페 2호점",
    ],
    "B구역": [
        "B11 위드센터",
        "B12 나비센터",
        "B13 충무관",
        "B14 환경해양관",
        "B15 자연과학1관",
        "B16 수위실(후문)",
        "B21 가온관",
        "B22 청운관",
    ],
    "C구역": [
        "C11 수산질병관리원",
        "C12 장영실관",
        "C13 해양공동연구관",
        "C14 부경대학교 어린이집",
        "C15 수산과학2관",
        "C21 수산과학관",
        "C22 건축관",
        "C23 호연관",
        "C24 자연과학2관",
        "C25 인문사회경영관",
        "C26 해양수산LMO격리사육동",
        "C27 수조실험동",
        "C28 아름관",
    ],
    "D구역": [
        "D11 행복기숙사",
        "D12 테니스장",
        "D13 대운동장",
        "D14 한울관",
        "D15 창의관",
        "D16 정보융합관",
        "D21 대학극장",
        "D22 체육관",
        "D23 안전관리관",
        "D24 수상레저관",
    ],
    "E구역": [
        "E11 세종1관",
        "E12 세종2관",
        "E13 공학1관",
        "E14 학술정보관",
        "E16 한솔관",
        "E18 한어울터",
        "E21 공학2관",
        "E22 동원 장보고관",
        "E23 부경컨벤션홀",
        "E26 솔동산",
        "E27 양어장",
        "E28 양어장주차장",
        "E29 양어장관리사",
    ],
    "기타 장소": [
        "U 선박공작실",
        "백경광장",
        "잔디밭",
        "정문",
        "후문",
        "교내 보행로",
        "기타",
    ],
}

# 검색 화면에서 사용할 전체 장소 목록
ALL_LOCATIONS = [
    location
    for locations in AREA_LOCATIONS.values()
    for location in locations
]


# 등록·수정 화면에서 공통으로 사용하는 카테고리 및 입력 제한
ITEM_CATEGORIES = [
    "선택해 주세요",
    "전자기기",
    "지갑·카드·신분증",
    "가방·파우치",
    "의류·액세서리",
    "학용품·서적",
    "생활용품·소지품",
    "기타",
]

MAX_PHOTOS = 10
MAX_PHOTO_BYTES = 5 * 1024 * 1024
MAX_TAGS = 15
MAX_TAG_LENGTH = 20
MAX_TITLE_LENGTH = 60
MAX_DESCRIPTION_LENGTH = 1000


# 등록·수정 화면에서 공통으로 사용하는 이미지 설정
IMAGE_BUCKET = "lost-item-images"
MIME_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
}


# 등록·수정 공통 이미지 업로드
def upload_item_image(supabase, item_id, photo):
    ext = Path(photo["name"]).suffix.lower()

    if ext not in MIME_TYPES:
        raise ValueError(
            "지원하지 않는 이미지 형식입니다. (jpg, jpeg, png)"
        )

    image_path = f"{item_id}/{uuid4().hex}{ext}"
    bucket = supabase.storage.from_(IMAGE_BUCKET)
    bucket.upload(
        path=image_path,
        file=photo["bytes"],
        file_options={
            "content-type": MIME_TYPES[ext]
        },
    )

    try:
        response = (
            supabase.table("lost_item_images")
            .insert({
                "lost_item_id": item_id,
                "image_path": image_path,
            })
            .execute()
        )

        if not response.data:
            raise RuntimeError(
                "사진 경로 저장 결과를 확인하지 못했습니다."
            )

    except Exception:
        bucket.remove([image_path])
        raise
    return image_path



# 상세·검색·수정 화면에서 공통으로 사용하는 서명 URL
def get_signed_image_url(supabase, image_path):
    """비공개 Storage 사진 접근용 1시간 유효 URL"""
    response = (
        supabase.storage.from_(IMAGE_BUCKET)
        .create_signed_url(image_path, 3600)
    )
    if isinstance(response, dict):
        return (
            response.get("signedURL")
            or response.get("signedUrl")
            or response.get("signed_url")
        )
    return None


# 상세·수정·검색에서 공통으로 사용하는 게시글/이미지 조회
def get_item_detail(item_id, supabase=None):
    """게시글 ID로 본문 정보 조회"""
    client = supabase if supabase is not None else get_supabase_client()
    response = (
        client.table("lost_items")
        .select("*")
        .eq("id", int(item_id))
        .limit(1)
        .execute()
    )
    return response.data[0] if response.data else None


def get_item_images(item_id, supabase=None):
    """게시글 ID로 사진 경로 조회"""
    client = supabase if supabase is not None else get_supabase_client()
    response = (
        client.table("lost_item_images")
        .select("image_path")
        .eq("lost_item_id", int(item_id))
        .order("id")
        .execute()
    )
    return [
        row["image_path"]
        for row in (response.data or [])
        if row.get("image_path")
    ]


def get_first_item_images(supabase, item_ids):
    """
    여러 게시글의 첫 번째 이미지 경로를 일괄 조회.

    Args:
        supabase: Supabase 클라이언트
        item_ids: 게시글 ID 목록

    Returns:
        dict: {게시글 ID: 첫 번째 이미지 경로}
    """
    if not item_ids:
        return {}

    # 중복 ID 제거
    item_ids = list(dict.fromkeys(item_ids))

    response = (
        supabase.table("lost_item_images")
        .select("lost_item_id, image_path")
        .in_("lost_item_id", item_ids)
        .order("id")
        .execute()
    )

    image_map = {}

    for image in response.data or []:
        item_id = image["lost_item_id"]
        image_path = image.get("image_path")

        if image_path:
            image_map.setdefault(item_id, image_path)

    return image_map


# 게시글 카드 목록의 조회 및 페이지 이동
ITEM_CARD_FIELDS = "id,title,status,category,location,lost_date,lost_item_images(image_path)"


def newest_items_query(supabase):
    """최신 등록순과 게시글별 대표 사진 한 장을 지정합니다."""
    return (
        supabase.table("lost_items")
        .select(ITEM_CARD_FIELDS, count="exact")
        .order("created_at", desc=True)
        .order("id", desc=True)
        .order("id", foreign_table="lost_item_images")
        .limit(1, foreign_table="lost_item_images")
    )


def load_item_page(query, page_key, *, page_size):
    """지정한 개수만 조회하고, 현재 페이지가 사라지면 마지막 페이지로 이동합니다."""
    if type(page_size) is not int or page_size < 1:
        raise ValueError("page_size는 1 이상의 정수여야 합니다.")

    requested_page = page = st.session_state.get(page_key, 1)

    try:
        for _ in range(3):
            start = (page - 1) * page_size
            try:
                response = query.range(start, start + page_size - 1).execute()
            except APIError as exc:
                if exc.code != "PGRST103" or page == 1:
                    raise
                page = 1
                continue

            total = response.count
            last_page = max(1, (total + page_size - 1) // page_size)
            requested_page = min(requested_page, last_page)
            if page == requested_page:
                st.session_state[page_key] = page
                return response.data or [], total, False

            page = requested_page

        raise RuntimeError("페이지 조회 중 게시글 목록이 변경되었습니다.")

    except Exception as exc:
        print(f"게시글 페이지 조회 오류 ({page_key}): {exc}")
        return [], None, True


def render_paginated_item_cards(
    supabase,
    items,
    total,
    load_error,
    *,
    page_key,
    page_size,
    section_key,
    title,
    empty_message,
    description=None,
    bookmark_ids=None,
):
    """조회한 페이지의 카드를 2열로 표시하고 페이지 이동 버튼을 추가합니다."""
    # item_card도 util의 load_css를 사용하므로 호출 시점에 가져옵니다.
    from views.common.item_card import render_item_card

    show_bookmark_button = bookmark_ids is not None
    bookmark_ids = bookmark_ids or set()

    with st.container(key=section_key, border=True):
        with st.container(
            horizontal=True, horizontal_alignment="distribute", vertical_alignment="center"
        ):
            st.subheader(title)

        if description:
            st.caption(description)

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
                        is_bookmarked=item["id"] in bookmark_ids,
                        show_bookmark_button=show_bookmark_button,
                        key_prefix=section_key,
                    )

        _render_item_page_controls(page_key, section_key, total, page_size)


def _render_item_page_controls(page_key, section_key, total, page_size):
    page_count = (total + page_size - 1) // page_size
    if page_count <= 1:
        return

    page = st.session_state[page_key]
    first_item = (page - 1) * page_size + 1
    last_item = min(page * page_size, total)
    first_page_number = max(1, min(page - 2, page_count - 4))
    last_page_number = min(page_count, first_page_number + 4)
    set_page = st.session_state.__setitem__

    with st.container(key=f"item_pagination_{section_key}"):
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
