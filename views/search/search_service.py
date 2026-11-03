from DB.database import get_supabase_client


def search_items(
    keyword="",
    search_type="전체",
    category="전체",
    location="전체",
    start_date=None,
    end_date=None
):
    """키워드와 검색 조건에 맞는 분실물/습득물 검색"""

    keyword = keyword.strip()

    # 검색 조건이 하나도 없으면 빈 결과 반환
    if (
        not keyword
        and search_type == "전체"
        and category == "전체"
        and location == "전체"
        and start_date is None
        and end_date is None
    ):
        return []

    supabase = get_supabase_client()

    query = supabase.table("lost_items").select("*")

    # 1. 키워드 검색
    if keyword:
        query = query.or_(
            f"title.ilike.%{keyword}%,"
            f"description.ilike.%{keyword}%,"
            f"category.ilike.%{keyword}%,"
            f"location.ilike.%{keyword}%"
        )

    # 2. 분실물 / 습득물 유형 필터
    if search_type == "분실물":
        query = query.eq("status", "분실")

    elif search_type == "습득물":
        query = query.eq("status", "습득")

    # 3. 카테고리 필터
    if category != "전체":
        query = query.eq("category", category)

    # 4. 장소 필터
    LOCATION_KEYWORDS = {
        "중앙도서관": ["중앙도서관", "중도"],
        "공학관": ["공학관"],
        "인문사회관": ["인문사회관"],
        "학생회관": ["학생회관"],
        "기숙사": ["기숙사"],
        "강의실": ["강의실"],
        "식당": ["식당"],
        "운동장": ["운동장"],
    }

    if location != "전체":
        keywords = LOCATION_KEYWORDS.get(location, [location])

        location_conditions = ",".join(
            f"location.ilike.%{word}%"
            for word in keywords
        )

        query = query.or_(location_conditions)

    # 5. 시작 날짜 필터
    if start_date is not None:
        query = query.gte(
            "lost_date",
            start_date.isoformat()
        )

    # 6. 종료 날짜 필터
    if end_date is not None:
        query = query.lte(
            "lost_date",
            end_date.isoformat()
        )

    # 최신 게시글 순으로 정렬
    result = (
        query
        .order("created_at", desc=True)
        .execute()
    )

    return result.data