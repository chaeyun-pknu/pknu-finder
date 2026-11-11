from DB.database import get_supabase_client
import streamlit as st
from pathlib import Path
from datetime import date
from uuid import uuid4
from hashlib import sha256


# ==========================================
# 등록 화면에서 사용할 물품 카테고리
# ==========================================

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


# ==========================================
# 대연캠퍼스 구역별 장소 목록
# ==========================================

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

def save_register_item(
    title,
    item_type,
    category,
    location,
    item_date,
    description,
    user_id,
    tags
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
        "tags": list(tags)
    }

    response = (
        supabase.table("lost_items")
        .insert(item_data)
        .execute()
    )

    if not response.data:
        raise RuntimeError(
            "게시글 저장 결과를 확인하지 못했습니다."
        )

    return response.data[0]


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

    # 기존 CSS 유지
    css_path = Path(__file__).with_name("register.css")

    st.markdown(
        f"<style>{css_path.read_text(encoding='utf-8')}</style>",
        unsafe_allow_html=True
    )

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
                                    use_container_width=True
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
                    use_container_width=True
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
                        uploaded_paths = []

                        try:

                            # 게시글 정보 저장
                            saved_item = save_register_item(
                                title=title,
                                item_type=item_type,
                                category=category,
                                location=location,
                                item_date=item_date,
                                description=description,
                                user_id=user_id,
                                tags=tags
                            )

                            item_id = saved_item["id"]

                            supabase = get_supabase_client()

                            # 등록된 사진 저장
                            photos_to_save = list(
                                st.session_state.register_photos.values()
                            )

                            for photo in photos_to_save:

                                image_path = upload_item_image(
                                    supabase=supabase,
                                    item_id=item_id,
                                    photo=photo
                                )

                                uploaded_paths.append(
                                    image_path
                                )

                        except Exception as exc:

                            st.error(
                                "등록 처리 중 오류가 발생했습니다."
                            )

                            st.error(str(exc))

                            if saved_item is not None:
                                st.warning(
                                    "게시글은 저장되었지만 사진 저장이 "
                                    "완료되지 않았을 수 있습니다. "
                                    f"게시글 ID: {saved_item['id']}. "
                                    "중복 등록하지 말고 저장 상태를 "
                                    "확인해 주세요."
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
