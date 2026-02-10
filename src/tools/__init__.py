"""한국 음식 에이전트 도구 모듈"""

from .image import search_food_by_image
from .restaurant import search_restaurant_info, get_restaurant_reviews
from .recipe import search_recipe_online
from .nutrition import get_nutrition_info
from .save_image import save_food_image
from .update_image import update_food_image

# 모든 도구 목록
ALL_TOOLS = [
    search_food_by_image,      # 이미지 → 음식 인식
    search_restaurant_info,    # 식당 검색
    search_recipe_online,      # 레시피 검색
    get_restaurant_reviews,    # 후기 크롤링
    get_nutrition_info,        # 영양정보 검색
    save_food_image,           # 새 이미지 저장 (DB)
    update_food_image,         # 검증 정보 업데이트 (DB)
]

__all__ = [
    "search_food_by_image",
    "search_restaurant_info",
    "search_recipe_online",
    "get_restaurant_reviews",
    "get_nutrition_info",
    "save_food_image",
    "update_food_image",
    "ALL_TOOLS",
]
