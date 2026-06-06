"""
数据库配置与模型定义
V2.0：新增 search_tasks, search_cache, website_cache, analysis_cache 表
       Customer 新增 discovery_source, discovery_keyword, first_found_at
"""
import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker

# 数据库文件路径（SQLite本地文件）
DATABASE_URL = "sqlite:///./app/customers.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Customer(Base):
    """客户数据模型（V2.0 新增发现来源字段）"""
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    company_name = Column(String(255), nullable=False, index=True, comment="公司名称")
    website = Column(String(500), nullable=True, comment="公司官网")
    country = Column(String(100), nullable=True, comment="国家")

    # V2.0 新增：发现来源记录
    discovery_source = Column(String(50), nullable=True, comment="发现来源（Google / Manual Import）")
    discovery_keyword = Column(String(200), nullable=True, comment="发现时使用的关键词")
    first_found_at = Column(DateTime, nullable=True, comment="首次发现时间")

    # 邮箱与官网内容
    emails = Column(Text, nullable=True, comment="提取的邮箱列表（JSON格式）")
    website_text = Column(Text, nullable=True, comment="官网爬取的纯文本内容")
    positive_keywords = Column(Text, nullable=True, comment="命中的正向关键词及次数（JSON格式）")
    negative_keywords = Column(Text, nullable=True, comment="命中的负向关键词及次数（JSON格式）")

    # 规则评分引擎字段
    industry_score = Column(Integer, nullable=True, comment="行业匹配度 0-30")
    project_score = Column(Integer, nullable=True, comment="项目匹配度 0-25")
    company_type_score = Column(Integer, nullable=True, comment="公司类型 0-20")
    country_score = Column(Integer, nullable=True, comment="国家优先级 0-15")
    contact_score = Column(Integer, nullable=True, comment="联系方式完整度 0-10")
    total_score = Column(Integer, nullable=True, comment="总分 0-100")
    priority = Column(String(1), nullable=True, comment="优先级 A/B/C/D")

    # AI分析字段
    company_type = Column(String(50), nullable=True, comment="AI分析的公司类型")
    ai_summary = Column(Text, nullable=True, comment="AI生成的150字以内摘要（英文）")
    sales_hook = Column(Text, nullable=True, comment="推荐开发切入点（中文）")
    target_position = Column(Text, nullable=True, comment="推荐联系职位（中文）")
    identified_projects = Column(Text, nullable=True, comment="AI识别的项目信息（JSON格式）")
    ai_raw_json = Column(Text, nullable=True, comment="AI返回的原始JSON数据")
    created_at = Column(DateTime, default=datetime.datetime.utcnow, comment="创建时间")
    analyzed_at = Column(DateTime, nullable=True, comment="分析完成时间")


class SearchTask(Base):
    """搜索任务（V2.0 新增）"""
    __tablename__ = "search_tasks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    country = Column(String(100), nullable=False, comment="搜索国家")
    keyword = Column(String(200), nullable=False, comment="原始关键词")
    expanded_keywords = Column(Text, nullable=True, comment="AI扩展的关键词列表（JSON数组）")
    search_depth = Column(Integer, default=50, comment="每个关键词期望搜索数量")
    status = Column(String(20), default="Pending", comment="任务状态: Pending/Running/Completed/Failed/Paused")
    found_websites = Column(Integer, default=0, comment="发现的网站数量")
    analyzed_companies = Column(Integer, default=0, comment="已分析的公司数量")
    new_companies = Column(Integer, default=0, comment="新增公司数量")
    current_keyword_index = Column(Integer, default=0, comment="当前处理到第几个扩展关键词（断点续跑）")
    error_message = Column(Text, nullable=True, comment="失败时的错误信息")
    created_at = Column(DateTime, default=datetime.datetime.utcnow, comment="创建时间")
    finished_at = Column(DateTime, nullable=True, comment="完成时间")


class SearchCache(Base):
    """搜索结果缓存（V2.0 新增，避免重复搜索相同关键词）"""
    __tablename__ = "search_cache"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    keyword = Column(String(200), nullable=False, index=True, comment="搜索关键词")
    country = Column(String(100), nullable=False, index=True, comment="搜索国家")
    website = Column(String(500), nullable=False, comment="发现的企业官网")
    title = Column(String(500), nullable=True, comment="搜索结果标题")
    snippet = Column(Text, nullable=True, comment="搜索结果摘要")
    created_at = Column(DateTime, default=datetime.datetime.utcnow, comment="缓存时间")


class WebsiteCache(Base):
    """官网抓取缓存（V2.0 新增，避免重复抓取相同网站）"""
    __tablename__ = "website_cache"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    website = Column(String(500), nullable=False, unique=True, index=True, comment="网站域名")
    content = Column(Text, nullable=True, comment="抓取的纯文本内容")
    content_hash = Column(String(64), nullable=True, comment="内容哈希值，用于判断内容是否变化")
    last_crawled = Column(DateTime, nullable=True, comment="上次抓取时间")


class AnalysisCache(Base):
    """AI分析缓存（V2.0 新增，避免重复调用DeepSeek）"""
    __tablename__ = "analysis_cache"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    website = Column(String(500), nullable=False, index=True, comment="网站域名")
    content_hash = Column(String(64), nullable=True, comment="对应官网内容的哈希值")
    company_type = Column(String(50), nullable=True, comment="公司类型")
    summary = Column(Text, nullable=True, comment="英文摘要")
    sales_hook = Column(Text, nullable=True, comment="开发切入点")
    target_position = Column(Text, nullable=True, comment="推荐联系职位")
    analysis_reason = Column(Text, nullable=True, comment="分析原因")
    identified_projects = Column(Text, nullable=True, comment="识别的项目信息")
    raw_json = Column(Text, nullable=True, comment="AI返回的原始JSON")
    created_at = Column(DateTime, default=datetime.datetime.utcnow, comment="缓存时间")


def get_db():
    """获取数据库会话的生成器函数"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """初始化数据库：创建所有表"""
    Base.metadata.create_all(bind=engine)
