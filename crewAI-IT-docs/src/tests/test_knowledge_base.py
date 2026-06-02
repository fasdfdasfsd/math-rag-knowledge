"""
知识库工具单元测试
"""
import tempfile
from pathlib import Path
from src.tools.knowledge_base import KnowledgeBaseTool


def test_knowledge_base_basic():
    """测试基本关键词搜索"""
    with tempfile.TemporaryDirectory() as tmp:
        kb_dir = Path(tmp)
        (kb_dir / "doc.md").write_text(
            "# Hello\n\nThis is a paragraph about API design.", encoding='utf-8'
        )
        tool = KnowledgeBaseTool(knowledge_dir=str(kb_dir))
        result = tool._run("API")
        assert "doc.md" in result
        assert "paragraph about API design" in result


def test_knowledge_base_empty_dir():
    """测试空目录应返回未找到"""
    with tempfile.TemporaryDirectory() as tmp:
        tool = KnowledgeBaseTool(knowledge_dir=str(tmp))
        result = tool._run("any")
        assert result == "未找到相关内容。"


def test_knowledge_base_missing_dir():
    """测试目录不存在时的提示"""
    tool = KnowledgeBaseTool(knowledge_dir="/nonexistent")
    result = tool._run("something")
    assert "目录不存在" in result
