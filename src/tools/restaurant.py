"""식당 검색 및 후기 도구"""

from langchain_core.tools import tool
from langgraph.config import get_stream_writer

try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

from ..services import get_kakao


@tool
def search_restaurant_info(query: str, page: int = 1) -> str:
    """
    맛집, 식당, 메뉴, 가격을 찾을 때 이 도구를 사용하세요.
    식당명으로 검색하면 메뉴명, 가격, 주소, 전화번호를 알 수 있습니다.
    "다른 맛집", "더 추천" 요청 시 page=2,3으로 다음 페이지를 검색하세요.

    Args:
        query: 검색어 (식당명, 지역+음식, 지역+맛집 등)
        page: 페이지 번호 (기본 1, 다른 결과 원하면 2,3 사용)

    Returns:
        식당 정보 (이름, 주소, 전화번호, 카테고리, 메뉴, 가격)
    """
    writer = get_stream_writer()
    writer({"tool": "search_restaurant_info", "status": "카카오맵 검색 중..."})

    kakao = get_kakao()
    result = kakao.search_restaurant(query, page=page)

    output = []
    place_id = None

    if result and result.get("documents"):
        first_place = result["documents"][0]
        place_url = first_place.get("place_url", "")
        place_id = kakao.get_place_id_from_url(place_url) if place_url else None

        coords_list = []

        for i, place in enumerate(result["documents"][:3], 1):
            output.append(f"[{i}] {place.get('place_name', '')}")
            output.append(f"   주소: {place.get('road_address_name', '') or place.get('address_name', '')}")
            output.append(f"   전화: {place.get('phone', '')}")
            output.append(f"   카테고리: {place.get('category_name', '')}")
            p_url = place.get('place_url', '')
            if p_url:
                output.append(f"   \ud83d\uddfa\ufe0f 지도: {p_url}")
            output.append("")

            x = place.get('x', '')
            y = place.get('y', '')
            name = place.get('place_name', '')
            address = place.get('road_address_name', '') or place.get('address_name', '')
            phone = place.get('phone', '')
            category = place.get('category_name', '').split(' > ')[-1] if place.get('category_name') else ''
            place_url = place.get('place_url', '')
            if x and y:
                info = f"{name}|{address}|{phone}|{category}|{place_url}"
                coords_list.append(f"{y},{x},{info}")

        if coords_list:
            coords_str = ";".join(coords_list)
            output.insert(0, f"[MAP:{coords_str}]")

    menu_text = ""
    if place_id and PLAYWRIGHT_AVAILABLE:
        writer({"tool": "search_restaurant_info", "status": "메뉴 정보 수집 중..."})
        menu_text = kakao.get_menu_via_playwright(place_id)

    if menu_text:
        output.append("[메뉴판]")
        output.append(menu_text)
    else:
        writer({"tool": "search_restaurant_info", "status": "메뉴 검색 중..."})
        menu_info = kakao.search_menu_via_serper(query)
        if menu_info:
            output.append("[메뉴 검색 결과]")
            output.append(menu_info)

    if not output:
        return f"'{query}' 검색 결과 없음"

    return "\n".join(output)


@tool
def get_restaurant_reviews(restaurant_name: str) -> str:
    """
    후기, 리뷰, 평점, 평가, 비교를 물으면 반드시 이 도구를 사용하세요.
    식당 비교 시 각 식당마다 이 도구를 호출하세요.

    Args:
        restaurant_name: 식당 이름

    Returns:
        식당 후기 목록 및 요약
    """
    if not PLAYWRIGHT_AVAILABLE:
        return "Playwright가 설치되지 않아 후기를 가져올 수 없습니다."

    kakao = get_kakao()
    result = kakao.search_restaurant(restaurant_name)

    if not result or not result.get("documents"):
        return f"'{restaurant_name}' 식당을 찾을 수 없습니다."

    place = result["documents"][0]
    place_name = place.get("place_name", "")
    place_url = place.get("place_url", "")
    address = place.get("address_name", "")

    place_id = kakao.get_place_id_from_url(place_url)

    if not place_id:
        return f"'{restaurant_name}' 후기 페이지를 찾을 수 없습니다."

    reviews_text = kakao.get_reviews_via_playwright(place_id, max_reviews=15)

    output = []
    output.append(f"[{place_name} 후기]")
    output.append(f"\ud83d\udccd 주소: {address}")
    output.append(f"\ud83d\udd17 카카오맵: {place_url}")
    output.append("")

    if reviews_text:
        output.append("\ud83d\udcdd 방문자 후기:")
        output.append(reviews_text)
        output.append("")
        output.append("[요약 요청] 위 후기들을 분석해서 장점, 단점, 추천 메뉴 등을 요약해주세요.")
    else:
        output.append("후기를 찾을 수 없습니다.")

    return "\n".join(output)
