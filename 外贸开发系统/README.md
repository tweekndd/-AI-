# AI Trade Customer Analyzer V2.0

**外贸客户AI分析系统** — 客户发现 + 客户分析 + 客户数据库平台

自动从 Google 发现潜在客户 → AI 分析客户官网 → 规则引擎评分 → 生成开发切入点，一站式完成。

---

## 功能概览

| 功能 | 说明 |
|------|------|
| **客户发现** | 输入国家 + 关键词 → AI扩展关键词 → SerpAPI搜索Google → 自动过滤企业官网 |
| **Excel导入** | 上传含 Company Name / Website / Country 三列的 Excel 文件 |
| **官网抓取** | 异步并发抓取 /about /services /projects 等页面，提取纯文本 |
| **邮箱提取** | 自动提取 info / sales / contact / procurement / project / marketing 前缀邮箱 |
| **关键词分析** | 14个正向 + 7个负向行业关键词命中统计 |
| **DeepSeek AI分析** | 识别公司类型、分析原因、生成开发切入点和推荐联系职位 |
| **规则评分引擎** | 5个维度评分：行业匹配度(30) + 项目匹配度(25) + 公司类型(20) + 国家优先级(15) + 联系方式(10) |
| **三级缓存** | 搜索缓存(30天) + 官网缓存(7天) + AI分析缓存(内容哈希) — 避免重复消耗 API 配额 |
| **断点续跑** | 搜索任务意外中断后，重新启动自动从断点继续 |
| **批量分析** | 一键分析所有未分析客户 |
| **导出Excel** | 导出完整分析报告 |
| **停止分析** | 随时点击停止按钮中止分析任务 |

---

## 快速开始

### 1. 环境要求

- Python 3.10+
- Windows / macOS / Linux

### 2. 安装依赖

```bash
cd AI-Trade-Customer-Analyzer
pip install -r requirements.txt
```

### 3. 获取 API Key

#### DeepSeek API（必填，用于 AI 分析和关键词扩展）
- 前往 https://platform.deepseek.com/ 注册获取 API Key
- 模型默认使用 `deepseek-v4-flash`

#### SerpAPI（搜索发现功能必填）
- 前往 https://serpapi.com/ 注册获取 API Key
- 免费账户每月 250 次搜索查询

### 4. 启动系统

**Windows (CMD):**
```cmd
set DEEPSEEK_API_KEY=sk-your-deepseek-api-key
set SERPAPI_API_KEY=your-serpapi-api-key
python main.py
```

**macOS / Linux:**
```bash
export DEEPSEEK_API_KEY=sk-your-deepseek-api-key
export SERPAPI_API_KEY=your-serpapi-api-key
python main.py
```

**PowerShell:**
```powershell
$env:DEEPSEEK_API_KEY="sk-your-deepseek-api-key"
$env:SERPAPI_API_KEY="your-serpapi-api-key"
python main.py
```

**可选环境变量：**

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `DEEPSEEK_API_URL` | `https://api.deepseek.com/v1/chat/completions` | 自定义 API 地址 |
| `DEEPSEEK_MODEL` | `deepseek-v4-flash` | 自定义模型名称 |
| `SERPAPI_API_KEY` | — | SerpAPI 密钥（搜索发现必需） |

### 5. 打开浏览器

访问 **http://localhost:8000**

---

## 使用教程

### 方式一：手动导入客户名单

1. 点击 **导入Excel**，上传 `.xlsx` 文件（表头含 Company Name / Website / Country）
2. 在列表中点击 ⚡ 按钮分析单个客户，或点击 **批量分析** 分析所有客户
3. 等待分析完成后，查看评分和优先级

### 方式二：Google 搜索发现新客户

1. 点击导航栏 **客户发现** 进入发现页面
2. 填写：
   - **Country**：目标国家（如 Saudi Arabia）
   - **Keyword**：行业关键词（如 wastewater contractor）
   - **Search Depth**：搜索深度（每个关键词获取的结果数，建议 30-50）
