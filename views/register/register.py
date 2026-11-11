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
# 등록 화면에서 사용할 장소 목록
# ==========================================

ITEM_LOCATIONS = [
    "선택해 주세요",
    "중앙도서관",
    "공학관",
    "인문사회관",
    "학생회관",
    "기숙사",
    "강의실",
    "식당",
    "운동장",
]


# ==========================================
# Supabase 사진 저장 설정
# ==========================================

IMAGE_BUCKET = "lost-item-images"

# 등록 화면 입력 제한 (필요하면 이 숫자만 변경)
MAX_PHOTOS = 10
MAX_PHOTO_BYTES = 5 * 1024 * 1024  # 사진 한 장당 5MB
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
# Supabase Storage에 사진 업로드
# ==========================================

def upload_item_image(supabase, item_id, photo):

    # 사진 확장자 확인
    ext = Path(photo["name"]).suffix.lower()

    if ext not in MIME_TYPES:
        raise ValueError(
            "지원하지 않는 이미지 형식입니다. (jpg, jpeg, png)"
        )

    # 파일별 고유 이름 생성
    image_path = f"{item_id}/{uuid4().hex}{ext}"

    bucket = supabase.storage.from_(IMAGE_BUCKET)

    # 1. 실제 사진을 Storage에 업로드
    bucket.upload(
        path=image_path,
        file=photo["bytes"],
        file_options={
            "content-type": MIME_TYPES[ext]
        },
    )

    # 2. 업로드한 사진의 경로를 DB에 저장
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
        # DB 저장 실패 시 Storage에 업로드한 사진 삭제
        bucket.remove([image_path])
        raise

    return image_path


# ==========================================
# Supabase에 게시글 저장
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

    # 등록 유형을 DB 상태 값으로 변환
    status = {
        "분실물": "분실",
        "습득물": "습득"
    }[item_type]

    # Supabase에 저장할 게시글 정보
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
# 1. 태그 관리 함수
# ==========================================

def add_tag():

    # 현재 등록 폼의 태그 입력창 key 확인
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

    # 이전 안내 문구를 새 입력 결과로 갱신
    st.session_state["register_tag_feedback"] = ""

    if not value:
        return

    tags = st.session_state.register_tags

    if len(value) > MAX_TAG_LENGTH:
        st.session_state["register_tag_feedback"] = (
            f"태그는 {MAX_TAG_LENGTH}자 이내로 입력해 주세요."
        )
    elif any(tag.casefold() == value.casefold() for tag in tags):
        st.session_state["register_tag_feedback"] = (
            "이미 추가한 태그입니다."
        )
    elif len(tags) >= MAX_TAGS:
        st.session_state["register_tag_feedback"] = (
            f"태그는 최대 {MAX_TAGS}개까지 추가할 수 있습니다."
        )
    else:
        tags.append(value)

    # 태그 입력창 초기화
    st.session_state[input_key] = ""


def remove_tag(tag):

    if tag in st.session_state.register_tags:
        st.session_state.register_tags.remove(tag)


# ==========================================
# 2. 사진 관리 함수
# ==========================================

def photo_changed():

    version = st.session_state.register_picker_version
    picker_key = f"register_picker_{version}"

    uploaded_files = (
        st.session_state.get(picker_key) or []
    )

    photos = st.session_state.register_photos
    # 사용자에게 보여줄 업로드 검증 메시지
    feedback = []
    existing_hashes = {
        sha256(saved["bytes"]).hexdigest()
        for saved in photos.values()
    }

    for photo in uploaded_files:
        # 허용 장수를 초과한 사진은 추가하지 않음
        if len(photos) >= MAX_PHOTOS:
            feedback.append(f"사진은 최대 {MAX_PHOTOS}장까지 등록할 수 있습니다.")
            break

        contents = photo.getvalue()
        if len(contents) > MAX_PHOTO_BYTES:
            feedback.append(f"{photo.name}: 사진 한 장은 5MB 이하여야 합니다.")
            continue

        # 파일 이름이 달라도 내용이 동일한 사진이면 중복으로 처리
        photo_hash = sha256(contents).hexdigest()
        if photo_hash in existing_hashes:
            feedback.append(f"{photo.name}: 이미 추가한 사진입니다.")
            continue

        photo_id = uuid4().hex
        photos[photo_id] = {
            "name": photo.name,
            "bytes": contents
        }
        existing_hashes.add(photo_hash)

    st.session_state["register_photo_feedback"] = list(dict.fromkeys(feedback))

    # 사진 선택 후 업로더 초기화
    st.session_state.register_picker_version += 1


def remove_photo(photo_id):

    st.session_state.register_photos.pop(
        photo_id, None
    )


# ==========================================
# 3. 등록 화면 상태 초기화 함수
# ==========================================

def clear_register_state():

    # 등록 폼 버전이 없으면 먼저 생성
    # PR 리뷰에서 지적된 KeyError 방지
    if "register_form_version" not in st.session_state:
        st.session_state["register_form_version"] = 0

    # 새로운 입력 폼 생성
    st.session_state["register_form_version"] += 1

    # 태그와 사진 목록 초기화
    st.session_state["register_tags"] = []
    st.session_state["register_photos"] = {}

    # 사진 업로더 버전이 없으면 먼저 생성
    # PR 리뷰에서 지적된 KeyError 방지
    if "register_picker_version" not in st.session_state:
        st.session_state["register_picker_version"] = 0

    # 새로운 사진 업로더 생성
    st.session_state["register_picker_version"] += 1

    # 이전 폼의 위젯 상태 정리
    # 로그인 관련 세션 상태는 건드리지 않음
    keep = {
        "register_form_version",
        "register_tags",
        "register_photos",
        "register_picker_version",
    }

    for key in list(st.session_state.keys()):

        if (
            key.startswith("register_")
            and key not in keep
        ):
            del st.session_state[key]


