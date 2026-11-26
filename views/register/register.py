from DB.database import get_supabase_client
from views.common.util import (
    AREA_LOCATIONS,
    ALL_LOCATIONS,
    load_css,
    upload_item_image,
    get_item_images,
    IMAGE_BUCKET,
    MIME_TYPES,
    ITEM_CATEGORIES,
    MAX_PHOTOS,
    MAX_PHOTO_BYTES,
    MAX_TAGS,
    MAX_TAG_LENGTH,
    MAX_TITLE_LENGTH,
    MAX_DESCRIPTION_LENGTH,
)
import streamlit as st
from pathlib import Path
from datetime import date
from uuid import uuid4
from hashlib import sha256




# ==========================================
# 등록 제한 및 이미지 설정
# ==========================================

IMAGE_BUCKET = "lost-item-images"

MAX_PHOTOS = 10
MAX_PHOTO_BYTES = 5 * 1024 * 1024

MAX_TAGS = 15
MAX_TAG_LENGTH = 20

MAX_TITLE_LENGTH = 60
MAX_DESCRIPTION_LENGTH = 1000

MIME_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
}


# ==========================================
# Supabase Storage 사진 업로드
# ==========================================

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


# ==========================================
# Supabase 게시글 저장
# ==========================================

class DuplicateSubmissionError(Exception):
    """동일한 등록 요청이 이미 DB에서 처리된 경우."""


def save_register_item(
    title,
    item_type,
    category,
    location,
    item_date,
    description,
    user_id,
    tags,
    submission_id
):

    supabase = get_supabase_client()

    status = {
        "분실물": "분실",
        "습득물": "습득"
    }[item_type]

    item_data = {
        "title": title.strip(),
        "status": status,
        "category": category,
        "location": location.strip(),
        "lost_date": item_date.isoformat(),
        "description": description.strip(),
        "user_id": str(user_id),
        "tags": list(tags),
        "submission_id": str(submission_id),
    }

    response = (
        supabase.table("lost_items")
        .upsert(
            item_data,
            on_conflict="user_id,submission_id",
            ignore_duplicates=True,
            returning="representation",
        )
        .execute()
    )

    if response.data:
        return response.data[0]

    # 재제출이면 현재 사용자의 동일한 요청으로 저장된 게시글을 확인합니다.
    existing = (
        supabase.table("lost_items")
        .select("id")
        .eq("user_id", item_data["user_id"])
        .eq("submission_id", item_data["submission_id"])
        .limit(1)
        .execute()
    )
    if not existing.data:
        raise RuntimeError("게시글 저장 결과를 확인하지 못했습니다.")

    return existing.data[0]


def save_submission_images(supabase, item_id, photos):
    """같은 게시글에 저장된 사진은 건너뛰고 누락된 사진만 추가합니다."""
    if not photos:
        return

    saved_paths = set(get_item_images(item_id, supabase))
    folder = str(item_id)
    bucket = supabase.storage.from_(IMAGE_BUCKET)

    for photo_id, photo in photos:
        ext = Path(photo["name"]).suffix.lower()
        if ext not in MIME_TYPES:
            raise ValueError("지원하지 않는 이미지 형식입니다. (jpg, jpeg, png)")

        # 같은 사진을 재시도해도 같은 Storage 경로를 사용합니다.
        contents = photo["bytes"]
        filename = f"submission-{photo_id}{ext}"
        image_path = f"{folder}/{filename}"
        if image_path in saved_paths:
            continue

        try:
            bucket.upload(
                path=image_path,
                file=contents,
                file_options={"content-type": MIME_TYPES[ext], "upsert": "false"},
            )
        except Exception:
            # Storage에만 파일이 남았거나 다른 실행이 먼저 저장했는지 확인합니다.
            files = bucket.list(folder, {"search": filename, "limit": 1})
            if not any(file.get("name") == filename for file in (files or [])):
                raise

        (
            supabase.table("lost_item_images")
            .upsert(
                {"lost_item_id": item_id, "image_path": image_path},
                on_conflict="lost_item_id,image_path",
                ignore_duplicates=True,
                returning="minimal",
            )
            .execute()
        )
        saved_paths.add(image_path)


# ==========================================
# 태그 추가 및 삭제
# ==========================================

