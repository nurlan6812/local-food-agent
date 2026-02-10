"""한국 음식 에이전트 FastAPI 백엔드"""

import os
import sys
import base64
import tempfile
from pathlib import Path

# 프로젝트 루트 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

# .env 로드
env_file = Path(__file__).parent.parent / '.env'
if env_file.exists():
    for line in env_file.read_text().split('\n'):
        if line and not line.startswith('#') and '=' in line:
            key, value = line.split('=', 1)
            os.environ[key.strip()] = value.strip()

import re
import uuid
from typing import Optional, List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import json

from src.agent import KoreanFoodAgent

app = FastAPI(title="Korean Food Agent API", version="1.0.0")

# CORS 설정 - 프론트엔드에서 접근 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 세션별 에이전트 관리
agents: dict[str, KoreanFoodAgent] = {}


def get_or_create_agent(session_id: str) -> KoreanFoodAgent:
    """세션 ID로 에이전트 가져오거나 생성"""
    if session_id not in agents:
        provider = os.getenv("MODEL_PROVIDER", "vllm")
        agents[session_id] = KoreanFoodAgent(provider=provider)
    return agents[session_id]


class ImageData(BaseModel):
    data: str  # base64 인코딩된 이미지 데이터
    mime_type: str = "image/jpeg"


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    images: Optional[List[ImageData]] = None  # base64 이미지 리스트


def save_base64_image(image_data: ImageData) -> str:
    """base64 이미지를 임시 파일로 저장하고 경로 반환"""
    # MIME 타입에서 확장자 추출
    ext_map = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/gif": ".gif",
        "image/webp": ".webp",
    }
    ext = ext_map.get(image_data.mime_type, ".jpg")

    # 임시 파일 생성
    temp_file = tempfile.NamedTemporaryFile(suffix=ext, delete=False)

    # base64 디코딩 후 파일 저장
    image_bytes = base64.b64decode(image_data.data)
    temp_file.write(image_bytes)
    temp_file.close()

    return temp_file.name


class ChatResponse(BaseModel):
    response: str
    session_id: str
    map_url: Optional[str] = None
    images: list[str] = []


def extract_media_tags(text: str) -> tuple[str, Optional[str], list[str]]:
    """[MAP:...], [IMAGE:url] 태그 추출"""
    map_url = None
    images = []

    # MAP 태그 추출 (좌표 형식 또는 URL 형식 모두 지원)
    map_pattern = r'\[MAP:([^\]]+)\]'
    map_match = re.search(map_pattern, text)
    if map_match:
        map_url = map_match.group(1)
        text = re.sub(map_pattern, '', text)

    # IMAGE 태그 추출
    img_pattern = r'\[IMAGE:(https?://[^\]]+)\]'
    images = re.findall(img_pattern, text)
    text = re.sub(img_pattern, '', text)
    text = re.sub(r'\[검색 결과 이미지\]\s*', '', text)

    # Plan: 내부 추론 제거
    text = re.sub(r'Plan:.*?(?=\n\n|\Z)', '', text, flags=re.DOTALL)
    text = text.strip()

    return text, map_url, images


