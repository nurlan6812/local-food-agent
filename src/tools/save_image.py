"""새 음식 이미지 저장 도구"""

import os
import uuid
from typing import Optional
from langchain_core.tools import tool
from langgraph.config import get_stream_writer

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def upload_to_supabase_storage(local_path: str, supabase) -> str:
    ext = os.path.splitext(local_path)[1] or '.jpg'
    file_name = f"food_images/{uuid.uuid4()}{ext}"

    with open(local_path, 'rb') as f:
        file_data = f.read()

    content_type_map = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.webp': 'image/webp',
    }
    content_type = content_type_map.get(ext.lower(), 'image/jpeg')

    result = supabase.storage.from_('images').upload(
        file_name,
        file_data,
        file_options={"content-type": content_type}
    )

    public_url = supabase.storage.from_('images').get_public_url(file_name)
    return public_url


@tool
def save_food_image(
    image_url: str,
    food_name: str,
    source_type: str = "",
    restaurant_name: str = "",
    location: str = ""
) -> str:
    """
    웹에 없는 새 이미지를 데이터베이스에 저장합니다.

    Args:
        image_url: 업로드된 이미지 URL 또는 로컬 파일 경로
        food_name: 음식 이름 (AI 추론값도 OK)
        source_type: "restaurant", "home_cooked", "delivery" 중 하나 (모르면 생략)
        restaurant_name: 식당 이름 (알면)
        location: 위치/지역 (알면)

    Returns:
        저장된 image_id (update_food_image에서 사용)
    """
    from ..db.client import get_supabase_client

    try:
        try:
            writer = get_stream_writer()
        except:
            writer = lambda x: None

        supabase = get_supabase_client()

        final_url = image_url
        if os.path.exists(image_url):
            writer({"tool": "save_food_image", "status": "이미지 업로드 중..."})
            print(f"\ud83d\udce4 로컬 이미지를 Supabase Storage에 업로드 중: {image_url}")
            final_url = upload_to_supabase_storage(image_url, supabase)
            print(f"\u2705 업로드 완료: {final_url}")

        writer({"tool": "save_food_image", "status": "데이터베이스 저장 중..."})
        data = {
            "image_url": final_url,
            "food_name": food_name,
            "food_source_type": source_type if source_type else "unknown",
            "food_verified": False,
            "restaurant_verified": False,
        }

        if restaurant_name:
            data["restaurant_name"] = restaurant_name
        if location:
            data["location"] = location

        result = supabase.table("food_images").insert(data).execute()

        if result.data:
            image_id = result.data[0]["id"]
            return f"새 이미지 저장 완료. image_id: {image_id}"
        else:
            return "저장 실패: 결과 없음"

    except Exception as e:
        return f"저장 실패: {str(e)}"
