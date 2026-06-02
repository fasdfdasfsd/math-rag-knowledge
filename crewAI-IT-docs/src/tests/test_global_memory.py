"""
全局记忆工具单元测试
"""
import os
import tempfile

from src.tools.global_memory import GlobalMemoryTool


def test_global_memory_write_read():
    """测试写入后读取"""
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
        tool = GlobalMemoryTool(memory_file=tmp.name)
        res = tool._run("write", "project", "AI-Docs")
        assert "已写入" in res
        res = tool._run("read", "project")
        assert res == "AI-Docs"
        res = tool._run("read", "nonexistent")
        assert "不存在" in res


def test_global_memory_new_file():
    """测试写入时应自动创建新文件"""
    with tempfile.TemporaryDirectory() as tmp:
        file_path = os.path.join(tmp, "new_mem.json")
        tool = GlobalMemoryTool(memory_file=file_path)
        tool._run("write", "key1", "val1")
        assert os.path.exists(file_path)
        res = tool._run("read", "key1")
        assert res == "val1"
