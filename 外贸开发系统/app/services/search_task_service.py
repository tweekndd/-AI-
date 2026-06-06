"""
搜索任务管理服务（V2.0 新增）
管理客户发现任务的整个生命周期：
关键词扩展 -> 缓存检查 -> Google搜索 -> 过滤 -> 标准化 -> 去重 -> 自动分析 -> 保存
支持断点续跑、失败重试
"""
import json
import datetime
import asyncio
import logging
from typing import Optional, List, Dict
from sqlalchemy.orm import Session

from app.database import SessionLocal, Customer, SearchTask
from app.services.url_normalizer import normalize_url
from app.services.company_filter import filter_search_results, is_blacklisted
from app.services.cache_manager import (
    get_search_cache,
    save_search_cache,
    get_website_cache,
    save_website_cache,
    get_analysis_cache,
    save_analysis_cache,
)
from app.services.retry_manager import retry_async
from app.services.keyword_expander import expand_keywords
from app.services.google_discovery import search_google
from app.services.website_scraper import scrape_website
from app.services.email_extractor import extract_emails_from_text
from app.services.keyword_analyzer import analyze_keywords
from app.services.deepseek_analyzer import analyze_company, generate_summary
from app.services.scoring_engine import calculate_scores

logger = logging.getLogger("search_task")
_global_stop_flag = False


def request_stop():
    """请求停止所有正在运行的搜索任务"""
    global _global_stop_flag
    _global_stop_flag = True


def reset_stop_flag():
    """重置停止标记"""
    global _global_stop_flag
    _global_stop_flag = False


def get_stop_flag() -> bool:
    """获取当前停止标记状态"""
    return _global_stop_flag


async def run_search_task(task_id: int):
    """
    执行搜索任务（包含完整的发现+分析流程，支持断点续跑）

    完整流程：
    1. 更新任务状态为Running
    2. AI扩展关键词（如果还没扩展）
    3. 遍历扩展关键词：
       a. 检查搜索缓存（30天内有效）
       b. Google搜索
       c. 过滤非企业官网
       d. 网址标准化
       e. 去重（检查是否已存在）
       f. 自动进入V1分析流程（官网抓取 -> 邮箱提取 -> 关键词分析 -> AI分析 -> 规则评分）
       g. 保存到数据库
    4. 更新任务状态为Completed
    """
    global _global_stop_flag
    reset_stop_flag()

    db = SessionLocal()
    try:
        task = db.query(SearchTask).filter(SearchTask.id == task_id).first()
        if not task:
            logger.error(f"任务 {task_id} 不存在")
            return

        # 更新状态为Running
        task.status = "Running"
        db.commit()

        logger.info(f"开始执行搜索任务 {task_id}: {task.country} / {task.keyword}")

        # 步骤1：AI扩展关键词（如果还未扩展）
        expanded_keywords = []
        if task.expanded_keywords:
            expanded_keywords = json.loads(task.expanded_keywords)
        else:
            logger.info(f"正在扩展关键词: {task.keyword}")
            expanded = await expand_keywords(task.keyword)
            if expanded and len(expanded) > 0:
                expanded_keywords = expanded
            else:
                expanded_keywords = [task.keyword]

            task.expanded_keywords = json.dumps(expanded_keywords, ensure_ascii=False)
            db.commit()
            logger.info(f"关键词扩展完成，共 {len(expanded_keywords)} 个")

        # 步骤2：从断点处继续
        start_index = task.current_keyword_index

        for idx in range(start_index, len(expanded_keywords)):
            # 检查停止标记
            if _global_stop_flag:
                logger.info(f"任务 {task_id} 被用户停止")
                task.status = "Paused"
                task.current_keyword_index = idx
                db.commit()
                return

            # 每次处理新关键词前重置状态（如果之前被暂停过）
            if task.status != "Running":
                task.status = "Running"
                db.commit()

            keyword = expanded_keywords[idx]
            logger.info(f"[{idx+1}/{len(expanded_keywords)}] 搜索关键词: {keyword}")

            # 更新当前进度
            task.current_keyword_index = idx
            task.status = "Running"
            db.commit()

            # 步骤3：检查搜索缓存
            cached_results = get_search_cache(db, keyword, task.country)
            if cached_results:
                logger.info(f"使用搜索缓存: {keyword} ({len(cached_results)}条)")
                search_results = cached_results
            else:
                # 步骤4：Google搜索
                search_results = await retry_async(
                    search_google,
                    keyword=keyword,
                    country=task.country,
                    max_results=task.search_depth or 50,
                    max_retries=2,
                    retry_delay=3.0,
                    task_name=f"Google搜索[{keyword}]",
                )
                if not search_results:
                    search_results = []

                # 保存到搜索缓存
                save_search_cache(db, keyword, task.country, search_results)
                logger.info(f"Google搜索完成: {keyword} ({len(search_results)}条)")

            # 步骤5：过滤非企业官网
            filtered_results = filter_search_results(search_results)
            logger.info(f"过滤后剩余: {len(filtered_results)}/{len(search_results)}条")

            task.found_websites = (task.found_websites or 0) + len(filtered_results)

            # 步骤6：遍历每个搜索结果
            for result in filtered_results:
                # 检查停止标记
                if _global_stop_flag:
                    task.status = "Paused"
                    task.current_keyword_index = idx
                    db.commit()
                    return

                raw_url = result.get("website", "")
                if not raw_url:
                    continue

                # 网址标准化
                domain = normalize_url(raw_url)

                # 二次检查黑名单
                if is_blacklisted(domain):
                    continue

                # 检查数据库是否已存在相同域名
                existing = db.query(Customer).filter(
                    Customer.website.ilike(f"%{domain}%")
                ).first()

                if existing:
                    logger.info(f"跳过已存在的公司: {domain}")
                    continue

                # 自动进入V1分析流程
                try:
                    await _auto_analyze_and_save(
                        db=db,
                        domain=domain,
                        country=task.country,
                        discovery_keyword=keyword,
                        title=result.get("title", ""),
                    )
                    task.new_companies = (task.new_companies or 0) + 1
                    task.analyzed_companies = (task.analyzed_companies or 0) + 1
                except Exception as e:
                    logger.error(f"分析失败 {domain}: {str(e)[:100]}")
                    continue

        # 任务完成
        task.status = "Completed"
        task.finished_at = datetime.datetime.utcnow()
        db.commit()
        logger.info(f"搜索任务 {task_id} 完成，新增 {task.new_companies} 个公司")

    except Exception as e:
        logger.error(f"搜索任务 {task_id} 异常: {str(e)[:200]}")
        db.rollback()
        task = db.query(SearchTask).filter(SearchTask.id == task_id).first()
        if task:
            task.status = "Failed"
            task.error_message = str(e)[:500]
            db.commit()
    finally:
        db.close()


