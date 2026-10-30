import streamlit as st
from pathlib import Path
from datetime import date
from uuid import uuid4


# ==========================================
# 1. 태그 관리 함수
# ==========================================

def add_tag():
    value = st.session_state.get(
        "register_tag_input", ""
    ).strip().lstrip("#").strip()

    if not value:
        return

    tags = st.session_state.register_tags

    if value not in tags and len(tags) < 10:
        tags.append(value)

    st.session_state.register_tag_input = ""


def remove_tag(tag):
    if tag in st.session_state.register_tags:
        st.session_state.register_tags.remove(tag)


# ==========================================
# 2. 사진 관리 함수
# ==========================================

def photo_changed():
    version = st.session_state.register_picker_version
    picker_key = f"register_picker_{version}"

    uploaded_files = st.session_state.get(picker_key) or []

    for photo in uploaded_files:
        photo_id = uuid4().hex

        st.session_state.register_photos[photo_id] = {
            "name": photo.name,
            "bytes": photo.getvalue()
        }

    # 사진 선택 직후 추가하고 업로더 초기화
    st.session_state.register_picker_version += 1


def remove_photo(photo_id):
    st.session_state.register_photos.pop(photo_id, None)


# ==========================================
# 3. 등록 화면 상태 초기화 함수
# ==========================================

def clear_register_state():

    # 등록 화면에서 사용한 세션 상태만 삭제
    keys = [
        key
        for key in list(st.session_state.keys())
        if key.startswith("register_")
        or key.startswith("delete_photo_")
        or key.startswith("photo_delete_")
        or key.startswith("tag_remove_")
    ]

    for key in keys:
        del st.session_state[key]


# ==========================================
# 4. 등록 화면
# ==========================================

def render_register():

    # 세션 상태 초기화
    if "register_tags" not in st.session_state:
        st.session_state.register_tags = []

    if "register_photos" not in st.session_state:
        st.session_state.register_photos = {}

    if "register_picker_version" not in st.session_state:
        st.session_state.register_picker_version = 0

    # ======================================
    # CSS 디자인 파일 불러오기
    # ======================================

    css_path = Path(__file__).with_name("register.css")

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
                    "선택 사항 · 여러 장 등록 가능"
                )

                # 업로드 영역은 항상 맨 위
                with st.container(key="register_uploader"):

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

                # 등록한 사진은 업로드 영역 아래
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
                    placeholder="예) 중앙도서관에서 지갑을 잃어버렸어요",
                    label_visibility="collapsed",
                    key="register_title"
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
                    ["선택해 주세요", "분실물", "습득물"],
                    label_visibility="collapsed",
                    key="register_type"
                )

                # 분실 / 습득 장소
                st.markdown(
                    '<div class="register-label">'
                    '분실 / 습득 장소'
                    '<span class="register-required">*</span>'
                    '</div>',
                    unsafe_allow_html=True
                )

                location = st.text_input(
                    "장소",
                    placeholder="예) 중앙도서관 2층",
                    label_visibility="collapsed",
                    key="register_location"
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
                    key="register_date"
                )

            st.divider()

            # ==============================
            # 태그 입력
            # ==============================

            st.markdown("#### 관련 태그")

            st.caption(
                "단어를 입력하고 Enter를 누르면 추가됩니다."
            )

            st.text_input(
                "태그 입력",
                placeholder="예) 지갑",
                key="register_tag_input",
                on_change=add_tag,
                label_visibility="collapsed"
            )

            tags = st.session_state.register_tags

            with st.container(key="register_tags"):

                # 필요한 너비만 사용하는 가로 컨테이너
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
                label_visibility="collapsed",
                key="register_description"
            )

            st.write("")

            # ==============================
            # 등록 버튼
            # ==============================

            with st.container(key="register_submit"):

                submitted = st.button(
                    "물품 등록하기",
                    type="primary",
                    use_container_width=True
                )

            # ==============================
            # 입력값 검사
            # ==============================

            if submitted:

                if not title.strip():
                    st.warning(
                        "게시글 제목을 입력해 주세요."
                    )

                elif item_type == "선택해 주세요":
                    st.warning(
                        "등록 유형을 선택해 주세요."
                    )

                elif not location.strip():
                    st.warning(
                        "장소를 입력해 주세요."
                    )

                elif not description.strip():
                    st.warning(
                        "상세 설명을 입력해 주세요."
                    )

                else:
                    st.success(
                        "입력 내용 확인 완료!"
                    )

                    st.info(
                        "현재는 등록 UI 테스트 단계입니다."
                    )
