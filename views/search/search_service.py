from DB.database import get_supabase_client
from views.common.util import AREA_LOCATIONS


def search_items(
    keyword="",
    search_type="전체",
    category="전체",
    location="전체",
    area="전체",
    start_date=None,
    end_date=None,
    page=1,
    page_size=9
):
    """검색 조건에 맞는 게시글을 페이지 단위로 조회"""

    keyword = (keyword or "").strip()

    # 페이지 번호와 페이지당 게시글 수 보정
    page = max(1, int(page))
    page_size = max(1, int(page_size))

    # Supabase range는 0부터 시작하며 끝 번호를 포함함
    start_index = (page - 1) * page_size
    end_index = start_index + page_size - 1

    supabase = get_supabase_client()

    # 전체 게시글 조회를 기본으로 하고, 입력된 조건만 적용
    query = supabase.table("lost_items").select(
        "*",
        count="exact"
    )

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
    if location != "전체":
        # 세부 장소를 선택한 경우
        query = query.eq("location", location)

    elif area != "전체":
        # 구역만 선택하고 세부 장소는 전체인 경우
        area_locations = AREA_LOCATIONS.get(area, [])

        if not area_locations:
            return [], 0

        query = query.in_("location", area_locations)

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

    # 7. 최신 게시글 순으로 정렬하고 현재 페이지 데이터만 조회
    result = (
        query
        .order("created_at", desc=True)
        .range(start_index, end_index)
        .execute()
    )

    # 현재 페이지 게시글 목록과 전체 검색 결과 수 반환
    return result.data, result.count or 0