import streamlit as st
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from DB.database import get_supabase_client
import logging

logger = logging.getLogger(__name__)

# 1. CSS 파일 불러오기

CSS_PATH = Path(__file__).parent / "chat.css"

def load_chat_css():
    with open(CSS_PATH, encoding="utf-8") as f:
        st.html(f"<style>{f.read()}</style>")

# 2. 세션 상태 초기화

def init_chat_state():
    if "selected_room" not in st.session_state:
        st.session_state.selected_room = None

    if "chat_send_error" not in st.session_state:
        st.session_state.chat_send_error = None

# 3. 날짜 및 시간 변환

def format_timestamp(timestamp):
    if not timestamp:
        return ""

    try:
        dt = datetime.fromisoformat(
            timestamp.replace("Z", "+00:00")
        )
        dt = dt.astimezone(ZoneInfo("Asia/Seoul"))
        return dt.strftime("%m/%d %H:%M")

    except (ValueError, TypeError):
        return str(timestamp)

# 4. 내가 참여한 채팅방 조회

def get_my_chat_rooms():
    user_id = st.session_state.get("user_id")

    if not user_id:
        return []

    supabase = get_supabase_client()

    response = (
        supabase.table("chat_rooms")
        .select("*")
        .or_(
            f"user1_id.eq.{user_id},user2_id.eq.{user_id}"
        )
        .order("created_at", desc=True)
        .execute()
    )

    return response.data

# 5. 채팅방 정보 및 메시지 조회

def get_room_info(room_id, supabase=None):
    if supabase is None:
        supabase = get_supabase_client()

    user_id = str(st.session_state.get("user_id"))

    response = (
        supabase.table("chat_rooms")
        .select("*")
        .eq("id", room_id)
        .execute()
    )

    if not response.data:
        return None

    room = response.data[0]

    # 현재 사용자가 채팅방 참여자인지 확인
    participants = [
        str(room["user1_id"]),
        str(room["user2_id"]),
    ]

    if user_id not in participants:
        return None

    return room


def get_or_create_chat_room(item_id, owner_id):
    my_id = st.session_state.get("user_id")

    if not my_id:
        raise PermissionError("로그인이 필요합니다.")

    if not owner_id:
        raise ValueError("게시글 작성자를 확인할 수 없습니다.")

    my_id = str(my_id)
    owner_id = str(owner_id)

    if my_id == owner_id:
        raise ValueError("본인 게시글에는 채팅할 수 없습니다.")

    supabase = get_supabase_client()

    # 기존 채팅방 확인
    response = (
        supabase.table("chat_rooms")
        .select("id, user1_id, user2_id")
        .eq("item_id", item_id)
        .or_(
            f"user1_id.eq.{my_id},user2_id.eq.{my_id}"
        )
        .execute()
    )

    for room in response.data:
        participants = {
            str(room["user1_id"]),
            str(room["user2_id"])
        }

        if participants == {my_id, owner_id}:
            return room["id"]

    # 기존 채팅방이 없으면 새로 생성
    response = (
        supabase.table("chat_rooms")
        .insert({
            "item_id": item_id,
            "user1_id": my_id,
            "user2_id": owner_id,
        })
        .execute()
    )

    return response.data[0]["id"]


def get_room_messages(room_id):

    # Supabase 클라이언트 재사용
    supabase = get_supabase_client()

    # 채팅방 참여 여부 확인
    room = get_room_info(room_id, supabase)

    if not room:
        raise PermissionError("접근할 수 없는 채팅방입니다.")

    # 메시지 조회
    response = (
        supabase.table("chats")
        .select("*")
        .eq("room_id", room_id)
        .order("timestamp", desc=False)
        .execute()
    )

    return response.data

def get_last_message(room_id, supabase):
    response = (
        supabase.table("chats")
        .select("message, timestamp")
        .eq("room_id", room_id)
        .order("timestamp", desc=True)
        .limit(1)
        .execute()
    )

    if response.data:
        return response.data[0]

    return None

def get_item_title(item_id):
    supabase = get_supabase_client()

    response = (
        supabase.table("lost_items")
        .select("title")
        .eq("id", item_id)
        .execute()
    )

    if response.data:
        return response.data[0]["title"]

    return f"게시글 #{item_id}"

# 6. 메시지 저장

