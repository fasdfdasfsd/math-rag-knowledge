"""Milvus 向量数据库客户端封装。"""

from __future__ import annotations

from pymilvus import Collection, connections

from src.core.config import get_settings


class MilvusClient:
    """Milvus 客户端封装。

    管理 Milvus 连接生命周期和 Collection 操作。
    使用单例模式，通过 FastAPI 依赖注入管理。
    """

    def __init__(self, collection_name: str | None = None) -> None:
        self._connected = False
        self._collection_name = collection_name
        self._collection: Collection | None = None

    async def connect(self) -> None:
        """连接到 Milvus 实例。"""
        if self._connected:
            return
        settings = get_settings()
        connections.connect(
            alias=settings.MILVUS_ALIAS,
            host=settings.MILVUS_HOST,
            port=settings.MILVUS_PORT,
        )
        self._connected = True

    async def connect_to_collection(self, collection_name: str) -> None:
        """连接到指定 Collection 并加载到内存。"""
        if not self._connected:
            await self.connect()
        self._collection_name = collection_name
        self._collection = Collection(collection_name)
        self._collection.load()

    async def get_public_collection(self) -> Collection:
        """获取公共知识库 Collection。"""
        settings = get_settings()
        if self._collection_name != settings.MILVUS_COLLECTION_PUBLIC or self._collection is None:
            await self.connect_to_collection(settings.MILVUS_COLLECTION_PUBLIC)
        return self._collection  # type: ignore[return-value]

    async def get_private_collection(self) -> Collection:
        """获取私有学情库 Collection。"""
        settings = get_settings()
        if self._collection_name != settings.MILVUS_COLLECTION_PRIVATE or self._collection is None:
            await self.connect_to_collection(settings.MILVUS_COLLECTION_PRIVATE)
        return self._collection  # type: ignore[return-value]

    async def disconnect(self) -> None:
        """断开 Milvus 连接。"""
        if self._connected:
            self._collection = None
            connections.disconnect(get_settings().MILVUS_ALIAS)
            self._connected = False

    @property
    def collection(self) -> Collection:
        """获取当前加载的 Collection。"""
        if self._collection is None:
            raise RuntimeError("Milvus collection not loaded. Call connect_to_collection() first.")
        return self._collection

    @property
    def is_connected(self) -> bool:
        """Milvus 是否已连接。"""
        return self._connected