def add_tag():

    version = st.session_state.get(
        "register_form_version", 0
    )

    input_key = f"register_tag_input_{version}"

    value = (
        st.session_state.get(input_key, "")
        .strip()
        .lstrip("#")
        .strip()
    )

    st.session_state["register_tag_feedback"] = ""

    if not value:
        return

    tags = st.session_state.register_tags

    if len(value) > MAX_TAG_LENGTH:
        st.session_state["register_tag_feedback"] = (
            f"태그는 {MAX_TAG_LENGTH}자 이내로 입력해 주세요."
        )

    elif any(
        tag.casefold() == value.casefold()
        for tag in tags
    ):
        st.session_state["register_tag_feedback"] = (
            "이미 추가한 태그입니다."
        )

    elif len(tags) >= MAX_TAGS:
        st.session_state["register_tag_feedback"] = (
            f"태그는 최대 {MAX_TAGS}개까지 추가할 수 있습니다."
        )

    else:
        tags.append(value)

    st.session_state[input_key] = ""


def remove_tag(tag):

    if tag in st.session_state.register_tags:
        st.session_state.register_tags.remove(tag)


# ==========================================
# 사진 추가 및 삭제
# ==========================================

def photo_changed():

    version = st.session_state.register_picker_version
    picker_key = f"register_picker_{version}"

    uploaded_files = (
        st.session_state.get(picker_key) or []
    )

    photos = st.session_state.register_photos
    feedback = []

    existing_hashes = {
        sha256(saved["bytes"]).hexdigest()
        for saved in photos.values()
    }

    for photo in uploaded_files:

        if len(photos) >= MAX_PHOTOS:
            feedback.append(
                f"사진은 최대 {MAX_PHOTOS}장까지 등록할 수 있습니다."
            )
            break

        contents = photo.getvalue()

        if len(contents) > MAX_PHOTO_BYTES:
            feedback.append(
                f"{photo.name}: 사진 한 장은 5MB 이하여야 합니다."
            )
            continue

        photo_hash = sha256(contents).hexdigest()

        if photo_hash in existing_hashes:
            feedback.append(
                f"{photo.name}: 이미 추가한 사진입니다."
            )
            continue

        photo_id = uuid4().hex

        photos[photo_id] = {
            "name": photo.name,
            "bytes": contents
        }

        existing_hashes.add(photo_hash)

    st.session_state["register_photo_feedback"] = list(
        dict.fromkeys(feedback)
    )

    st.session_state.register_picker_version += 1


def remove_photo(photo_id):

    st.session_state.register_photos.pop(
        photo_id, None
    )


# ==========================================
# 등록 완료 후 입력 상태 초기화
# ==========================================

def clear_register_state():

    if "register_form_version" not in st.session_state:
        st.session_state["register_form_version"] = 0

    st.session_state["register_form_version"] += 1

    st.session_state["register_tags"] = []
    st.session_state["register_photos"] = {}

    if "register_picker_version" not in st.session_state:
        st.session_state["register_picker_version"] = 0

    st.session_state["register_picker_version"] += 1

    keep = {
        "register_form_version",
        "register_tags",
        "register_photos",
        "register_picker_version",
    }

    for key in list(st.session_state.keys()):
        if key.startswith("register_") and key not in keep:
            del st.session_state[key]


# ==========================================
# 메인 등록 화면
# ==========================================

