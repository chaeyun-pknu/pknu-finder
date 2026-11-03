from database import get_supabase_client


def search_items(keyword, search_type="전체"):
    """키워드와 검색 유형에 맞는 분실물/습득물 검색"""

    keyword = keyword.strip()

    if not keyword:
        return []

    supabase = get_supabase_client()

    query = (
        supabase.table("lost_items")
        .select("*")
        .or_(
            f"title.ilike.%{keyword}%,"
            f"description.ilike.%{keyword}%,"
            f"category.ilike.%{keyword}%"
        )
    )

    # 분실물 또는 습득물 필터링
    if search_type == "분실물":
        query = query.eq("status", "분실")
    elif search_type == "습득물":
        query = query.eq("status", "습득")

    result = query.order("created_at", desc=True).execute()

    return result.data