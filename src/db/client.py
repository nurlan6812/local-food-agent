"""Supabase 클라이언트"""

import os
from typing import Optional
from supabase import create_client, Client

_client: Optional[Client] = None


def get_supabase_client() -> Client:
    """Supabase 클라이언트 싱글톤 반환"""
    global _client

    if _client is None:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_ANON_KEY")

        if not url or not key:
            raise ValueError("SUPABASE_URL과 SUPABASE_ANON_KEY 환경변수를 설정하세요.")

        _client = create_client(url, key)

    return _client