def render_register():

    # 세션 초기화
    if "register_form_version" not in st.session_state:
        st.session_state.register_form_version = 0

    if "register_picker_version" not in st.session_state:
        st.session_state.register_picker_version = 0

    if "register_tags" not in st.session_state:
        st.session_state.register_tags = []

    if "register_photos" not in st.session_state:
        st.session_state.register_photos = {}

    # 등록 완료 후 초기화
    if st.session_state.pop(
        "registration_reset_pending", False
    ):
        clear_register_state()

    # 같은 작성 화면에서 재제출할 때 동일한 요청 ID를 사용합니다.
    if "register_submission_id" not in st.session_state:
        st.session_state["register_submission_id"] = str(uuid4())

    registration_success = st.session_state.pop(
        "registration_success", False
    )

    if registration_success:
        st.toast(
            "물품이 정상적으로 등록되었습니다!",
            icon="✅",
            duration="short"
        )

    form_version = st.session_state.register_form_version

    # CSS 불러오기
    css_path = Path(__file__).with_name("register.css")
    load_css(css_path)

    with st.container(key="register_page"):

        st.markdown("**:blue[PKNU FINDER]**")
        st.title("분실물 · 습득물 등록")

        st.caption(
            "잃어버렸거나 발견한 물건의 정보를 등록해 주세요."
        )

        st.write("")

        with st.container(key="register_card"):

            photo_col, info_col = st.columns(
                [1, 1.15],
                gap="large"
            )

            # ==================================
            # 왼쪽: 물품 사진
            # ==================================

            with photo_col:

                st.markdown(
                    '<div class="register-label">'
                    '물품 사진'
                    '</div>',
                    unsafe_allow_html=True
                )

                st.caption(
                    f"선택 사항 · 최대 {MAX_PHOTOS}장 · 사진당 5MB 이하"
                )

                with st.container(key="register_uploader"):

                    picker_key = (
                        f"register_picker_"
                        f"{st.session_state.register_picker_version}"
                    )

                    st.file_uploader(
                        "사진 업로드",
                        type=["jpg", "jpeg", "png"],
                        accept_multiple_files=True,
                        max_upload_size=5,
                        key=picker_key,
                        on_change=photo_changed,
                        label_visibility="collapsed"
                    )

                for message in st.session_state.get(
                    "register_photo_feedback", []
                ):
                    st.warning(message)

                photos = st.session_state.register_photos

                if photos:

                    st.markdown(
                        f"**등록한 사진 ({len(photos)}장)**"
                    )

                    preview_cols = st.columns(
                        3,
                        gap="small"
                    )

                    for i, (photo_id, photo) in enumerate(
                        list(photos.items())
                    ):

                        with preview_cols[i % 3]:

                            with st.container(
                                key=f"register_tile_{photo_id}"
                            ):

                                st.image(
                                    photo["bytes"],
                                    width = "stretch"
                                )

                                with st.container(
                                    key=f"photo_delete_{photo_id}"
                                ):

                                    st.button(
                                        "×",
                                        key=f"delete_photo_{photo_id}",
                                        help="이 사진 삭제",
                                        on_click=remove_photo,
                                        args=(photo_id,)
                                    )

            # ==================================
            # 오른쪽: 게시글 기본 정보
            # ==================================

            with info_col:

                # 게시글 제목
                st.markdown(
                    '<div class="register-label">'
                    '게시글 제목'
                    '<span class="register-required">*</span>'
                    '</div>',
                    unsafe_allow_html=True
                )

                title = st.text_input(
                    "게시글 제목",
                    placeholder=(
                        "예) 중앙도서관에서 지갑을 잃어버렸어요"
                    ),
                    max_chars=MAX_TITLE_LENGTH,
                    label_visibility="collapsed",
                    key=f"register_title_{form_version}"
                )

                st.caption(
                    f"{len(title)}/{MAX_TITLE_LENGTH}자"
                )

                # 등록 유형
                st.markdown(
                    '<div class="register-label">'
                    '등록 유형'
                    '<span class="register-required">*</span>'
                    '</div>',
                    unsafe_allow_html=True
                )

                item_type = st.selectbox(
                    "등록 유형",
                    [
                        "선택해 주세요",
                        "분실물",
                        "습득물"
                    ],
                    label_visibility="collapsed",
                    key=f"register_type_{form_version}",
                    filter_mode=None
                )

                # 물품 카테고리
                st.markdown(
                    '<div class="register-label">'
                    '물품 카테고리'
                    '<span class="register-required">*</span>'
                    '</div>',
                    unsafe_allow_html=True
                )

                category = st.selectbox(
                    "물품 카테고리",
                    ITEM_CATEGORIES,
                    label_visibility="collapsed",
                    key=f"register_category_{form_version}",
                    filter_mode=None
                )

                # ==================================
                # 구역별 장소 선택
                # ==================================

                st.markdown(
                    '<div class="register-label">'
                    '분실 / 습득 장소'
                    '<span class="register-required">*</span>'
                    '</div>',
                    unsafe_allow_html=True
                )

                # 1단계: 구역 선택
                st.caption("1단계 · 구역 선택")

                area = st.radio(
                    "구역 선택",
                    list(AREA_LOCATIONS.keys()),
                    horizontal=True,
                    label_visibility="collapsed",
                    key=f"register_location_area_{form_version}"
                )

                # 선택한 구역의 장소만 표시
                location_options = AREA_LOCATIONS[area]

                # 2단계: 세부 장소
                st.caption("2단계 · 세부 장소 선택")

                location = st.selectbox(
                    "장소",
                    location_options,
                    index=None,
                    placeholder="장소를 선택하세요",
                    label_visibility="collapsed",
                    key=f"register_location_{form_version}_{area}"
                )

                if location:
                    st.caption(
                        f"현재 선택: {area} / {location}"
                    )

                # 분실 / 습득 날짜
                st.markdown(
                    '<div class="register-label">'
                    '분실 / 습득 날짜'
                    '<span class="register-required">*</span>'
                    '</div>',
                    unsafe_allow_html=True
                )

                item_date = st.date_input(
                    "날짜",
                    value=date.today(),
                    max_value=date.today(),
                    label_visibility="collapsed",
                    key=f"register_date_{form_version}"
                )

            st.divider()

            # ==================================
            # 관련 태그
            # ==================================

            st.markdown("#### 관련 태그")

            st.caption(
                f"태그는 최대 {MAX_TAGS}개, 태그당 {MAX_TAG_LENGTH}자까지 "
                "입력할 수 있습니다. Enter를 눌러 추가해 주세요."
            )

            st.text_input(
                "태그 입력",
                placeholder="예) 지갑",
                key=f"register_tag_input_{form_version}",
                on_change=add_tag,
                label_visibility="collapsed"
            )

            tags = st.session_state.register_tags

            st.caption(
                f"등록된 태그: {len(tags)}/{MAX_TAGS}개"
            )

            if st.session_state.get("register_tag_feedback"):
                st.warning(
                    st.session_state["register_tag_feedback"]
                )

            with st.container(key="register_tags"):

                with st.container(
                    horizontal=True,
                    horizontal_alignment="left",
                    gap="small"
                ):

                    for i, tag in enumerate(tags):
                        st.button(
                            f"#{tag} ×",
                            key=f"tag_remove_{i}",
                            on_click=remove_tag,
                            args=(tag,)
                        )

            st.divider()

            # ==================================
            # 상세 설명
            # ==================================

            st.markdown(
                '<div class="register-label">'
                '상세 설명'
                '<span class="register-required">*</span>'
                '</div>',
                unsafe_allow_html=True
            )

            description = st.text_area(
                "상세 설명",
                placeholder=(
                    "물품의 색상, 특징, 분실 또는 습득 상황을 "
                    "자세히 작성해 주세요."
                ),
                height=200,
                max_chars=MAX_DESCRIPTION_LENGTH,
                label_visibility="collapsed",
                key=f"register_description_{form_version}"
            )

            st.caption(
                f"{len(description)}/{MAX_DESCRIPTION_LENGTH}자"
            )

            st.write("")

            # ==================================
            # 등록 버튼
            # ==================================

            with st.container(key="register_submit"):

                submitted = st.button(
                    "물품 등록하기",
                    type="primary",
                    width="stretch",
                    key=f"register_submit_{form_version}",
                )

            # ==================================
            # 입력값 검사
            # ==================================

            if submitted:

                if not title.strip():
                    st.warning(
                        "게시글 제목을 입력해 주세요."
                    )

                elif len(title) > MAX_TITLE_LENGTH:
                    st.warning(
                        f"게시글 제목은 {MAX_TITLE_LENGTH}자 이내로 입력해 주세요."
                    )

                elif item_type == "선택해 주세요":
                    st.warning(
                        "등록 유형을 선택해 주세요."
                    )

                elif category == "선택해 주세요":
                    st.warning(
                        "물품 카테고리를 선택해 주세요."
                    )

                elif not location:
                    st.warning(
                        "장소를 선택해 주세요."
                    )

                elif not description.strip():
                    st.warning(
                        "상세 설명을 입력해 주세요."
                    )

                elif len(description) > MAX_DESCRIPTION_LENGTH:
                    st.warning(
                        f"상세 설명은 {MAX_DESCRIPTION_LENGTH}자 이내로 입력해 주세요."
                    )

                else:

                    user_id = st.session_state.get(
                        "user_id"
                    )

                    if not user_id:
                        st.error(
                            "로그인 사용자 정보를 확인할 수 없습니다. "
                            "다시 로그인해 주세요."
                        )

                    else:

                        saved_item = None

                        try:
                            photos_to_save = list(
                                st.session_state.register_photos.items()
                            )
                            saved_item = save_register_item(
                                title=title,
                                item_type=item_type,
                                category=category,
                                location=location,
                                item_date=item_date,
                                description=description,
                                user_id=user_id,
                                tags=tags,
                                submission_id=st.session_state[
                                    "register_submission_id"
                                ],
                            )

                            save_submission_images(
                                get_supabase_client(), saved_item["id"], photos_to_save
                            )

                        except Exception as exc:

                            st.error(
                                "등록 처리 중 오류가 발생했습니다."
                            )

                            st.error(str(exc))

                            if saved_item is not None:
                                st.warning(
                                    "게시글은 저장되었지만 사진 저장을 마치지 못했습니다. "
                                    f"게시글 ID: {saved_item['id']}. "
                                    "이 화면에서 물품 등록하기를 다시 누르면 남은 사진을 저장합니다."
                                )

                        else:

                            # 등록 성공 메시지 예약
                            st.session_state[
                                "registration_success"
                            ] = True

                            # 입력 폼 초기화 예약
                            st.session_state[
                                "registration_reset_pending"
                            ] = True

                            st.rerun()
