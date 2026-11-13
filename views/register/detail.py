"""PKNU-FINDER 게시글 상세 페이지.

검색/마이페이지에서 show_item_detail(item_id)를 호출합니다.
현재 상세 화면은 조회만 담당하고, 화면 전환/뒤로가기는 호출하는 화면에서 처리합니다.
"""

from html import escape
from pathlib import Path

import streamlit as st
from DB.database import get_supabase_client
from views.mypage.bookmark import *

#===============================
# CSS 불러오기
#===============================
IMAGE_BUCKET = "lost-item-images"
CSS_PATH = Path(__file__).with_name("detail.css")

def _load_css():
    if CSS_PATH.exists():
        st.markdown(
            f"<style>{CSS_PATH.read_text(encoding='utf-8')}</style>",
            unsafe_allow_html=True,
        )

# ==============================
# DB 조회
# =============================#
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

def _read_only_field(label, value):
    """등록 화면 입력 필드와 같은 모양의 읽기 전용 정보"""
    label_text = escape(str(label))
    display_text = escape(str(value)) if value not in (None, "") else "정보 없음"
    st.markdown(
        f'<div class="detail-label">{label_text}</div>'
        f'<div class="detail-value">{display_text}</div>',
        unsafe_allow_html=True,
    )


def show_item_detail(item_id):
    """상세 화면 출력: show_item_detail(게시글ID) 형태로 호출"""
    if item_id is None:
        st.info("상세보기할 게시글이 선택되지 않았습니다.")
        return

    try:
        supabase = get_supabase_client()
        item = get_item_detail(item_id, supabase)
    except (TypeError, ValueError):
        st.warning("올바르지 않은 게시글 번호입니다.")
        return
    except Exception as exc:
        print(f"게시글 조회 오류: {exc}")
        st.error("게시글을 불러오지 못했습니다. 로그인 상태와 DB 연결을 확인해 주세요.")
        return

    if item is None:
        st.warning("해당 게시글을 찾을 수 없습니다.")
        return

    image_urls = []
    try:
        image_paths = get_item_images(item["id"], supabase)
        for image_path in image_paths:
            try:
                url = get_signed_image_url(supabase, image_path)
                if url:
                    image_urls.append(url)
            except Exception as exc:
                print(f"사진 URL 발급 오류 ({image_path}): {exc}")
    except Exception as exc:
        print(f"사진 조회 오류: {exc}")
        st.warning("사진 목록을 불러오지 못했습니다.")

    status = {"분실": "분실물", "습득": "습득물"}.get(
        item.get("status"), item.get("status") or "정보 없음"
    )
    tags = item.get("tags") or []
    if isinstance(tags, str):
        tags = [tags]

    _load_css()

    with st.container(key="detail_page"):
        # 등록 화면과 동일한 상단 헤더
        st.markdown("**:blue[PKNU FINDER]**")
        st.title("분실물 · 습득물 상세")
        st.caption("등록된 물품의 정보를 확인해 주세요.")
        st.write("")

        # 등록 화면의 register_card와 동일한 전체 카드
        with st.container(key="detail_card"):
            photo_col, info_col = st.columns([1, 1.15], gap="large")

            # 왼쪽: 등록 화면 업로드 영역 위치에 사진 출력
            with photo_col:
                st.markdown(
                    '<div class="detail-label">물품 사진</div>',
                    unsafe_allow_html=True,
                )
                st.caption(f"등록 유형 · {status}")

                with st.container(key="detail_photo_box"):
                    if image_urls:
                        image_idx = st.selectbox(
                            "사진 선택",
                            options=list(range(len(image_urls))),
                            format_func=lambda i: f"사진 {i + 1} / {len(image_urls)}",
                            key=f"detail_image_choice_{item['id']}",
                            label_visibility="collapsed" if len(image_urls) == 1 else "visible",
                        ) if len(image_urls) > 1 else 0
                        st.image(
                            image_urls[image_idx],
                            width="stretch",
                        )
                    else:
                        st.markdown(
                            '<div class="detail-photo-empty">등록된 사진이 없습니다.</div>',
                            unsafe_allow_html=True,
                        )

                # 북마크
                button_label = (
                    "❤️ 북마크 해제"
                    if is_bookmarked(item["id"])
                    else "🤍 북마크"
                )
                if st.button(
                    button_label,
                    key=f"detail_bookmark_{item['id']}",
                ):
                    if is_bookmarked(item["id"]):
                        success = delete_bookmark(item['id'])
                        if success:
                            st.toast("북마크를 해제했습니다.")
                        else:
                            st.error("북마크 해제에 실패했습니다.")

                    else:
                        success, message = register_bookmark(item['id'])
                        if success:
                            st.toast(message)
                        else:
                            st.error(message)
                    st.rerun()

            # 오른쪽: 등록 화면의 입력 영역 위치에 읽기 전용 정보
            with info_col:
                _read_only_field("게시글 제목", item.get("title"))
                _read_only_field("등록 유형", status)
                _read_only_field("물품 카테고리", item.get("category"))
                _read_only_field("분실 / 습득 장소", item.get("location"))
                _read_only_field("분실 / 습득 날짜", item.get("lost_date"))

            st.divider()

            # 하단 태그, 설명, 버튼도 등록 화면과 같은 순서
            st.markdown("#### 관련 태그")
            with st.container(key="detail_tags"):
                if tags:
                    tag_html = "".join(
                        f'<span class="detail-tag">#{escape(str(tag).lstrip("#"))}</span>'
                        for tag in tags
                    )
                    st.markdown(
                        f'<div class="detail-tags-row">{tag_html}</div>',
                        unsafe_allow_html=True,
                    )
                else:
                    st.caption("등록된 태그가 없습니다.")

            st.divider()

            st.markdown(
                '<div class="detail-label">상세 설명</div>',
                unsafe_allow_html=True,
            )
            description = escape(str(item.get("description") or "등록된 설명이 없습니다."))
            st.markdown(
                f'<div class="detail-description">{description}</div>',
                unsafe_allow_html=True,
            )

            st.write("")
            with st.container(key="detail_chat_area"):
                st.button(
                    "채팅하기",
                    key=f"detail_chat_{item['id']}",
                    type="primary",
                    use_container_width=True,
                    disabled=True,
                    help="채팅 기능 연동 후 활성화됩니다.",
                )
