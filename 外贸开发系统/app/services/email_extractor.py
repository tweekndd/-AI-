"""
邮箱提取服务
从网页文本中提取目标前缀的邮箱地址以及mailto链接中的邮箱
"""
import re
from typing import List


# 目标邮箱前缀（提取这些前缀的邮箱）
TARGET_PREFIXES = [
    "info",
    "sales",
    "contact",
    "procurement",
    "project",
    "marketing",
]

# 编译正则：匹配这些前缀的邮箱地址
PREFIX_PATTERN = re.compile(
    r"\b(" + "|".join(TARGET_PREFIXES) + r")@[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?)*\.[a-zA-Z]{2,}\b",
    re.IGNORECASE,
)

# 通用邮箱正则
GENERAL_EMAIL_PATTERN = re.compile(
    r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?)*\.[a-zA-Z]{2,}",
    re.IGNORECASE,
)


def extract_emails_from_text(text: str) -> List[str]:
    """
    从文本中提取邮箱地址
    优先提取目标前缀邮箱
    同时提取mailto:中的邮箱
    返回去重后的邮箱列表
    """
    found_emails = set()

    if not text:
        return []

    # 1. 提取目标前缀邮箱
    for match in PREFIX_PATTERN.finditer(text):
        found_emails.add(match.group(0).lower())

    # 2. 从mailto:链接中提取邮箱
    mailto_pattern = re.compile(
        r'mailto:([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
        re.IGNORECASE
    )
    for match in mailto_pattern.finditer(text):
        found_emails.add(match.group(1).lower())

    # 3. 若目标前缀邮箱很少（少于3个），尝试提取所有邮箱
    if len(found_emails) < 3:
        for match in GENERAL_EMAIL_PATTERN.finditer(text):
            found_emails.add(match.group(0).lower())

    return sorted(found_emails)