async def _auto_analyze_and_save(
    db: Session,
    domain: str,
    country: str,
    discovery_keyword: str,
    title: str,
):
    """
    自动执行完整的V1分析流程：
    官网抓取(缓存) -> 邮箱提取 -> 关键词分析 -> AI分析(缓存) -> 规则评分 -> 保存
    """
    website = f"https://{domain}"

    # 创建新客户记录
    now = datetime.datetime.utcnow()
    customer = Customer(
        company_name=title[:255] if title else domain,
        website=domain,
        country=country,
        discovery_source="Google",
        discovery_keyword=discovery_keyword,
        first_found_at=now,
        created_at=now,
    )
    db.add(customer)
    db.flush()  # 获取id

    # 步骤1：官网抓取（检查缓存）
    cached_website = get_website_cache(db, domain)
    if cached_website:
        website_text = cached_website["content"]
        logger.info(f"使用官网缓存: {domain}")
    else:
        website_text = await retry_async(
            scrape_website,
            website,
            max_retries=2,
            task_name=f"官网抓取[{domain}]",
        )
        if website_text:
            save_website_cache(db, domain, website_text)

    if website_text:
        customer.website_text = website_text

        # 检查停止标记 — 爬取完成后，AI分析前
        if _global_stop_flag:
            logger.info(f"停止信号已触发，跳过 {domain} 的AI分析")
            customer.analyzed_at = datetime.datetime.utcnow()
            db.commit()
            return

        # 步骤2：邮箱提取
        emails = extract_emails_from_text(website_text)
        email_list = list(set(emails))
        customer.emails = json.dumps(email_list, ensure_ascii=False)

        # 步骤3：关键词分析
        pos_hits, neg_hits = analyze_keywords(website_text)
        customer.positive_keywords = json.dumps(pos_hits, ensure_ascii=False)
        customer.negative_keywords = json.dumps(neg_hits, ensure_ascii=False)

        # 步骤4：DeepSeek AI分析（检查缓存）
        cached_analysis = get_analysis_cache(db, domain, website_text)
        if cached_analysis:
            ai_result = cached_analysis
            logger.info(f"使用AI分析缓存: {domain}")
        else:
            # 检查停止标记 — AI分析前（AI分析是最耗时步骤）
            if _global_stop_flag:
                logger.info(f"停止信号已触发，跳过 {domain} 的AI分析")
                customer.analyzed_at = datetime.datetime.utcnow()
                db.commit()
                return

            ai_result = await retry_async(
                analyze_company,
                website_text,
                max_retries=2,
                task_name=f"AI分析[{domain}]",
            )
            if ai_result:
                save_analysis_cache(db, domain, website_text, ai_result)

        if ai_result:
            customer.ai_raw_json = json.dumps(ai_result, ensure_ascii=False)
            customer.company_type = ai_result.get("company_type", "")
            customer.sales_hook = ai_result.get("sales_hook", "")
            customer.target_position = ai_result.get("target_position", "")
            customer.identified_projects = ai_result.get("identified_projects", "")
            customer_info = {"country": country, "company_name": title}
            customer.ai_summary = generate_summary(ai_result, customer_info)

        # 步骤5：规则评分
        scores = calculate_scores(
            website_text=website_text,
            positive_keywords=pos_hits,
            company_type=customer.company_type,
            country=country,
            emails=email_list,
        )

        customer.industry_score = scores["industry_score"]
        customer.project_score = scores["project_score"]
        customer.company_type_score = scores["company_type_score"]
        customer.country_score = scores["country_score"]
        customer.contact_score = scores["contact_score"]
        customer.total_score = scores["total_score"]
        customer.priority = scores["priority"]

    customer.analyzed_at = datetime.datetime.utcnow()
    db.commit()
    logger.info(f"新公司自动分析完成: {domain} (评分: {customer.total_score})")


def get_paused_tasks(db: Session) -> List[SearchTask]:
    """获取所有已暂停的任务（用于断点续跑）"""
    return db.query(SearchTask).filter(
        SearchTask.status == "Paused"
    ).all()


def resume_paused_task(task_id: int):
    """标记暂停任务为Pending，以便重新调度"""
    db = SessionLocal()
    try:
        task = db.query(SearchTask).filter(SearchTask.id == task_id).first()
        if task and task.status == "Paused":
            task.status = "Pending"
            db.commit()
            return True
        return False
    finally:
        db.close()