# ==========================================
# 4. 등록 화면
# ==========================================

def render_register():

    # ======================================
    # 세션 상태 초기화
    # ======================================

    if "register_form_version" not in st.session_state:
        st.session_state.register_form_version = 0

    if "register_picker_version" not in st.session_state:
        st.session_state.register_picker_version = 0

    if "register_tags" not in st.session_state:
        st.session_state.register_tags = []

    if "register_photos" not in st.session_state:
        st.session_state.register_photos = {}

    # ======================================
    # 등록 완료 후 입력값 초기화
    # ======================================

    if st.session_state.pop(
        "registration_reset_pending", False
    ):
        clear_register_state()

    # ======================================
    # 등록 완료 알림
    # ======================================

    registration_success = st.session_state.pop(
        "registration_success", False
    )

    if registration_success:
        st.toast(
            "물품이 정상적으로 등록되었습니다!",
            icon="✅",
            duration="short"
        )

    # 현재 입력 폼 버전
    form_version = (
        st.session_state.register_form_version
    )

    # ======================================
    # CSS 디자인 파일 불러오기
    # ======================================

    css_path = Path(__file__).with_name(
        "register.css"
    )

    st.markdown(
        f"<style>{css_path.read_text(encoding='utf-8')}</style>",
        unsafe_allow_html=True
    )

    # ======================================
    # 페이지 시작
    # ======================================

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

            # ==============================
            # 왼쪽: 사진 등록
            # ==============================

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

                # 업로드 영역
                with st.container(
                    key="register_uploader"
                ):

                    picker_key = (
                        f"register_picker_"
                        f"{st.session_state.register_picker_version}"
                    )

                    st.file_uploader(
                        "사진 업로드",
                        type=["jpg", "jpeg", "png"],
                        accept_multiple_files=True,
                        key=picker_key,
                        on_change=photo_changed,
                        label_visibility="collapsed"
                    )

                for message in st.session_state.get(
                    "register_photo_feedback", []
                ):
                    st.warning(message)

                # 사진 미리보기
                photos = (
                    st.session_state.register_photos
                )

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

            # ==============================
            # 오른쪽: 게시글 기본 정보
            # ==============================

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
                st.caption(f"{len(title)}/{MAX_TITLE_LENGTH}자")

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

                # ==============================
                # 물품 카테고리
                # ==============================

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

                # ==============================
                # 분실 / 습득 장소 드롭다운
                # ==============================

                st.markdown(
                    '<div class="register-label">'
                    '분실 / 습득 장소'
                    '<span class="register-required">*</span>'
                    '</div>',
                    unsafe_allow_html=True
                )

                location = st.selectbox(
                    "장소",
                    ITEM_LOCATIONS,
                    label_visibility="collapsed",
                    key=f"register_location_{form_version}",
                    filter_mode=None
                )

                # ==============================
                # 분실 / 습득 날짜
                # ==============================

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

            # ==============================
            # 태그 입력
            # ==============================

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
            st.caption(f"등록된 태그: {len(tags)}/{MAX_TAGS}개")
            if st.session_state.get("register_tag_feedback"):
                st.warning(st.session_state["register_tag_feedback"])

            with st.container(
                key="register_tags"
            ):

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

            # ==============================
            # 상세 설명
            # ==============================

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
            st.caption(f"{len(description)}/{MAX_DESCRIPTION_LENGTH}자")

            st.write("")

            # ==============================
            # 등록 버튼
            # ==============================

            with st.container(
                key="register_submit"
            ):

                submitted = st.button(
                    "물품 등록하기",
                    type="primary",
                    use_container_width=True
                )

            # ==============================
            # 필수 입력값 검사
            # ==============================

            if submitted:

                if not title.strip():

                    st.warning(
                        "게시글 제목을 입력해 주세요."
                    )

                elif len(title) > MAX_TITLE_LENGTH:

                    st.warning(f"게시글 제목은 {MAX_TITLE_LENGTH}자 이내로 입력해 주세요.")

                elif item_type == "선택해 주세요":

                    st.warning(
                        "등록 유형을 선택해 주세요."
                    )

                elif category == "선택해 주세요":

                    st.warning(
                        "물품 카테고리를 선택해 주세요."
                    )

                elif location == "선택해 주세요":

                    st.warning(
                        "장소를 선택해 주세요."
                    )

                elif not description.strip():

                    st.warning(
                        "상세 설명을 입력해 주세요."
                    )

                elif len(description) > MAX_DESCRIPTION_LENGTH:

                    st.warning(f"상세 설명은 {MAX_DESCRIPTION_LENGTH}자 이내로 입력해 주세요.")

                else:

                    # 현재 로그인한 사용자 ID 확인
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

                            # ==========================
                            # 1. 게시글 기본 정보 저장
                            # ==========================

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

                            # ==========================
                            # 2. Supabase 연결
                            # ==========================

                            supabase = (
                                get_supabase_client()
                            )

                            # ==========================
                            # 3. 사진 저장
                            # ==========================

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

                            # ==========================
                            # 4. 등록 성공
                            # ==========================

                            # 완료 알림 표시 예약
                            st.session_state[
                                "registration_success"
                            ] = True

                            # 전체 입력값 초기화 예약
                            st.session_state[
                                "registration_reset_pending"
                            ] = True

                            # 화면 다시 실행
                            st.rerun()
