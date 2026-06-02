"""
知识库检索工具
----------------
在本地 Markdown/TXT 文件中按关键词搜索相关段落。
继承 CrewAI BaseTool，可作为 Agent 的工具调用。

检索策略：按段落（\n\n 分隔）匹配任意关键词，最多返回 3 条结果。
"""
from pathlib import Path
from typing import Type
from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class KnowledgeBaseInput(BaseModel):
    """知识库查询输入模式"""
    query: str = Field(description="搜索关键词，多个词用空格分隔")


class KnowledgeBaseTool(BaseTool):
    name: str = "knowledge_base"
    description: str = "检索本地知识库中的 Markdown/TXT 文件内容。"
    args_schema: Type[BaseModel] = KnowledgeBaseInput

    knowledge_dir: str = ""

    def __init__(self, knowledge_dir: str, **kwargs):
        """
        :param knowledge_dir: 知识库目录路径
        """
        super().__init__(knowledge_dir=knowledge_dir, **kwargs)
        self.knowledge_dir = knowledge_dir

    def _run(self, query: str) -> str:
        """
        执行关键词检索。
        :param query: 用户查询字符串
        :return: 最多 3 条相关段落（每段截取前 500 字符）
        """
        kb_path = Path(self.knowledge_dir)
        if not kb_path.exists():
            return "知识库目录不存在。"

        results = []
        for f in kb_path.glob("*"):
            if f.suffix.lower() in (".md", ".txt"):
                content = f.read_text(encoding='utf-8')
                for para in content.split("\n\n"):
                    if any(kw.lower() in para.lower() for kw in query.split()):
                        results.append(f"📄 {f.name}:\n{para[:500]}...")
                        if len(results) >= 3:
                            break
            if len(results) >= 3:
                break

        return "\n\n".join(results) if results else "未找到相关内容。"