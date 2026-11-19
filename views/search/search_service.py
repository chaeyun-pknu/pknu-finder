from DB.database import get_supabase_client
from views.common.util import AREA_LOCATIONS


def search_items(
    keyword="",
    search_type="전체",
    category="전체",
    location="전체",
    area="전체",
    start_date=None,
    end_date=None
):
    """키워드와 검색 조건에 맞는 분실물/습득물 검색"""

    keyword = keyword.strip()

    # 1. 검색 조건이 하나도 없는 경우
    if (
        not keyword
        and search_type == "전체"
        and category == "전체"
        and area == "전체"
        and location == "전체"
        and start_date is None
        and end_date is None
    ):
        return []

    supabase = get_supabase_client()

    query = supabase.table("lost_items").select("*")

    # 2. 키워드 검색
    if keyword:
        query = query.or_(
            f"title.ilike.%{keyword}%,"
            f"description.ilike.%{keyword}%,"
            f"category.ilike.%{keyword}%,"
            f"location.ilike.%{keyword}%"
        )

    # 3. 분실물 / 습득물 유형 필터
    if search_type == "분실물":
        query = query.eq("status", "분실")

    elif search_type == "습득물":
        query = query.eq("status", "습득")

    # 4. 카테고리 필터
    if category != "전체":
        query = query.eq("category", category)

    # 5. 장소 필터
    if location != "전체":
        # 세부 장소를 선택한 경우
        query = query.eq("location", location)

    elif area != "전체":
        # 구역만 선택하고 세부 장소는 전체인 경우
        area_locations = AREA_LOCATIONS.get(area, [])

        if area_locations:
            query = query.in_("location", area_locations)
        else:
            return []

    # 6. 시작 날짜 필터
    if start_date is not None:
        query = query.gte(
            "lost_date",
            start_date.isoformat()
        )

    # 7. 종료 날짜 필터
    if end_date is not None:
        query = query.lte(
            "lost_date",
            end_date.isoformat()
        )

    # 8. 최신 게시글 순으로 정렬
    result = (
        query
        .order("created_at", desc=True)
        .execute()
    )

    return result.data