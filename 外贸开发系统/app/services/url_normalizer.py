"""
网址标准化服务（V2.0 新增）
将各种URL格式统一为标准域名格式，用于去重和缓存索引
"""
from urllib.parse import urlparse, urlunparse
import re


def normalize_url(raw_url: str) -> str:
    """
    统一URL格式为标准域名
    输入: https://abc.com/about, http://www.abc.com, abc.com
    输出: abc.com
    """
    if not raw_url:
        return ""

    url = raw_url.strip().lower()

    # 移除协议前缀
    url = re.sub(r'^https?://', '', url)

    # 移除 www. 前缀
    url = re.sub(r'^www\.', '', url)

    # 取域名部分（去掉路径/参数/锚点）
    url = url.split('/')[0]

    # 去掉末尾可能的点号
    url = url.rstrip('.')

    return url


def extract_domain(raw_url: str) -> str:
    """
    从URL中提取域名
    输入: https://www.abc.com/about-us
    输出: abc.com
    """
    if not raw_url:
        return ""

    # 确保有协议
    url = raw_url.strip()
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
        return url


def is_same_domain(url1: str, url2: str) -> bool:
    """判断两个URL是否属于同一域名"""
    return normalize_url(url1) == normalize_url(url2)
