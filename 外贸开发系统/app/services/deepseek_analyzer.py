"""
DeepSeek AI分析服务
调用DeepSeek API分析客户官网文本
生成客户类型、采购概率、开发切入点等分析结果
API Key 通过环境变量 DEEPSEEK_API_KEY 传入
"""
import os
import json
from typing import Optional, Dict, Any
import httpx


# DeepSeek API配置
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_API_URL = os.environ.get(
    "DEEPSEEK_API_URL", "https://api.deepseek.com/v1/chat/completions"
)
DEEPSEEK_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-v4-flash")


def _build_prompt(website_text: str) -> str:
    """构建发送给AI的提示词，控制在3000字符以内"""
    truncated_text = website_text[:3000]

    prompt = f"""请分析以下公司网页内容，返回严格的JSON格式（不要包含其他文字）：

网页内容：
{truncated_text}

请分析并返回JSON，格式如下：
{{
    "company_type": "公司类型（EPC / Contractor / Water Treatment Company / Manufacturer / Distributor / Consultant / End User / Other）",
    "analysis_reason": "分析原因（中文，50字以内）",
    "sales_hook": "推荐开发切入点（中文，50字以内）",
    "target_position": "推荐联系职位（中文，如CEO / Procurement Manager / Project Manager）",
    "summary": "英文客户摘要，50字以内",
    "identified_projects": "如果页面中有项目案例信息，请提取描述（中文，100字以内），没有则返回空字符串"
}}"""

    return prompt


async def analyze_company(website_text: str) -> Optional[Dict[str, Any]]:
    """调用DeepSeek API分析公司，返回解析后的JSON字典"""
    if not DEEPSEEK_API_KEY:
        print("未设置DEEPSEEK_API_KEY环境变量，跳过AI分析")
        return None

    prompt = _build_prompt(website_text)

    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": [
            {
                "role": "system",
                "content": "你是一位专业的外贸客户分析专家。请根据公司官网内容分析客户类型和采购潜力。只返回JSON格式数据。",
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.3,
        "max_tokens": 1000,
    }

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                DEEPSEEK_API_URL, headers=headers, json=payload
            )
            response.raise_for_status()
            result = response.json()

            ai_content = result["choices"][0]["message"]["content"]
            return _parse_ai_response(ai_content)

    except httpx.TimeoutException:
        print("DeepSeek API 请求超时")
        return None
    except httpx.HTTPStatusError as e:
        print(f"DeepSeek API HTTP错误: {e.response.status_code}")
        return None
    except Exception as e:
        print(f"DeepSeek API 调用异常: {str(e)}")
        return None


def _parse_ai_response(content: str) -> Optional[Dict[str, Any]]:
    """解析AI返回的JSON内容，处理Markdown代码块包裹的情况"""
    content = content.strip()

    # 移除可能的Markdown代码块标记
    if content.startswith("```"):
        lines = content.split("\n")
        json_lines = []
        in_code_block = False
        for line in lines:
            if line.strip().startswith("```"):
                in_code_block = not in_code_block
                continue
            if in_code_block:
                json_lines.append(line)
        if json_lines:
            content = "\n".join(json_lines)

    # 尝试解析JSON
    try:
        data = json.loads(content)
        return data
    except json.JSONDecodeError:
        try:
            start = content.index("{")
            end = content.rindex("}") + 1
            json_str = content[start:end]
            data = json.loads(json_str)
            return data
        except (ValueError, json.JSONDecodeError):
            print(f"无法解析AI返回的JSON: {content[:200]}")
            return None


def generate_summary(ai_result: Dict[str, Any], customer_info: Dict[str, str]) -> str:
    """根据AI分析结果生成150字以内的英文摘要"""
    # 优先使用AI返回的summary字段
    summary = ai_result.get("summary", "")
    if summary and len(summary) <= 150:
        return summary

    # 备用：手动拼接
    company_type = ai_result.get("company_type", "")
    country = customer_info.get("country", "")
    parts = []
    if country:
        parts.append(country)
    if company_type and company_type != "Other":
        parts.append(company_type)

    summary = " ".join(parts) if parts else "Company"
    if len(summary) > 150:
        summary = summary[:147] + "..."

    return summary
