# 更新日志

## v2.0.1（2026-06-06）

### 🛠 修复：停止任务按钮无响应问题

#### 问题描述

点击发现页面的「停止任务」按钮时，页面没有任何视觉反馈，且任务不会立即停止。用户会误以为按钮失效。

#### 原因分析

1. **前端缺少视觉反馈**—— `stopSearchTask()` 只是默默发了 POST 请求，没有在界面上显示任何"停止信号已发送"的提示，用户感觉按钮"没反应"。
2. **后端停止检查点不足**—— 停止信号 `_global_stop_flag` 只在 `run_search_task()` 的以下两个位置被检查：
   - 处理每个**扩展关键词**之前
   - 处理每个**搜索结果**之前

   而每个搜索结果（公司）的完整分析流程 `_auto_analyze_and_save()` 内部——包含官网抓取、邮箱提取、关键词分析、**DeepSeek AI 分析**（最耗时，通常 30-60 秒）——完全没有检查停止标志，导致用户点击停止后仍需等待当前公司的 AI 分析完成才能生效。

#### 修改内容

##### 前端 — `app/templates/discovery.html`

- `stopSearchTask()` 函数增加实时反馈：
  - 点击后按钮立即置灰并显示「⏳ 正在停止...」加载动画
  - 状态栏文字立即更新为「正在停止」
  - 3 秒后自动刷新任务状态，以便前端及时反映后端处理结果
  - 请求失败时弹出错误提示

##### 后端 — `app/services/search_task_service.py`

在 `_auto_analyze_and_save()` 内部新增**两处停止信号检查**：

1. **官网爬取完成后、邮箱提取前**（第 265-270 行）
   - 场景：爬取完成但 AI 分析还未开始
   - 行为：保存已爬取的内容，标记公司为已分析，安全返回

2. **DeepSeek AI 分析调用前**（第 288-293 行）
   - 场景：即将进入最耗时的 AI 分析步骤
   - 行为：跳过 AI 分析，直接保存当前已有数据（邮箱、关键词等），标记公司为已分析，安全返回

同时优化了 `run_search_task()` 的主循环：
- 在每次处理新关键词时重置任务状态为 `Running`，避免状态同步问题

#### 预期效果

- 点击「停止任务」后页面立即显示停止状态反馈
- 任务在 2-3 秒内（而非 30-60 秒）停止响应
- 已抓取但未完成 AI 分析的公司数据不会丢失，会以部分分析状态保存到数据库
- 停止后可通过「恢复」按钮继续未完成的搜索任务（断点续跑）

#### 涉及文件

| 文件 | 修改类型 |
|------|----------|
| `app/templates/discovery.html` | 前端交互优化 |
| `app/services/search_task_service.py` | 后端停止逻辑增强 |

---

---

## v2.2.0（2026-06-12）

### 新增：多语言搜索支持

#### 问题描述

搜索非英语国家（如 Poland、Spain）时，即使输入英文关键词+国家名，Google 搜索结果仍然以美国/英语公司为主。根本原因是：关键词是英文的，搜索参数（hl/lr/cr）也未限制到目标国家语言，导致 Google 优先返回英语世界的结果。

例如：搜索 "Poland" + "wastewater treatment" → 结果全是美国公司。

#### 修改方案

改造整个搜索链路，使系统能根据目标国家自动使用本地语言进行搜索：

1. **创建国家→语言映射表** — 覆盖 60+ 国家，精确映射每个国家的搜索语言和 Google 参数
2. **AI 关键词扩展增加多语言支持** — 输入英文关键词，AI 一次性完成翻译+扩展，生成目标国家语言的关键词列表
3. **SerpAPI 搜索增加国家/语言限制** — 设置 hl（界面语言）、lr（语言限制）、cr（国家限制）三个参数

#### 改造后的工作流

```
输入: 国家="Poland", 关键词="wastewater treatment"
  ↓
AI 翻译+扩展为波兰语关键词（一次API调用）:
["oczyszczalnia ścieków", "przetwarzanie ścieków", ...]
  ↓
SerpAPI 搜索:
hl=pl, lr=lang_pl, cr=countryPL, gl=pl
  ↓
结果: 波兰本地企业
```

#### 新增文件

| 文件 | 说明 |
|------|------|
| `app/services/country_language_map.py` | 国家→语言映射表（60+国家，含西班牙语、波兰语、阿拉伯语、法语、德语、俄语、日语等） |

#### 修改文件

| 文件 | 修改内容 |
|------|----------|
| `app/services/keyword_expander.py` | `expand_keywords()` 新增 `country` 参数，非英语国家自动使用本地语言扩展 |
| `app/services/google_discovery.py` | 移除旧的 `_get_country_code()` 映射表，改用 `country_language_map`；`_fetch_via_serpapi()` 新增 hl/lr/cr 多语言参数 |
| `app/services/search_task_service.py` | 调用 `expand_keywords` 时传入 `country` |
| `app/api/routes.py` | 预览关键词 API 新增 `country` 参数 |
| `app/templates/discovery.html` | 预览关键词时传入 country，结果显示语言提示 |

#### 支持的语言及对应国家

