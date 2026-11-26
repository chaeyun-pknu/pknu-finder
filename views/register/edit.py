from datetime import date
from hashlib import sha256
from pathlib import Path

import streamlit as st

from DB.database import get_supabase_client
from views.common.util import (
    load_css,
    upload_item_image,
    get_signed_image_url,
    get_item_detail,
    get_item_images,
    IMAGE_BUCKET,
    MIME_TYPES,
    AREA_LOCATIONS,
    ITEM_CATEGORIES,
    MAX_DESCRIPTION_LENGTH,
    MAX_PHOTO_BYTES,
    MAX_PHOTOS,
    MAX_TAG_LENGTH,
    MAX_TAGS,
    MAX_TITLE_LENGTH,
)


# ==========================================
# 태그 입력 및 삭제
# ==========================================

def _add_edit_tag(tags_key, input_key):
    value = st.session_state.get(input_key, "").strip().lstrip("#").strip()
    tags = st.session_state[tags_key]

    if not value:
        return
    if len(value) > MAX_TAG_LENGTH:
        st.session_state["edit_tag_message"] = f"태그는 {MAX_TAG_LENGTH}자 이하여야 합니다."
    elif len(tags) >= MAX_TAGS:
        st.session_state["edit_tag_message"] = f"태그는 최대 {MAX_TAGS}개까지 추가할 수 있습니다."
    elif any(tag.casefold() == value.casefold() for tag in tags):
        st.session_state["edit_tag_message"] = "이미 추가된 태그입니다."
    else:
        tags.append(value)
        st.session_state["edit_tag_message"] = ""

    st.session_state[input_key] = ""


def _remove_edit_tag(tags_key, tag):
    if tag in st.session_state[tags_key]:
        st.session_state[tags_key].remove(tag)


def _remove_existing_photo(removed_key, image_path):
    """수정 화면에서만 사진을 숨김. 실제 DB 삭제는 저장할 때 처리."""
    removed = st.session_state[removed_key]
    if image_path not in removed:
        removed.append(image_path)


def _restore_existing_photos(removed_key):
    """저장 전 삭제 예약한 사진을 모두 되돌림."""
    st.session_state[removed_key] = []


def _finish_edit(item_id, version):
    """수정 관련 입력 상태를 정리하고 상세보기로 돌아갈 준비."""
    st.session_state.pop(f"edit_tags_{item_id}_{version}", None)
    st.session_state.pop(f"edit_removed_{item_id}_{version}", None)
    st.session_state.pop("edit_tag_message", None)
    st.session_state["edit_form_version"] = version + 1
    st.session_state["editing_item_id"] = None


# ==========================================
# 입력값 검사 및 Supabase 저장
# ==========================================

