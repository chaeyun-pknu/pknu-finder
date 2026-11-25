import streamlit as st
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