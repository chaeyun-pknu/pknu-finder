import hashlib
import sqlite3
from datetime import datetime, timedelta

DB_NAME = "pkunfinder.db" #DB이름 pknufinder.db로 임시 설정함.

# 데이터베이스 테이블 생성 시 필요한 상수
CATEGORIES = ["전자기기", "지갑/카드", "의류", "도서/문구", "기타"] # 카테고리 수정 필요
LOCATIONS = ["인문사회과학대학", "공학관", "중앙도서관", "학생회관", "대운동장", "청운관"] #장소 추가 필요
STATUSES = ["습득", "보관중", "수령완료"]

# 데이터베이스 연결 및 초기화
def get_connection():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

# 데이터베이스 초기화
def init_db():
    with get_connection() as conn:
        cursor = conn.cursor()

        # 유저테이블
        # - id: 유저 고유 번호, 자동 증가
        # - username: 유저 아이디 (중복 불가)
        # - password: 암호화(해싱)된 비밀번호 
        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )"""
        )

        # 분실물 테이블  필요시 한희님/유진님 수정
        # - title: 글 제목 / 물건 이름
        # - description: 상세 설명
        # - category: 물건 카테고리 (전자기기, 지갑/카드 등) 위에서 상수 설정, 추후 드롭바 사용
        # - location: 습득/분실 위치 / 위에서 상수 설정, 추후 드롭바 사용
        # - lost_date: 습득/분실 날짜
        # - status: 상태 (습득, 보관중, 수령완료) / 위에 상수 설정 완료, 드롭바 사용
        # - created_at: 게시글 작성 시각 (기본값: 현재 시간)
        # - user_id: 작성자 ID (users.id 참조 외래키)
        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS lost_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            category TEXT NOT NULL,
            location TEXT,
            lost_date TEXT,
            status TEXT DEFAULT '습득',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        )"""
        )

        # 채팅 테이블  필요 시 채윤님 수정
        # - item_id: 분실물 게시글 ID (lost_items.id 참조)
        # - user_id: 메시지 작성자 ID (users.id 참조)
        # - message: 채팅 내용
        # - timestamp: 전송 시각
        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            message TEXT NOT NULL,
            timestamp TEXT,
            FOREIGN KEY(item_id) REFERENCES lost_items(id) ON DELETE CASCADE,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        )"""
        )

        # 북마크 테이블
        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS bookmarks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            item_id INTEGER NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY(item_id) REFERENCES lost_items(id) ON DELETE CASCADE,
            UNIQUE(user_id, item_id)
        )"""
        )

        conn.commit()

# 사용자 인증 관련 함수
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def get_username(user_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM users WHERE id=?", (user_id,))
        result = cursor.fetchone()
        return result[0] if result else None