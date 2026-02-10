"""레시피 검색 도구"""

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


def _crawl_recipe_fast(url: str) -> str:
    """requests로 빠른 레시피 크롤링"""
    if not BS4_AVAILABLE:
        return "BeautifulSoup 라이브러리가 필요합니다."

    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        resp = requests.get(url, headers=headers, timeout=10)
        resp.encoding = 'utf-8'

        if resp.status_code != 200:
            return f"페이지 로드 실패: {url}"

        soup = BeautifulSoup(resp.text, 'html.parser')

        if '10000recipe.com' in url:
            output = []

            main_img = soup.select_one('#main_thumbs img, .view2_pic_best img, .centeredcrop img')
            if main_img:
                img_url = main_img.get('src', '') or main_img.get('data-src', '')
                if img_url and img_url.startswith('http') and 'btn_' not in img_url and 'icon' not in img_url:
                    output.append(f"[IMAGE:{img_url}]")

            title_el = soup.select_one('.view2_summary h3, .view2_summary_tit')
            if title_el:
                output.append(f"[{title_el.get_text(strip=True)}]")

            output.append(f"출처: {url}")

            desc_el = soup.select_one('.view2_summary_in')
            if desc_el:
                output.append(f"\n{desc_el.get_text(strip=True)}")

            info_els = soup.select('.view2_summary_info span')
            if info_els:
                info_text = ' | '.join([el.get_text(strip=True) for el in info_els])
                output.append(f"({info_text})")

            ingredients = []
            for li in soup.select('.ready_ingre3 li'):
                text = li.get_text(strip=True).replace('구매', '').strip()
                if text:
                    ingredients.append(text)
            if ingredients:
                output.append("\n[재료]")
                for ing in ingredients[:20]:
                    output.append(f"  - {ing}")

            steps = []
            for step in soup.select('.view_step_cont'):
                text = step.get_text(strip=True)
                if text:
                    steps.append(text)
            if steps:
                output.append("\n[조리 순서]")
                for i, step in enumerate(steps[:15], 1):
                    if len(step) > 200:
                        step = step[:200] + "..."
                    output.append(f"  {i}. {step}")

            return "\n".join(output)

        else:
            if 'blog.naver.com' in url and 'm.blog.naver.com' not in url:
                url = url.replace('blog.naver.com', 'm.blog.naver.com')
                resp = requests.get(url, headers=headers, timeout=10)
                soup = BeautifulSoup(resp.text, 'html.parser')
                content = soup.select_one('.se-main-container, #postViewArea, .post-view')
            else:
                content = soup.select_one('article, .post-content, .entry-content, main, .content')
                if not content:
                    content = soup.body

            if content:
                text = content.get_text(separator='\n')
                lines = [l.strip() for l in text.split('\n') if l.strip()]
                body_text = '\n'.join(lines)[:3500]
                return f"[레시피]\n출처: {url}\n\n{body_text}"

    except Exception as e:
        return f"크롤링 실패: {str(e)}\nURL: {url}"

    return f"레시피 내용을 추출하지 못했습니다.\nURL: {url}"


@tool
def search_recipe_online(query: str) -> str:
    """
    레시피, 만드는 법, 요리법, 조리법을 물으면 반드시 이 도구를 사용하세요.
    직접 레시피를 답변하지 말고 이 도구로 검색하세요.
    Args:
        query: 검색 쿼리 (예: "김치찌개 레시피", "백종원 된장찌개")

    Returns:
        레시피 정보 (재료, 조리 순서)
    """
    writer = get_stream_writer()
    writer({"tool": "search_recipe_online", "status": "레시피 검색 중..."})

    searcher = get_searcher()
    search_result = searcher.search_text(query)

    if "error" in search_result:
        return f"검색 실패: {search_result['error']}"

    organic = search_result.get("organic_results", [])

    if not organic:
        return f"'{query}' 검색 결과가 없습니다."

    writer({"tool": "search_recipe_online", "status": "레시피 페이지 분석 중..."})
    output = [f"[검색: {query}]"]
    for i, item in enumerate(organic[:1], 1):
        link = item.get("link", "")
        recipe_data = _crawl_recipe_fast(link)
        output.append(f"\n=== 레시피 {i} ===\n{recipe_data}")

    return "\n".join(output)
