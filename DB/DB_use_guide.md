# PKNU Finder Supabase 사용 가이드

> **검증 기준:** 이 문서는 2026-11-05을 기준으로 작성되었습니다. 예제는 기초적인 사용법을 설명하며 실제 기능완성을 보장하지 않습니다.

이 문서는 PKNU Finder 프로젝트에 참여하는 팀원/기여자들이 Supabase를 처음 사용하더라도 데이터베이스의 구조를 이해하고, 필요한 데이터를 직접 저장하고 조회할 수 있도록 작성되었습니다.

단순히 코드를 복사하는 것보다 어떤 데이터를 어느 테이블에 저장해야 하는지, 각 데이터가 어떻게 연결되는지 이해하는 것을 목표로 합니다.


------------------------------------------------------------------------

# 목차

1.  [Supabase란?](#1-supabase란)
2.  [Supabase 연결하기](#2-supabase-연결하기)
3.  [PKNU Finder 데이터베이스 구조
    이해하기](#3-pknu-finder-데이터베이스-구조-이해하기)
4.  [데이터베이스 기본 사용법](#4-데이터베이스-기본-사용법)
5.  [분실물 게시글 관리하기](#5-분실물-게시글-관리하기)
6.  [채팅 메시지 관리하기](#6-채팅-메시지-관리하기)
7.  [북마크 관리하기](#7-북마크-관리하기)
8.  [이미지 관리하기](#8-이미지-관리하기)
9.  [데이터 수정 및 삭제하기](#9-데이터-수정-및-삭제하기)
10. [자주 발생하는 오류](#10-자주-발생하는-오류)
11. [팀원들이 기억해야 할 사항](#11-팀원들이-기억해야-할-사항)
12. [참고 문서](#12-참고-자료-references)

------------------------------------------------------------------------

# 1. Supabase란?

## 1-1. Supabase 소개

[Supabase](https://supabase.com/)는 웹이나 앱에서 사용하는 데이터를 저장하고 관리할 수 있도록
도와주는 서비스입니다.

쉽게 말하면 PKNU Finder에서 사용하는 **온라인 데이터베이스**라고
생각하면 됩니다.

예를 들어 PKNU Finder에서 다음과 같은 기능을 제공한다고 가정해
보겠습니다.

- 사용자가 분실물 게시글을 작성한다.
- 다른 사용자가 게시글을 검색한다.
- 게시글에 관심이 있으면 북마크한다.
- 게시글 작성자에게 채팅을 보낸다.
- 게시글에 사진을 첨부한다.

이때 작성한 게시글, 채팅 내용, 북마크 정보 등을 저장할 공간이 필요합니다. 이 역할을 Supabase가 담당합니다.

## 1-2. PKNU Finder에서 Supabase가 하는 일

PKNU Finder에서는 Supabase의 다음 기능을 사용합니다.

| 기능           | 역할                        | PKNU Finder 활용              |
|:---------------|:----------------------------|:------------------------------|
| Database       | 데이터를 저장하고 관리      | 게시글, 사용자, 채팅, 북마크  |
| Authentication | 사용자 인증 및 로그인       | Google, GitHub, 이메일 로그인 |
| Storage        | 이미지와 파일 저장          | 분실물 사진 저장                |
| API            | Python 코드에서 데이터 접근 | 게시글 등록 및 조회 등        |

각 기능의 역할을 구분해서 이해하면 좋습니다.

예를 들어 분실물 사진을 등록한다고 해서 사진 자체를 Database에 넣는 것은 아닙니다.

- 사진 파일: Storage에 저장
- 사진 파일의 위치: Database에 저장

이렇게 역할을 나누어 관리합니다.

## 1-3. Supabase에서 데이터를 관리하는 방법

Supabase Dashboard에 접속하면 Table Editor를 통해 데이터베이스를 확인할 수 있습니다.

여기서는 엑셀과 비슷한 형태로 데이터를 확인할 수 있습니다.

- **Table:** 데이터를 저장하는 표
- **Row:** 표의 한 행. 하나의 데이터
- **Column:** 표의 열. 데이터의 항목
- **Primary Key (PK):** 각 행을 구분하는 고유한 값
- **Foreign Key (FK):** 다른 테이블의 데이터를 연결하는 값

예를 들어 `lost_items` 테이블은 다음과 같은 형태입니다.

| id  | title              | category | location   |
|:----|:-------------------|:---------|:-----------|
| 1   | 검은색 지갑        | 지갑     | 학생회관   |
| 2   | 흰색 에어팟 케이스 | 전자기기 | 도서관     |
| 3   | 파란색 우산        | 우산     | 중앙도서관 |

각 행이 하나의 게시글이고, 각 열은 게시글이 가진 정보를 의미합니다.

------------------------------------------------------------------------

# 2. Supabase 연결하기

## 2-1. 프로젝트 폴더 구조

PKNU Finder에서는 Supabase 연결과 관련된 코드를 `DB` 폴더에서 관리합니다.

``` text
pknu-finder/
│
├── DB/
│   ├── database.py       # Supabase 연결 및 공통 함수
│   ├── database.md       # Supabase 생성·스키마·초기 설정 가이드
│   └── DB_use_guide.md   # Python 코드에서 DB를 사용하는 가이드
│
├── views/
│   ├── register/         # 게시글 등록
│   ├── search/           # 게시글 검색
│   ├── chat/             # 채팅
│   └── mypage/           # 마이페이지
│
├── .streamlit/
│   └── secrets.toml      # Supabase 접속 정보
│
└── main.py
```

## 2-2. Supabase 연결하기

먼저 `DB/database.py`에서 제공하는 `get_supabase_client()` 함수를 가져옵니다.

``` python
from DB.database import get_supabase_client

supabase = get_supabase_client()
```

이제 `supabase`라는 변수를 통해 **로그인한 사용자 권한으로** 데이터베이스에 접근할 수 있습니다. 이 함수는 `SUPABASE_ANON_KEY`로 클라이언트를 만들고 `supabase_access_token`, `supabase_refresh_token`, `user_id` 세션 상태를 검사합니다. **로그인하지 않은 페이지에서 호출하면 실패합니다.**

| 함수 | 키 | 용도 |
|---|---|---|
| `get_supabase_client()` | anon 키 + 로그인 사용자 세션 | 일반 CRUD 및 Storage; 사용자 RLS 적용 |
| `create_auth_client()` | anon 키 | 로그인·회원가입 및 로그인 전 초기화 |
| `get_supabase_admin_client()` | service_role 키 | 엄격하게 제한된 서버 측 관리자 작업; RLS 우회 |

```python
from DB.database import create_auth_client, get_supabase_admin_client

auth_client = create_auth_client()  # 로그인 전 인증
# admin_client = get_supabase_admin_client()  # 인증·관리 목적에 한해 서버에서만
```

관리자 클라이언트를 일반 사용자 CRUD의 편의 수단으로 사용하지 않습니다.


## 2-3. 로그인한 사용자 정보 가져오기

PKNU Finder는 Supabase Authentication을 이용해 로그인 기능을 구현하고
있습니다.

사용자가 로그인하면 Supabase Auth에서 고유한 사용자 ID(UUID)를
발급합니다.

우리 프로젝트에서는 로그인 성공 후 이 UUID를 Streamlit의
`session_state`에 저장해 사용합니다.

``` python
st.session_state["user_id"] = str(user.id)
```
이 코드는 로그인 성공 처리 과정에서 실행됩니다.

게시글을 등록하거나 채팅을 작성할 때는 이미 저장한 UUID를 가져오면 됩니다.

``` python
import streamlit as st

user_id = st.session_state.get("user_id")
```

로그인하지 않은 사용자는 `None`이 반환되므로 다음과 같이 확인합니다.

``` python
if not user_id:
    st.warning("로그인이 필요합니다.")
    st.stop()
```

이후 게시글, 채팅, 북마크 등을 저장할 때 `user_id`를 사용하면 됩니다.

**중요:** `session_state`에 사용자 ID를 저장하는 것과 데이터베이스에서 해당 사용자의 권한을 검증하는 것은 별개입니다. 실제 데이터 수정 및 삭제 시에는 서버에서도 권한을 확인이 필요합니다.
현재 `get_supabase_client()`는 저장된 인증 토큰을 Supabase 세션에 적용한 뒤 실제 인증 사용자 UUID가 `st.session_state["user_id"]`와 일치하는지 확인합니다. 로그인 전 인증 요청에는 `create_auth_client()`를 사용합니다. RLS는 전달한 사용자 ID가 아니라 실제 인증 토큰의 `auth.uid()`를 기준으로 평가됩니다.

------------------------------------------------------------------------

# 3. PKNU Finder 데이터베이스 구조 이해하기


기능을 구현하기 전, 각 테이블의 역할과 데이터 연결에 관해 다룹니다.

## 3-1. 전체 테이블 살펴보기

PKNU Finder는 크게 6개의 테이블을 사용합니다.

| 테이블 이름        | 테이블 내용 | 저장하는 데이터                       |
|:-------------------|:-------------------|:--------------------------------------|
| `users`            | 회원 명단          | 사용자 이름 및 사용자 ID              |
| `lost_items`       | 게시글 목록        | 분실물·습득물 정보 및 태그            |
| `lost_item_images` | 게시글 사진 목록   | 게시글에 첨부된 이미지 경로           |
| `bookmarks`        | 관심 게시글 목록   | 사용자가 북마크한 게시글              |
| `chat_rooms`       | 채팅방 목록        | 게시글, 채팅 참여자, 채팅방 생성 시간 |
| `chats`            | 대화 기록          | 채팅방에 속한 개별 메시지             |

각 테이블은 서로 독립적으로 존재하는 것이 아니라, ID를 이용해 연결되어 있습니다.

예를 들어 한 사용자가 게시글을 작성하면 다음과 같은 일이 발생합니다.

1.  `users`에서 로그인한 사용자를 확인합니다.
2.  `lost_items`에 새로운 게시글을 등록합니다.
3.  게시글에 사진이 있다면 `lost_item_images`에 사진 경로를 저장합니다.
4.  다른 사용자가 해당 게시글을 북마크하면 `bookmarks`에 기록합니다.
5.  다른 사용자가 게시글에서 채팅을 시작하면 `chat_rooms`에 채팅방을
    만들거나 기존 채팅방을 찾습니다.
6.  채팅방에서 메시지를 주고받으면 각 메시지를 `chats`에 저장합니다.

**ID 생성 및 삭제 관계:** `users.id`는 Auth UUID를 공유하며, 나머지 5개 테이블의 BIGINT `id`는 `GENERATED BY DEFAULT AS IDENTITY`입니다. 게시글 삭제는 이미지 메타데이터·북마크·일부 채팅 FK의 CASCADE와 연관되지만 `chat_rooms.item_id`, `chats.room_id` 등은 기본 NO ACTION이므로 참조 관계 때문에 삭제가 실패할 수 있습니다. 실제 삭제 전 관련 데이터와 Storage 파일을 확인이 필요합니다.

## 3-2. 테이블 간 관계 이해하기

코드보다 먼저 실제 서비스에서 어떤 관계가 만들어지는지 생각해 보겠습니다.

## ① 사용자와 게시글의 관계

먼저 사용자가 게시글을 작성하는 상황을 생각해 보겠습니다.

### `users` (사용자)

| id     | username |
|:-------|:---------|
| UUID-A | 사용자 A |
| UUID-B | 사용자 B |
| UUID-C | 사용자 C |

### `lost_items` (게시글)

| id  | title         | user_id |
|:----|:--------------|:--------|
| 1   | 검은색 지갑   | UUID-A  |
| 2   | 파란색 우산   | UUID-A  |
| 3   | 에어팟 케이스 | UUID-B  |

한 명의 사용자는 여러 게시글을 작성할 수 있습니다.

예를 들어 사용자 A가 검은색 지갑과 파란색 우산 게시글을 작성했다면, 두 게시글의 `user_id`에는 모두 사용자 A의 고유 ID인 `UUID-A`가 저장됩니다.

즉, `lost_items.user_id`는 게시글을 작성한 사용자가 누구인지 알려주는 값입니다.

**정리**

``` text
users
 ├── UUID-A (사용자 A)
 │    ├── 게시글 1 (검은색 지갑)
 │    └── 게시글 2 (파란색 우산)
 │
 ├── UUID-B (사용자 B)
 │    └── 게시글 3 (에어팟 케이스)
 │
 └── UUID-C (사용자 C)
```

따라서 `users`와 `lost_items`는 **일대다(1:N) 관계**입니다.

- `id`는 자동으로 생성되므로 직접 입력하지 않습니다.
- 한 명의 사용자는 여러 게시글을 작성할 수 있습니다.
- 하나의 게시글은 작성자에게 연결되지만 `lost_items.user_id`는 NULL을 허용합니다. 관련 사용자가 하드 삭제되는 경우 FK의 `ON DELETE SET NULL` 동작으로 작성자 연결이 없어질 수 있습니다.

------------------------------------------------------------------------

## ② 게시글과 이미지의 관계

이번에는 게시글 하나에 사진 여러 장을 등록하는 상황을 생각해 보겠습니다.

### `lost_items` (게시글)

| id  | title       |
|:----|:------------|
| 1   | 검은색 지갑 |
| 2   | 파란색 우산 |

### `lost_item_images` (게시글 이미지)

| id  | lost_item_id | image_path          |
|:----|:-------------|:--------------------|
| 1   | 1            | 1/a1b2c3.jpg        |
| 2   | 1            | 1/d4e5f6.jpg        |
| 3   | 1            | 1/0a9b8c.jpg        |
| 4   | 2            | 2/7c6d5e.jpg        |

`lost_item_images.lost_item_id`는 이미지가 어떤 게시글에 속하는지 알려주는 값입니다.

예를 들어 `lost_item_id`가 모두 1인 이미지 3장은 게시글 ID가 1인 검은색 지갑 게시글에 등록된 사진입니다.

**정리**

``` text
lost_items
 ├── 게시글 1 (검은색 지갑)
 │    ├── 이미지 1
 │    ├── 이미지 2
 │    └── 이미지 3
 │
 └── 게시글 2 (파란색 우산)
      └── 이미지 4
```

따라서 `lost_items`와 `lost_item_images`도 **일대다(1:N) 관계**입니다.

- `id`는 자동으로 생성되므로 직접 입력하지 않습니다.
- 하나의 게시글에는 여러 장의 이미지가 연결될 수 있습니다.
- 하나의 이미지는 하나의 게시글에 연결됩니다.

- 참고
실제 이미지 파일은 Storage의 `lost-item-images` 버킷에 저장하고,
데이터베이스에는 해당 파일의 경로만 저장하는 방식입니다.

------------------------------------------------------------------------

## ③ 게시글과 채팅방의 관계

PKNU Finder에서는 사용자가 게시글을 보고 게시글 작성자에게 채팅을 시작할 수 있습니다.

이때 채팅방 정보와 채팅 메시지를 서로 다른 테이블에 저장합니다.

- `chat_rooms`: 어떤 게시글에서 누가 누구와 대화하는지 저장합니다.
- `chats`: 해당 채팅방에서 주고받은 개별 메시지를 저장합니다.

### `chat_rooms` (채팅방)

| id  | item_id | user1_id | user2_id |
|:----|:--------|:---------|:---------|
| 1   | 1       | UUID-A   | UUID-B   |
| 2   | 1       | UUID-A   | UUID-C   |
| 3   | 2       | UUID-B   | UUID-C   |

각 컬럼의 의미는 다음과 같습니다.

- `id`: 채팅 방의 고유 번호 (자동 생성)
- `item_id`: 채팅이 시작된 게시글 ID
- `user1_id`: 해당 채팅방 내 유저1 ID
- `user2_id`: 해당 채팅방 내 유저2 ID


위 예시를 해석하면 다음과 같습니다.

- 채팅방 1: 게시글 1에 대해 사용자 A와 B가 대화합니다.
- 채팅방 2: 같은 게시글 1에 대해 사용자 A와 C가 대화합니다.
- 채팅방 3: 게시글 2에 대해 사용자 B와 C가 대화합니다.

같은 게시글이라도 대화 상대가 다르면 서로 다른 채팅방이 만들어집니다.

### `chats` (채팅 메시지)

| id  | room_id | item_id | user_id | receiver_id | message                     |
|:----|:--------|:--------|:--------|:------------|:----------------------------|
| 1   | 1       | 1       | UUID-B  | UUID-A      | 혹시 지갑을 찾으셨나요?     |
| 2   | 1       | 1       | UUID-A  | UUID-B      | 네, 제가 등록한 지갑입니다. |
| 3   | 1       | 1       | UUID-B  | UUID-A      | 어디에서 만날 수 있을까요?  |
| 4   | 2       | 1       | UUID-C  | UUID-A      | 아직 지갑을 찾고 계신가요?  |

각 컬럼의 의미는 다음과 같습니다.

- `id`: 채팅 메시지의 고유 번호
- `room_id`: 메시지가 속한 채팅방 ID
- `item_id`: 메시지와 관련된 게시글 ID
- `user_id`: 메시지를 보낸 사용자의 ID
- `receiver_id`: 메시지를 받는 사용자의 ID
- `message`: 실제 메시지 내용
- `timestamp`: 메시지가 작성된 시간

예를 들어 `room_id`가 1인 메시지는 모두 1번 채팅방의 대화입니다. 
따라서 같은 게시글에 대한 메시지라도 `room_id`가 다르면 서로 다른 대화로 구분할 수 있습니다.

**정리**

``` text
lost_items
 ├── 게시글 1 (검은색 지갑)
 │    ├── chat_rooms
 │    │    ├── 채팅방 1 (사용자 A ↔ 사용자 B)
 │    │    │    ├── 메시지 1
 │    │    │    ├── 메시지 2
 │    │    │    └── 메시지 3
 │    │    │
 │    │    └── 채팅방 2 (사용자 A ↔ 사용자 C)
 │    │         └── 메시지 4
 │    │
 │    └── 게시글에 연결된 채팅방들
 │
 └── 게시글 2 (파란색 우산)
      └── chat_rooms
           └── 채팅방 3 (사용자 B ↔ 사용자 C)
```

### `chat_rooms`와 `chats`를 분리한 이유?

채팅방과 메시지를 하나의 테이블로 관리하면 같은 채팅방의 참여자 정보가
메시지마다 반복해서 저장될 수 있습니다.

두 테이블을 분리하면 다음과 같은 장점이 있습니다.

- 채팅방 하나에 여러 메시지를 연결할 수 있습니다.
- 채팅방 목록과 메시지 내역을 따로 조회할 수 있습니다.
- 같은 게시글에서 같은 두 사용자가 다시 채팅을 시작할 때 기존 채팅방을
  재사용할 수 있습니다.
- 나중에 마지막 메시지, 읽음 여부, 알림 등의 기능을 확장하기 쉽습니다.

**관계 정리**

- `lost_items` : `chat_rooms` = 일대다(1:N)
- `users` : `chat_rooms` = 참여자 역할에 따른 일대다(1:N)
- `chat_rooms` : `chats` = 일대다(1:N)
- `users` : `chats` = 일대다(1:N)

현재 `chats.item_id`도 `lost_items.id`를 직접 참조하도록 유지되어 있습니다. 
따라서 메시지에서 게시글 ID를 직접 확인할 수도 있지만, 대화 구분과 메시지 조회의 기준은 `room_id`입니다. 
`chats.item_id`에는 해당 채팅방의 `item_id`와 같은 값을 저장해야 합니다.

현재 DB에는 같은 게시글과 같은 두 사용자 조합의 중복을 막는 순서 무관 UNIQUE 표현식 인덱스가 이미 적용되어 있습니다. 자세한 정의는 `database.md` 3-10절을 참고하세요.

------------------------------------------------------------------------

## ④ 사용자와 북마크의 관계

이번에는 사용자가 관심 있는 게시글을 북마크에 저장하는 상황을 생각해 보겠습니다.

### `users` (사용자)

| id     | username |
|:-------|:---------|
| UUID-A | 사용자 A |
| UUID-B | 사용자 B |

### `lost_items` (게시글)

| id  | title         |
|:----|:--------------|
| 1   | 검은색 지갑   |
| 2   | 파란색 우산   |
| 3   | 에어팟 케이스 |

### `bookmarks` (북마크)

| id  | user_id | item_id |
|:----|:--------|:--------|
| 1   | UUID-A  | 1       |
| 2   | UUID-A  | 3       |
| 3   | UUID-B  | 1       |
| 4   | UUID-B  | 2       |

각 컬럼의 의미는 다음과 같습니다.

- `id`: 북마크 데이터의 고유 번호
- `user_id`: 북마크를 등록한 사용자의 ID
- `item_id`: 북마크한 게시글의 ID

예를 들어 사용자 A는 1, 3 아이템에 북마크를,
사용자 B는 1, 2 아이템에 북마크했습니다.

이처럼 하나의 게시글을 여러 사용자가 북마크할 수도 있고, 
한 명의 사용자가 여러 게시글을 북마크할 수도 있습니다.

**정리**

``` text
users
 ├── UUID-A (사용자 A)
 │    └── bookmarks
 │         ├── 게시글 1
 │         └── 게시글 3
 │
 └── UUID-B (사용자 B)
      └── bookmarks
           ├── 게시글 1
           └── 게시글 2
```

`bookmarks`는 `users`와 `lost_items` 사이에서 두 테이블을 연결해 주는 역할을 합니다.

- 한 명의 사용자는 여러 게시글을 북마크할 수 있습니다.
- 하나의 게시글은 여러 사용자에게 북마크될 수 있습니다.
- 하나의 북마크 데이터는 한 명의 사용자와 하나의 게시글에 연결됩니다.

따라서 다음과 같은 관계가 만들어집니다.

- `users` : `bookmarks` = 일대다(1:N)
- `lost_items` : `bookmarks` = 일대다(1:N)

결과적으로 `users`와 `lost_items`는 `bookmarks` 테이블을 통해
**다대다(N:M) 관계**를 형성합니다.

즉, 북마크 테이블은 사용자가 어떤 게시글에 관심을 표시했는지 기록하는 중간 연결 테이블이라고 이해하면 됩니다.

------------------------------------------------------------------------

## ⑤ 전체 테이블 관계 정리

지금까지 살펴본 관계를 하나로 정리하면 다음과 같습니다.

``` text
users
 ├── lost_items
 │     ├── lost_item_images
 │     └── chat_rooms
 │           └── chats
 │
 ├── chat_rooms (user1_id / user2_id)
 ├── chats (user_id / receiver_id)
 └── bookmarks
        └── lost_items
```

| 테이블     | 연결되는 테이블  | 관계 | 설명                                            |
|:-----------|:-----------------|:-----|:------------------------------------------------|
| users      | lost_items       | 1:N  | 한 사용자가 여러 게시글 작성                    |
| lost_items | lost_item_images | 1:N  | 한 게시글에 여러 이미지 등록                    |
| lost_items | chat_rooms       | 1:N  | 한 게시글에서 여러 채팅방 생성 가능             |
| users      | chat_rooms       | 1:N  | 한 사용자가 여러 채팅방에 참여 가능             |
| chat_rooms | chats            | 1:N  | 한 채팅방에 여러 메시지 저장                    |
| users      | chats            | 1:N  | 한 사용자가 여러 메시지를 보내거나 받을 수 있음 |
| users      | bookmarks        | 1:N  | 한 사용자가 여러 게시글 북마크                  |
| lost_items | bookmarks        | 1:N  | 한 게시글을 여러 사용자가 북마크                |

이처럼 각 테이블은 서로 독립적으로 존재하는 것이 아니라, 고유 ID와 외래키(Foreign Key)를 이용해 연결되어 있습니다.

**요약**

- `id`: 각 데이터 자체를 구분하는 고유 번호
- `user_id`: 메시지를 보낸 사용자 또는 게시글 작성자 등 사용자와 관련된
  데이터를 연결하는 값
- `receiver_id`: 메시지를 받는 사용자를 연결하는 값
- `item_id`: 게시글과 관련된 데이터를 연결하는 값
- `room_id`: 채팅 메시지와 채팅방을 연결하는 값
- `lost_item_id`: 게시글과 이미지 데이터를 연결하는 값

이러한 관계를 이해하면 게시글 작성, 이미지 조회, 채팅, 북마크 기능이 데이터베이스에서 어떻게 동작하는지 쉽게 파악할 수 있습니다.

## 3-3. 각 테이블의 컬럼 자세히 알아보기

이제 각 테이블에 어떤 항목이 있는지 살펴보겠습니다.

### ① users — 사용자 정보

사용자의 기본 정보를 저장하는 테이블입니다.

실제 로그인과 비밀번호 등 인증 정보는 Supabase Authentication에서 관리하고, 
`users`는 서비스에서 필요한 사용자 정보를 저장합니다.

| 컬럼         | 자료형      | 의미                  | 예시           |
|:-------------|:------------|:----------------------|:---------------|
| `id`         | UUID        | 사용자 고유 ID (Auth UUID) | `550e8400-...` |
| `username`   | TEXT        | 사용자 이름(닉네임)        | 홍길동         |
| `created_at` | TIMESTAMPTZ | 사용자 정보 생성 시각      | 자동 생성      |
| `is_deleted` | BOOLEAN     | 회원 탈퇴 여부             | `FALSE`        |
| `deleted_at` | TIMESTAMPTZ | 회원 탈퇴 시각             | NULL           |

**중요**

- `id`는 Supabase Auth에서 발급한 UUID입니다.
- `users.id`는 `auth.users.id`와 연결됩니다.
- 로그인 성공 후 앱에서 `id`, `username`을 `public.users`에 upsert합니다.
- `is_deleted = TRUE`인 사용자는 탈퇴 처리된 계정이므로 로그인 단계에서 차단해야 합니다.
- `username`에는 `users_username_unique` UNIQUE 인덱스가 적용되어 있습니다(대소문자는 구분). 앱의 사전 중복 검사와 별개로 DB가 동일 문자열의 중복을 방지합니다.

### ② lost_items — 분실물 및 습득물 게시글

분실물과 습득물 게시글의 정보를 저장하는 테이블입니다.

| 컬럼          | 자료형      | 의미                | 예시                           |
|:--------------|:------------|:--------------------|:-------------------------------|
| `id`          | BIGINT      | 게시글 고유 번호    | 1                              |
| `title`       | TEXT        | 게시글 제목         | 검은색 지갑을 찾습니다         |
| `description` | TEXT        | 상세 설명           | 학생회관 근처에서 분실했습니다 |
| `category`    | TEXT        | 물품 종류           | 지갑                           |
| `location`    | TEXT        | 분실 또는 습득 장소 | 학생회관                       |
| `lost_date`   | TEXT        | 분실 또는 습득 날짜 | 2026-11-02                     |
| `status`      | TEXT        | 게시글 상태         | 분실                           |
| `created_at`  | TIMESTAMPTZ | 게시글 작성 시각    | 자동 생성                      |
| `user_id`     | UUID        | 게시글 작성자       | UUID-A                         |
| `tags`        | TEXT[]      | 게시글 태그 목록    | `["아이폰", "도서관"]`          |

**기억할 점**

- `id`는 자동으로 생성되므로 직접 입력하지 않습니다.
- `user_id`는 게시글 작성자의 UUID입니다.
- `created_at`은 기본값으로 현재 시간이 저장됩니다.
- `title`, `category`는 NOT NULL이므로 반드시 값을 넣어야 합니다.
- `status`의 기본값은 `습득`이며, 앱에서는 `분실` 또는 `습득` 값을 사용합니다. DB CHECK 제약은 없으므로 다른 값을 임의로 사용하지 않도록 합니다.
- `lost_date`는 TEXT 자료형이므로 날짜 문자열(`YYYY-MM-DD`)로 저장합니다. Python의 `date` 객체는 `.isoformat()`으로 변환합니다.
- `tags`는 `TEXT[]` 배열이며 기본값은 빈 배열(`{}`)입니다. 등록 화면에서는 최대 10개까지 태그를 입력할 수 있습니다. 태그를 저장할 때는 문자열 리스트를 전달합니다.

### ③ lost_item_images — 게시글 이미지 정보

게시글에 첨부된 이미지의 경로를 저장합니다.

이미지 파일 자체를 이 테이블에 저장하는 것은 아닙니다.

| 컬럼           | 자료형      | 의미                    | 예시            |
|:---------------|:------------|:------------------------|:----------------|
| `id`           | BIGINT      | 이미지 데이터 고유 번호 | 1               |
| `lost_item_id` | BIGINT      | 연결된 게시글 ID        | 1               |
| `image_path`   | TEXT        | Storage에 저장된 경로   | `1/image_a.jpg` |
| `created_at`   | TIMESTAMPTZ | 이미지 등록 시각        | 자동 생성       |

**기억할 점**

- `id`는 자동으로 생성되므로 직접 입력하지 않습니다.
- 실제 사진은 Supabase Storage에 저장합니다.
- 이 테이블에는 사진이 저장된 **경로**만 기록합니다.
- `lost_item_id`를 이용해 어떤 게시글의 사진인지 구분합니다.
- 하나의 게시글에 여러 이미지가 연결될 수 있습니다.

### ④ bookmarks — 북마크 정보

사용자가 어떤 게시글을 북마크했는지 저장합니다.

| 컬럼      | 자료형 | 의미             | 예시   |
|:----------|:-------|:-----------------|:-------|
| `id`      | BIGINT | 북마크 고유 번호 | 1      |
| `user_id` | UUID   | 북마크한 사용자  | UUID-A |
| `item_id` | BIGINT | 북마크한 게시글  | 1      |

**기억할 점**

- `id`는 자동으로 생성되므로 직접 입력하지 않습니다.
- `user_id`는 북마크를 등록한 사용자입니다.
- `item_id`는 북마크 대상 게시글입니다.
- 두 값을 조합하여 사용자의 북마크 목록을 가져올 수 있습니다. `UNIQUE (user_id, item_id)`가 DB에 적용되어 동일 사용자의 중복 북마크를 방지합니다.

### ⑤ chat_rooms — 채팅방 정보

채팅방 자체의 정보를 저장하는 테이블입니다. 개별 메시지는 `chats` 테이블에 저장합니다.

| 컬럼         | 자료형      | 의미                      | 예시      |
|:-------------|:------------|:--------------------------|:----------|
| `id`         | BIGINT      | 채팅방 고유 번호          | 1         |
| `item_id`    | BIGINT      | 채팅이 시작된 게시글 ID   | 1         |
| `user1_id`   | UUID        | 채팅 참여자 1의 사용자 ID | UUID-A    |
| `user2_id`   | UUID        | 채팅 참여자 2의 사용자 ID | UUID-B    |
| `created_at` | TIMESTAMPTZ | 채팅방 생성 시각          | 자동 생성 |

**중요**

- `id`는 자동으로 생성되므로 직접 입력하지 않습니다.
- `item_id`는 채팅이 어떤 게시글에서 시작되었는지 나타냅니다.
- `user1_id`, `user2_id`는 채팅방에 참여하는 두 사용자의 UUID입니다.
- `user1_id`와 `user2_id`에는 서로 다른 사용자가 들어가야 합니다.
- `chat_rooms_unique_conversation` UNIQUE 인덱스는 `(item_id, LEAST(user1_id, user2_id), GREATEST(user1_id, user2_id))` 조합의 중복 채팅방을 막습니다. 세 컬럼 모두 `NOT NULL`입니다.
- `CHECK (user1_id <> user2_id)`로 본인과의 채팅방 생성을 막습니다.
- 현재 동일한 UNIQUE 인덱스 정의가 `chat_rooms_unique_pair`에도, 동일한 CHECK 정의가 `chat_rooms_users_different`에도 중복 존재합니다. 문서 확인만 하고 운영 DB에서는 임의로 삭제하지 않습니다.
- 한 채팅방에는 여러 메시지가 연결될 수 있습니다.

### ⑥ chats — 채팅 메시지 정보

채팅방 안에서 주고받는 개별 메시지를 저장하는 테이블입니다.

| 컬럼          | 자료형      | 의미                    | 예시       |
|:--------------|:------------|:------------------------|:-----------|
| `id`          | BIGINT      | 메시지 고유 번호        | 1          |
| `room_id`     | BIGINT      | 메시지가 속한 채팅방 ID | 1          |
| `item_id`     | BIGINT      | 관련 게시글 ID          | 1          |
| `user_id`     | UUID        | 메시지를 보낸 사용자    | UUID-A     |
| `receiver_id` | UUID        | 메시지를 받는 사용자    | UUID-B     |
| `message`     | TEXT        | 메시지 내용             | 안녕하세요 |
| `timestamp`   | TIMESTAMPTZ | 메시지 작성 시각        | 자동 생성  |

**요약**

- `id`는 자동으로 생성되므로 직접 입력하지 않습니다.
- `room_id`를 이용해 메시지가 어느 채팅방에 속하는지 구분합니다.
- `item_id`는 관련 게시글을 나타냅니다. 현재 구조에서는
  `chat_rooms.item_id`와 같은 값을 저장해야 합니다.
- `user_id`는 메시지를 보낸 사용자의 UUID입니다.
- `receiver_id`는 메시지를 받는 사용자의 UUID입니다.
- `timestamp`는 메시지 작성 시각이며 기본값으로 현재 시간이 저장됩니다.
- 메시지를 조회할 때는 `item_id`가 아니라 `room_id`를 기준으로 조회해야
  서로 다른 채팅방의 대화가 섞이지 않습니다.

------------------------------------------------------------------------

# 4. 데이터베이스 기본 사용법

이제 Python 코드에서 데이터를 다루는 방법을 알아보겠습니다.


| 작업   | 의미               | Supabase 메서드 |
|:-------|:-------------------|:----------------|
| INSERT | 새로운 데이터 저장 | `.insert()`     |
| SELECT | 저장된 데이터 조회 | `.select()`     |
| UPDATE | 기존 데이터 수정   | `.update()`     |
| DELETE | 데이터 삭제        | `.delete()`     |

모든 요청은 마지막에 `.execute()`를 호출해야 실행됩니다.

## 4-1. 공통 연결 코드

각 화면에서 Supabase를 사용할 때는 다음 코드를 작성합니다.

``` python
import streamlit as st
from DB.database import get_supabase_client

# Supabase 연결
supabase = get_supabase_client()

# 현재 로그인한 사용자 ID
user_id = st.session_state.get("user_id")
```

이 코드는 해당 화면에서 Supabase를 사용하기 위한 기본 준비 과정입니다.

단, `user_id`는 로그인 성공 시 세션에 저장됩니다. 로그인 상태가 아닐 시
`None`.

## 4-2. 데이터 입력하기 — INSERT

새로운 데이터를 테이블에 저장할 때 사용합니다.

예를 들어 게시글을 등록하려면 다음과 같이 작성합니다.

``` python
data = {
    "title": "검은색 지갑",
    "description": "...",
    "category": "지갑",
    "location": "학생회관",
    .
    .
    .
    "user_id": user_id
}

response = (
    supabase
    .table("lost_items")
    .insert(data)
    .execute()
)
```

여기서 `.table("lost_items")`는 데이터를 저장할 테이블이고, `data`는 실제로
저장할 내용입니다.

## 4-3. 데이터 가져오기 — SELECT

저장된 데이터를 가져올 때 사용합니다.

``` python
response = (
    supabase
    .table("lost_items")
    .select("*")
    .execute()
)

items = response.data
```

`response.data`에는 조회된 데이터가 리스트 형태로 저장됩니다.

예를 들어 게시글이 3개라면 다음과 같은 형태입니다.

``` python
[
    {"id": 1, "title": "검은색 지갑", "description": "..." ...},
    {"id": 2, "title": "흰색 우산", "description": "..." ...},
    {"id": 3, "title": "에어팟 케이스", "description": "..." ...}
]
```

실제 조회 결과에는 테이블의 다른 컬럼도 포함될 수 있습니다.

## 4-4. 특정 데이터만 가져오기

전체 게시글이 아니라 특정 게시글만 가져오고 싶다면 `.eq()`를 사용합니다.

``` python
response = (
    supabase
    .table("lost_items")
    .select("*")
    .eq("id", 1)
    .execute()
)

items = response.data                  # 결과는 항상 리스트입니다.
item = items[0] if items else None     # 조회 결과가 없으면 None
```

위 코드는 게시글 ID가 1인 데이터를 조회합니다. 결과가 리스트로 반환되므로
첫 번째 요소를 꺼내 사용하며, 실제 코드에서는 `1` 대신 사용자가 선택한
게시글의 ID를 넣습니다.

## 4-5. 데이터 수정하기 — UPDATE

기존 게시글의 제목을 수정할 수 있습니다.

``` python
response = (
    supabase
    .table("lost_items")
    .update({
        "title": "수정된 게시글 제목"
    })
    .eq("id", 1)
    .execute()
)
```

`.eq("id", 1)`은 게시글 ID가 1인 데이터만 수정하라는 의미입니다.

## 4-6. 데이터 삭제하기 — DELETE

특정 게시글을 삭제할 때 사용합니다.

``` python
response = (
    supabase
    .table("lost_items")
    .delete()
    .eq("id", 1)
    .execute()
)
```

실제 서비스에서는 삭제 전에 작성자 권한(로그인 유저 == 게시글 작성자)을
확인해야 합니다.

------------------------------------------------------------------------

# 5. 분실물 게시글 관리하기

게시글 등록과 조회 방법을 알아보겠습니다.

## 5-1. 게시글 등록하기

사용자가 입력한 게시글 정보를 `lost_items` 테이블에 저장합니다.

``` python
import streamlit as st
from datetime import date
from DB.database import get_supabase_client

supabase = get_supabase_client()

user_id = st.session_state.get("user_id")

if not user_id:
    st.warning("로그인이 필요합니다.")
    st.stop()

item_date = date.today()  # 예: st.date_input()으로 받은 값

item_data = {
    "title": "검은색 지갑을 찾습니다.",       # NOT NULL
    "description": "학생회관 근처에서 분실했습니다.",
    "category": "지갑",                       # NOT NULL
    "location": "학생회관",
    "lost_date": item_date.isoformat(),       # TEXT 컬럼이므로 문자열로 변환
    "status": "분실",                         # "분실" 또는 "습득"
    "user_id": user_id,
    "tags": ["아이폰", "도서관"],               # TEXT[]: 문자열 리스트, 최대 10개
}

response = (
    supabase
    .table("lost_items")
    .insert(item_data)
    .execute()
)

if not response.data:
    st.error("게시글 등록 결과를 확인할 수 없습니다.")
    st.stop()

new_item = response.data[0]  # insert는 삽입된 행을 기본으로 반환합니다.

st.success("게시글이 등록되었습니다.")
st.write("등록된 게시글 ID:", new_item["id"])
```

### 요약

- `user_id`는 현재 로그인한 사용자의 UUID입니다.
- `id`는 게시글이 등록될 때 자동으로 생성되므로 직접 입력할 필요가 없습니다.
- `title`, `category`는 NOT NULL이므로 빠뜨리면 오류가 발생합니다.
- `lost_date`는 TEXT 컬럼입니다. `st.date_input()`이 반환하는 `date` 객체를
  그대로 넣으면 JSON 변환 오류가 나므로 `.isoformat()`으로 문자열로 바꿉니다.
- Python 클라이언트의 `insert()`는 별도의 `.select()` 없이도 삽입된 행을
  `response.data`로 반환합니다. (`.insert(...).select(...)`는 JavaScript
  클라이언트의 문법이며 Python에서는 사용할 수 없습니다.)
- `new_item` 변수는 새로 작성된 게시글의 정보를 담아두는 변수입니다.
- `category`는 등록 화면의 카테고리 선택값을 저장합니다. DB에는 별도의 ENUM/CHECK 제약이 없으므로 앱에서 사용하는 카테고리 문자열을 일관되게 전달해야 합니다.
- `tags`는 문자열 리스트로 전달합니다. 예: `["아이폰", "도서관"]`. 빈 태그는 저장 전에 정리하고, 등록 화면의 최대 10개 제한을 지킵니다.

## 5-2. 게시글 목록 가져오기

등록된 게시글 전체를 가져오는 예제입니다.

``` python
response = (
    supabase
    .table("lost_items")
    .select("*")
    .order("created_at", desc=True)
    .execute()
)

items = response.data

for item in items:
    st.write(item["title"])
    st.write(item["category"])
    st.write(item["location"])
```

`order("created_at", desc=True)`는 내림차순(최근에 등록된 게시글 순서)
정렬합니다.

## 5-3. 특정 사용자가 작성한 게시글 가져오기

마이페이지에서 내가 작성한 게시글을 보여줄 때 사용할 수 있습니다.

``` python
response = (
    supabase
    .table("lost_items")
    .select("*")
    .eq("user_id", user_id)
    .execute()
)

my_items = response.data
```

`user_id`가 현재 로그인한 사용자의 UUID와 같은 게시글만 가져옵니다.

## 5-4. 카테고리별 게시글 검색하기

``` python
response = (
    supabase
    .table("lost_items")
    .select("*")
    .eq("category", "지갑")
    .execute()
)

search_items = response.data
```

위 코드는 카테고리가 지갑인 게시글만 가져옵니다.

등록 화면에서 사용하는 `category`는 선택된 카테고리 문자열을 그대로 저장합니다. DB 컬럼은 `TEXT`이며 카테고리 목록을 DB가 강제하지 않으므로, 등록 화면과 검색 필터에서 같은 값을 사용해야 합니다.

태그는 `lost_items.tags`의 `TEXT[]` 컬럼에 저장합니다.

```python
# 태그 등록
item_data = {
    "title": "아이폰을 찾습니다.",
    "category": "전자기기",
    "user_id": user_id,
    "tags": ["아이폰", "도서관", "검정색"],
}

# 태그가 포함된 게시글 조회
response = (
    supabase.table("lost_items")
    .select("*")
    .contains("tags", ["도서관"])
    .execute()
)
```

`tags`는 문자열 배열입니다. 태그 입력은 등록 화면의 최대 10개 제한을 지키고, `#` 기호를 포함할지 여부는 앱에서 정한 입력·표시 규칙에 맞춰 통일합니다.

## 5-5. 검색어로 게시글 찾기

``` python
keyword = "지갑"

response = (
    supabase
    .table("lost_items")
    .select("*")
    .ilike("title", f"%{keyword}%")
    .execute()
)

items = response.data
```

`ilike()`는 제목에 검색어가 포함된 게시글을 찾는 데 사용할 수 있습니다.

------------------------------------------------------------------------

# 6. 채팅 메시지 관리하기

채팅 기능은 채팅방 정보와 개별 메시지를 분리해서 관리합니다.

- `chat_rooms`: 채팅방 ID, 게시글 ID, 참여자 정보를 저장합니다.
- `chats`: 채팅방에서 주고받은 메시지와 발신자·수신자 정보를 저장합니다.

따라서 채팅 기능을 구현할 때는 먼저 채팅방을 확인하거나 생성한 다음,
해당 채팅방의 `room_id`를 이용해 메시지를 저장하고 조회해야 합니다.

## 6-1. 채팅방 만들기 또는 기존 채팅방 가져오기

사용자가 게시글에서 채팅하기를 눌렀다고 가정하겠습니다.

먼저 다음 정보가 필요합니다.

- `item_id`: 채팅을 시작한 게시글의 ID
- `user_id`: 현재 로그인한 사용자의 UUID
- `other_user_id`: 대화 상대방의 UUID (일반적으로 게시글 작성자)

같은 게시글에서 같은 두 사용자가 다시 채팅을 시작하면 새 채팅방을 만들지
않고 기존 채팅방을 사용해야 합니다.

``` python
import streamlit as st
from DB.database import get_supabase_client

supabase = get_supabase_client()


def find_chat_room(item_id, user_a, user_b):
    """같은 게시글에서 두 사용자가 참여한 채팅방을 찾습니다.
    user1_id / user2_id 의 순서가 반대여도 같은 채팅방으로 찾습니다."""
    response = (
        supabase
        .table("chat_rooms")
        .select("*")
        .eq("item_id", item_id)
        .or_(
            f"and(user1_id.eq.{user_a},user2_id.eq.{user_b}),"
            f"and(user1_id.eq.{user_b},user2_id.eq.{user_a})"
        )
        .limit(1)
        .execute()
    )
    return response.data[0] if response.data else None


def get_or_create_chat_room(item_id, user_id, other_user_id):
    # 1) 기존 채팅방이 있으면 그대로 사용합니다.
    room = find_chat_room(item_id, user_id, other_user_id)
    if room:
        return room

    # 2) 없으면 새로 생성합니다.
    try:
        response = (
            supabase
            .table("chat_rooms")
            .insert({
                "item_id": item_id,
                "user1_id": user_id,
                "user2_id": other_user_id,
            })
            .execute()
        )
        if response.data:
            return response.data[0]
    except Exception:
        # 두 사용자가 거의 동시에 채팅을 시작하면 고유 인덱스 오류가
        # 발생할 수 있습니다. 아래에서 기존 채팅방을 다시 조회합니다.
        pass

    # 3) 생성 중 오류가 났거나 반환값이 없으면 다시 조회합니다.
    return find_chat_room(item_id, user_id, other_user_id)


user_id = st.session_state.get("user_id")

if not user_id:
    st.warning("로그인이 필요합니다.")
    st.stop()

# 예시 값
item_id = 1
other_user_id = "상대방의-UUID"

if user_id == other_user_id:
    st.warning("본인이 작성한 게시글에는 채팅을 시작할 수 없습니다.")
    st.stop()

room = get_or_create_chat_room(item_id, user_id, other_user_id)

if not room:
    st.error("채팅방을 만들 수 없습니다.")
    st.stop()

room_id = room["id"]

st.write("채팅방 ID:", room_id)
```

**요약**

- `item_id`, `user_id`, `other_user_id`는 실제 게시글과 로그인 정보를
  바탕으로 가져와야 합니다. 
- `user1_id`와 `user2_id`의 순서가 반대여도 같은 채팅방으로 찾을 수
  있도록 두 경우를 모두 확인해야 합니다.
- `chat_rooms.id`는 데이터베이스에서 자동 생성되므로 직접 입력하지
  않습니다.
- `chat_rooms_unique_conversation` UNIQUE 인덱스가 이미 적용되어 있어 사용자 순서가 달라도 동일 게시글·동일 두 사용자 조합의 중복 생성을 막습니다.
- 사전 조회와 INSERT 사이에 다른 요청이 먼저 생성할 수 있으므로, 중복 INSERT 오류 시 다시 조회하는 흐름을 사용합니다.
- `CHECK (user1_id <> user2_id)`도 이미 적용되어 있습니다.

## 6-2. 채팅 메시지 등록하기

메시지 등록 시에는 다음 정보를 전달합니다.

- `room_id`: 메시지가 속한 채팅방 ID
- `item_id`: 채팅방에 연결된 게시글 ID
- `user_id`: 현재 로그인한 사용자 ID (보낸 사람)
- `receiver_id`: 상대방 ID (받는 사람)
- `message`: 실제 메시지 내용

``` python
# 예제

if user_id == room["user1_id"]:
    receiver_id = room["user2_id"]
elif user_id == room["user2_id"]:
    receiver_id = room["user1_id"]
else:
    st.error("이 채팅방에 참여할 권한이 없습니다.")
    st.stop()

message_text = "안녕하세요. 해당 물건을 확인하고 싶습니다.".strip()

if not message_text:
    st.warning("메시지를 입력해 주세요.")
    st.stop()

chat_data = {
    "room_id": room["id"],
    "item_id": room["item_id"],
    "user_id": user_id,
    "receiver_id": receiver_id,
    "message": message_text,
}

response = (
    supabase
    .table("chats")
    .insert(chat_data)
    .execute()
)

if not response.data:
    st.error("메시지 등록 결과를 확인할 수 없습니다.")
    st.stop()

st.success("메시지를 전송했습니다.")
st.write("메시지 ID:", response.data[0]["id"])
```

**각 컬럼의 의미**

| 컬럼          | 값               | 의미                 |
|:--------------|:-----------------|:---------------------|
| `room_id`     | 채팅방 ID        | 메시지가 속한 채팅방 |
| `item_id`     | 게시글 ID        | 채팅과 관련된 게시글 |
| `user_id`     | 현재 사용자 UUID | 메시지를 보낸 사람   |
| `receiver_id` | 상대방 UUID      | 메시지를 받는 사람   |
| `message`     | 메시지 내용      | 실제 전송할 내용     |

`id`와 `timestamp`는 데이터베이스에서 자동 생성되므로 직접 입력하지
않습니다.

`chats.item_id`는 기존 테이블 구조와의 호환성을 위해 유지하고 있습니다.
반드시 해당 채팅방의 `chat_rooms.item_id`와 같은 값을 저장해야 합니다.

## 6-3. 특정 채팅방의 메시지 가져오기

메시지를 조회 시 하나의 게시글에 여러 채팅방이 만들어질 수 있기 때문에

`item_id`가 아니라 `room_id`를 기준으로 조회해야 합니다.


``` python
room_id = 1  # 예시: 조회할 채팅방 ID

response = (
    supabase
    .table("chats")
    .select("*")
    .eq("room_id", room_id)
    .order("timestamp", desc=False)
    .execute()
)

messages = response.data
```

위 코드는 채팅방 ID가 1인 메시지만 가져옵니다.

`order("timestamp", desc=False)`는 오래된 메시지부터 최신 메시지 순서로
정렬합니다.

## 6-4. 채팅 화면에 메시지 표시하기

조회한 메시지의 `user_id`와 현재 로그인한 사용자의 ID를 비교하면 내가
보낸 메시지인지 상대방이 보낸 메시지인지 구분할 수 있습니다.

``` python
for message in messages:
    if message["user_id"] == user_id:
        st.write("나:", message["message"])
    else:
        st.write("상대방:", message["message"])
```

Streamlit의 `st.chat_message()`를 사용가능.


## 6-5. 내가 참여한 채팅방 목록 가져오기

마이페이지나 채팅 화면에서 현재 로그인한 사용자가 참여 중인 채팅방을
보여줄 수 있습니다.

``` python
response = (
    supabase
    .table("chat_rooms")
    .select("*")
    .or_(
        f"user1_id.eq.{user_id},user2_id.eq.{user_id}"
    )
    .order("created_at", desc=True)
    .execute()
)

my_rooms = response.data

for room in my_rooms:
    st.write("채팅방 ID:", room["id"])
    st.write("게시글 ID:", room["item_id"])

    if room["user1_id"] == user_id:
        other_user_id = room["user2_id"]
    else:
        other_user_id = room["user1_id"]

    st.write("상대방 ID:", other_user_id)
```

위 코드는 채팅방 목록과 상대방 UUID를 가져오는 기본 예시입니다. 상대방의
이름이나 게시글 제목을 화면에 표시하려면 `users`와 `lost_items`
테이블에서 관련 정보를 추가로 조회해야 합니다.

## 6-6. 채팅 기능 구현 시 주의할 점

1.  채팅방 ID와 메시지 ID는 다릅니다.
    - `chat_rooms.id`: 채팅방을 구분하는 ID
    - `chats.id`: 개별 메시지를 구분하는 ID
2.  메시지 조회에는 `room_id`를 사용합니다.
    - 같은 게시글이라도 상대방이 다르면 채팅방이 다를 수 있습니다.
    - `item_id`만으로 조회하면 서로 다른 채팅방의 메시지가 섞일 수
      있습니다.
3.  보낸 사람과 받는 사람을 구분합니다.
    - `user_id`: 메시지를 보낸 사람
    - `receiver_id`: 메시지를 받는 사람
4.  채팅방 참여자만 메시지를 조회하고 전송할 수 있어야 합니다.
    - 화면에서 사용자 ID를 비교하는 것만으로는 보안이 보장되지 않습니다.
    - 실제 DB에는 채팅방 참여자 SELECT/INSERT 및 메시지 참여자 SELECT/INSERT RLS 정책이 적용되어 있습니다.
    - 앱에서도 `room["user1_id"]`, `room["user2_id"]`와 인증된 사용자를 비교해 입력 오류를 방지합니다. (6-2 예제 참고)
5.  Service Role Key 사용에 주의합니다.
    - Service Role Key를 사용하는 클라이언트는 RLS를 우회할 수 있습니다.
    - `get_supabase_client()`는 anon 키와 인증된 사용자 세션을 사용하므로 RLS가 적용됩니다.
    - `get_supabase_admin_client()`는 서비스 키를 사용해 RLS를 우회하므로 별도의 서버 측 권한 검증이 필수입니다.
6.  중복 채팅방 생성에 주의합니다.
    - 같은 게시글과 같은 두 사용자의 채팅방은 기존 방을 재사용해야 합니다.
    - 순서 무관 UNIQUE 인덱스가 DB에 이미 적용되어 있어 동시 요청 중 하나는 UNIQUE 충돌이 발생할 수 있습니다. 충돌 시 기존 채팅방을 재조회하세요.

# 7. 북마크 관리하기

북마크 기능은 사용자가 관심 있는 게시글을 저장하고 다시 확인할 수 있도록
하는 기능입니다.

`bookmarks` 테이블에는 사용자 ID와 게시글 ID가 저장됩니다.

## 7-1. 북마크 등록하기

``` python
bookmark_data = {
    "user_id": user_id,
    "item_id": 1
}

response = (
    supabase
    .table("bookmarks")
    .insert(bookmark_data)
    .execute()
)
```

## 7-2. 중복 북마크 확인하기

같은 사용자가 같은 게시글을 여러 번 북마크하지 않도록 먼저 확인하는 것이
좋습니다.

``` python
existing = (
    supabase
    .table("bookmarks")
    .select("id")
    .eq("user_id", user_id)
    .eq("item_id", 1)
    .execute()
)

if not existing.data:
    supabase.table("bookmarks").insert({
        "user_id": user_id,
        "item_id": 1
    }).execute()
else:
    st.info("이미 북마크한 게시글입니다.")
```

`bookmarks_user_item_unique` UNIQUE 제약이 이미 적용되어 있습니다.

```sql
UNIQUE (user_id, item_id)
```

## 7-3. 내가 북마크한 게시글 가져오기

먼저 내가 저장한 북마크 목록을 가져옵니다.

``` python
response = (
    supabase
    .table("bookmarks")
    .select("item_id")
    .eq("user_id", user_id)
    .execute()
)

item_ids = [row["item_id"] for row in response.data]
```

이제 게시글 ID를 이용해 실제 게시글을 조회합니다.

``` python
if item_ids:
    items_response = (
        supabase
        .table("lost_items")
        .select("*")
        .in_("id", item_ids)
        .execute()
    )

    bookmarked_items = items_response.data
else:
    bookmarked_items = []
```

이렇게 두 번 조회하는 이유는 북마크 테이블에는 게시글의 제목이나 설명이
아니라 게시글 ID만 저장하기 때문입니다.

------------------------------------------------------------------------

# 8. 이미지 관리하기

PKNU Finder에서는 이미지 파일과 이미지 정보를 별도로 관리합니다.

| 저장 위치 | 저장하는 것 | 예시 |
|:--|:--|:--|
| Supabase Storage (`lost-item-images`) | 실제 이미지 파일 | `1/a1b2c3.jpg` |
| `lost_item_images` 테이블 | 이미지 파일의 경로, 게시글 연결 정보 | `lost_item_id = 1` |

파일은 Storage에, 파일의 위치와 게시글 연결 정보는 Database에 저장합니다.

## 8-1. 이미지 업로드하기

이미지 파일을 `lost-item-images` Bucket에 업로드하고, 파일 경로를
`lost_item_images` 테이블에 저장합니다.

등록 화면(`views/register/register.py`)은 선택한 사진을
`{"name": 파일명, "bytes": 파일 내용}` 형태로
`st.session_state.register_photos`에 보관합니다.

``` python
import uuid
from pathlib import Path
from DB.database import get_supabase_client

# 로그인 사용자 인증 세션으로 Storage와 DB에 접근합니다.
supabase = get_supabase_client()

MIME_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
}


def upload_item_image(supabase, item_id, photo):
    """photo: {"name": "wallet.png", "bytes": b"..."}"""
    ext = Path(photo["name"]).suffix.lower()
    if ext not in MIME_TYPES:
        raise ValueError("지원하지 않는 이미지 형식입니다. (jpg, jpeg, png)")

    image_path = f"{item_id}/{uuid.uuid4().hex}{ext}"
    bucket = supabase.storage.from_("lost-item-images")

    # 1) Storage에 파일 업로드
    bucket.upload(
        path=image_path,
        file=photo["bytes"],
        file_options={"content-type": MIME_TYPES[ext]},
    )

    # 2) DB에 경로 저장
    try:
        supabase.table("lost_item_images").insert({
            "lost_item_id": item_id,
            "image_path": image_path,
        }).execute()
    except Exception:
        # DB 저장에 실패하면 Storage에 남은 파일(고아 파일)을 삭제합니다.
        bucket.remove([image_path])
        raise

    return image_path


# 사용 예시 (5-1에서 만든 new_item 사용)
for photo in st.session_state.register_photos.values():
    upload_item_image(supabase, new_item["id"], photo)
```

**주의할 점**

- 실제 `lost-item-images` 버킷은 **비공개(`public=false`)**이고 Storage RLS가 켜져 있습니다. 버킷 자체의 `file_size_limit`, `allowed_mime_types`는 둘 다 `NULL`이며 별도 버킷 제한이 설정되지 않았습니다.
- Storage의 INSERT/DELETE는 인증된 사용자에게만 허용되며, 파일 경로의 **첫 번째 폴더가 본인이 작성한 `lost_items.id`**와 일치해야 합니다. 따라서 게시글을 먼저 저장한 뒤 `{item_id}/{파일명}`으로 업로드합니다.
- `lost_item_images` 메타데이터 INSERT/DELETE에도 동일한 게시글 소유권 검사가 적용됩니다. 단, 조회는 `anon`/`authenticated` 모두에게 허용됩니다.
- 위 코드는 확장자만 검사합니다. 운영 환경에서는 파일 크기와 실제 이미지
  형식도 함께 검사하는 것이 좋습니다.
- Storage 업로드는 성공했는데 DB 저장이 실패하면 파일만 남게 되므로, 위
  예제처럼 실패 시 파일을 삭제합니다.

## 8-2. 이미지 경로 가져오기

``` python
response = (
    supabase
    .table("lost_item_images")
    .select("image_path")
    .eq("lost_item_id", 1)
    .execute()
)

image_paths = [
    row["image_path"]
    for row in response.data
]
```

## 8-3. Private Bucket 이미지 표시하기

현재 버킷은 **Private**입니다. `get_public_url()`은 이 버킷의 이미지 공개 접근을 보장하지 않으므로, 인증된 다운로드 또는 접근 가능한 사용자 클라이언트의 **Signed URL**을 사용해야 합니다. 현재 Storage SELECT 정책은 `anon`/`authenticated`에게 이 버킷 객체 읽기를 허용하지만, 버킷의 공개 설정 자체가 바뀐 것은 아닙니다.

``` python
def get_signed_image_url(supabase, image_path):
    response = (
        supabase.storage
        .from_("lost-item-images")
        .create_signed_url(image_path, 3600)
    )

    # 라이브러리 버전에 따라 키 이름이 다를 수 있어 둘 다 확인합니다.
    return response.get("signedURL") or response.get("signedUrl")
```

Streamlit에서 표시하는 예시입니다.

``` python
for image_path in image_paths:
    image_url = get_signed_image_url(supabase, image_path)

    if image_url:
        st.image(image_url)
    else:
        st.caption("이미지를 불러올 수 없습니다.")
```

`3600`은 URL의 유효 시간이며 단위는 초입니다. 반환되는 키 이름은 설치된
`supabase` 라이브러리 버전에 따라 다를 수 있으므로, 사용 중인 버전에서 확인이 필요합니다.


------------------------------------------------------------------------

# 9. 데이터 수정 및 삭제하기 (데이터 수정 및 삭제는 구현 검토 중입니다.)

## 9-1. 게시글 수정하기

``` python
response = (
    supabase
    .table("lost_items")
    .update({
        "title": "수정된 게시글 제목",
        "description": "수정된 상세 설명"
    })
    .eq("id", 1)
    .eq("user_id", user_id)
    .execute()
)
```

게시글 ID와 작성자 ID를 함께 조건으로 지정합니다.

## 9-2. 게시글 상태 변경하기

``` python
response = (
    supabase
    .table("lost_items")
    .update({
        "status": "습득"  # 허용해서 사용하는 값: "분실" 또는 "습득"
    })
    .eq("id", 1)
    .eq("user_id", user_id)
    .execute()
)
```

현재 앱에서 사용하는 `status` 값은 `분실` 또는 `습득`입니다. 

## 9-3. 북마크 삭제하기

``` python
response = (
    supabase
    .table("bookmarks")
    .delete()
    .eq("user_id", user_id)
    .eq("item_id", 1)
    .execute()
)
```

## 9-4. 채팅 메시지 삭제하기

``` python
response = (
    supabase
    .table("chats")
    .delete()
    .eq("id", 1)
    .eq("user_id", user_id)
    .execute()
)
```

**현재 `chats`에는 DELETE RLS 정책이 없습니다.** 일반 로그인 사용자 클라이언트로 실행하는 위 DELETE는 RLS에 의해 허용되지 않습니다. 이 코드는 삭제 API 형태를 설명하는 예시일 뿐, 현재 설정에서 작동하는 메시지 삭제 기능이 아닙니다. 기능을 추가하려면 삭제 규칙을 결정한 뒤 적절한 RLS 정책과 앱 코드를 함께 검토해야 합니다.

**중요:** `lost_items`와 `bookmarks`의 수정·삭제에는 본인 소유 RLS가 적용됩니다. API 필터(`.eq(...)`)도 함께 사용하되, 필터만을 권한 검증으로 간주하지 마세요. 관리자 클라이언트는 RLS를 우회합니다. 

------------------------------------------------------------------------

# 10. 자주 발생하는 오류

## 10-1. ModuleNotFoundError

예시:

``` text
ModuleNotFoundError: No module named 'database'
```

기존 폴더 구조가 변경되었으므로 import 경로를 확인합니다.

잘못된 코드:

``` python
#예시
from database import get_supabase_client
```

올바른 코드:

``` python
#예시
from DB.database import get_supabase_client
```

## 10-2. 테이블을 찾을 수 없는 경우

예시:

``` text
relation "public.lost_items" does not exist
```

확인할 사항:

- Supabase Dashboard에 해당 테이블이 존재하는지 확인합니다.
- 테이블 이름이 코드와 일치하는지 확인합니다.
- SQL Editor에서 테이블 생성이 정상적으로 완료되었는지 확인합니다.

## 10-3. Foreign Key 오류

예시:

``` text
violates foreign key constraint
```

다른 테이블에 존재하지 않는 ID를 참조할 때 발생할 수 있습니다.

예를 들어 `chats.item_id`에 999를 입력했지만 `lost_items`에 ID가 999인
게시글이 없다면 오류가 발생합니다.

데이터를 입력하기 전에 참조하는 게시글이나 사용자가 실제로 존재하는지
확인해야 합니다.

## 10-4. RLS 권한 오류

예시:

``` text
new row violates row-level security policy
```

RLS(Row Level Security)는 데이터베이스의 각 행에 대한 접근 권한을
제한하는 보안 기능입니다.

확인할 사항:

- 해당 테이블의 RLS 정책이 설정되어 있는지 확인합니다.
- 현재 로그인한 사용자의 UUID가 올바른지 확인합니다.
- INSERT, SELECT, UPDATE, DELETE 작업에 필요한 정책이 있는지 확인합니다.

RLS가 활성화되어 있다고 해서 모든 사용자가 데이터를 자유롭게 조회하거나
수정할 수 있는 것은 아닙니다.

## 10-5. 데이터가 저장되지 않는 경우

확인할 사항:

1.  `get_supabase_client()`로 연결했는지 확인합니다.
2.  테이블 이름과 컬럼 이름이 정확한지 확인합니다.
3.  NOT NULL 컬럼에 값이 전달되었는지 확인합니다.
4.  외래 키로 연결된 데이터가 존재하는지 확인합니다.
5.  RLS 정책 및 권한을 확인합니다.

## 10-6. Supabase API Key 주의

현재 프로젝트의 `DB/database.py`에서 사용하는 주요 함수는 다음과 같습니다.

- `get_supabase_client()`: 일반 DB 작업에 사용하는 클라이언트
- `get_supabase_admin_client()`: 서버 측 관리자 작업용 클라이언트
- `create_auth_client()`: Supabase Auth 인증 작업용 클라이언트

`get_supabase_client()`는 **항상 `SUPABASE_ANON_KEY`와 유효한 사용자 인증 세션**을 사용하며, `user_id` 일치 여부까지 검사합니다. 관리자 키를 우선 선택하지 않습니다. `create_auth_client()`도 anon 키를 사용합니다. 관리자용 `get_supabase_admin_client()`만 `SUPABASE_SERVICE_ROLE_KEY`를 사용하며 RLS를 우회합니다.

- service_role 키를 GitHub, 브라우저, 로그에 노출하지 않습니다.
- 일반 CRUD/Storage에는 `get_supabase_client()`를 사용합니다.
- 로그인·회원가입 전에는 `create_auth_client()`를 사용합니다.
- 관리자 작업은 서버 내부에서만 수행하고 명시적인 권한 검증을 거칩니다.

**2026-11-05 기준 실제 DB 정책 및 활성화 상태**

| 테이블 | RLS | SELECT | INSERT | UPDATE | DELETE |
|---|---|---|---|---|---|
| `users` | ON | 본인 | 정책 없음 | 본인 | 정책 없음 |
| `lost_items` | ON | anon/auth 전체 | 본인 | 본인 | 본인 |
| `lost_item_images` | ON | anon/auth 전체 | 게시글 소유자 | 정책 없음 | 게시글 소유자 |
| `bookmarks` | ON | 본인 | 본인 | 정책 없음 | 본인 |
| `chat_rooms` | ON | 참여자 | 참여자 | 정책 없음 | 정책 없음 |
| `chats` | ON | 참여자 | 발신자 본인 + 상대방이 방 참여자 | 정책 없음 | 정책 없음 |

`storage.objects` RLS ON입니다. `lost-item-images`에 대해 anon/auth SELECT, 인증된 게시글 소유자의 INSERT/DELETE 정책이 존재합니다. 이 표는 **정책 정의**를 나타내며 실제 작업 성공에는 테이블 권한, 인증 세션, 제약 조건 등도 필요합니다.

**주의:** 현재 `users`는 자기 프로필만 SELECT 가능하므로 일반 사용자 클라이언트의 `get_username(other_user_id)` 및 `get_user_by_id(other_user_id)`는 다른 사람의 프로필을 조회하지 못합니다. 

자세한 연결 설정은 [database.md](database.md)를 참고합니다.

------------------------------------------------------------------------

# 11. 팀원들이 기억해야 할 사항

기능을 구현하기 전에 아래 내용을 확인해 주세요.

| 작업                | 사용할 테이블             | 핵심 컬럼                                                 |
|:--------------------|:--------------------------|:----------------------------------------------------------|
| 게시글 등록         | `lost_items`              | `title`, `category`, `description`, `user_id`, `tags`    |
| 게시글 검색         | `lost_items`              | `title`, `category`, `location`, `status`                 |
| 내가 작성한 게시글  | `lost_items`              | `user_id`                                                 |
| 이미지 등록         | `lost_item_images`        | `lost_item_id`, `image_path`                              |
| 이미지 조회         | `lost_item_images`        | `lost_item_id`                                            |
| 북마크 등록         | `bookmarks`               | `user_id`, `item_id`                                      |
| 북마크 조회         | `bookmarks`, `lost_items` | `user_id`, `item_id`                                      |
| 채팅방 생성 및 조회 | `chat_rooms`              | `item_id`, `user1_id`, `user2_id`                         |
| 채팅방 목록 조회    | `chat_rooms`              | `user1_id`, `user2_id`, `created_at`                      |
| 채팅 메시지 등록    | `chats`                   | `room_id`, `item_id`, `user_id`, `receiver_id`, `message` |
| 채팅 메시지 조회    | `chats`                   | `room_id`, `timestamp`                                    |
| 사용자 정보 조회    | `users`                   | `id`, `username`                                          |

## 중요한 사항

**1. 사용자 ID와 게시글 ID는 서로 다른 값입니다.**

- 사용자 ID: UUID
- 게시글 ID: 자동 생성되는 숫자형 ID

**2. 게시글을 등록할 때 작성자 ID를 함께 저장해야 합니다.**

`user_id`를 저장해야 나중에 내가 작성한 게시글을 조회할 수 있습니다.

**회원 탈퇴는 Soft Delete 방식입니다.**

- `users` 행은 유지하고 `is_deleted = TRUE`, `deleted_at`을 기록합니다.
- 닉네임은 `탈퇴한 유저_{사용자 ID 앞 8자리}` 형식으로 변경합니다.
- 해당 사용자의 북마크는 삭제하지만 게시글, 이미지, 채팅방, 메시지는 유지합니다.
- 탈퇴 계정은 로그인 처리에서 차단해야 합니다.

**3. 다른 테이블과 연결할 때는 ID를 사용합니다.**

예를 들어 채팅방은 `item_id`로 게시글과 연결하고, 개별 채팅 메시지는
`room_id`로 채팅방과 연결합니다.

**4. 채팅방과 메시지는 서로 다른 테이블에 저장합니다.**

- `chat_rooms`: 채팅방과 참여자 정보
- `chats`: 채팅방 안의 개별 메시지
- `user_id`: 메시지를 보낸 사용자
- `receiver_id`: 메시지를 받는 사용자

메시지를 조회할 때는 게시글 ID인 `item_id`가 아니라 채팅방 ID인
`room_id`를 기준으로 조회해야 합니다.

**5. 이미지 파일과 이미지 경로는 별도로 관리합니다.**

Storage에는 실제 파일을, `lost_item_images`에는 파일 경로를 저장합니다.

**6. 데이터를 수정하거나 삭제할 때는 권한을 확인해야 합니다.**

다른 사용자의 게시글이나 채팅을 임의로 수정하거나 삭제할 수 없도록 서버
측 검증과 RLS 정책을 함께 고려해야 합니다.

------------------------------------------------------------------------

# 12. 참고 자료 (References)

이 가이드의 설명과 Python 코드 예제는 Supabase 공식 문서를 참고하여
작성했습니다.

## 12-1. Supabase 기본 사용법

| 참고 자료                                                                               | 설명                                             |
|:----------------------------------------------------------------------------------------|:-------------------------------------------------|
| [Supabase 공식 문서](https://supabase.com/docs)                                         | Supabase 전체 기능 및 사용 방법                  |
| [Python Quickstart](https://supabase.com/docs/guides/getting-started/quickstarts/flask) | Python 프로젝트에서 Supabase 연결 및 데이터 조회 |
| [Python Client Library](https://supabase.com/docs/reference/python/introduction)        | Python 클라이언트 라이브러리 사용법              |

## 12-2. 데이터베이스 CRUD

| 참고 자료                                                           | 설명                                   |
|:--------------------------------------------------------------------|:---------------------------------------|
| [Insert data](https://supabase.com/docs/reference/python/insert)    | 테이블에 새로운 데이터 입력            |
| [Select data](https://supabase.com/docs/reference/python/select)    | 테이블에 저장된 데이터 조회            |
| [Update data](https://supabase.com/docs/reference/python/update)    | 기존 데이터 수정                       |
| [Delete data](https://supabase.com/docs/reference/python/delete)    | 기존 데이터 삭제                       |
| [Filters](https://supabase.com/docs/reference/python/using-filters) | 특정 조건에 맞는 데이터 검색 및 필터링 |
| [Order results](https://supabase.com/docs/reference/python/order)   | 조회 결과 정렬                         |

## 12-3. 사용자 인증 (Authentication)

| 참고 자료                                                                   | 설명                                  |
|:----------------------------------------------------------------------------|:--------------------------------------|
| [Supabase Auth](https://supabase.com/docs/guides/auth)                      | 회원가입, 로그인, 사용자 인증         |
| [Get User](https://supabase.com/docs/reference/python/auth-getuser)         | 현재 인증된 사용자 정보 가져오기      |
| [User Management](https://supabase.com/docs/guides/auth/managing-user-data) | 사용자 정보 관리 및 데이터베이스 연결 |

## 12-4. 이미지 및 파일 관리 (Storage)

| 참고 자료                                                                                           | 설명                                            |
|:----------------------------------------------------------------------------------------------------|:------------------------------------------------|
| [Supabase Storage](https://supabase.com/docs/guides/storage)                                        | 파일 및 이미지 저장소 사용 방법                 |
| [Python Upload File](https://supabase.com/docs/reference/python/storage-from-upload)                | Python에서 파일 업로드                          |
| [Python Create Signed URL](https://supabase.com/docs/reference/python/storage-from-createsignedurl) | Private Bucket 파일 접근을 위한 Signed URL 생성 |
| [Storage Access Control](https://supabase.com/docs/guides/storage/security/access-control)          | Storage 파일 접근 권한 및 정책 설정             |

## 12-5. 데이터베이스 보안 (RLS)

| 참고 자료                                                                                   | 설명                           |
|:--------------------------------------------------------------------------------------------|:-------------------------------|
| [Row Level Security](https://supabase.com/docs/guides/database/postgres/row-level-security) | 사용자별 데이터 접근 권한 설정 |
| [Database Security](https://supabase.com/docs/guides/database/secure-data)                  | 데이터베이스 보안 및 권한 관리 |

## 12-6. Python 라이브러리

| 참고 자료                                                     | 설명                                              |
|:--------------------------------------------------------------|:--------------------------------------------------|
| [supabase-py GitHub](https://github.com/supabase/supabase-py) | Supabase Python 라이브러리 소스 코드 및 사용 예제 |
| [supabase-py PyPI](https://pypi.org/project/supabase/)        | Python 라이브러리 설치 및 버전 확인               |

------------------------------------------------------------------------

## 마무리

Supabase를 사용할 때 가장 중요한 것은 각 테이블의 역할과 관계를 이해하는
것입니다.

모든 데이터를 하나의 테이블에 저장하는 것이 아니라,
사용자·게시글·이미지·북마크·채팅 정보를 각각의 테이블에 저장하고 ID를
통해 연결합니다.

기능을 구현하기 전에 이 가이드를 참고하고, 데이터베이스의 컬럼이나
관계를 변경해야 한다면 팀원들과 먼저 공유해 주세요.

**추가 참고 문서**
- [database.md](database.md): Supabase 가입, 프로젝트 생성, 실제 테이블 스키마, 외래 키, RLS, Storage 및 인증 설정
- [DB_use_guide.md](DB_use_guide.md): 실제 Python 코드에서 데이터를 입력하고 조회하는 방법