def send_message(room_id, message):

    # 메시지 입력 검사
    if not isinstance(message, str) or not message.strip():
        raise ValueError("메시지를 입력해 주세요.")

    user_id = st.session_state.get("user_id")

    if not user_id:
        raise PermissionError("로그인이 필요합니다.")

    user_id = str(user_id)
    message = message.strip()

    # Supabase 클라이언트 생성
    supabase = get_supabase_client()

    # 채팅방 정보 조회
    room = get_room_info(room_id, supabase)

    if not room:
        raise PermissionError("참여 중인 채팅방이 아닙니다.")

    # 상대방 UUID 확인
    if user_id == str(room["user1_id"]):
        receiver_id = room["user2_id"]
    else:
        receiver_id = room["user1_id"]

    # 메시지 저장
    response = (
        supabase.table("chats")
        .insert({
            "room_id": room_id,
            "user_id": user_id,
            "receiver_id": receiver_id,
            "message": message,
        })
        .execute()
    )

    return response.data


# 메시지 전송 콜백
def submit_chat_message(room_id):
    message = st.session_state.get("chat_message_input")

    if not message or not message.strip():
        return

    try:
        send_message(room_id, message.strip())
        st.session_state.chat_send_error = None

    except Exception:
        logger.exception("메시지 전송 실패")
        st.session_state.chat_send_error = (
            "메시지 전송에 실패했습니다. 다시 시도해 주세요."
        )


# 7. 채팅 목록 화면

def render_chat_list():
    st.title("채팅")
    st.caption("분실물과 습득물에 관한 대화를 확인하세요.")
    st.divider()

    rooms = get_my_chat_rooms()

    if not rooms:
        st.info("참여 중인 채팅방이 없습니다.")
        return

    # 클라이언트 한 번 생성하여 재사용
    supabase = get_supabase_client()

    for room in rooms:
        room_id = room["id"]
        item_id = room["item_id"]

        title_response = (
            supabase.table("lost_items")
            .select("title")
            .eq("id", item_id)
            .execute()
        )

        if title_response.data:
            title = title_response.data[0]["title"]
        else:
            title = f"게시글 #{item_id}"

        # 마지막 메시지 한 개만 조회
        last_chat = get_last_message(room_id, supabase)

        if last_chat:
            message = last_chat["message"]
            timestamp = format_timestamp(
                last_chat["timestamp"]
            )
        else:
            message = "아직 메시지가 없습니다."
            timestamp = format_timestamp(
                room["created_at"]
            )

        button_label = (
            f"**{title}**\n\n"
            f"{message}\n\n"
            f"{timestamp}"
        )

        if st.button(
            button_label,
            key=f"chat_room_{room_id}",
            use_container_width=True,
        ):
            st.session_state.selected_room = room_id
            st.session_state.chat_send_error = None
            st.rerun()


# 메시지 자동 갱신

@st.fragment(run_every="3s")
def render_messages(room_id):

    try:
        messages = get_room_messages(room_id)
        my_id = str(st.session_state.get("user_id"))

        # 메시지가 없는 경우
        if not messages:
            st.info("아직 메시지가 없습니다. 첫 메시지를 보내보세요!")
            return

        # 메시지 표시
        for chat in messages:

            is_me = str(chat["user_id"]) == my_id
            role = "me" if is_me else "other"

            with st.container(
                key=f"chat-msg-{role}-{chat['id']}"
            ):
                with st.container(
                    key=f"bubble-{chat['id']}"
                ):
                    st.write(chat["message"])

                st.caption(
                    format_timestamp(chat["timestamp"])
                )

    except PermissionError:
        st.warning("채팅 메시지에 접근할 수 없습니다.")

    except Exception:
        logger.exception("채팅 메시지 조회 실패")
        st.error("메시지를 불러오지 못했습니다.")


# 8. 채팅방 상세 화면

def render_chat_room(room_id):

    room = get_room_info(room_id)

    if not room:
        st.warning("채팅방을 찾을 수 없습니다.")

        if st.button("채팅 목록으로"):
            st.session_state.selected_room = None
            st.session_state.chat_send_error = None
            st.rerun()

        return

    # 게시글 제목
    item_title = get_item_title(room["item_id"])

    # 뒤로가기
    if st.button("← 채팅 목록"):
        st.session_state.selected_room = None
        st.session_state.chat_send_error = None
        st.rerun()
        return

    # 채팅방 제목
    st.subheader(f"{item_title}의 채팅방")
    st.divider()

    # 메시지 자동 갱신
    render_messages(room_id)

    # 메시지 전송 오류 표시
    if st.session_state.get("chat_send_error"):
        st.error(st.session_state.chat_send_error)

    # 메시지 입력창 (하단 고정)
    st.chat_input(
        "메시지를 입력하세요.",
        key="chat_message_input",
        on_submit=submit_chat_message,
        args=(room_id,),
    )

# 9. 채팅 메인 함수

def render_chat():

    init_chat_state()
    load_chat_css()

    try:
        selected_room = st.session_state.selected_room

        if selected_room is None:
            render_chat_list()
        else:
            render_chat_room(selected_room)

    except Exception:
        logger.exception("채팅 데이터 조회 실패")
        st.error("채팅 데이터를 불러오지 못했습니다.")
