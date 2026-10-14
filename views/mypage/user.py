import streamlit as st
import sqlite3
from database import get_connection, hash_password

# 회원가입, 로그인, 회원탈퇴 관련 함수

# 회원가입, username과 password를 받아 users 테이블에 저장
def create_user(username, password):
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, hash_password(password)),
            )
            conn.commit()
            return True
    except sqlite3.IntegrityError:
        return False


# 로그인 체크: username과 password가 일치하는지 확인
def check_login(username, password):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id FROM users WHERE username = ? AND password = ?",
            (username, hash_password(password)),
        )
        result = cursor.fetchone()
        return result[0] if result else None

# 회원 탈퇴: PRAGMA foreign_keys = ON 설정으로 users 삭제 시
def delete_user(user_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE id=?", (user_id,))
        conn.commit()