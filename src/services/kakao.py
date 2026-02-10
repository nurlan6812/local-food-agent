"""카카오맵 API 클라이언트 - 식당 검색 + Playwright 크롤링"""

import os
import re
import asyncio
from typing import Optional, Dict, Any, List
from collections import Counter

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


class KakaoLocalAPI:
    """카카오 로컬 API를 활용한 식당 정보 검색"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("KAKAO_API_KEY")
        self.base_url = "https://dapi.kakao.com/v2/local/search/keyword.json"

    def search_restaurant(self, query: str, page: int = 1) -> Optional[Dict[str, Any]]:
        """식당명으로 카카오 로컬 검색"""
        if not self.api_key:
            return None

        headers = {"Authorization": f"KakaoAK {self.api_key}"}
        params = {"query": query, "category_group_code": "FD6", "size": 5, "page": page}

        try:
            response = requests.get(self.base_url, headers=headers, params=params, timeout=10)
            if response.status_code == 200:
                return response.json()
        except:
            pass
        return None

    def get_place_id_from_url(self, place_url: str) -> Optional[str]:
        """place_url에서 place_id 추출"""
        match = re.search(r'/(\d+)$', place_url)
        return match.group(1) if match else None

    def search_menu_via_serper(self, query: str) -> str:
        """Serper.dev로 식당/메뉴 정보 가져오기"""
        api_key = os.getenv("SERPER_API_KEY") or os.getenv("SERPAPI_KEY")
        if not api_key:
            return ""

        headers = {"X-API-KEY": api_key, "Content-Type": "application/json"}
        data = {"q": query, "gl": "kr", "hl": "ko"}

        try:
            response = requests.post("https://google.serper.dev/search", headers=headers, json=data, timeout=10)
            if response.status_code != 200:
                return ""

            result = response.json()
            output = []
            for item in result.get("organic", [])[:5]:
                title = item.get("title", "")
                snippet = item.get("snippet", "")
                if snippet:
                    output.append(f"{title}: {snippet}")
            return "\n".join(output)
        except:
            return ""

    def get_menu_via_playwright(self, place_id: str) -> str:
        """Playwright로 카카오맵에서 메뉴 텍스트 크롤링"""
        if not PLAYWRIGHT_AVAILABLE:
            return ""

        async def _fetch_menu():
            menu_text = ""
            try:
                async with async_playwright() as p:
                    browser = await p.chromium.launch(
                        headless=True,
                        args=['--no-sandbox', '--disable-dev-shm-usage']
                    )
                    page = await browser.new_page()
                    url = f'https://place.map.kakao.com/{place_id}'
                    await page.goto(url, wait_until='networkidle', timeout=15000)

                    try:
                        menu_tab = await page.query_selector('a[href*="menuInfo"]')
                        if menu_tab:
                            await menu_tab.click()
                            await page.wait_for_timeout(2000)
                    except:
                        pass

                    for _ in range(5):
                        await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                        await page.wait_for_timeout(400)

                    price_elements = await page.query_selector_all('//*[contains(text(), "원")]')
                    menu_lines = []
                    seen = set()

                    for price_el in price_elements:
                        try:
                            grandparent = await price_el.evaluate_handle('el => el.parentElement?.parentElement')
                            if grandparent:
                                text = await grandparent.inner_text()
                                text = ' '.join(text.split())
                                if ('원' in text and len(text) > 5 and len(text) < 80 and
                                    text not in seen and '블로그' not in text):
                                    seen.add(text)
                                    menu_lines.append(text)
                        except:
                            pass

                    menu_text = '\n'.join(menu_lines[:60])
                    await browser.close()
            except:
                pass
            return menu_text

        try:
            return asyncio.run(_fetch_menu())
        except:
            try:
                import nest_asyncio
                nest_asyncio.apply()
                loop = asyncio.get_event_loop()
                return loop.run_until_complete(_fetch_menu())
            except:
                return ""

    def get_reviews_via_playwright(self, place_id: str, max_reviews: int = 15) -> str:
        """Playwright로 카카오맵에서 후기 크롤링"""
        if not PLAYWRIGHT_AVAILABLE:
            return ""

        async def _fetch_reviews():
            result = {"rating": None, "review_count": 0, "tags": {}, "reviews": []}

            try:
                async with async_playwright() as p:
                    browser = await p.chromium.launch(
                        headless=True,
                        args=['--no-sandbox', '--disable-dev-shm-usage']
                    )
                    page = await browser.new_page()
                    url = f'https://place.map.kakao.com/{place_id}'
                    await page.goto(url, wait_until='networkidle', timeout=15000)

                    all_elements = await page.query_selector_all('a, button, span')
                    tab_clicked = False

                    for el in all_elements:
                        try:
                            text = await el.inner_text()
                            text = text.strip()
                            if '후기' in text and ('개' in text or '건' in text) and len(text) < 30:
                                await el.click()
                                await page.wait_for_timeout(2000)
                                tab_clicked = True
                                break
                        except:
                            continue

                    is_blog_fallback = False
                    if not tab_clicked:
                        blog_tab = await page.query_selector('a[href*="blog"]')
                        if blog_tab:
                            await blog_tab.click()
                            await page.wait_for_timeout(2000)
                            is_blog_fallback = True
                        else:
                            await browser.close()
                            return "매장주 요청으로 후기가 제공되지 않는 장소입니다."

                    for _ in range(5):
                        await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                        await page.wait_for_timeout(400)

                    body_text = await page.inner_text('body')
                    lines = [l.strip() for l in body_text.split('\n') if l.strip()]

                    for i, line in enumerate(lines):
                        if line == '별점' and i + 1 < len(lines):
                            try:
                                result["rating"] = float(lines[i + 1])
                            except:
                                pass
                        if '후기' in line and i + 1 < len(lines):
                            try:
                                count = int(lines[i + 1].replace(',', ''))
                                if count > result["review_count"]:
                                    result["review_count"] = count
                            except:
                                pass

                    tag_names = ['맛', '가성비', '친절', '분위기', '주차', '청결', '양']
                    for i, line in enumerate(lines):
                        if line in tag_names and i + 1 < len(lines):
                            next_line = lines[i + 1]
                            if '명' in next_line:
                                try:
                                    count = int(next_line.replace('명', '').replace(',', ''))
                                    result["tags"][line] = count
                                except:
                                    pass

                    reviews = []
                    seen = set()
                    review_keywords = ['맛있', '좋', '추천', '또', '최고', '아쉬', '별로', '짜',
                                      '친절', '불친절', '웨이팅', '기다', '양이', '가성비',
                                      '재방문', '단골', '인정', '대박', '실망', '만족', '냄새']

                    for line in lines:
                        if 15 < len(line) < 300 and line not in seen:
                            if line.startswith('http') or '원' in line[:8]:
                                continue
                            if any(skip in line for skip in ['더보기', '접기', '신고', '공유', '저장', '로그인', '바로가기']):
                                continue
                            if any(kw in line for kw in review_keywords):
                                seen.add(line)
                                reviews.append(line)
                                if len(reviews) >= max_reviews:
                                    break

                    result["reviews"] = reviews
                    result["is_blog"] = is_blog_fallback
                    await browser.close()

            except Exception as e:
                return f"후기 크롤링 실패: {e}"

            output = []
            if result["rating"]:
                output.append(f"⭐ 평점: {result['rating']}점")
            if result["review_count"]:
                output.append(f"📝 후기: {result['review_count']}개")
            if result["tags"]:
                output.append("")
                output.append("[태그별 평가]")
                for tag, count in sorted(result["tags"].items(), key=lambda x: -x[1]):
                    output.append(f"  • {tag}: {count}명")
            if result["reviews"]:
                output.append("")
                output.append(f"[최근 후기 {len(result['reviews'])}개]")
                for r in result["reviews"]:
                    output.append(f"  • {r}")

            return '\n'.join(output) if output else "후기를 찾을 수 없습니다."

        try:
            return asyncio.run(_fetch_reviews())
        except:
            try:
                import nest_asyncio
                nest_asyncio.apply()
                loop = asyncio.get_event_loop()
                return loop.run_until_complete(_fetch_reviews())
            except:
                return ""


# 싱글톤 인스턴스
_kakao: Optional[KakaoLocalAPI] = None


def get_kakao() -> KakaoLocalAPI:
    """카카오 API 싱글톤 인스턴스 반환"""
    global _kakao
    if _kakao is None:
        _kakao = KakaoLocalAPI()
    return _kakao