3. 点击 **Start Search**
4. 系统自动完成：AI扩展关键词 → 搜索Google → 过滤官网 → 去重 → 官网抓取 → AI分析 → 规则评分 → 保存入库
5. 在 **客户列表** 页查看结果

### 查看详情

点击任意客户名称进入详情页，查看：
- **评分明细**：各维度得分及进度条
- **提取邮箱**：所有发现的邮箱地址
- **关键词分析**：正向/负向关键词命中情况
- **AI分析结果**：公司类型、分析原因
- **开发建议**：开发切入点、推荐联系职位
- **识别项目**：AI 从官网提取的项目信息
- **官网原文**：抓取的纯文本内容

---

## 项目结构

```
AI-Trade-Customer-Analyzer/
├── main.py                          # FastAPI 主入口
├── requirements.txt                 # 依赖清单
├── app/
│   ├── database.py                  # 数据库模型（6张表）
│   ├── database_init.py             # 数据库初始化
│   ├── api/
│   │   └── routes.py                # 全部 API 路由
│   ├── services/
│   │   ├── excel_importer.py        # Excel 导入
│   │   ├── website_scraper.py       # 官网抓取（异步）
│   │   ├── email_extractor.py       # 邮箱提取
│   │   ├── keyword_analyzer.py      # 关键词分析
│   │   ├── keyword_expander.py      # AI 关键词扩展
│   │   ├── deepseek_analyzer.py     # DeepSeek AI 分析
│   │   ├── scoring_engine.py        # 规则评分引擎
│   │   ├── google_discovery.py      # SerpAPI Google 搜索
│   │   ├── search_task_service.py   # 搜索任务管理 + 断点续跑
│   │   ├── cache_manager.py         # 三级缓存管理
│   │   ├── url_normalizer.py        # 网址标准化
│   │   ├── company_filter.py        # 结果过滤
│   │   ├── retry_manager.py         # 失败重试
│   │   ├── industry_config.json     # 行业配置中心
│   │   └── country_weights.json     # 国家权重配置
│   ├── static/css/
│   │   └── style.css
│   └── templates/
│       ├── index.html               # 客户列表页
│       ├── detail.html              # 客户详情页
│       └── discovery.html           # 客户发现页
```

---

## 数据库表

| 表名 | 说明 |
|------|------|
| `customers` | 客户数据（含评分、AI分析、发现来源） |
| `search_tasks` | 搜索任务（支持断点续跑） |
| `search_cache` | 搜索结果缓存（30天有效） |
| `website_cache` | 官网抓取缓存（7天有效） |
| `analysis_cache` | AI 分析缓存（内容哈希比对） |

---

## 评分系统说明

系统采用 **规则评分引擎**，AI 仅负责信息提取，评分完全由程序计算：

| 维度 | 满分 | 说明 |
|------|------|------|
| 行业匹配度 | 30 | 官网命中行业关键词的数量和权重 |
| 项目匹配度 | 25 | 是否有项目案例页面、是否涉及水处理 |
| 公司类型 | 20 | EPC=20, Contractor=18, 水处理公司=18... |
| 国家优先级 | 15 | 从 `country_weights.json` 读取（可配置） |
| 联系方式 | 10 | 1个邮箱=3分, 2个=5分, 3个=8分, 4个+=10分 |

优先级：A(80-100) / B(60-79) / C(40-59) / D(0-39)

评分规则可通过修改 `app/services/industry_config.json` 和 `app/services/country_weights.json` 调整，无需修改代码。

---

## 技术栈

- **后端**：FastAPI + SQLAlchemy + SQLite
- **前端**：Bootstrap 5 + JavaScript
- **AI**：DeepSeek API
- **搜索**：SerpAPI (Google Search API)
- **爬虫**：httpx + BeautifulSoup（异步并发）
