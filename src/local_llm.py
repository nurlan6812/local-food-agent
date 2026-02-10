"""로컬 GLM-4.6V-Flash 모델 통합 모듈 (Tool Calling 지원)"""

import json
import torch
from typing import Any, Dict, Iterator, List, Optional, Sequence, Union
from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.tools import BaseTool
from langchain_core.utils.function_calling import convert_to_openai_tool
from pydantic import Field


class LocalGLM4V(BaseChatModel):
    """GLM-4.6V-Flash를 LangChain ChatModel로 래핑 (Tool Calling 지원)"""

    model_path: str = Field(default="/home/ondamlab/.cache/huggingface/hub/models--zai-org--GLM-4.6V-Flash/snapshots/main")
    temperature: float = Field(default=0.7)
    max_new_tokens: int = Field(default=2048)
    tools: List[Dict] = Field(default_factory=list)

    _model: Any = None
    _processor: Any = None
    _device: str = "cuda"

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._load_model()

    def bind_tools(self, tools: Sequence[Union[Dict[str, Any], BaseTool]], **kwargs) -> "LocalGLM4V":
        formatted_tools = []
        for tool in tools:
            if isinstance(tool, BaseTool):
                formatted_tools.append(convert_to_openai_tool(tool))
            else:
                formatted_tools.append(tool)
        return LocalGLM4V(
            model_path=self.model_path,
            temperature=self.temperature,
            max_new_tokens=self.max_new_tokens,
            tools=formatted_tools
        )

    def _load_model(self):
        if self._model is not None:
            return
        from transformers import AutoProcessor, Glm4vForConditionalGeneration
        print(f"\ud83d\udd04 Loading GLM-4.6V-Flash from {self.model_path}...")
        self._processor = AutoProcessor.from_pretrained(self.model_path, use_fast=False)
        self._model = Glm4vForConditionalGeneration.from_pretrained(
            self.model_path, torch_dtype=torch.bfloat16, device_map="auto"
        )
        print(f"\u2705 Model loaded! GPU Memory: {torch.cuda.memory_allocated()/1024**3:.2f} GB")

    @property
    def _llm_type(self) -> str:
        return "glm-4.6v-flash"

    @property
    def _identifying_params(self) -> dict:
        return {"model_path": self.model_path, "temperature": self.temperature, "max_new_tokens": self.max_new_tokens}

    def _convert_messages_to_glm_format(self, messages: List[BaseMessage]) -> List[dict]:
        glm_messages = []
        system_content = ""
        for msg in messages:
            if isinstance(msg, SystemMessage):
                system_content = msg.content
            elif isinstance(msg, HumanMessage):
                content = msg.content
                if isinstance(content, list):
                    glm_content = []
                    for item in content:
                        if isinstance(item, dict):
                            if item.get("type") == "text":
                                text = item.get("text", "")
                                if system_content:
                                    text = f"{system_content}\n\n{text}"
                                    system_content = ""
                                glm_content.append({"type": "text", "text": text})
                            elif item.get("type") == "image_url":
                                import base64
                                from PIL import Image
                                from io import BytesIO
                                image_url = item.get("image_url", {})
                                url = image_url.get("url", "") if isinstance(image_url, dict) else image_url
                                if url.startswith("data:"):
                                    header, data = url.split(",", 1)
                                    image_data = base64.b64decode(data)
                                    image = Image.open(BytesIO(image_data))
                                    glm_content.append({"type": "image", "image": image})
                        elif isinstance(item, str):
                            text = item
                            if system_content:
                                text = f"{system_content}\n\n{text}"
                                system_content = ""
                            glm_content.append({"type": "text", "text": text})
                    glm_messages.append({"role": "user", "content": glm_content})
                else:
                    text = content
                    if system_content:
                        text = f"{system_content}\n\n{text}"
                        system_content = ""
                    glm_messages.append({"role": "user", "content": [{"type": "text", "text": text}]})
            elif isinstance(msg, AIMessage):
                glm_messages.append({"role": "assistant", "content": [{"type": "text", "text": msg.content}]})
        return glm_messages

    def _build_tools_prompt(self) -> str:
        if not self.tools:
            return ""
        tools_desc = "\n\n## 사용 가능한 도구들:\n"
        for tool in self.tools:
            func = tool.get("function", {})
            name = func.get("name", "unknown")
            desc = func.get("description", "")
            params = func.get("parameters", {})
            tools_desc += f"\n### {name}\n"
            tools_desc += f"설명: {desc}\n"
            if params.get("properties"):
                tools_desc += "파라미터:\n"
                for param_name, param_info in params["properties"].items():
                    param_desc = param_info.get("description", "")
                    param_type = param_info.get("type", "string")
                    required = param_name in params.get("required", [])
                    tools_desc += f"  - {param_name} ({param_type}{'*' if required else ''}): {param_desc}\n"
        tools_desc += """\n## 도구 호출 형식:\n도구를 호출하려면 다음 JSON 형식을 사용하세요:\n```tool_call\n{"name": "도구이름", "arguments": {"param1": "value1"}}\n```\n\n도구 호출이 필요 없으면 일반 텍스트로 응답하세요.\n"""
        return tools_desc

    def _parse_tool_calls(self, text: str) -> tuple[str, List[Dict]]:
        import re
        tool_calls = []
        pattern = r'```tool_call\s*\n?(.*?)\n?```'
        matches = re.findall(pattern, text, re.DOTALL)
        for match in matches:
            try:
                call = json.loads(match.strip())
                if "name" in call:
                    tool_calls.append({
                        "id": f"call_{len(tool_calls)}",
                        "type": "function",
                        "function": {
                            "name": call["name"],
                            "arguments": json.dumps(call.get("arguments", {}))
                        }
                    })
            except json.JSONDecodeError:
                continue
        clean_text = re.sub(pattern, '', text, flags=re.DOTALL).strip()
        return clean_text, tool_calls

    def _generate(self, messages: List[BaseMessage], stop: Optional[List[str]] = None, run_manager: Optional[CallbackManagerForLLMRun] = None, **kwargs) -> ChatResult:
        glm_messages = self._convert_messages_to_glm_format(messages)
        if self.tools and glm_messages:
            tools_prompt = self._build_tools_prompt()
            first_msg = glm_messages[0]
            if first_msg["role"] == "user" and first_msg["content"]:
                for item in first_msg["content"]:
                    if item.get("type") == "text":
                        item["text"] = tools_prompt + "\n\n" + item["text"]
                        break
        inputs = self._processor.apply_chat_template(
            glm_messages, tokenize=True, add_generation_prompt=True, return_dict=True, return_tensors="pt"
        ).to(self._model.device)
        inputs.pop("token_type_ids", None)
        with torch.no_grad():
            generated_ids = self._model.generate(
                **inputs, max_new_tokens=self.max_new_tokens,
                temperature=self.temperature if self.temperature > 0 else None,
                do_sample=self.temperature > 0,
            )
        output_text = self._processor.decode(generated_ids[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)
        if "<think>" in output_text and "</think>" in output_text:
            import re
            output_text = re.sub(r'<think>.*?</think>\s*', '', output_text, flags=re.DOTALL)
        clean_text, tool_calls = self._parse_tool_calls(output_text)
        ai_message = AIMessage(
            content=clean_text,
            tool_calls=[{"id": tc["id"], "name": tc["function"]["name"], "args": json.loads(tc["function"]["arguments"])} for tc in tool_calls] if tool_calls else []
        )
        return ChatResult(generations=[ChatGeneration(message=ai_message)])

    def _stream(self, messages: List[BaseMessage], stop: Optional[List[str]] = None, run_manager: Optional[CallbackManagerForLLMRun] = None, **kwargs) -> Iterator[ChatGeneration]:
        result = self._generate(messages, stop, run_manager, **kwargs)
        yield result.generations[0]


_glm_instance: Optional[LocalGLM4V] = None


def get_local_glm(model_path: Optional[str] = None, temperature: float = 0.7, max_new_tokens: int = 2048) -> LocalGLM4V:
    global _glm_instance
    if _glm_instance is None:
        _glm_instance = LocalGLM4V(
            model_path=model_path or "/home/ondamlab/.cache/huggingface/hub/models--zai-org--GLM-4.6V-Flash/snapshots/main",
            temperature=temperature, max_new_tokens=max_new_tokens
        )
    return _glm_instance
