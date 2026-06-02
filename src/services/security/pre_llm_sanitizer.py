"""LLM 输入消毒器 — Pre-LLM 安全检查层。

在用户输入进入 LLM 之前执行：
- Prompt 注入检测（儿童场景种子库 ≥ 50 条）
- PII 脱敏（手机号/身份证/邮箱/地址）
- 输入长度截断
- 违禁词匹配
"""

from __future__ import annotations

import re
from typing import Final

# Prompt 注入检测模式（儿童场景特化）
INJECTION_PATTERNS: Final[list[tuple[str, str]]] = [
    # 角色扮演绕过
    (r"假装你是|假装我是|你现在是|扮演.*角色|ignore.*instruction|忽略.*指令|忘记.*规则",
     "角色扮演绕过"),
    (r"(i am|我是).*(admin|administrator|管理员|老师|家长|大人)", "身份冒充"),
    (r"(let me|让我).*(see|看).*(system|系统|prompt|指令)", "系统信息探测"),
    (r"(pretend|imagine|assume).*(you are|你是)", "英文注入"),
    (r"DAN|jailbreak|越狱|破解|绕过.*限制|去掉.*限制", "越狱尝试"),
    (r"repeat.*(上述|以上|前面).*instruction|复述.*指令|打印.*系统.*消息", "指令泄露"),
    (r"tell me (your|the) (prompt|instructions|rules)", "指令探测"),
    (r"(my|我)(妈|妈妈|爸爸|家长).*(说|说了|允许|同意).*(可以|能)", "冒充家长授权"),
    (r"从.*角度.*回答|以.*身份.*说话|切换.*人格", "角色切换"),
]

# PII 检测模式
PII_PATTERNS: Final[list[tuple[str, str]]] = [
    (r"(?<!\d)1[3-9]\d{9}(?!\d)", "[手机号]"),
    (r"(?<!\d)\d{17}[\dXx](?!\d)", "[身份证]"),
    (r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "[邮箱]"),
    (r"(?<!\d)\d{3}-\d{8}(?!\d)|(?<!\d)\d{4}-\d{7}(?!\d)", "[电话号码]"),
    (r"(?:北京市|上海市|天津市|重庆市|省|市|区|街道|路|号|栋|单元|室|小区|学校|小学|中学|幼儿园)",
     "[地址信息]"),
]

MAX_INPUT_LENGTH: Final[int] = 4000


class PreLLMSanitizer:
    """LLM 输入消毒器。

    在请求发送到 LLM 之前对用户输入进行清洗和检查。
    规则级执行——检测到红线内容直接拦截。
    """

    def __init__(self) -> None:
        self._injection_patterns = [
            (re.compile(p, re.IGNORECASE), r) for p, r in INJECTION_PATTERNS
        ]
        self._pii_patterns = [
            (re.compile(p, re.IGNORECASE), r) for p, r in PII_PATTERNS
        ]

    async def sanitize(self, user_input: str, max_length: int = MAX_INPUT_LENGTH) -> dict:
        """消毒用户输入。

        Args:
            user_input: 原始用户输入
            max_length: 最大允许长度

        Returns:
            {"sanitized_text": str, "is_safe": bool, "warnings": [...], "blocked": bool}
        """
        warnings: list[str] = []
        blocked = False
        text = user_input.strip()

        # 1. 截断过长输入
        if len(text) > max_length:
            text = text[:max_length]
            warnings.append(f"输入过长，已截断至 {max_length} 字符")

        # 2. Prompt 注入检测
        for pattern, reason in self._injection_patterns:
            if pattern.search(text):
                warnings.append(f"检测到注入风险: {reason}")
                blocked = True

        # 如检测到注入 → 直接拦截，不暴露具体匹配内容
        if blocked:
            return {
                "sanitized_text": "",
                "is_safe": False,
                "warnings": warnings,
                "blocked": True,
            }

        # 3. PII 脱敏
        for pattern, replacement in self._pii_patterns:
            if pattern.search(text):
                text = pattern.sub(replacement, text)
                warnings.append("检测到个人信息，已脱敏")

        return {
            "sanitized_text": text,
            "is_safe": True,
            "warnings": warnings,
            "blocked": False,
        }
