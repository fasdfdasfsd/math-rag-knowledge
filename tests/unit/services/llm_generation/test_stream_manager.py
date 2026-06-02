"""Stream manager tests — 完整覆盖 SSE 流式场景。"""

from __future__ import annotations

import asyncio
from typing import AsyncIterator

import pytest

from src.services.llm_generation.stream_manager import (
    SSE_HEARTBEAT_INTERVAL,
    SSE_TIMEOUT,
    StreamManager,
)


def _make_chunk(content: str, is_last: bool = False, finish_reason: str | None = None):
    """创建模拟 LLM chunk 对象。"""
    return type("Chunk", (), {
        "content": content,
        "is_last": is_last,
        "finish_reason": finish_reason,
    })()


class TestStreamManager:
    """SSE 流式管理器测试。"""

    async def test_sse_response_type_and_headers(self) -> None:
        """验证 SSE 响应类型和必要头部。"""
        manager = StreamManager()

        async def mock_stream() -> AsyncIterator:
            yield _make_chunk("hello", is_last=True)

        response = await manager.to_sse_response(mock_stream(), "lvl_01")
        assert response.media_type == "text/event-stream"
        headers = response.headers
        assert "no-cache" in headers.get("cache-control", "")
        assert headers.get("x-accel-buffering") == "no"
        assert headers.get("x-level-id") == "lvl_01"

    async def test_multi_segment_stream(self) -> None:
        """验证多段落流式推送——每段产生 segment_ready 事件。"""
        manager = StreamManager()

        async def mock_stream() -> AsyncIterator:
            yield _make_chunk("第一段", is_last=False)
            yield _make_chunk("第二段", is_last=False)
            yield _make_chunk("最后一段", is_last=True, finish_reason="stop")

        response = await manager.to_sse_response(mock_stream(), "lvl_02")
        # 消费 SSE 事件生成器
        events = [chunk async for chunk in response.body_iterator]

        segment_events = [e for e in events if "segment_ready" in e]
        complete_events = [e for e in events if "complete" in e]

        assert len(segment_events) == 3
        assert len(complete_events) == 1
        # 验证最后一段包含 is_last=True
        assert '"is_last": true' in segment_events[2] or '"is_last": True' in segment_events[2]
        # 验证完成事件包含 segments 计数
        assert '"segments": 3' in complete_events[0]

    async def test_timeout_handling(self) -> None:
        """验证 SSE 超时保护——超时后产生 error 事件而非崩溃。"""
        manager = StreamManager()

        async def slow_stream() -> AsyncIterator:
            # 使用一个极短的超时来模拟（通过 monkeypatch SSE_TIMEOUT 不够优雅，
            # 这里验证 error 事件格式即可——超时由 asyncio.timeout 触发）
            yield _make_chunk("start")
            await asyncio.sleep(999)  # 在实际测试中不会被等待
            yield _make_chunk("never_reached")

        # 使用 monkeypatch 缩短超时来触发 TimeoutError
        import src.services.llm_generation.stream_manager as sm
        original_timeout = sm.SSE_TIMEOUT
        sm.SSE_TIMEOUT = 0.001  # 极短超时
        try:
            response = await manager.to_sse_response(slow_stream(), "lvl_timeout")
            events = [chunk async for chunk in response.body_iterator]
            error_events = [e for e in events if "error" in e and "timeout" in e]
            assert len(error_events) >= 1
        finally:
            sm.SSE_TIMEOUT = original_timeout

    async def test_exception_handling(self) -> None:
        """验证流内异常被捕获为 error 事件而非传播。"""
        manager = StreamManager()

        async def failing_stream() -> AsyncIterator:
            yield _make_chunk("ok")
            raise RuntimeError("LLM 调用失败")

        response = await manager.to_sse_response(failing_stream(), "lvl_err")
        events = [chunk async for chunk in response.body_iterator]

        error_events = [e for e in events if "error" in e]
        assert len(error_events) >= 1
        assert "LLM 调用失败" in error_events[0]

    async def test_complete_event_format(self) -> None:
        """验证正常完成时的 complete 事件格式。"""
        manager = StreamManager()

        async def mock_stream() -> AsyncIterator:
            yield _make_chunk("done", is_last=True)

        response = await manager.to_sse_response(mock_stream(), "lvl_complete")
        events = [chunk async for chunk in response.body_iterator]

        complete = [e for e in events if "complete" in e]
        assert len(complete) == 1
        assert "lvl_complete" in complete[0]
        assert '"segments": 1' in complete[0]

    async def test_empty_stream(self) -> None:
        """验证空流（无输出段落）不会崩溃，仍然产生 complete 事件。"""
        manager = StreamManager()

        async def empty_stream() -> AsyncIterator:
            # 不 yield 任何内容
            if False:
                yield

        response = await manager.to_sse_response(empty_stream(), "lvl_empty")
        events = [chunk async for chunk in response.body_iterator]

        complete = [e for e in events if "complete" in e]
        assert len(complete) == 1
        assert '"segments": 0' in complete[0]

    async def test_finish_reason_propagation(self) -> None:
        """验证 finish_reason 正确传递到 SSE 事件。"""
        manager = StreamManager()

        async def mock_stream() -> AsyncIterator:
            yield _make_chunk("内容", is_last=True, finish_reason="stop")

        response = await manager.to_sse_response(mock_stream(), "lvl_fr")
        events = [chunk async for chunk in response.body_iterator]

        segment = [e for e in events if "segment_ready" in e]
        assert len(segment) == 1
        assert '"finish_reason": "stop"' in segment[0]

    async def test_constants(self) -> None:
        """验证 SSE 常量在合理范围内。"""
        assert SSE_TIMEOUT > 0
        assert SSE_HEARTBEAT_INTERVAL > 0
        assert SSE_TIMEOUT > SSE_HEARTBEAT_INTERVAL
