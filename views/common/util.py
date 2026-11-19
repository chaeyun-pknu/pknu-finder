import streamlit as st

def load_css(css_path):
    if not css_path.exists():
        st.error(f"CSS 파일을 찾을 수 없습니다: {css_path}")
        return

    with open(css_path, "r", encoding="utf-8") as file:
        st.markdown(
            f"<style>{file.read()}</style>",
            unsafe_allow_html=True
        )

# 부경대학교 대연캠퍼스 구역별 장소 목록
AREA_LOCATIONS = {
    "A구역": [
        "A11 대학본부",
        "A12 웅비관",
        "A13 누리관",
        "A15 향파관",
        "A17 워커하우스",
        "A21 미래관",
        "A22 디자인관",
        "A23 나래관",
        "A26 부산창업카페 2호점",
    ],
    "B구역": [
        "B11 위드센터",
        "B12 나비센터",
        "B13 충무관",
        "B14 환경해양관",
        "B15 자연과학1관",
        "B16 수위실(후문)",
        "B21 가온관",
        "B22 청운관",
    ],
    "C구역": [
        "C11 수산질병관리원",
        "C12 장영실관",
        "C13 해양공동연구관",
        "C14 부경대학교 어린이집",
        "C15 수산과학2관",
        "C21 수산과학관",
        "C22 건축관",
        "C23 호연관",
        "C24 자연과학2관",
        "C25 인문사회경영관",
        "C26 해양수산LMO격리사육동",
        "C27 수조실험동",
        "C28 아름관",
    ],
    "D구역": [
        "D11 행복기숙사",
        "D12 테니스장",
        "D13 대운동장",
        "D14 한울관",
        "D15 창의관",
        "D16 정보융합관",
        "D21 대학극장",
        "D22 체육관",
        "D23 안전관리관",
        "D24 수상레저관",
    ],
    "E구역": [
        "E11 세종1관",
        "E12 세종2관",
        "E13 공학1관",
        "E14 학술정보관",
        "E16 한솔관",
        "E18 한어울터",
        "E21 공학2관",
        "E22 동원 장보고관",
        "E23 부경컨벤션홀",
        "E26 솔동산",
        "E27 양어장",
        "E28 양어장주차장",
        "E29 양어장관리사",
    ],
    "기타 장소": [
        "U 선박공작실",
        "백경광장",
        "잔디밭",
        "정문",
        "후문",
        "교내 보행로",
        "기타",
    ],
}

# 검색 화면에서 사용할 전체 장소 목록
ALL_LOCATIONS = [
    location
    for locations in AREA_LOCATIONS.values()
    for location in locations
]