@app.get("/")
async def root():
    return {"message": "Korean Food Agent API", "version": "1.0.0"}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """동기 채팅 API"""
    session_id = request.session_id or str(uuid.uuid4())
    agent = get_or_create_agent(session_id)

    try:
        # 이미지가 있으면 임시 파일로 저장하고 경로를 메시지에 추가
        message = request.message
        temp_files = []

        if request.images:
            for img in request.images:
                temp_path = save_base64_image(img)
                temp_files.append(temp_path)

            # 이미지 경로를 메시지 앞에 추가
            image_paths = " ".join(temp_files)
            message = f"{image_paths} {message}"

        response = agent.chat(message)
        text, map_url, images = extract_media_tags(response)

        # 임시 파일 정리
        for temp_path in temp_files:
            try:
                os.unlink(temp_path)
            except:
                pass

        return ChatResponse(
            response=text,
            session_id=session_id,
            map_url=map_url,
            images=images
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """스트리밍 채팅 API"""
    session_id = request.session_id or str(uuid.uuid4())
    agent = get_or_create_agent(session_id)

    # 이미지가 있으면 임시 파일로 저장
    message = request.message
    temp_files = []

    if request.images:
        for img in request.images:
            temp_path = save_base64_image(img)
            temp_files.append(temp_path)

        # 이미지 경로를 메시지 앞에 추가
        image_paths = " ".join(temp_files)
        message = f"{image_paths} {message}"

    def generate():
        try:
            current_tool = None
            final_text = ""
            tool_map_url = None
            tool_images = []
            text_started = False

            # 세션 ID 전송
            yield f"data: {json.dumps({'type': 'session', 'session_id': session_id})}\n\n"

            for item in agent.stream(message):
                # 여러 stream_mode 사용 시 (mode, chunk) 튜플 형식
                if isinstance(item, tuple) and len(item) == 2:
                    mode, chunk = item

                    # Custom 이벤트 처리 (도구 진행 상황)
                    if mode == "custom":
                        if isinstance(chunk, dict):
                            tool_name = chunk.get("tool", "")
                            status_msg = chunk.get("status", "")
                            if tool_name and status_msg:
                                yield f"data: {json.dumps({'type': 'tool_progress', 'tool': tool_name, 'status': status_msg})}\n\n"
                        continue

                    # Messages 모드일 때만 아래 로직 실행
                    if mode != "messages":
                        continue

                    # Messages 모드의 chunk는 (message, metadata) 튜플일 수 있음
                    if isinstance(chunk, tuple) and len(chunk) == 2:
                        chunk, _ = chunk  # message만 추출
                else:
                    chunk = item

                # 도구 호출 감지
                if hasattr(chunk, 'tool_call_chunks') and chunk.tool_call_chunks:
                    for tc in chunk.tool_call_chunks:
                        tool_name = tc.get("name", "")
                        tool_args = tc.get("args", "")
                        if tool_name and tool_name != current_tool:
                            current_tool = tool_name
                            import logging
                            logging.getLogger("uvicorn.error").warning(f"[TOOL_CALL] {tool_name} args={tool_args}")
                            yield f"data: {json.dumps({'type': 'tool', 'tool': tool_name, 'status': 'start'})}\n\n"

                # 도구 완료 - 도구 결과에서 MAP 태그 직접 추출
                elif hasattr(chunk, 'type') and chunk.type == "tool":
                    if current_tool:
                        yield f"data: {json.dumps({'type': 'tool', 'tool': current_tool, 'status': 'done'})}\n\n"
                        # 도구 결과에서 MAP/IMAGE 태그 추출
                        tool_content = chunk.content if isinstance(chunk.content, str) else str(chunk.content)
                        map_match = re.search(r'\[MAP:([^\]]+)\]', tool_content)
                        if map_match and not tool_map_url:
                            tool_map_url = map_match.group(1)
                        img_matches = re.findall(r'\[IMAGE:(https?://[^\]]+)\]', tool_content)
                        if img_matches:
                            tool_images.extend(img_matches)
                    current_tool = None

                # AI 응답 텍스트
                elif hasattr(chunk, 'content') and chunk.content:
                    if not (hasattr(chunk, 'tool_calls') and chunk.tool_calls):
                        if isinstance(chunk.content, str):
                            txt = chunk.content
                            if not text_started:
                                txt = txt.lstrip('\n')
                                if txt:
                                    text_started = True
                            if txt:
                                final_text += txt
                                yield f"data: {json.dumps({'type': 'text', 'content': txt})}\n\n"
                        elif isinstance(chunk.content, list):
                            for item_content in chunk.content:
                                if isinstance(item_content, dict) and item_content.get('type') == 'text':
                                    txt = item_content.get('text', '')
                                    if not text_started:
                                        txt = txt.lstrip('\n')
                                        if txt:
                                            text_started = True
                                    if txt:
                                        final_text += txt
                                        yield f"data: {json.dumps({'type': 'text', 'content': txt})}\n\n"

            # 최종 미디어 태그 추출 결과
            text, map_url, images = extract_media_tags(final_text)
            # Qwen3가 태그를 안 넣었으면 도구 결과에서 추출한 것 사용
            if not map_url and tool_map_url:
                map_url = tool_map_url
            if not images and tool_images:
                images = tool_images
            yield f"data: {json.dumps({'type': 'done', 'map_url': map_url, 'images': images})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )

@app.post("/session/clear")
async def clear_session(session_id: str):
    """세션 초기화"""
    if session_id in agents:
        agents[session_id].clear_history()
    return {"status": "ok", "session_id": session_id}


@app.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """세션 삭제"""
    if session_id in agents:
        del agents[session_id]
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