| 语言 | 覆盖国家 |
|------|----------|
| 西班牙语 | Spain、Mexico、Argentina、Chile、Colombia 等 20 个西语国家 |
| 波兰语 | Poland |
| 阿拉伯语 | Saudi Arabia、UAE、Qatar、Kuwait、Egypt 等 18 个阿拉伯国家 |
| 法语 | France、Belgium、Morocco、Algeria、Tunisia 等 |
| 德语 | Germany、Austria |
| 意大利语 | Italy |
| 葡萄牙语 | Portugal、Brazil、Angola、Mozambique |
| 俄语 | Russia、Kazakhstan、Belarus 等 |
| 日语 | Japan |
| 韩语 | South Korea |
| 土耳其语 | Turkey |
| 泰语 | Thailand |
| 越南语 | Vietnam |
| 中文 | China、Taiwan、Hong Kong |
| 英语（增加国家限制） | UK、Australia、Canada、India、Singapore 等（保持英文但限制国家，不再搜到美国公司） |

---

## v2.2.1（2026-06-12）

### 新增：客户跟进状态管理 & 抓取失败可视化 & 局部重试

基于 V2.2 产品改进文档的两个高优先级方向，实现了 MVP 版本。

---

#### 方向① 客户跟进状态管理

**问题描述：** 系统只能「发现」和「分析」客户，但业务员无处记录跟进进度（如已发邮件、已回复、无效线索等），用完就关，没有复访动机。

**改进目标：** 让系统从「一次性分析工具」升级为「持续使用的客户管理平台」。

**数据层 — `app/database.py`**

Customer 模型新增三个字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `status` | String(20) | 跟进状态枚举：待联系（默认）/ 已发邮件 / 已回复 / 无效线索 / 成单 |
| `follow_up_date` | Date | 下次跟进日期 |
| `notes` | Text | 跟进备注文本 |

**后端 API — `app/api/routes.py`**

- `list_customers` 新增 `status` 查询参数，支持按跟进状态筛选
- 列表接口和详情接口均返回 `status` / `follow_up_date` / `notes` 字段
- 新增 `POST /api/customers/{id}/follow-up` 接口：更新跟进状态、日期、备注

**前端 — `app/templates/index.html`（客户列表页）**

- 表头新增「状态」列，每行显示带色块的状态标签（待联系=灰色 / 已发邮件=蓝色 / 已回复=绿色 / 无效线索=黑色 / 成单=黄色）
- 筛选栏新增「所有状态」下拉框，支持按状态筛选

**前端 — `app/templates/detail.html`（客户详情页）**

- 新增「跟进记录」卡片区，包含：跟进状态下拉 + 下次跟进日期输入 + 备注输入框 + 保存按钮
- 保存成功后显示绿色提示「已保存」，2秒后自动消失

---

#### 方向② 抓取失败可视化 & 局部重试

**问题描述：** 分析链路（搜索→抓取→AI分析→评分）较长，每一步都可能失败，但用户看到的结果都是「空数据」——分不清到底是真的没有数据，还是中途出错。

**改进目标：** 让数据状态对用户透明，支持局部重试，不需要重跑整个任务。

**数据层 — `app/database.py`**

Customer 模型新增三个字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `scrape_status` | String(20) | 官网抓取状态：success / failed / partial / skipped |
| `ai_status` | String(20) | AI分析状态：success / failed / skipped |
| `fail_reason` | String(500) | 失败原因描述（如超时、反爬、API错误等） |

**后端分析流程写入状态 — `app/services/search_task_service.py`**

`_auto_analyze_and_save()` 中：
- 官网缓存命中 → `scrape_status=success`
- 官网抓取成功 → `scrape_status=success`
- 官网抓取失败 → `scrape_status=failed` + `fail_reason="官网抓取失败（网站可能无法访问或反爬）"`，标记已分析后安全返回
- AI分析成功 → `ai_status=success`
- AI分析失败 → `ai_status=failed` + `fail_reason="AI分析失败（API可能超时）"`

**后端 API — `app/api/routes.py`**

- `analyze_single` 分析过程中写入 `scrape_status` / `ai_status` / `fail_reason`
- 列表和详情接口返回上述状态字段
- 新增 `POST /api/customers/{id}/re-scrape`：重新抓取官网 + 重跑邮箱提取/关键词分析/评分，保留已有AI结果
- 新增 `POST /api/customers/{id}/re-analyze`：仅重新调用DeepSeek AI分析 + 重算评分，不重新抓取

**前端 — `app/templates/index.html`（客户列表页）**

- 来源列后方显示抓取状态图标（✅成功 / ❌失败 / ⚠️部分）+ AI状态图标（🧠成功 / 💀失败 / ⏭️跳过）
- 操作按钮组新增「重新抓取」和「重新AI分析」两个独立按钮（分别调用不同API）
- 鼠标悬停在状态图标上时通过 `title` 属性显示失败原因

**前端 — `app/templates/detail.html`（客户详情页）**

- 操作栏增加「重新抓取」「重新AI分析」按钮
- 基本信息区在发现来源标签旁显示状态图标（抓取成功/失败、分析成功/失败）

---

#### 涉及文件

| 文件 | 修改类型 |
|------|----------|
| `app/database.py` | Customer 模型新增 6 个字段（status/follow_up_date/notes/scrape_status/ai_status/fail_reason） |
| `app/api/routes.py` | 新增 3 个接口（跟进更新/重新抓取/重新分析），列表/详情接口新增状态字段返回，支持 status 筛选 |
| `app/services/search_task_service.py` | `_auto_analyze_and_save` 中写入 scrape_status/ai_status/fail_reason |
| `app/templates/index.html` | 新增状态列+状态筛选+状态图标+重新抓取/重新分析按钮 |
| `app/templates/detail.html` | 新增跟进记录区+状态图标+重新抓取/重新分析按钮 |

---

### 历史版本

- **v2.0.1** —— 修复：停止任务按钮无响应问题
- **v2.0.0** —— 初始版本：客户发现 + 客户分析 + 客户数据库平台
