"""영양정보 검색 도구"""

from langchain_core.tools import tool
from langgraph.config import get_stream_writer

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False

from ..services import get_searcher


def _crawl_nutrition_page(url: str) -> str:
    """영양정보 페이지 본문 크롤링"""
    if not BS4_AVAILABLE:
        return ""

    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

        if 'blog.naver.com' in url and 'm.blog' not in url:
            url = url.replace('blog.naver.com', 'm.blog.naver.com')

        resp = requests.get(url, headers=headers, timeout=10)
        resp.encoding = 'utf-8'

        if resp.status_code != 200:
            return ""

        soup = BeautifulSoup(resp.text, 'html.parser')

        for tag in soup(['script', 'style']):
            tag.decompose()

        if soup.body:
            text = soup.body.get_text(separator='\n')
            lines = [l.strip() for l in text.split('\n') if l.strip()]
            return '\n'.join(lines)[:2000]

    except:
        return ""

    return ""


@tool
def get_nutrition_info(query: str) -> str:
    """
    칼로리, 영양성분, 열량, 탄수화물, 단백질 등을 물으면 반드시 이 도구를 사용하세요.
    직접 영양정보를 답변하지 말고 이 도구로 검색하세요.

    Args:
        query: 검색 쿼리 (예: "김치찌개 칼로리", "스타볅스 아메리카노 열량")

    Returns:
        영양정보 검색 결과
    """
    writer = get_stream_writer()
    writer({"tool": "get_nutrition_info", "status": "영양 정보 검색 중..."})

    searcher = get_searcher()
    search_result = searcher.search_text(query)

    if "error" in search_result:
        return f"검색 실패: {search_result['error']}"

    organic = search_result.get("organic_results", [])

    if not organic:
        return f"'{query}' 검색 결과가 없습니다."

    writer({"tool": "get_nutrition_info", "status": f"검색 결과 {len(organic)}개 분석 중..."})

    output = [f"[검색: {query}]"]

    for item in organic[:3]:
        title = item.get("title", "")
        link = item.get("link", "")

        content = _crawl_nutrition_page(link)

        if content:
            output.append(f"\n=== {title} ===")
            output.append(f"출처: {link}")
            output.append(content)

    writer({"tool": "get_nutrition_info", "status": "분석 완료!"})

    return "\n".join(output)
