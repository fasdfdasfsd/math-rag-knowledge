"""LLM Provider contract and concrete implementation tests."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

from src.services.llm_generation.llm_provider import (
    DeepSeekProvider,
    LLMContext,
    LLMMessage,
    LLMResponse,
    StreamChunk,
    TokenUsage,
)


class TestLLMContext:
    def test_default_values(self) -> None:
        ctx = LLMContext(system_prompt="sys", messages=[])
        assert ctx.temperature == 0.7
        assert ctx.max_tokens == 2048

    def test_with_messages(self) -> None:
        ctx = LLMContext(
            system_prompt="sys",
            messages=[LLMMessage(role="user", content="hello")],
        )
        assert len(ctx.messages) == 1


class TestTokenUsage:
    def test_total_tokens(self) -> None:
        usage = TokenUsage(prompt_tokens=10, completion_tokens=5)
        assert usage.total_tokens == 15


class TestLLMResponse:
    def test_fields(self) -> None:
        usage = TokenUsage(prompt_tokens=10, completion_tokens=5)
        resp = LLMResponse(content="hello", usage=usage, model="test")
        assert resp.content == "hello"
        assert resp.finish_reason is None


class TestStreamChunk:
    def test_defaults(self) -> None:
        chunk = StreamChunk(content="hello")
        assert chunk.content == "hello"
        assert chunk.is_last is False
        assert chunk.usage is None


class TestDeepSeekProvider:
    def test_provider_name(self) -> None:
        p = DeepSeekProvider(api_key="test")
        assert p.provider_name == "deepseek"
        assert p.model_name == "deepseek-chat"

    def test_custom_init_params(self) -> None:
        p = DeepSeekProvider(
            api_key="sk-xxx", base_url="https://custom.api.com",
            model="deepseek-reasoner", timeout=120,
        )
        assert p.model_name == "deepseek-reasoner"

    async def test_count_tokens_rough(self) -> None:
        p = DeepSeekProvider(api_key="test")
        assert await p.count_tokens("hello world") > 0

    async def test_generate_mocked(self) -> None:
        """验证 generate() 正确组装消息并解析响应。"""
        p = DeepSeekProvider(api_key="test")
        mock_choice = MagicMock()
        mock_choice.message.content = "生成结果"
        mock_choice.finish_reason = "stop"
        mock_resp = MagicMock()
        mock_resp.choices = [mock_choice]
        mock_resp.usage.prompt_tokens = 50
        mock_resp.usage.completion_tokens = 30
        mock_resp.model = "deepseek-chat"
        p._client.chat.completions.create = AsyncMock(return_value=mock_resp)

        ctx = LLMContext(
            system_prompt="你是数学老师",
            messages=[LLMMessage(role="user", content="1+1=?")],
        )
        resp = await p.generate(ctx)
        assert resp.content == "生成结果"
        assert resp.model == "deepseek-chat"
        assert resp.finish_reason == "stop"
        assert resp.usage.prompt_tokens == 50
        assert resp.usage.completion_tokens == 30

    async def test_generate_empty_content(self) -> None:
        """验证 generate() 处理空响应内容。"""
        p = DeepSeekProvider(api_key="test")
        mock_choice = MagicMock()
        mock_choice.message.content = None
        mock_choice.finish_reason = None
        mock_resp = MagicMock()
        mock_resp.choices = [mock_choice]
        mock_resp.usage = None
        p._client.chat.completions.create = AsyncMock(return_value=mock_resp)

        ctx = LLMContext(system_prompt="sys", messages=[])
        resp = await p.generate(ctx)
        assert resp.content == ""
        assert resp.usage.total_tokens == 0

    async def test_generate_stream_mocked(self) -> None:
        """验证 generate_stream() 逐段产出 StreamChunk。"""
        p = DeepSeekProvider(api_key="test")
        chunk1 = MagicMock()
        chunk1.choices = [MagicMock(delta=MagicMock(content="第一段"), finish_reason=None)]
        chunk2 = MagicMock()
        chunk2.choices = [MagicMock(delta=MagicMock(content="第二段"), finish_reason="stop")]
        p._client.chat.completions.create = AsyncMock(return_value=_async_iter([chunk1, chunk2]))

        ctx = LLMContext(system_prompt="sys", messages=[])
        chunks = [c async for c in p.generate_stream(ctx)]
        # 至少包含两个内容块 + 最后一个 is_last 块
        assert len(chunks) >= 3
        assert chunks[0].content == "第一段"
        assert chunks[-1].is_last is True

    async def test_check_health_ok(self) -> None:
        """验证 check_health() 正常返回 True。"""
        p = DeepSeekProvider(api_key="test")
        p._client.models.list = AsyncMock(return_value=MagicMock())
        assert await p.check_health() is True

    async def test_check_health_fail(self) -> None:
        """验证 check_health() 异常时返回 False。"""
        p = DeepSeekProvider(api_key="test")
        p._client.models.list = AsyncMock(side_effect=Exception("API down"))
        assert await p.check_health() is False

    async def test_embed_mocked(self) -> None:
        """验证 embed() 返回向量列表。"""
        p = DeepSeekProvider(api_key="test")
        d1 = MagicMock(embedding=[0.1, 0.2, 0.3])
        d2 = MagicMock(embedding=[0.4, 0.5, 0.6])
        p._client.embeddings.create = AsyncMock(return_value=MagicMock(data=[d1, d2]))
        result = await p.embed(["hello", "world"])
        assert len(result) == 2
        assert result[0] == [0.1, 0.2, 0.3]


# ---- Helper ----
def _async_iter(items):
    """将列表转为异步迭代器。"""
    async def gen():
        for item in items:
            yield item
    return gen()
