"""로컬 LLM 기반 도구 결과 요약 서비스"""

import os
import time
from typing import Optional, Dict, Any
from dataclasses import dataclass

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


@dataclass
class SummaryResult:
    """요약 결과"""
    original_length: int
    summary_length: int
    summary: str
    latency_ms: float
    compression_ratio: float


# 도구별 요약 프롬프트
TOOL_PROMPTS = {
    "search_food_by_image": """다음 이미지 검색 결과에서 핵심 정보만 추출하세요:
- 음식 이름 (확실한 것만)
- 식당 이름 (있다면)
- 주요 특징 (재료, 맛 등)

불필요한 광고, 블로그 서론, 반복 내용은 제외하세요.""",

    "search_restaurant_info": """다음 식당 검색 결과에서 핵심 정보만 추출하세요:
- 식당명, 주소, 전화번호
- 대표 메뉴와 가격 (상위 5개)
- 영업시간 (있다면)
- [MAP:...] 태그는 그대로 유지

불필요한 설명이나 반복은 제외하세요.""",

    "get_restaurant_reviews": """다음 후기에서 핵심만 요약하세요:
- 평점, 후기 수
- 긍정적 의견 요약 (2-3줄)
- 부정적 의견 요약 (있다면, 1-2줄)
- 추천 메뉴

개별 후기 전체를 나열하지 말고 종합 요약만 하세요.""",

    "search_recipe_online": """다음 레시피에서 핵심만 추출하세요:
- 음식명
- 재료 목록 (분량 포함)
- 조리 순서 (간결하게)

블로그 서론, 후기, 광고는 제외하세요.""",

    "get_nutrition_info": """다음 영양정보에서 핵심만 추출하세요:
- 1인분 기준 칼로리
- 주요 영양소 (탄수화물, 단백질, 지방)
- 특이사항 (있다면)

출처나 부가 설명은 제외하세요.""",
}

# 기본 프롬프트
DEFAULT_PROMPT = """다음 내용에서 핵심 정보만 간결하게 추출하세요.
불필요한 반복, 광고, 서론은 제외하고 사실 정보만 포함하세요."""


class LocalSummarizer:
    """vLLM 기반 로컬 요약 서비스"""

    def __init__(
        self,
        base_url: str = "http://localhost:8081/v1",
        api_key: str = "local-vllm-key",
        model: str = "LGAI-EXAONE/EXAONE-3.5-7.8B-Instruct-AWQ",
        enabled: bool = True,
        min_length_to_summarize: int = 1000,  # 이 길이 이상일 때만 요약
    ):
        self.base_url = base_url
        self.api_key = api_key
        self.model = model
        self.enabled = enabled
        self.min_length = min_length_to_summarize
        self.client: Optional[OpenAI] = None
        self._initialized = False

    def _init_client(self) -> bool:
        """클라이언트 초기화 (lazy)"""
        if self._initialized:
            return self.client is not None

        self._initialized = True

        if not OPENAI_AVAILABLE:
            print("[Summarizer] openai 패키지가 설치되지 않음")
            return False

        try:
            self.client = OpenAI(
                base_url=self.base_url,
                api_key=self.api_key,
            )
            # 연결 테스트
            self.client.models.list()
            print(f"[Summarizer] vLLM 서버 연결 성공: {self.base_url}")
            return True
        except Exception as e:
            print(f"[Summarizer] vLLM 서버 연결 실패: {e}")
            self.client = None
            return False

    def is_available(self) -> bool:
        """서비스 사용 가능 여부"""
        return self.enabled and self._init_client()

    def should_summarize(self, text: str) -> bool:
        """요약이 필요한지 판단"""
        return len(text) >= self.min_length

    def summarize(
        self,
        tool_name: str,
        tool_result: str,
        max_tokens: int = 500,
    ) -> SummaryResult:
        """
        도구 결과를 요약합니다.

        Args:
            tool_name: 도구 이름
            tool_result: 도구 실행 결과
            max_tokens: 최대 출력 토큰

        Returns:
            SummaryResult 객체
        """
        original_length = len(tool_result)

        # 요약 불필요하거나 서비스 사용 불가
        if not self.should_summarize(tool_result) or not self.is_available():
            return SummaryResult(
                original_length=original_length,
                summary_length=original_length,
                summary=tool_result,
                latency_ms=0,
                compression_ratio=1.0,
            )

        # 도구별 프롬프트 선택
        system_prompt = TOOL_PROMPTS.get(tool_name, DEFAULT_PROMPT)

        start_time = time.time()

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": tool_result},
                ],
                max_tokens=max_tokens,
                temperature=0.3,  # 요약은 낮은 temperature
            )

            summary = response.choices[0].message.content
            latency_ms = (time.time() - start_time) * 1000

            return SummaryResult(
                original_length=original_length,
                summary_length=len(summary),
                summary=summary,
                latency_ms=latency_ms,
                compression_ratio=len(summary) / original_length if original_length > 0 else 1.0,
            )

        except Exception as e:
            print(f"[Summarizer] 요약 실패: {e}")
            return SummaryResult(
                original_length=original_length,
                summary_length=original_length,
                summary=tool_result,
                latency_ms=0,
                compression_ratio=1.0,
            )


# 싱글톤 인스턴스
_summarizer: Optional[LocalSummarizer] = None


def get_summarizer() -> LocalSummarizer:
    """요약 서비스 싱글톤 인스턴스 반환"""
    global _summarizer
    if _summarizer is None:
        _summarizer = LocalSummarizer(
            base_url=os.getenv("VLLM_BASE_URL", "http://localhost:8081/v1"),
            api_key=os.getenv("VLLM_API_KEY", "local-vllm-key"),
            enabled=os.getenv("ENABLE_LOCAL_SUMMARIZER", "false").lower() == "true",
            min_length_to_summarize=int(os.getenv("SUMMARIZE_MIN_LENGTH", "1000")),
        )
    return _summarizer
