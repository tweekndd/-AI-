"""
评分引擎（V2.0 更新）
由程序规则完成客户评分，AI不再负责打分
评分配置从 industry_config.json 读取，无需修改代码即可调整
"""
import json
import os
import re
from typing import Dict, List, Optional, Tuple


def _load_config() -> dict:
    """加载行业配置中心"""
    config_path = os.path.join(os.path.dirname(__file__), "industry_config.json")
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"scoring": {}}


def _load_country_weights() -> Dict[str, int]:
    """加载国家权重配置"""
    config_path = os.path.join(os.path.dirname(__file__), "country_weights.json")
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"Saudi Arabia": 15, "UAE": 12, "Qatar": 12, "Other": 5}


def _score_industry_match(website_text: str) -> Tuple[int, str]:
    """计算行业匹配度（最高30分），从配置读取关键词权重"""
    config = _load_config()
    industry_cfg = config.get("scoring", {}).get("industry_match", {})
    max_score = industry_cfg.get("max_score", 30)
    keyword_weights = industry_cfg.get("keywords", {})

    if not website_text or not keyword_weights:
        return 0, "无官网内容"

    total_score = 0
    hit_details = []
    text_lower = website_text.lower()

    for keyword, weight in keyword_weights.items():
        if " " in keyword:
            pattern = re.compile(re.escape(keyword), re.IGNORECASE)
        else:
            pattern = re.compile(r'\b' + re.escape(keyword) + r'\b', re.IGNORECASE)
        count = len(pattern.findall(text_lower))
        if count > 0:
            points = min(weight, 5)
            total_score += points
            hit_details.append(f"{keyword}(+{points})")

    total_score = min(total_score, max_score)
    detail = "、".join(hit_details) if hit_details else "未命中行业关键词"
    return total_score, detail


def _score_project_match(website_text: str) -> Tuple[int, str]:
    """计算项目匹配度（最高25分），从配置读取"""
    config = _load_config()
    proj_cfg = config.get("scoring", {}).get("project_match", {})
    max_score = proj_cfg.get("max_score", 25)
    detection_kw = proj_cfg.get("detection_keywords", [])
    content_kw = proj_cfg.get("content_keywords", [])

    if not website_text:
        return 0, "无官网内容"

    score = 0
    details = []
    text_lower = website_text.lower()

    # 检测项目相关内容
    has_project = False
    for kw in detection_kw:
        if kw in text_lower:
            has_project = True
            break

    if has_project:
        score += proj_cfg.get("has_project_base", 10)
        details.append("存在项目案例页面(+10)")

    # 检测是否涉及水处理
    has_water = False
    for kw in content_kw:
        if re.search(r'\b' + re.escape(kw) + r'\b', text_lower):
            has_water = True
            break

    if has_water:
        score += proj_cfg.get("has_water_content", 15)
        details.append("项目涉及水处理(+15)")
    elif score > 0:
        score += proj_cfg.get("low_relevance", 5)
        details.append("项目与水务相关度低(+5)")

    score = min(score, max_score)
    detail = "、".join(details) if details else "未识别到项目信息"
    return score, detail


def _score_company_type(company_type: Optional[str]) -> Tuple[int, str]:
    """计算公司类型分数，从配置读取"""
    config = _load_config()
    type_cfg = config.get("scoring", {}).get("company_type", {})
    max_score = type_cfg.get("max_score", 20)
    type_scores = type_cfg.get("types", {})

    if not company_type:
        return 0, "未识别"

    score = type_scores.get(company_type, 0)
    if score == 0:
        ct_lower = company_type.lower()
        for key, val in type_scores.items():
            if key.lower() in ct_lower or ct_lower in key.lower():
                score = val
                break

    return score, f"{company_type}(+{score})"


def _score_country(country: Optional[str]) -> Tuple[int, str]:
    """计算国家优先级分数"""
    if not country:
        return 0, "未指定国家"

    weights = _load_country_weights()
    score = weights.get(country)

    if score is None:
        country_lower = country.lower()
        score = 0
        for key, val in weights.items():
            if key.lower() in country_lower or country_lower in key.lower():
                score = val
                break
        if score == 0:
            score = weights.get("Other", 5)

    max_score = _load_config().get("scoring", {}).get("country", {}).get("max_score", 15)
    score = min(score, max_score)
    return score, f"{country}(+{score})"


def _score_contact(emails: List[str]) -> Tuple[int, str]:
    """计算联系方式完整度分数"""
    contact_cfg = _load_config().get("scoring", {}).get("contact", {})
    tiers = contact_cfg.get("tiers", [])
    count = len(emails) if emails else 0

    score = 0
    for tier in tiers:
        if count >= tier.get("min_emails", 0):
            score = tier.get("score", 0)

    detail = f"{count}个邮箱(+{score})" if count > 0 else "无邮箱(+0)"
    return score, detail


def calculate_scores(
    website_text: Optional[str],
    positive_keywords: Optional[Dict[str, int]],
    company_type: Optional[str],
    country: Optional[str],
    emails: List[str],
) -> Dict:
    """
    综合计算所有维度分数
    返回各维度分数和总分的字典
    """
    priority_rules = _load_config().get("priority_rules", {
        "A": {"min": 80}, "B": {"min": 60}, "C": {"min": 40}, "D": {"min": 0}
    })

    kw_text = website_text or ""

    industry_score, industry_detail = _score_industry_match(kw_text)
    project_score, project_detail = _score_project_match(kw_text)
    type_score, type_detail = _score_company_type(company_type)
    country_score, country_detail = _score_country(country)
    contact_score, contact_detail = _score_contact(emails)

    total_score = industry_score + project_score + type_score + country_score + contact_score
    total_score = min(total_score, 100)

    # 计算优先级
    priority = "D"
    for level, rules in sorted(priority_rules.items(), key=lambda x: -x[1].get("min", 0)):
        if total_score >= rules.get("min", 0):
            priority = level
            break

    return {
        "industry_score": industry_score,
        "industry_detail": industry_detail,
        "project_score": project_score,
        "project_detail": project_detail,
        "company_type_score": type_score,
        "company_type_detail": type_detail,
        "country_score": country_score,
        "country_detail": country_detail,
        "contact_score": contact_score,
        "contact_detail": contact_detail,
        "total_score": total_score,
        "priority": priority,
    }
