"""
- Supabase SQL Editor에서 public.users 테이블을 먼저 생성해야 합니다.
"""

from __future__ import annotations
from typing import Any
from postgrest.exceptions import APIError
from database import (
    DatabaseOperationError,
    get_supabase_client,
    hash_password,
)

# 회원가입, 
def create_user(username: str, password: str) -> bool:
    if not isinstance(username, str) or not username.strip():
        raise ValueError("아이디를 입력해주세요.")
    if not isinstance(password, str) or not password:
        raise ValueError("비밀번호를 입력해주세요.")

    clean_username = username.strip()

    try:
        response = (
            get_supabase_client()
            .table("users")
            .insert(
                {
                    "username": clean_username,
                    "password": hash_password(password),
                }
            )
            .execute()
        )
        return bool(response.data)
    
    except APIError as exc:
        # 아이디 중복
        if getattr(exc, "code", None) == "23505":
            return False

        # 실제 Supabase 오류 확인
        error_code = getattr(exc, "code", "UNKNOWN")
        error_message = getattr(exc, "message", str(exc))

        raise DatabaseOperationError(
            f"회원가입 실패 (코드: {error_code}): {error_message}"
        ) from exc
    except (ValueError, TypeError):
        raise
    except Exception as exc:
        raise DatabaseOperationError("회원가입 중 Supabase 오류가 발생했습니다.") from exc



# 로그인 확인
def check_login(username: str, password: str) -> int | str | None:
    if not isinstance(username, str) or not username.strip():
        return None
    if not isinstance(password, str) or not password:
        return None

    try:
        response = (
            get_supabase_client()
            .table("users")
            .select("id")
            .eq("username", username.strip())
            .eq("password", hash_password(password))
            .limit(1)
            .execute()
        )
    except Exception as exc:
        raise DatabaseOperationError(
            "로그인 정보를 확인하지 못했습니다. Supabase 연결을 확인해주세요."
        ) from exc

    rows: list[dict[str, Any]] = response.data or []
    if not rows:
        return None
    return rows[0].get("id")


# 회원 탈퇴
def delete_user(user_id: int | str) -> bool:
    if user_id is None or (isinstance(user_id, str) and not user_id.strip()):
        raise ValueError("유효한 사용자 ID가 필요합니다.")

    try:
        response = (
            get_supabase_client()
            .table("users")
            .delete()
            .eq("id", user_id)
            .execute()
        )
    except Exception as exc:
        raise DatabaseOperationError(
            "회원 탈퇴에 실패했습니다. Supabase 연결과 테이블 설정을 확인해주세요."
        ) from exc

    return bool(response.data)