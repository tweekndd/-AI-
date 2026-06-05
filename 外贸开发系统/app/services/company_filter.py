"""
公司结果过滤服务（V2.0 新增）
自动过滤社交媒体、招聘、新闻、政府、教育等非企业官网
修复：将子串匹配改为更精确的域名匹配，避免误伤正常企业域名
"""
import re
from typing import List, Dict
from urllib.parse import urlparse


# 需要过滤的完整域名黑名单（精确匹配域名主体）
BLACKLIST_DOMAINS_EXACT = {
    # 社交媒体
    "linkedin.com", "facebook.com", "instagram.com", "twitter.com",
    "x.com", "youtube.com", "tiktok.com", "pinterest.com",
    "snapchat.com", "reddit.com", "medium.com",
    # 百科
    "wikipedia.org",
    # 招聘网站
    "indeed.com", "monster.com", "glassdoor.com", "careerbuilder.com",
    "ziprecruiter.com", "simplyhired.com", "dice.com",
    # 新闻网站
    "cnn.com", "bbc.com", "bbc.co.uk", "reuters.com", "bloomberg.com",
    "forbes.com", "businesswire.com", "prnewswire.com",
    "globenewswire.com", "newsweek.com", "theguardian.com",
    "nytimes.com", "wsj.com", "economist.com",
    # 政府（完整域名）
    "usa.gov", "gov.uk",
    # 黄页/目录
    "yellowpages.com", "yell.com", "manta.com", "thomasnet.com",
    "alibaba.com", "made-in-china.com", "tradekey.com", "ec21.com",
    "ecplaza.net", "exportersindia.com", "tradesparq.com",
    "industryweek.com", "kompass.com",
}


def _extract_domain(url: str) -> str:
    """从URL中提取纯域名（不含www）"""
    if not url:
        return ""
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        # 移除 www. 前缀
        if domain.startswith("www."):
            domain = domain[4:]
        return domain
    except Exception:
        return url.lower()


def is_blacklisted(url: str) -> bool:
    """判断URL是否属于应过滤的黑名单"""
    if not url:
        return True

    domain = _extract_domain(url)
    if not domain:
        return True

    # 1. 精确匹配完整域名
    if domain in BLACKLIST_DOMAINS_EXACT:
        return True

    # 2. 顶级域名后缀过滤
    # .gov 结尾（各国政府网站）
    if domain.endswith(".gov") or re.search(r'\.gov\.[a-z]{2,}$', domain):
        return True
    # .edu 结尾（教育机构）
    if domain.endswith(".edu") or re.search(r'\.edu\.[a-z]{2,}$', domain):
        return True
    # .ac.uk 等学术域名
    if re.search(r'\.ac\.[a-z]{2,}$', domain):
        return True

    # 3. 域名关键词判定（使用.分隔后的完整段匹配，避免子串误伤）
    parts = domain.split(".")

    for part in parts:
        # 跳过纯通用词（如 com, org, co, uk, au 等）
        if part in {"com", "org", "net", "co", "uk", "au", "de", "fr", "jp",
                     "cn", "gov", "edu", "ac", "io", "www", "au"}:
            continue
        # 如果域名某个部分完全等于这些词，才判定为黑名单
        if part in {"wikipedia", "linkedin", "facebook", "instagram",
                     "twitter", "youtube", "tiktok", "reddit"}:
            return True

    # 4. 已知子域名黑名单（如 jobs.company.com 仍是企业官网，不过滤）
    # 但如果域名本身就是 jobsite.com 这种，需要过滤
    if domain in {"jobsite.com", "jobs.com", "careers.com", "monster.com",
                   "indeed.com"}:
        return True

    return False


def filter_search_results(results: List[Dict]) -> List[Dict]:
    """
    过滤搜索结果，只保留企业官网
    """
    filtered = []
    for result in results:
        website = result.get("website", "")
        if not website:
            continue
        if is_blacklisted(website):
            continue
        filtered.append(result)

    return filtered
