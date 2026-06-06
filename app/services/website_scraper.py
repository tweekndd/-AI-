"""
官网抓取服务
异步方式访问网站，优先抓取指定页面路径的纯文本内容
"""
import asyncio
from typing import Optional
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

# 优先抓取的页面路径（按优先级排序）
PRIORITY_PATHS = [
    "/about",
    "/about-us",
    "/company",
    "/services",
    "/projects",
    "/contact",
    "/",
]

# 请求超时设置
TIMEOUT_SECONDS = 15
# 最大并发数
MAX_CONCURRENT = 5


def _extract_text_from_html(html: str) -> str:
    """
    从HTML中提取纯文本
    - 自动过滤HTML标签、JS、CSS
    - 保留可阅读文本
    """
    soup = BeautifulSoup(html, "html.parser")

    # 移除script和style标签
    for tag in soup(["script", "style", "noscript", "iframe", "svg"]):
        tag.decompose()

    # 获取文本
    text = soup.get_text(separator="\n")

    # 清理多余空白
    lines = []
    for line in text.splitlines():
        line = line.strip()
        if line:
            lines.append(line)

    # 合并成段落
    cleaned = "\n\n".join(lines)
    return cleaned


def _normalize_url(website_url: str) -> Optional[str]:
    """规范化URL，确保有scheme"""
    if not website_url:
        return None
    if not website_url.startswith(("http://", "https://")):
        website_url = "https://" + website_url
    parsed = urlparse(website_url)
    if not parsed.netloc:
        return None
    return f"{parsed.scheme}://{parsed.netloc}"


async def _fetch_single_page(
    client: httpx.AsyncClient, url: str, semaphore: asyncio.Semaphore
) -> Optional[str]:
    """抓取单个页面，返回纯文本内容"""
    async with semaphore:
        try:
            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                "Accept": "text/html,application/xhtml+xml",
                "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8",
            }
            response = await client.get(
                url, headers=headers, timeout=TIMEOUT_SECONDS, follow_redirects=True
            )
            response.raise_for_status()

            # 只处理HTML页面
            content_type = response.headers.get("content-type", "")
            if "text/html" not in content_type:
                return None

            return _extract_text_from_html(response.text)

        except Exception:
            return None


async def scrape_website(website_url: str) -> Optional[str]:
    """
    异步抓取客户官网
    优先抓取 /, /about, /about-us, /company, /services, /projects, /contact
    合并所有抓取到的文本返回
    """
    base_url = _normalize_url(website_url)
    if not base_url:
        return None

    semaphore = asyncio.Semaphore(MAX_CONCURRENT)

    async with httpx.AsyncClient(verify=False) as client:
        tasks = []
        for path in PRIORITY_PATHS:
            url = base_url + path
            tasks.append(_fetch_single_page(client, url, semaphore))

        # 并发抓取所有页面
        results = await asyncio.gather(*tasks)

    # 合并非空结果，去重
    all_texts = []
    seen_texts = set()
    for text in results:
        if text and len(text) > 50:
            key = text[:100]
            if key not in seen_texts:
                seen_texts.add(key)
                all_texts.append(text)

    if not all_texts:
        return None

    # 合并所有文本
    combined = "\n\n===== 下一页 =====\n\n".join(all_texts)

    # 限制总长度
    if len(combined) > 50000:
        combined = combined[:50000]

    return combined
