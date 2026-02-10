"""음식 이미지 정보 업데이트 도구"""

import os
from typing import Optional
from langchain_core.tools import tool
from langgraph.config import get_stream_writer

# 환경 변수 로드
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


@tool
def update_food_image(
    image_id: str,
    food_name: str = "",
    source_type: str = "",
    restaurant_name: str = "",
    location: str = ""
) -> str:
    """
    사용자가 확인해준 음식 정보로 DB를 업데이트합니다.

    Args:
        image_id: save_food_image에서 반환된 이미지 ID
        food_name: 확인된 음식 이름 → food_verified=true
        source_type: "restaurant", "home_cooked", "delivery" 중 하나
        restaurant_name: 확인된 식당 이름 → restaurant_verified=true
        location: 위치/지역

    Returns:
        업데이트 결과 메시지
    """
    from ..db.client import get_supabase_client

    try:
        # get_stream_writer는 LangGraph 컨텍스트에서만 동작
        try:
            writer = get_stream_writer()
            writer({"tool": "update_food_image", "status": "정보 업데이트 중..."})
        except:
            pass  # LangGraph 밖에서는 무시

        supabase = get_supabase_client()

        data = {}

        if food_name:
            data["food_name"] = food_name
            data["food_verified"] = True
        if source_type:
            data["food_source_type"] = source_type
        if restaurant_name:
            data["restaurant_name"] = restaurant_name
            data["restaurant_verified"] = True
        if location:
            data["location"] = location

        if not data:
            return "업데이트할 정보가 없습니다"

        result = supabase.table("food_images").update(data).eq("id", image_id).execute()

        verified_parts = []
        if data.get("food_verified"):
            verified_parts.append("음식")
        if data.get("restaurant_verified"):
            verified_parts.append("식당")

        if result.data:
            return f"업데이트 완료 (검증됨: {', '.join(verified_parts) if verified_parts else '없음'})"
        else:
            return f"업데이트 실패: image_id={image_id}를 찾을 수 없음"

    except Exception as e:
        return f"업데이트 실패: {str(e)}"
