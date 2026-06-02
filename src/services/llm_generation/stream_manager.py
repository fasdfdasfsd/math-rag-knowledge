"""流式管理器 — SSE 段落级流式输出的编排与推送。"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
import json

from fastapi.responses import StreamingResponse

SSE_HEARTBEAT_INTERVAL: float = 15.0  # SSE 心跳间隔（秒）
SSE_TIMEOUT: float = 60.0  # 总超时（秒）


class StreamManager:
    """流式响应管理器。

    将 LLMProvider.generate_stream() 的段落级输出转为 SSE 事件流。
    每完成一段 → 推送给前端逐段渲染。
    支持心跳保活和超时保护。
    """

    async def to_sse_response(
        self,
        stream: AsyncIterator,
        level_id: str,
    ) -> StreamingResponse:
        """将流式迭代器转为 SSE StreamingResponse。

        Args:
            stream: LLMProvider.generate_stream() 返回的异步迭代器
            level_id: 当前关卡 ID（用于追踪和日志）

        Returns:
            FastAPI StreamingResponse（text/event-stream）
        """
        async def event_generator() -> AsyncIterator[str]:
            segment_index = 0
            try:
                async with asyncio.timeout(SSE_TIMEOUT):
                    async for chunk in stream:
                        segment_index += 1
                        event_data = json.dumps({
                            "segment": segment_index,
                            "content": chunk.content,
                            "is_last": getattr(chunk, "is_last", False),
                            "finish_reason": getattr(chunk, "finish_reason", None),
                        }, ensure_ascii=False)
                        yield f"event: segment_ready\ndata: {event_data}\n\n"

                        # 每段之间给前端渲染呼吸时间
                        await asyncio.sleep(0.05)

                # 全部段落完成
                yield f"event: complete\ndata: {{\"session_id\": \"{level_id}\", \"segments\": {segment_index}}}\n\n"

            except TimeoutError:
                yield f"event: error\ndata: {{\"error\": \"timeout\", \"segments_done\": {segment_index}}}\n\n"
            except Exception as exc:
                yield f"event: error\ndata: {{\"error\": \"{exc!s}\", \"segments_done\": {segment_index}}}\n\n"

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
                "X-Level-Id": level_id,
            },
        )
