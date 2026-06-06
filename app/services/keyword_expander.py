"""
AI关键词扩展服务（V2.0 新增）
调用DeepSeek自动将用户输入的1个关键词扩展为10~20个相关关键词
用于Google搜索发现更多潜在客户
"""
import os
import json
from typing import Optional, List
import httpx


DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_API_URL = os.environ.get(
    "DEEPSEEK_API_URL", "https://api.deepseek.com/v1/chat/completions"
)
DEEPSEEK_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-v4-flash")


async def expand_keywords(base_keyword: str) -> Optional[List[str]]:
    """
    调用DeepSeek将基础关键词扩展为10~20个相关关键词
    用于Google搜索发现客户
    返回关键词列表
    """
    if not DEEPSEEK_API_KEY:
        print("未设置DEEPSEEK_API_KEY，无法扩展关键词")
        return [base_keyword]

    prompt = f"""请根据用户输入的行业关键词，扩展出10~20个相关的搜索关键词。
这些关键词将用于在Google搜索潜在客户。

用户输入的关键词：{base_keyword}

要求：
1. 扩展10~20个相关关键词
2. 每个关键词应是与原词相关的不同搜索词
3. 包含不同角度（如不同业务类型、不同应用场景）
4. 返回JSON数组格式

返回格式：
["keyword1", "keyword2", "keyword3", ...]

只返回JSON数组，不要包含其他文字。"""

    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": [
            {
                "role": "system",
                "content": "你是一个专业的B2B营销关键词扩展专家。返回严格的JSON数组格式。",
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.7,
        "max_tokens": 1000,
    }

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                DEEPSEEK_API_URL, headers=headers, json=payload
            )
            response.raise_for_status()
            result = response.json()

            content = result["choices"][0]["message"]["content"]
            return _parse_keyword_list(content)

    except Exception as e:
        print(f"关键词扩展API调用失败: {str(e)[:100]}")
        return [base_keyword]


def _parse_keyword_list(content: str) -> Optional[List[str]]:
    """解析AI返回的关键词列表"""
    content = content.strip()

    # 移除Markdown代码块标记
    if content.startswith("```"):
        lines = content.split("\n")
        json_lines = []
        in_block = False
        for line in lines:
            if line.strip().startswith("```"):
                in_block = not in_block
                continue
            if in_block:
                json_lines.append(line)
        if json_lines:
            content = "\n".join(json_lines)

    try:
        keywords = json.loads(content)
        if isinstance(keywords, list) and len(keywords) > 0:
            # 去重并限制数量
            unique = []
            seen = set()
            for kw in keywords:
                kw_lower = kw.strip().lower()
                if kw_lower not in seen and kw_lower:
                    seen.add(kw_lower)
                    unique.append(kw.strip())
            return unique[:20]
    except (json.JSONDecodeError, TypeError):
        pass

    # 如果解析失败，返回原始关键词作为兜底
    return None
