import streamlit as st
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
# 3. 등록 화면
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
    # CSS 디자인
    # ======================================

    st.markdown("""
    <style>

    /* 전체 등록 카드 */
    .st-key-register_card {
        background: #FFFFFF;
        border: 1px solid #E5EAF3;
        border-radius: 20px;
        padding: 28px;
        box-shadow: 0 8px 28px rgba(29,62,108,0.06);
    }

    /* 일반 입력창 */
    .st-key-register_page input:not([type="file"]),
    .st-key-register_page textarea {
        background: #F8FAFD !important;
        border: 1px solid #DFE6F0 !important;
        border-radius: 11px !important;
        color: #17243A !important;
    }

    .st-key-register_page input:focus,
    .st-key-register_page textarea:focus {
        border-color: #2563EB !important;
        box-shadow: 0 0 0 2px rgba(37,99,235,0.12) !important;
    }

    /* 입력 항목 라벨 */
    .register-label {
        color: #334155;
        font-size: 15px;
        font-weight: 600;
        margin-bottom: 8px;
    }

    /* 빨간색 필수 별표 */
    .register-required {
        color: #EF4444;
        font-size: 17px;
        font-weight: 700;
        margin-left: 4px;
    }

    /* 사진 업로드 구역 */
    .st-key-register_uploader
    [data-testid="stFileUploaderDropzone"] {
        background: #F3F7FF;
        border: 2px dashed #AFC8F0;
        border-radius: 16px;
        min-height: 190px;
        cursor: pointer;
        transition: 0.2s ease;
    }

    .st-key-register_uploader
    [data-testid="stFileUploaderDropzone"]:hover {
        border-color: #2563EB;
        background: #EDF4FF;
    }

    .st-key-register_uploader
    [data-testid="stFileUploaderDropzone"] button {
        background: #FFFFFF;
        color: #2563EB;
        border: 1px solid #BDD0EE;
        border-radius: 9px;
    }

    /* 업로드 영역 전체 클릭 */
    .st-key-register_uploader
    [data-testid="stFileUploaderDropzone"] {
        position: relative;
    }

    .st-key-register_uploader
    [data-testid="stFileUploaderDropzone"] input[type="file"] {
        position: absolute !important;
        inset: 0 !important;
        width: 100% !important;
        height: 100% !important;
        opacity: 0 !important;
        cursor: pointer !important;
        z-index: 5 !important;
    }

    /* 사진 카드 */
    [class*="st-key-register_tile_"] {
        position: relative !important;
        border-radius: 12px;
        background: #F1F5F9;
        padding: 5px;
    }

    /* 정사각형 사진 */
    [class*="st-key-register_tile_"]
    [data-testid="stImage"] img {
        width: 100%;
        aspect-ratio: 1 / 1;
        object-fit: cover;
        border-radius: 10px;
        display: block;
    }

    /* 사진 오른쪽 상단 삭제 버튼 */
    [class*="st-key-register_tile_"]
    [class*="st-key-photo_delete_"] {
        position: absolute !important;
        top: 8px !important;
        right: 8px !important;
        z-index: 30 !important;
        width: 30px !important;
    }

    [class*="st-key-register_tile_"]
    [class*="st-key-photo_delete_"] button {
        width: 30px !important;
        height: 30px !important;
        min-height: 30px !important;
        padding: 0 !important;
        background: rgba(15,23,42,0.85) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 50% !important;
        font-size: 19px !important;
        font-weight: 700 !important;
        box-shadow: 0 2px 6px rgba(0,0,0,0.2);
    }

    [class*="st-key-register_tile_"]
    [class*="st-key-photo_delete_"] button:hover {
        background: #EF4444 !important;
        color: #FFFFFF !important;
    }

    /* 태그 영역: 가로 배치, 간격 최소화 */
    .st-key-register_tags [data-testid="stHorizontalBlock"] {
        gap: 6px !important;
    }

    .st-key-register_tags button {
        width: auto !important;
        min-height: 30px !important;
        padding: 4px 10px !important;
        border-radius: 100px !important;
        background: #EFF6FF !important;
        color: #2563EB !important;
        border: 1px solid #D8E7FF !important;
        font-size: 13px !important;
        white-space: nowrap !important;
    }

    .st-key-register_tags button:hover {
        background: #DBEAFE !important;
        border-color: #93C5FD !important;
    }

    /* 등록 버튼 */
    .st-key-register_submit button {
        background: #2563EB !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 12px !important;
        min-height: 52px !important;
        font-weight: 700 !important;
    }

    .st-key-register_submit button:hover {
        background: #1D4ED8 !important;
    }

    </style>
    """, unsafe_allow_html=True)

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
            st.caption("단어를 입력하고 Enter를 누르면 추가됩니다.")

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
                    st.success("입력 내용 확인 완료!")

                    st.info(
                        "현재는 등록 UI 테스트 단계입니다. "
                    )
