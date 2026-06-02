"""Push Notification API — PWA Web Push 订阅管理。

存储用户推送订阅信息，供后台任务（预生成完成/新内容提醒）发送推送通知。
"""

from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import BaseModel

router = APIRouter()

# 内存存储（MVP — 后续迁移到 Redis/DB）
_subscriptions: dict[str, dict] = {}


class PushSubscriptionRequest(BaseModel):
    """Web Push 订阅对象（PushSubscription.toJSON()）。"""
    endpoint: str
    keys: dict[str, str]


@router.post("/subscribe", status_code=201)
async def subscribe(request: Request, sub: PushSubscriptionRequest) -> dict:
    """注册或更新推送订阅。"""
    user_id = getattr(request.state, "user_id", "anonymous")
    key = f"{user_id}:{sub.endpoint[-32:]}"
    _subscriptions[key] = {
        "user_id": user_id,
        "endpoint": sub.endpoint,
        "keys": sub.keys,
    }
    return {"status": "subscribed", "key": key}


@router.delete("/unsubscribe")
async def unsubscribe(request: Request, endpoint: str) -> dict:
    """取消推送订阅。"""
    user_id = getattr(request.state, "user_id", "anonymous")
    to_remove = [
        k for k, v in _subscriptions.items()
        if v["user_id"] == user_id and v["endpoint"] == endpoint
    ]
    for k in to_remove:
        del _subscriptions[k]
    return {"status": "unsubscribed", "removed": len(to_remove)}