def save_edited_item(item_id, item_data, removed_paths, new_files):
    """작성자 확인 → 새 사진 추가 → 본문 수정 → 기존 사진 삭제.

    반환값: 본문은 저장됐으나 사진 정리가 일부 실패한 경우의 경고 목록.
    """
    client = get_supabase_client()
    user_id = st.session_state.get("user_id")
    item = get_item_detail(item_id, client)

    if not user_id or not item or str(item.get("user_id")) != str(user_id):
        raise PermissionError("본인이 작성한 게시글만 수정할 수 있습니다.")

    title = item_data["title"].strip()
    description = item_data["description"].strip()
    tags = item_data["tags"]

    if not title or len(title) > MAX_TITLE_LENGTH:
        raise ValueError(f"제목은 1~{MAX_TITLE_LENGTH}자로 입력해 주세요.")
    if not description or len(description) > MAX_DESCRIPTION_LENGTH:
        raise ValueError(f"상세 설명은 1~{MAX_DESCRIPTION_LENGTH}자로 입력해 주세요.")
    if item_data["status"] not in ("분실", "습득"):
        raise ValueError("등록 유형을 선택해 주세요.")
    if item_data["category"] in ("", "선택해 주세요", None):
        raise ValueError("물품 카테고리를 선택해 주세요.")
    if not item_data["location"]:
        raise ValueError("분실/습득 장소를 선택해 주세요.")
    if len(tags) > MAX_TAGS or any(len(tag) > MAX_TAG_LENGTH for tag in tags):
        raise ValueError("태그 개수 또는 길이가 제한을 초과했습니다.")

    original_paths = get_item_images(item_id, client)
    if len(removed_paths) != len(set(removed_paths)) or not set(removed_paths).issubset(original_paths):
        raise ValueError("사진 목록이 변경되었습니다. 수정 화면을 다시 열어 주세요.")
    if len(original_paths) - len(removed_paths) + len(new_files) > MAX_PHOTOS:
        raise ValueError(f"기존 사진과 새 사진을 합쳐 최대 {MAX_PHOTOS}장까지 가능합니다.")

    photos_to_upload = []
    new_hashes = set()
    for photo in new_files:
        ext = Path(photo.name).suffix.lower()
        contents = photo.getvalue()
        if ext not in MIME_TYPES:
            raise ValueError(f"{photo.name}: JPG/JPEG/PNG 파일만 업로드할 수 있습니다.")
        if len(contents) > MAX_PHOTO_BYTES:
            raise ValueError(f"{photo.name}: 사진은 한 장당 5MB 이하여야 합니다.")
        digest = sha256(contents).hexdigest()
        if digest in new_hashes:
            raise ValueError("추가할 사진 중에 중복된 파일이 있습니다.")
        new_hashes.add(digest)
        photos_to_upload.append({"name": photo.name, "bytes": contents})

    # 공통 이미지 업로드 함수를 사용합니다.
    uploaded_paths = []
    try:
        for photo in photos_to_upload:
            path = upload_item_image(client, int(item_id), photo)
            uploaded_paths.append(path)

        response = (
            client.table("lost_items")
            .update(item_data)
            .eq("id", int(item_id))
            .eq("user_id", str(user_id))
            .execute()
        )
        if not response.data:
            raise RuntimeError("수정된 게시글을 확인하지 못했습니다.")
    except Exception as exc:
        # 본문 저장 실패 시 이번에 추가한 사진만 정리 시도
        cleanup_errors = []
        for path in uploaded_paths:
            try:
                client.table("lost_item_images").delete().eq(
                    "lost_item_id", int(item_id)
                ).eq("image_path", path).execute()
                client.storage.from_(IMAGE_BUCKET).remove([path])
            except Exception as cleanup_exc:
                cleanup_errors.append(str(cleanup_exc))
        if cleanup_errors:
            raise RuntimeError(
                "본문 저장 실패 후 사진 정리에도 문제가 발생했습니다. "
                "Supabase DB와 Storage를 확인해 주세요."
            ) from exc
        raise

    # 본문 UPDATE가 성공한 뒤에만 기존 사진을 삭제합니다.
    warnings = []
    for path in removed_paths:
        try:
            deleted = (
                client.table("lost_item_images")
                .delete()
                .eq("lost_item_id", int(item_id))
                .eq("image_path", path)
                .execute()
            )
            if not deleted.data:
                warnings.append(f"사진 DB 기록 삭제 미확인: {path}")
                continue
            client.storage.from_(IMAGE_BUCKET).remove([path])
        except Exception as exc:
            warnings.append(f"사진 삭제 중 오류: {path} ({exc})")
    return warnings


# ==========================================
# 수정 화면
# ==========================================

