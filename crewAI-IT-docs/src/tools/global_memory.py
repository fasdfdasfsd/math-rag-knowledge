"""
全局共享记忆工具
-------------------
基于本地 JSON 文件，提供键值对的读写能力。
支持跨会话共享，智能体可通过此工具存储项目偏好、历史决策等。

安全设计：
  - 使用绝对路径（Path.resolve()），避免运行目录变更影响
  - 自动创建不存在的父目录和文件
"""
import json
from pathlib import Path
from typing import Type
from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class GlobalMemoryInput(BaseModel):
    """记忆操作输入模式"""
    action: str = Field(description="操作类型，'read' 或 'write'")
    key: str = Field(description="记忆的键")
    value: str = Field(default="", description="写入的值（读取时留空）")


class GlobalMemoryTool(BaseTool):
    name: str = "global_memory"
    description: str = "读写全局共享记忆，可用于存储项目偏好、历史决策等。"
    args_schema: Type[BaseModel] = GlobalMemoryInput

    memory_file: str = ""

    def _run(self, action: str, key: str, value: str = "") -> str:
        """
        执行记忆读写操作。
        :param action: 'read' 或 'write'
        :param key: 键名
        :param value: 值（仅写入时使用）
        :return: 操作结果字符串
        """
        if not self.memory_file:
            return "未指定记忆文件路径。"

        # 使用绝对路径，避免当前工作目录变更影响
        file_path = Path(self.memory_file).resolve()

        # 读取现有数据（文件不存在时视为空字典）
        if file_path.exists():
            data = json.loads(file_path.read_text(encoding='utf-8'))
        else:
            data = {}

        if action == "read":
            return data.get(key, f"键 '{key}' 不存在")
        elif action == "write":
            data[key] = value
            # 确保父目录存在
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(
                json.dumps(data, indent=2, ensure_ascii=False),
                encoding='utf-8'
            )
            return f"已写入 {key}"
        else:
            return "无效操作，请使用 'read' 或 'write'"