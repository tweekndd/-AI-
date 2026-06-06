"""
Excel导入服务
支持上传含 Company Name, Website, Country 三列的Excel文件
"""
import openpyxl
from typing import List, Dict
from app.database import SessionLocal, Customer


# 期望的列名映射（兼容中英文及大小写变化）
COLUMN_MAPPING = {
    "company name": "company_name",
    "company": "company_name",
    "公司名称": "company_name",
    "公司名": "company_name",
    "website": "website",
    "web": "website",
    "官网": "website",
    "网站": "website",
    "country": "country",
    "国家": "country",
}

# 需要的最终字段
REQUIRED_FIELDS = ["company_name", "website", "country"]


def _normalize_column_name(raw: str) -> str:
    """标准化列名：转小写去空格后查询映射表"""
    cleaned = raw.strip().lower()
    return COLUMN_MAPPING.get(cleaned, cleaned)


def parse_excel(file_path: str) -> List[Dict]:
    """
    解析Excel文件，返回客户数据列表
    每行数据为 dict: {company_name, website, country}
    跳过完全空行
    """
    wb = openpyxl.load_workbook(file_path, read_only=True)
    ws = wb.active

    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return []

    # 处理表头行：找到各列的位置
    header_row = rows[0]
    col_index = {}
    for i, cell in enumerate(header_row):
        if cell is not None:
            normalized = _normalize_column_name(str(cell))
            if normalized in REQUIRED_FIELDS:
                col_index[normalized] = i

    # 确认至少 company_name 存在
    if "company_name" not in col_index:
        raise ValueError(
            "Excel文件缺少必要列：Company Name / Website / Country。"
            "请确保表头包含这些字段。"
        )

    customers = []
    for row in rows[1:]:
        # 跳过完全为空的行
        if all(cell is None or str(cell).strip() == "" for cell in row):
            continue

        record = {}
        for field in REQUIRED_FIELDS:
            idx = col_index.get(field)
            if idx is not None and idx < len(row):
                val = row[idx]
                record[field] = str(val).strip() if val is not None else ""
            else:
                record[field] = ""

        # 跳过公司名为空的行
        if not record["company_name"]:
            continue

        customers.append(record)

    wb.close()
    return customers


def import_customers(customers: List[Dict]) -> int:
    """
    将客户数据导入数据库
    若已存在同名公司则跳过（避免重复导入）
    返回成功导入的数量
    """
    db = SessionLocal()
    count = 0
    try:
        for c in customers:
            # 检查是否已存在
            existing = db.query(Customer).filter(
                Customer.company_name == c["company_name"]
            ).first()
            if existing:
                continue

            customer = Customer(
                company_name=c["company_name"],
                website=c.get("website", ""),
                country=c.get("country", ""),
            )
            db.add(customer)
            count += 1

        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

    return count
