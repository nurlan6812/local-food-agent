"""Serper.dev API 클라이언트 - Google Lens + 텍스트 검색"""

import os
import re
import base64
from pathlib import Path
from typing import Optional, Dict, Any, List

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


class SerperImageSearcher:
    """Serper.dev를 활용한 이미지 검색기

    Google Lens + 텍스트 검색 지원
    로컬 파일도 지원 (임시 업로드)
    """

    def __init__(self, api_key: Optional[str] = None):
        self.serper_key = api_key or os.getenv("SERPER_API_KEY")
        self.serpapi_key = os.getenv("SERPAPI_KEY")
        self.api_key = self.serper_key
        self.lens_url = "https://google.serper.dev/lens"
        self.search_url = "https://google.serper.dev/search"
        self.serpapi_url = "https://serpapi.com/search"

    def _apply_exif_orientation(self, file_path: str) -> str:
        """EXIF orientation을 적용한 이미지를 임시 파일로 저장"""
        try:
            from PIL import Image, ExifTags

            img = Image.open(file_path)
            orientation_key = None
            for key in ExifTags.TAGS.keys():
                if ExifTags.TAGS[key] == 'Orientation':
                    orientation_key = key
                    break

            exif = img._getexif()
            if exif and orientation_key and orientation_key in exif:
                orientation = exif[orientation_key]

                if orientation == 3:
                    img = img.rotate(180, expand=True)
                elif orientation == 6:
                    img = img.rotate(270, expand=True)
                elif orientation == 8:
                    img = img.rotate(90, expand=True)
                else:
                    return file_path

                import random
                pixels = img.load()
                x, y = img.width - 1, img.height - 1
                r, g, b = pixels[x, y][:3] if len(pixels[x, y]) >= 3 else (pixels[x, y], pixels[x, y], pixels[x, y])
                pixels[x, y] = (r, g, (b + random.randint(1, 5)) % 256)

                import tempfile
                temp_file = tempfile.NamedTemporaryFile(suffix='.jpeg', delete=False)
                img.save(temp_file.name, format='JPEG', quality=90)
                return temp_file.name

        except Exception:
            pass
        return file_path

    def upload_image(self, file_path: str) -> Optional[str]:
        """로컬 이미지를 임시 호스팅 서비스에 업로드"""
        if not os.path.exists(file_path):
            return None

        file_path = self._apply_exif_orientation(file_path)

        upload_services = [
            self._upload_to_litterbox,
            self._upload_to_imgbb,
            self._upload_to_freeimage,
        ]

        for upload_func in upload_services:
            try:
                url = upload_func(file_path)
                if url:
                    return url
            except Exception:
                continue
        return None

    def _upload_to_imgbb(self, file_path: str) -> Optional[str]:
        with open(file_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode()

        response = requests.post(
            'https://api.imgbb.com/1/upload',
            data={
                'key': 'da2d77ea2fc52e04d4e62a6d3906f48f',
                'image': image_data,
                'expiration': 600,
            },
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                return data['data']['url']
        return None

    def _upload_to_freeimage(self, file_path: str) -> Optional[str]:
        with open(file_path, 'rb') as f:
            response = requests.post(
                'https://freeimage.host/api/1/upload',
                data={'key': '6d207e02198a847aa98d0a2a901485a5'},
                files={'source': f},
                timeout=30
            )

        if response.status_code == 200:
            data = response.json()
            if data.get('status_code') == 200:
                return data['image']['url']
        return None

    def _upload_to_litterbox(self, file_path: str) -> Optional[str]:
        with open(file_path, 'rb') as f:
            response = requests.post(
                'https://litterbox.catbox.moe/resources/internals/api.php',
                data={'reqtype': 'fileupload', 'time': '1h'},
                files={'fileToUpload': f},
                timeout=60
            )

        if response.status_code == 200:
            url = response.text.strip()
            if url.startswith('http'):
                return url
        return None

    def get_image_url(self, image_source: str) -> Optional[str]:
        """이미지 소스(URL 또는 로컬 경로)에서 공개 URL 획득"""
        if image_source.startswith('http://') or image_source.startswith('https://'):
            return image_source

        if os.path.exists(image_source):
            uploaded_url = self.upload_image(image_source)
            if uploaded_url:
                return uploaded_url
        return None

    def search_with_lens(self, image_url: str) -> Dict[str, Any]:
        """Google Lens로 이미지 검색 (Serper.dev 우선)"""
        if not REQUESTS_AVAILABLE:
            return {"error": "requests 라이브러리가 설치되지 않았습니다."}

        # Serper.dev 우선
        if self.serper_key:
            try:
                headers = {
                    "X-API-KEY": self.serper_key,
                    "Content-Type": "application/json"
                }
                data = {"url": image_url, "gl": "kr", "hl": "ko"}
                response = requests.post(self.lens_url, headers=headers, json=data, timeout=30)
                response.raise_for_status()
                result = response.json()
                organic = result.get("organic", [])
                if organic:
                    return {
                        "visual_matches": organic,
                        "text": [],
                        "knowledge_graph": {}
                    }
            except Exception:
                pass

        # SerpAPI 폴백
        if self.serpapi_key:
            try:
                params = {
                    "engine": "google_lens",
                    "url": image_url,
                    "api_key": self.serpapi_key,
                    "hl": "ko",
                    "country": "kr"
                }
                response = requests.get(self.serpapi_url, params=params, timeout=30)
                response.raise_for_status()
                result = response.json()
                return {
                    "visual_matches": result.get("visual_matches", []),
                    "text": result.get("text_results", []),
                    "knowledge_graph": result.get("knowledge_graph", {})
                }
            except Exception:
                pass

        return {"error": "API 키가 설정되지 않았습니다."}

    def search_with_combined(self, image_url: str) -> Dict[str, Any]:
        """여러 검색 방법을 조합하여 최상의 결과 반환"""
        lens_result = self.search_with_lens(image_url)
        if "error" not in lens_result:
            return lens_result
        return {"error": "검색 결과를 찾지 못했습니다."}

    def search_text(self, query: str) -> Dict[str, Any]:
        """Serper 텍스트 검색"""
        if not self.api_key:
            return {"error": "SERPER_API_KEY가 설정되지 않았습니다."}

        headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json"
        }
        data = {"q": query, "gl": "kr", "hl": "ko"}

        try:
            response = requests.post(self.search_url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            result = response.json()
            return {
                "organic_results": result.get("organic", []),
                "answer_box": result.get("answerBox", {})
            }
        except requests.RequestException as e:
            return {"error": f"API 요청 실패: {str(e)}"}


# 싱글톤 인스턴스
_searcher: Optional[SerperImageSearcher] = None


def get_searcher() -> SerperImageSearcher:
    """검색기 싱글톤 인스턴스 반환"""
    global _searcher
    if _searcher is None:
        _searcher = SerperImageSearcher()
    return _searcher