def render_edit_item(item_id):
    """상세보기에서 '수정하기' 클릭 시 호출."""
    try:
        client = get_supabase_client()
        item = get_item_detail(item_id, client)
        if not item:
            st.warning("게시글을 찾을 수 없습니다.")
            return
        if str(item.get("user_id")) != str(st.session_state.get("user_id")):
            st.error("본인이 작성한 게시글만 수정할 수 있습니다.")
            return
        old_paths = get_item_images(item_id, client)
    except Exception as exc:
        print(f"게시글 수정 화면 조회 실패: {exc}")
        st.error("게시글 정보를 불러오지 못했습니다.")
        return

    version = st.session_state.get("edit_form_version", 0)
    key = f"edit_{item_id}_{version}"
    tags_key = f"edit_tags_{item_id}_{version}"
    removed_key = f"edit_removed_{item_id}_{version}"
    input_key = f"{key}_tag_input"
    if removed_key not in st.session_state:
        st.session_state[removed_key] = []
    if tags_key not in st.session_state:
        old_tags = item.get("tags") or []
        st.session_state[tags_key] = list(old_tags) if isinstance(old_tags, list) else [str(old_tags)]

    old_location = item.get("location") or ""
    area_options = list(AREA_LOCATIONS.keys())
    old_area = next(
        (area for area, places in AREA_LOCATIONS.items() if old_location in places),
        "기타 장소",
    )
    category_options = list(ITEM_CATEGORIES)
    if item.get("category") and item["category"] not in category_options:
        category_options.append(item["category"])
    current_type = "분실물" if item.get("status") == "분실" else "습득물"
    try:
        old_date = date.fromisoformat(str(item.get("lost_date"))[:10])
    except (ValueError, TypeError):
        old_date = date.today()

    css_path = Path(__file__).with_name("register.css")
    load_css(css_path)

    with st.container(key="register_page"):
        st.markdown("**:blue[PKNU FINDER]**")
        st.title("분실물 · 습득물 수정")
        st.caption("등록된 물품 정보를 변경한 후 저장해 주세요.")
        st.write("")

        with st.container(key="register_card"):
            photo_col, info_col = st.columns([1, 1.15], gap="large")

            with photo_col:
                st.markdown('<div class="register-label">물품 사진</div>', unsafe_allow_html=True)
                st.caption(f"최대 {MAX_PHOTOS}장 · 사진당 5MB 이하")
                # 기존 등록 화면처럼 사진 3열 미리보기 + X 버튼
                removed_paths = st.session_state[removed_key]
                visible_paths = [
                    path for path in old_paths if path not in removed_paths
                ]

                st.markdown(f"**기존 사진 ({len(visible_paths)}장)**")
                if not visible_paths:
                    st.info("현재 표시할 기존 사진이 없습니다.")
                else:
                    preview_cols = st.columns(3, gap="small")
                    for i, path in enumerate(visible_paths):
                        photo_key = sha256(path.encode("utf-8")).hexdigest()[:16]
                        with preview_cols[i % 3]:
                            with st.container(key=f"register_tile_{key}_{photo_key}"):
                                try:
                                    signed_url = get_signed_image_url(client, path)
                                    if signed_url:
                                        st.image(signed_url, width = "stretch")
                                    else:
                                        st.caption("사진 미리보기를 표시할 수 없습니다.")
                                except Exception:
                                    st.caption("사진 미리보기를 표시할 수 없습니다.")

                                with st.container(key=f"photo_delete_{key}_{photo_key}"):
                                    st.button(
                                        "×",
                                        key=f"edit_delete_{key}_{photo_key}",
                                        help="이 사진 삭제 예약",
                                        on_click=_remove_existing_photo,
                                        args=(removed_key, path),
                                    )

                if removed_paths:
                    st.caption(
                        f"기존 사진 {len(removed_paths)}장 삭제 예정 "
                        "(아직 DB에서 삭제되지 않았습니다.)"
                    )
                    st.button(
                        "삭제 취소 (모두 되돌리기)",
                        key=f"{key}_undo_photos",
                        on_click=_restore_existing_photos,
                        args=(removed_key,),
                    )

                st.markdown("**사진 추가**")
                with st.container(key="register_uploader"):
                    new_files = st.file_uploader(
                        "새 사진 업로드",
                        type=["jpg", "jpeg", "png"],
                        accept_multiple_files=True,
                        max_upload_size=5,
                        key=f"{key}_files",
                        label_visibility="collapsed",
                    ) or []
                for photo in new_files:
                    st.image(photo, width=160)
                st.caption(
                    f"유지 {len(old_paths) - len(removed_paths)}장 "
                    f"+ 새 사진 {len(new_files)}장 / 최대 {MAX_PHOTOS}장"
                )

            with info_col:
                title = st.text_input(
                    "게시글 제목 *", value=item.get("title") or "",
                    max_chars=MAX_TITLE_LENGTH, key=f"{key}_title",
                )
                item_type = st.selectbox(
                    "등록 유형 *", ["분실물", "습득물"],
                    index=["분실물", "습득물"].index(current_type),
                    key=f"{key}_type",
                )
                category = st.selectbox(
                    "물품 카테고리 *", category_options,
                    index=category_options.index(item.get("category"))
                    if item.get("category") in category_options else 0,
                    key=f"{key}_category",
                )
                area = st.radio(
                    "1단계 · 구역 선택", area_options,
                    index=area_options.index(old_area), horizontal=True,
                    key=f"{key}_area",
                )
                places = list(AREA_LOCATIONS[area])
                if area == old_area and old_location and old_location not in places:
                    places.append(old_location)
                location = st.selectbox(
                    "2단계 · 분실/습득 장소 *", places,
                    index=places.index(old_location) if old_location in places else None,
                    placeholder="장소를 선택해 주세요",
                    key=f"{key}_place_{area}",
                )
                item_date = st.date_input(
                    "분실/습득 날짜 *", value=min(old_date, date.today()),
                    max_value=date.today(), key=f"{key}_date",
                )

            st.divider()
            st.markdown("#### 관련 태그")
            st.caption(f"최대 {MAX_TAGS}개, 태그당 {MAX_TAG_LENGTH}자 · Enter로 추가")
            st.text_input(
                "태그 추가", placeholder="예) 지갑",
                key=input_key, on_change=_add_edit_tag,
                args=(tags_key, input_key), label_visibility="collapsed",
            )
            if st.session_state.get("edit_tag_message"):
                st.warning(st.session_state["edit_tag_message"])
            with st.container(key="register_tags"):
                with st.container(horizontal=True, horizontal_alignment="left", gap="small"):
                    for index, tag in enumerate(list(st.session_state[tags_key])):
                        st.button(
                            f"#{tag} ×", key=f"{key}_tag_{index}",
                            on_click=_remove_edit_tag, args=(tags_key, tag),
                        )

            st.divider()
            description = st.text_area(
                "상세 설명 *", value=item.get("description") or "",
                height=200, max_chars=MAX_DESCRIPTION_LENGTH,
                key=f"{key}_description",
            )
            save_col, cancel_col = st.columns([3, 1])
            with save_col:
                submitted = st.button(
                    "수정 내용 저장", type="primary", width = "stretch",
                    key=f"{key}_submit",
                )
            with cancel_col:
                canceled = st.button(
                    "취소", width = "stretch", key=f"{key}_cancel",
                )

            if canceled:
                _finish_edit(item_id, version)
                st.rerun()

            if submitted:
                item_data = {
                    "title": title.strip(),
                    "status": "분실" if item_type == "분실물" else "습득",
                    "category": category,
                    "location": location or "",
                    "lost_date": item_date.isoformat(),
                    "description": description.strip(),
                    "tags": list(st.session_state[tags_key]),
                }
                try:
                    warnings = save_edited_item(
                        item_id, item_data, removed_paths, new_files
                    )
                except (ValueError, PermissionError) as exc:
                    st.warning(str(exc))
                except Exception as exc:
                    print(f"게시글 수정 저장 실패: {exc}")
                    st.error(f"수정 도중 오류가 발생했습니다: {exc}")
                else:
                    # 검색 화면에 유지 중인 결과도 함께 갱신
                    results = st.session_state.get("search_results")
                    if isinstance(results, list):
                        for row in results:
                            if str(row.get("id")) == str(item_id):
                                row.update(item_data)
                    _finish_edit(item_id, version)
                    st.session_state["edit_saved"] = True
                    st.session_state["edit_warnings"] = warnings
                    st.rerun()
