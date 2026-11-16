import streamlit as st
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from DB.database import get_supabase_client

# ==========================================
# 1. CSS 파일 불러오기
# ==========================================

CSS_PATH = Path(__file__).parent / "chat.css"


def load_chat_css():
    with open(CSS_PATH, encoding="utf-8") as f:
        st.html(f"<style>{f.read()}</style>")


# ==========================================
# 2. 세션 상태 초기화
# ==========================================

def init_chat_state():
    if "selected_room" not in st.session_state:
        st.session_state.selected_room = None


# ==========================================
# 3. 날짜 및 시간 변환
# ==========================================

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


# ==========================================
# 4. 내가 참여한 채팅방 조회
# ==========================================

def get_my_chat_rooms():
    supabase = get_supabase_client()

    user_id = st.session_state.get("user_id")

    if not user_id:
        return []

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


# ==========================================
# 5. 채팅방 정보 및 메시지 조회
# ==========================================

def get_room_info(room_id):
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

    # 현재 사용자가 이 방의 참여자인지 확인
    participants = [
        str(room["user1_id"]),
        str(room["user2_id"]),
    ]

    if user_id not in participants:
        return None

    return room


def get_room_messages(room_id):
    supabase = get_supabase_client()

    response = (
        supabase.table("chats")
        .select("*")
        .eq("room_id", room_id)
        .order("timestamp", desc=False)
        .execute()
    )

    return response.data


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


# ==========================================
# 6. 메시지 저장
# ==========================================

def send_message(room_id, message):
    supabase = get_supabase_client()

    user_id = str(st.session_state.get("user_id"))

    room = get_room_info(room_id)

    if not room:
        raise ValueError("참여 중인 채팅방이 아닙니다.")

    # 상대방 UUID 확인
    if user_id == str(room["user1_id"]):
        receiver_id = room["user2_id"]
    else:
        receiver_id = room["user1_id"]

    # Supabase에 메시지 저장
    response = (
        supabase.table("chats")
        .insert({
            "item_id": room["item_id"],
            "room_id": room_id,
            "user_id": user_id,
            "receiver_id": receiver_id,
            "message": message,
        })
        .execute()
    )

    return response.data


# ==========================================
# 7. 채팅 목록 화면
# ==========================================

def render_chat_list():
    st.title("채팅")
    st.caption("분실물과 습득물에 관한 대화를 확인하세요.")

    st.divider()

    rooms = get_my_chat_rooms()

    if not rooms:
        st.info("참여 중인 채팅방이 없습니다.")
        return

    for room in rooms:
        room_id = room["id"]
        item_id = room["item_id"]

        # 게시글 제목 조회
        title = get_item_title(item_id)

        # 마지막 메시지 조회
        messages = get_room_messages(room_id)

        if messages:
            last_chat = messages[-1]
            message = last_chat["message"]
            timestamp = format_timestamp(
                last_chat["timestamp"]
            )
        else:
            message = "아직 메시지가 없습니다."
            timestamp = format_timestamp(
                room["created_at"]
            )

        # 기존 UI 유지
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
            st.rerun()


# ==========================================
# 8. 채팅방 상세 화면
# ==========================================

def render_chat_room(room_id):

    room = get_room_info(room_id)

    if not room:
        st.warning("채팅방을 찾을 수 없습니다.")

        if st.button("채팅 목록으로"):
            st.session_state.selected_room = None
            st.rerun()
        return

    # 실제 DB 데이터 조회
    messages = get_room_messages(room_id)

    item_title = get_item_title(room["item_id"])
    my_id = str(st.session_state.get("user_id"))

    # 뒤로가기
    if st.button("← 채팅 목록"):
        st.session_state.selected_room = None
        st.rerun()

    st.subheader(f"{item_title}의 채팅방")
    st.divider()

    if not messages:
        st.info("아직 메시지가 없습니다. 첫 메시지를 보내보세요!")

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

    # 메시지 입력
    new_message = st.chat_input("메시지를 입력하세요.")

    if new_message and new_message.strip():
        try:
            send_message(
                room_id,
                new_message.strip()
            )
            st.rerun()

        except Exception as e:
            st.error(f"메시지 전송 실패: {e}")


# ==========================================
# 9. 채팅 메인 함수
# ==========================================

def render_chat():

    init_chat_state()

    load_chat_css()

    try:
        selected_room = st.session_state.selected_room

        if selected_room is None:
            render_chat_list()
        else:
            render_chat_room(selected_room)

    except Exception as e:
        st.error(f"채팅 데이터 조회 실패: {e}")
