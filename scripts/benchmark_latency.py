#!/usr/bin/env python
"""
Latency 벤치마크 스크립트
- 기존 방식 (요약 없음) vs 로컬 LLM 요약 방식 비교
"""

import os
import sys
import time
import json
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Any

# 프로젝트 루트 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agent import KoreanFoodAgent
from src.services.summarizer import get_summarizer, LocalSummarizer


@dataclass
class BenchmarkResult:
    """벤치마크 결과"""
    test_name: str
    query: str
    mode: str  # "baseline" or "with_summarizer"

    # 시간 측정 (ms)
    total_latency_ms: float
    tool_latency_ms: float
    summarizer_latency_ms: float
    llm_latency_ms: float

    # 토큰 정보
    tool_result_length: int
    summarized_length: int
    compression_ratio: float

    # 응답
    response_preview: str


def run_single_benchmark(
    agent: KoreanFoodAgent,
    query: str,
    test_name: str,
    use_summarizer: bool = False,
) -> BenchmarkResult:
    """단일 벤치마크 실행"""

    summarizer = get_summarizer() if use_summarizer else None

    # 시간 측정 시작
    start_total = time.time()

    # 에이전트 실행
    response = agent.chat(query)

    total_latency = (time.time() - start_total) * 1000

    # 결과 생성
    return BenchmarkResult(
        test_name=test_name,
        query=query,
        mode="with_summarizer" if use_summarizer else "baseline",
        total_latency_ms=total_latency,
        tool_latency_ms=0,  # TODO: 도구별 측정 추가 필요
        summarizer_latency_ms=0,  # TODO: 요약 시간 측정 추가 필요
        llm_latency_ms=0,  # TODO: LLM 호출 시간 측정 추가 필요
        tool_result_length=0,
        summarized_length=0,
        compression_ratio=1.0,
        response_preview=response[:200] + "..." if len(response) > 200 else response,
    )


def run_benchmark_suite():
    """벤치마크 스위트 실행"""

    print("=" * 60)
    print("Korean Food Agent Latency Benchmark")
    print("=" * 60)

    # 테스트 쿼리
    test_cases = [
        ("simple_greeting", "안녕"),
        ("restaurant_search", "강남역 비빔밥 맛집 추천해줘"),
        ("recipe_search", "김치찌개 레시피 알려줘"),
        ("nutrition_info", "비빔밥 칼로리 알려줘"),
    ]

    results: List[BenchmarkResult] = []

    # Baseline (요약 없음)
    print("\n[1/2] Baseline 테스트 (요약 없음)")
    print("-" * 40)

    os.environ["ENABLE_LOCAL_SUMMARIZER"] = "false"
    agent_baseline = KoreanFoodAgent(provider="gemini")

    for test_name, query in test_cases:
        print(f"  - {test_name}: {query[:30]}...")
        try:
            result = run_single_benchmark(agent_baseline, query, test_name, use_summarizer=False)
            results.append(result)
            print(f"    \u2192 {result.total_latency_ms:.0f}ms")
        except Exception as e:
            print(f"    \u2192 실패: {e}")

        # 세션 초기화
        agent_baseline.clear_history()
        time.sleep(1)  # Rate limit 방지

    # With Summarizer (요약 적용)
    print("\n[2/2] Summarizer 테스트 (로컬 LLM 요약)")
    print("-" * 40)

    os.environ["ENABLE_LOCAL_SUMMARIZER"] = "true"

    # vLLM 서버 확인
    summarizer = get_summarizer()
    if not summarizer.is_available():
        print("  \u26a0\ufe0f vLLM 서버가 실행 중이 아닙니다. Summarizer 테스트 스킵.")
    else:
        agent_summarizer = KoreanFoodAgent(provider="gemini")

        for test_name, query in test_cases:
            print(f"  - {test_name}: {query[:30]}...")
            try:
                result = run_single_benchmark(agent_summarizer, query, test_name, use_summarizer=True)
                results.append(result)
                print(f"    \u2192 {result.total_latency_ms:.0f}ms")
            except Exception as e:
                print(f"    \u2192 실패: {e}")

            agent_summarizer.clear_history()
            time.sleep(1)

    # 결과 출력
    print("\n" + "=" * 60)
    print("Results Summary")
    print("=" * 60)

    # 테스트별 비교
    baseline_results = {r.test_name: r for r in results if r.mode == "baseline"}
    summarizer_results = {r.test_name: r for r in results if r.mode == "with_summarizer"}

    print(f"\n{'Test':<20} {'Baseline':>12} {'Summarizer':>12} {'Diff':>10}")
    print("-" * 56)

    for test_name, query in test_cases:
        baseline = baseline_results.get(test_name)
        summarized = summarizer_results.get(test_name)

        b_time = f"{baseline.total_latency_ms:.0f}ms" if baseline else "N/A"
        s_time = f"{summarized.total_latency_ms:.0f}ms" if summarized else "N/A"

        if baseline and summarized:
            diff = summarized.total_latency_ms - baseline.total_latency_ms
            diff_str = f"{diff:+.0f}ms"
        else:
            diff_str = "N/A"

        print(f"{test_name:<20} {b_time:>12} {s_time:>12} {diff_str:>10}")

    # 결과 저장
    output_file = Path(__file__).parent.parent / "benchmark_results.json"
    with open(output_file, "w") as f:
        json.dump([asdict(r) for r in results], f, indent=2, ensure_ascii=False)

    print(f"\n결과 저장: {output_file}")


if __name__ == "__main__":
    run_benchmark_suite()
