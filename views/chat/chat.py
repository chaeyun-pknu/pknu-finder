import streamlit as st
from pathlib import Path
from html import escape

# CSS 파일 경로
CSS_PATH = Path(__file__).parent / "chat.css"

def load_chat_css():
    with open(CSS_PATH, encoding="utf-8") as f:
        st.html(f"<style>{f.read()}</style>")

# ==========================================
# 1. 임시 채팅 데이터
# 추후 Supabase chats 테이블과 연동
# ==========================================

SAMPLE_CHATS = [
    {
        "id": 1,
        "item_id": 1,
        "item_title": "검정 지갑",
        "user_id": "user_a",
        "message": "안녕하세요! 검정 지갑을 습득하셨나요?",
        "timestamp": "14:20",
        "room_id": 1,
    },
    {
        "id": 2,
        "item_id": 1,
        "item_title": "검정 지갑",
        "user_id": "me",
        "message": "네, 도서관 앞에서 발견했어요.",
        "timestamp": "14:21",
        "room_id": 1,
    },
    {
        "id": 3,
        "item_id": 2,
        "item_title": "에어팟 프로",
        "user_id": "user_b",
        "message": "혹시 에어팟을 발견하셨나요?",
        "timestamp": "13:10",
        "room_id": 2,
    },
]


# ==========================================
# 2. 세션 상태 초기화
# ==========================================

def init_chat_state():
    if "selected_room" not in st.session_state:
        st.session_state.selected_room = None

    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = [
            chat.copy() for chat in SAMPLE_CHATS
        ]


# ==========================================
# 3. 채팅 목록 화면
# ==========================================


def render_chat_list():
    st.title("채팅")
    st.caption("분실물과 습득물에 관한 대화를 확인하세요.")

    st.divider()

    messages = st.session_state.chat_messages

    # 임시 채팅방 구성
    rooms = {}

    for chat in messages:
        room_id = chat["room_id"]

        if room_id not in rooms:
            rooms[room_id] = {
                "item_title": chat["item_title"],
                "last_message": chat["message"],
                "timestamp": chat["timestamp"],
            }
        else:
            rooms[room_id]["last_message"] = chat["message"]
            rooms[room_id]["timestamp"] = chat["timestamp"]

    if not rooms:
        st.info("참여 중인 채팅방이 없습니다.")
        return

    
    # 채팅방 목록 표시
    for room_id, room in rooms.items():

        # 버튼 내부에 표시할 내용
        title = room["item_title"]
        message = room["last_message"]
        timestamp = room["timestamp"]

        button_label = (
            f"**{title}**\n\n"
            f"{message}\n\n"
            f"{timestamp}"
        )

        # 채팅방 전체가 하나의 버튼
        if st.button(
            button_label,
            key=f"chat_room_{room_id}",
            use_container_width=True,
        ):
            st.session_state.selected_room = room_id
            st.rerun()


# ==========================================
# 4. 채팅방 상세 화면
# ==========================================

def render_chat_room(room_id):

    messages = [
        chat
        for chat in st.session_state.chat_messages
        if chat["room_id"] == room_id
    ]

    if not messages:
        st.warning("채팅방을 찾을 수 없습니다.")

        if st.button("채팅 목록으로"):
            st.session_state.selected_room = None
            st.rerun()
        return

    item_title = messages[0]["item_title"]

    # 뒤로가기
    if st.button("← 채팅 목록"):
        st.session_state.selected_room = None
        st.rerun()

    st.subheader(f"{item_title}의 채팅방")
    st.divider()


    # 메시지 표시
    for chat in messages:

        is_me = chat["user_id"] == "me"

        # 발신자에 따라 컨테이너 구분
        role = "me" if is_me else "other"

        # 메시지와 시간을 묶는 전체 영역
        with st.container(key=f"chat-msg-{role}-{chat['id']}"):

            # 말풍선 영역
            with st.container(key=f"bubble-{chat['id']}"):
                st.write(chat["message"])

            # 말풍선 밖의 시간
            st.caption(chat["timestamp"])



    # 메시지 입력
    new_message = st.chat_input("메시지를 입력하세요.")

    if new_message:

        new_chat = {
            "id": max(
                chat["id"]
                for chat in st.session_state.chat_messages
            ) + 1,
            "item_id": messages[0]["item_id"],
            "item_title": item_title,
            "user_id": "me",
            "message": new_message,
            "timestamp": "방금",
            "room_id": room_id,
        }

        st.session_state.chat_messages.append(new_chat)
        st.rerun()

#user_id랑 timestamp 임시구현 수정필요

# ==========================================
# 5. 채팅 메인 함수
# ==========================================

def render_chat():

    init_chat_state()

    # 채팅 CSS 적용
    load_chat_css()
    
    selected_room = st.session_state.selected_room

    if selected_room is None:
        render_chat_list()
    else:
        render_chat_room(selected_room)
