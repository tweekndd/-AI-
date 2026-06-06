"""
关键词识别服务
统计文本中正向和负向行业关键词的命中次数
"""
import re
from typing import Dict, Tuple


# 正向关键词（表示该客户可能是潜在买家）
POSITIVE_KEYWORDS = [
    "wastewater",
    "water treatment",
    "sewage",
    "effluent",
    "biogas",
    "anaerobic",
    "digester",
    "tank",
    "storage tank",
    "reservoir",
    "municipal water",
    "desalination",
    "irrigation",
    "industrial water",
]

# 负向关键词（表示该客户可能不是目标客户）
NEGATIVE_KEYWORDS = [
    "career",
    "job",
    "vacancy",
    "news",
    "blog",
    "school",
    "university",
]


def analyze_keywords(text: str) -> Tuple[Dict[str, int], Dict[str, int]]:
    """
    分析文本中关键词的命中情况
    返回 (正向关键词计数字典, 负向关键词计数字典)
    """
    if not text:
        return {}, {}

    text_lower = text.lower()

    positive_hits = _count_keywords(text_lower, POSITIVE_KEYWORDS)
    negative_hits = _count_keywords(text_lower, NEGATIVE_KEYWORDS)

    return positive_hits, negative_hits


def _count_keywords(text: str, keywords: list) -> Dict[str, int]:
    """统计一组关键词在文本中的出现次数"""
    result = {}
    for keyword in keywords:
        if " " in keyword:
            # 多词关键词，直接查找子串
            pattern = re.compile(re.escape(keyword), re.IGNORECASE)
        else:
            # 单次关键词：使用单词边界确保完整匹配
            pattern = re.compile(r'\b' + re.escape(keyword) + r'\b', re.IGNORECASE)

        count = len(pattern.findall(text))
        if count > 0:
            result[keyword] = count

    # 按次数降序排序
    return dict(sorted(result.items(), key=lambda x: x[1], reverse=True))
