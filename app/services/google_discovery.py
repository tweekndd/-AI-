"""
Google搜索发现服务（V2.2 升级）
支持多语言搜索：根据目标国家自动设置 hl/lr/cr 参数
通过 SerpAPI 调用 Google 搜索，稳定可靠，无需处理反爬
"""
import os
import asyncio
from typing import List, Dict, Optional
from urllib.parse import urlparse

import httpx

from app.services.country_language_map import get_language_info


# SerpAPI 配置
SERPAPI_API_KEY = os.environ.get("SERPAPI_API_KEY", "")
SERPAPI_URL = "https://serpapi.com/search"

# 每次搜索获取的结果数量
RESULTS_PER_PAGE = 10

# 搜索间隔（秒）
SEARCH_INTERVAL = 1.0


async def search_google(
    keyword: str,
    country: str,
    max_results: int = 50,
) -> List[Dict]:
    """
    通过 SerpAPI 搜索 Google，返回搜索结果列表
    支持多语言：自动根据 country 设置搜索语言和国家限制
    每个结果包含：title, website, snippet
    注意：每次API调用算一次搜索，翻页也会消耗配额
    """
    if not SERPAPI_API_KEY:
        print("错误: 未设置 SERPAPI_API_KEY 环境变量，无法使用 SerpAPI 搜索")
        return []

    all_websites = set()
    results_list = []

    # 最多获取的页数（限制最多5页=50条，节省API配额）
    max_pages = min((max_results + RESULTS_PER_PAGE - 1) // RESULTS_PER_PAGE, 5)

    # 从语言映射表获取完整参数
    lang_info = get_language_info(country) if country else None

    if lang_info:
        country_code = lang_info["gl"]           # gl 参数（如 "pl", "es"）
        hl_code = lang_info["hl"]               # hl 参数（如 "pl", "es"）
        lr_code = lang_info["lr"]               # lr 参数（如 "lang_pl"）
        cr_code = lang_info["cr"]               # cr 参数（如 "countryPL"）
        language = lang_info["language"]
        print(f"  多语言搜索: {country} → {language} (hl={hl_code}, lr={lr_code}, cr={cr_code}, gl={country_code})")
    else:
        country_code = ""
        hl_code = "en"
        lr_code = ""
        cr_code = ""

    # 关键词直接用（如果是多语言模式，关键词已经是目标语言，无需拼接国家名）
    search_query = keyword

    for page in range(max_pages):
        start = page * RESULTS_PER_PAGE

        results = await _fetch_via_serpapi(search_query, country_code, hl_code, lr_code, cr_code, start)

        if not results:
            print(f"  SerpAPI 第{page+1}页无结果，停止翻页")
            break

        # 去重
        new_count = 0
        for r in results:
            website = r.get("website", "")
            if website and website not in all_websites:
                all_websites.add(website)
                results_list.append(r)
                new_count += 1

        print(f"  SerpAPI [{keyword[:25]}...] 第{page+1}页: {len(results)}条, 新增{new_count}条")

        if new_count == 0:
            break

        if page < max_pages - 1:
            await asyncio.sleep(SEARCH_INTERVAL)

    return results_list


async def _fetch_via_serpapi(
    query: str,
    country_code: str,
    hl_code: str = "en",
    lr_code: str = "",
    cr_code: str = "",
    start: int = 0,
) -> Optional[List[Dict]]:
    """
    调用 SerpAPI 获取 Google 搜索结果
    支持多语言参数：hl（界面语言）、lr（结果语言限制）、cr（国家限制）
    API 文档: https://serpapi.com/search-api
    """
    params = {
        "api_key": SERPAPI_API_KEY,
        "engine": "google",
        "q": query,
        "num": RESULTS_PER_PAGE,
        "start": start,
        "hl": hl_code,
    }

    # 添加国家限制
    if country_code:
        params["gl"] = country_code       # 地理位置（Google 会优先返回该地区结果）
    if lr_code:
        params["lr"] = lr_code            # 语言限制（只返回该语言的结果）
    if cr_code:
        params["cr"] = cr_code            # 国家限制（只返回该国家/地区的结果）

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(SERPAPI_URL, params=params)

            # 先检查HTTP状态
            if response.status_code != 200:
                print(f"  SerpAPI HTTP {response.status_code}: {query[:40]}")
                if response.status_code == 429:
                    print("  SerpAPI 速率限制，等待5秒...")
                    await asyncio.sleep(5)
                return None

            # 尝试解析JSON
            try:
                data = response.json()
            except Exception:
                # 返回的不是JSON，可能是余额不足或API Key无效的页面
                text_preview = response.text[:300].replace("\n", " ")
                print(f"  SerpAPI 返回非JSON响应(可能API Key无效或余额不足): {text_preview}")
                return None

            # 检查SerpAPI返回的业务错误
            if "error" in data:
                print(f"  SerpAPI 返回错误: {data['error']}")
                return None

            # 检查搜索配额是否用尽
            search_metadata = data.get("search_metadata", {})
            if search_metadata.get("status") == "Error":
                error_msg = data.get("error", "未知错误")
                print(f"  SerpAPI 搜索失败: {error_msg}")
                return None

            # 解析 organic_results
            return _parse_serpapi_response(data)

    except httpx.TimeoutException:
        print(f"  SerpAPI 请求超时: {query[:40]}")
        return None
    except httpx.HTTPStatusError as e:
        print(f"  SerpAPI HTTP错误 {e.response.status_code}: {query[:40]}")
        return None
    except Exception as e:
        print(f"  SerpAPI 异常 [{type(e).__name__}]: {str(e)[:200]}")
        return None


def _parse_serpapi_response(data: dict) -> List[Dict]:
    """
    解析 SerpAPI 返回的 JSON 数据
    SerpAPI 返回格式: { "organic_results": [ { "title": ..., "link": ..., "snippet": ... } ] }
    """
    results = []
    organic_results = data.get("organic_results", [])

    for item in organic_results:
        try:
            title = item.get("title", "").strip()
            link = item.get("link", "").strip()
            snippet = item.get("snippet", "").strip() if item.get("snippet") else ""

            if not title or not link:
                continue

            # 验证URL是否有效
            parsed = urlparse(link)
            if not parsed.netloc:
                continue

            results.append({
                "title": title,
                "website": link,
                "snippet": snippet[:300],
            })

        except Exception:
            continue

    return results
