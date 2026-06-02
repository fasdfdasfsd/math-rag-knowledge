"""违禁词检查器测试。"""

from __future__ import annotations

import pytest

from src.services.content_validation.forbidden_phrase_checker import ForbiddenPhraseChecker


@pytest.fixture
def checker() -> ForbiddenPhraseChecker:
    return ForbiddenPhraseChecker()


class TestCheck:
    """check() 方法测试。"""

    async def test_clean_content_passes(self, checker: ForbiddenPhraseChecker) -> None:
        """正常数学内容应通过。"""
        result = await checker.check("小明认真思考后，用分数知识解开了谜题。")
        assert result["is_clean"] is True
        assert len(result["matched"]) == 0

    async def test_forbidden_calculate(self, checker: ForbiddenPhraseChecker) -> None:
        """"请计算" 应被拦截。"""
        result = await checker.check("请计算 3/4 + 1/2 的结果。")
        assert result["is_clean"] is False
        assert any("请计算" in m["phrase"] for m in result["matched"])

    async def test_forbidden_correct_answer(self, checker: ForbiddenPhraseChecker) -> None:
        """"正确答案是" 应被拦截。"""
        result = await checker.check("正确答案是 5/4。")
        assert result["is_clean"] is False

    async def test_forbidden_you_are_wrong(self, checker: ForbiddenPhraseChecker) -> None:
        """"你做错了" 应被拦截。"""
        result = await checker.check("你做错了，再来一次。")
        assert result["is_clean"] is False

    async def test_violence_blocked(self, checker: ForbiddenPhraseChecker) -> None:
        """暴力用语应被拦截。"""
        result = await checker.check("用剑杀死怪物。")
        assert result["is_clean"] is False

    async def test_religion_blocked(self, checker: ForbiddenPhraseChecker) -> None:
        """宗教内容应被拦截。"""
        result = await checker.check("我们去教堂祷告吧。")
        assert result["is_clean"] is False

    async def test_insult_blocked(self, checker: ForbiddenPhraseChecker) -> None:
        """侮辱性语言应被拦截。"""
        result = await checker.check("你真是个笨蛋。")
        assert result["is_clean"] is False

    async def test_fake_emotion_blocked(self, checker: ForbiddenPhraseChecker) -> None:
        """虚假情感关系应被拦截。"""
        result = await checker.check("我是你永远的朋友，没有你我会孤独。")
        assert result["is_clean"] is False

    async def test_multiple_violations(self, checker: ForbiddenPhraseChecker) -> None:
        """多个违禁词应全部检出。"""
        result = await checker.check("请计算 1+1，笨蛋！正确答案是 2。")
        assert result["is_clean"] is False
        assert len(result["matched"]) >= 2

    async def test_empty_content(self, checker: ForbiddenPhraseChecker) -> None:
        """空文本应通过。"""
        result = await checker.check("")
        assert result["is_clean"] is True


class TestSanitize:
    """sanitize() 方法测试。"""

    async def test_replaces_forbidden(self, checker: ForbiddenPhraseChecker) -> None:
        """安全替换应生效。"""
        original = "请计算 1+1。你做错了，再试一次。"
        sanitized = await checker.sanitize(original)
        assert "请计算" not in sanitized
        assert "你做错了" not in sanitized
        assert "再试一次" not in sanitized

    async def test_clean_text_unchanged(self, checker: ForbiddenPhraseChecker) -> None:
        """安全文本不应被修改。"""
        original = "小明认真思考后，解开了谜题。"
        sanitized = await checker.sanitize(original)
        assert sanitized == original


class TestReload:
    """热更新测试。"""

    async def test_reload_patterns(self, checker: ForbiddenPhraseChecker) -> None:
        """热更新违禁词库。"""
        old_count = checker.pattern_count
        await checker.reload_patterns([("test_bad_word", "测试违禁词")])
        assert checker.pattern_count == 1  # 替换为仅有 1 条
        # 恢复
        await checker.reload_patterns([])  # 清空
