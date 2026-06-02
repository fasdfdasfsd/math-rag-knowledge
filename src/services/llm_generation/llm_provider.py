"""LLM Provider 抽象接口 — 多模型适配层。

支持 DeepSeek / Tongyi 等 LLM 的统一调用接口。
所有实现必须支持：
- 同步生成（完整响应）
- SSE 流式生成（段落级 Token 推送）
- Token 用量统计
- Prompt Caching
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Dict, List, Optional

from pydantic import BaseModel


class LLMMessage(BaseModel):
    """对话消息。"""
    role: str           # "system" | "user" | "assistant"
    content: str


@dataclass(frozen=True)
class LLMContext:
    """LLM 调用上下文。"""
    system_prompt: str
    messages: List[LLMMessage]
    temperature: float = 0.7
    max_tokens: int = 2048
    model_params: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class TokenUsage:
    """Token 用量统计。"""
    prompt_tokens: int
    completion_tokens: int
    cached_prompt_tokens: int = 0
    reasoning_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens


@dataclass(frozen=True)
class LLMResponse:
    """LLM 完整响应。"""
    content: str
    usage: TokenUsage
    model: str
    finish_reason: str | None = None


@dataclass(frozen=True)
class StreamChunk:
    """流式响应片段。"""
    content: str
    is_last: bool = False
    index: int = 0
    usage: Optional[TokenUsage] = None
    finish_reason: str | None = None


class LLMProvider(ABC):
    """LLM Provider 抽象基类。

    所有 Provider 实现（DeepSeek, Tongyi 等）必须继承此类。
    实现必须是无状态的 —— 状态由调用者管理。
    """

    @abstractmethod
    async def generate(self, context: LLMContext) -> LLMResponse:
        """同步生成完整响应。

        Args:
            context: LLM 调用上下文（System Prompt + 消息 + 参数）

        Returns:
            包含生成内容和 Token 统计的完整响应
        """
        ...

    @abstractmethod
    async def generate_stream(
        self,
        context: LLMContext,
    ) -> AsyncIterator[StreamChunk]:
        """SSE 流式生成响应。

        逐段（段落级而非 Token 级）产出 StreamChunk。
        最后一个 chunk 的 is_last=True，携带总 usage。

        Args:
            context: LLM 调用上下文

        Yields:
            StreamChunk: 每个包含一个完整段落或达到段落边界的片段
        """
        ...  # pragma: no cover
        if False:  # type: ignore[unreachable]
            yield  # trick to make ABC recognize this as async generator

    @abstractmethod
    async def count_tokens(self, text: str) -> int:
        """统计文本的 Token 数（使用模型对应 tokenizer）。"""
        ...

    @property
    @abstractmethod
    def model_name(self) -> str:
        """返回当前使用的模型名称。"""
        ...

    @abstractmethod
    async def check_health(self) -> bool:
        """检查 Provider 服务是否可用。"""
        ...


# ---- Concrete Provider Implementations ----

class DeepSeekProvider(LLMProvider):
    """DeepSeek Chat API provider (OpenAI-compatible)."""

    def __init__(self, api_key: str, base_url: str = "https://api.deepseek.com", model: str = "deepseek-chat", timeout: int = 60) -> None:
        from openai import AsyncOpenAI
        self._client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self._model = model
        self._timeout = timeout

    @property
    def provider_name(self) -> str:
        return "deepseek"

    @property
    def model_name(self) -> str:
        return self._model

    async def generate(self, context: LLMContext) -> LLMResponse:
        """Synchronous generation."""
        import time as _time
        start = _time.time()
        messages = [{"role": "system", "content": context.system_prompt}]
        messages.extend({"role": m.role, "content": m.content} for m in context.messages)
        resp = await self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            temperature=context.temperature,
            max_tokens=context.max_tokens,
            **context.model_params,
        )
        usage = resp.usage
        return LLMResponse(
            content=resp.choices[0].message.content or "",
            usage=TokenUsage(
                prompt_tokens=usage.prompt_tokens if usage else 0,
                completion_tokens=usage.completion_tokens if usage else 0,
            ),
            model=resp.model,
            finish_reason=resp.choices[0].finish_reason or "stop",
        )

    async def generate_stream(self, context: LLMContext):
        """Streaming generation."""
        messages = [{"role": "system", "content": context.system_prompt}]
        messages.extend({"role": m.role, "content": m.content} for m in context.messages)
        stream = await self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            temperature=context.temperature,
            max_tokens=context.max_tokens,
            stream=True,
            **context.model_params,
        )
        idx = 0
        async for chunk in stream:
            delta = chunk.choices[0].delta if chunk.choices else None
            if delta and delta.content:
                idx += 1
                yield StreamChunk(content=delta.content, index=idx, finish_reason=chunk.choices[0].finish_reason)
        yield StreamChunk(content="", is_last=True, finish_reason="stop")

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Text embedding via DeepSeek API."""
        resp = await self._client.embeddings.create(model="deepseek-embedding", input=texts)
        return [d.embedding for d in resp.data]

    async def count_tokens(self, text: str) -> int:
        """Rough token count (~2 chars per token for Chinese)."""
        return len(text) // 2

    async def check_health(self) -> bool:
        """Health check via API call."""
        try:
            await self._client.models.list()
            return True
        except Exception:
            return False
