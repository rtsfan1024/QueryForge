# QueryForge（表语通）

QueryForge（中文名：**表语通**）是一款面向数据库探索与查询分析的 Web 工具。它支持连接 PostgreSQL 数据库，自动采集 Schema（模式）元数据，执行只读 SQL 查询，并通过自然语言生成 SQL，帮助用户更高效地理解和检索数据库内容。

本项目采用前后端分离架构：

- 后端：FastAPI + SQLite + PostgreSQL + `sqlglot` + OpenAI 兼容 LLM
- 前端：React + TypeScript + Vite + Ant Design + Monaco Editor

***

## 目录

- [特性](#特性)
- [在线效果](#在线效果)
- [技术栈](#技术栈)
- [项目结构](#项目结构)
- [支持范围与说明](#支持范围与说明)
- [快速开始](#快速开始)
- [环境变量](#环境变量)
- [后端启动](#后端启动)
- [前端启动](#前端启动)
- [数据库连接与使用](#数据库连接与使用)
- [API 概览](#api-概览)
- [测试与验收](#测试与验收)
- [常见问题](#常见问题)
- [开发说明](#开发说明)
- [许可证](#许可证)

***

## 特性

- 支持保存数据库连接到 SQLite
- 自动抓取 PostgreSQL 的表、视图、列信息与基础关系信息
- 支持手写 SQL 查询
- 仅允许只读查询（`SELECT`）
- 未显式包含 `LIMIT` 时自动追加默认 `LIMIT 1000`，避免全量误查
- 支持自然语言生成 SQL
- 自然语言生成后会复用同一套只读校验与查询执行链路
- 前端提供数据库连接管理、Schema 浏览、SQL 编辑、结果展示
- 支持真实 PostgreSQL 集成测试

***

## 在线效果

- 数据库连接管理
- Schema 浏览
- SQL 编辑与执行
- 自然语言生成 SQL
- 查询结果表格展示

***

## 技术栈

### 后端

- Python 3.11+
- FastAPI
- SQLite
- PostgreSQL
- `psycopg[binary]`
- `sqlglot`
- OpenAI Python SDK（通过兼容接口调用）

### 前端

- React
- TypeScript
- Vite
- Ant Design
- Monaco Editor

***

## 项目结构

```text
w2/db_query/
├─ backend/                  # FastAPI 后端
│  ├─ src/
│  │  ├─ api/                # 路由层
│  │  ├─ llm/                # LLM 调用封装
│  │  ├─ models/             # 数据模型
│  │  ├─ repositories/       # SQLite / PostgreSQL 元数据访问
│  │  └─ services/           # SQL 执行与元数据服务
│  ├─ tests/                 # 单元测试与集成测试
│  ├─ pyproject.toml         # Python 依赖与测试配置
│  └─ pytest.ini             # pytest 标记配置
├─ frontend/                 # React 前端
│  ├─ src/
│  │  ├─ app.tsx             # 主页面
│  │  ├─ services/           # API 请求封装
│  │  └─ types.ts            # 前端类型
│  ├─ package.json
│  └─ vite.config.ts
├─ db_query.db               # SQLite 数据文件（运行后生成）
└─ README.md
```

***

## 支持范围与说明

### 当前已实现

- PostgreSQL 数据源连接
- PostgreSQL Schema 元数据采集
- 手写 SQL 查询执行
- 自然语言生成 SQL
- 只读 SQL 校验
- 默认 `LIMIT 1000`
- 前端查询与展示
- 集成测试

### 重要说明

当前项目**主目标是 PostgreSQL**。虽然代码里已经引入了 OpenAI 兼容 LLM 接口和 schema 上下文构建，但**自然语言生成 SQL 的最终准确性仍受目标数据库方言、schema 完整度和 LLM 输出质量影响**。

换言之：

- 对于 PostgreSQL：支持最好，当前是主要目标数据库
- 对于 MySQL / Oracle：目前**没有完整的方言适配和元数据适配**，不能保证自然语言转 SQL 一定正确

如果你计划后续扩展多数据库支持，建议继续增加：

- 数据库方言识别
- 目标方言 SQL 生成提示词
- 针对 MySQL / Oracle 的元数据读取适配
- 针对不同数据库的 SQL 校验与执行层适配

***

## 快速开始

### 1. 克隆项目

```powershell
git clone <your-repo-url>
cd <repo-root>/w2/db_query
```

### 2. 准备 PostgreSQL

确保本地或远程 PostgreSQL 可访问。

示例连接：

- Host: `localhost`
- Port: `5432`
- Database: `test` 或 `postgres`
- User: `postgres`
- Password: `postgres`

### 3. 配置环境变量

参见下方 [环境变量](#环境变量)。

### 4. 启动后端

参见 [后端启动](#后端启动)。

### 5. 启动前端

参见 [前端启动](#前端启动)。

***

## 环境变量

### 后端必需 / 推荐

- `OPENAI_BASE_URL`
  - OpenAI 兼容中转站地址
  - 当前推荐值：`https://api.vveai.com/v1`
- `OPENAI_API_KEY`
  - OpenAI 兼容接口密钥
- `OPENAI_MODEL`
  - LLM 模型名
  - 当前推荐值：`gpt-4o`
- `DB_QUERY_POSTGRES_PASSWORD`
  - PostgreSQL 默认密码
  - 如果数据库连接 URL 里没有带密码，后端会尝试使用它补全
- `POSTGRES_PASSWORD`
  - 与 `DB_QUERY_POSTGRES_PASSWORD` 兼容的备选项

### 真实集成测试使用

- `DB_QUERY_POSTGRES_DSN`
  - 真实 PostgreSQL 集成测试使用的连接串

示例（PowerShell）：

```powershell
$env:OPENAI_BASE_URL="https://api.vveai.com/v1"
$env:OPENAI_API_KEY="your_openai_compatible_key"
$env:OPENAI_MODEL="gpt-4o"
$env:DB_QUERY_POSTGRES_PASSWORD="postgres"
$env:DB_QUERY_POSTGRES_DSN="postgres://postgres:postgres@localhost:5432/postgres"
```

***

## 后端启动

进入后端目录：

```powershell
cd D:\Project\Cursor\w2\db_query\backend
```

安装依赖后启动：

```powershell
python -m uvicorn src.main:app --reload --port 8000
```

后端默认地址：

- `http://localhost:8000`

***

## 前端启动

进入前端目录：

```powershell
cd D:\Project\Cursor\w2\db_query\frontend
```

安装依赖：

```powershell
npm install
```

启动开发服务器：

```powershell
npm run dev
```

前端默认地址：

- `http://localhost:5173`

***

## 数据库连接与使用

### 1. 添加数据库连接

在前端中输入：

- 连接名：例如 `test`
- 数据库 URL：例如 `postgres://postgres@localhost:5432/test`
- 密码：例如 `postgres`

点击“添加数据库”。

### 2. 查看 Schema

添加成功后，系统会：

- 保存连接到 SQLite
- 连接 PostgreSQL
- 抓取表 / 视图 / 列 / 关系信息
- 在前端展示 Schema 列表

### 3. 执行手写 SQL

在 SQL 编辑器中输入，例如：

```sql
SELECT 1 AS value
```

点击“执行 SQL”。

### 4. 自然语言生成 SQL

输入自然语言，例如：

```text
查询 高一3班 所有学生信息
```

点击“生成 SQL”。

系统会：

1. 读取当前数据库的 Schema
2. 将结构化 Schema 上下文传给 LLM
3. 生成 SQL
4. 进行只读与字段校验
5. 执行 PostgreSQL 查询
6. 将结果展示在页面上

***

## API 概览

### 数据库连接

- `GET /api/v1/dbs`
  - 获取数据库连接列表
- `POST /api/v1/dbs/{name}`
  - 新增或更新数据库连接
- `GET /api/v1/dbs/{name}`
  - 获取数据库 Schema 详情

### SQL 查询

- `POST /api/v1/dbs/{name}/query`
  - 执行手写 SQL
- `POST /api/v1/dbs/{name}/query/natural`
  - 根据自然语言生成 SQL 并执行

***

## 测试与验收

### 1. 单元测试

```powershell
cd D:\Project\Cursor\w2\db_query\backend
pytest
```

### 2. PostgreSQL 真实集成测试

先设置环境变量：

```powershell
$env:DB_QUERY_POSTGRES_DSN="postgres://postgres:postgres@localhost:5432/postgres"
```

然后执行：

```powershell
cd D:\Project\Cursor\w2\db_query\backend
pytest -m integration
```

### 3. 验收建议

- 新增数据库连接成功
- Schema 元数据展示正确
- 手写 SQL 能返回正确结果
- 非 `SELECT` 语句被拒绝
- 自然语言生成 SQL 后能显示生成内容
- 自然语言生成结果能执行并返回结果

***

## 常见问题

### 1. 连接时报 `fe_sendauth: no password supplied`

原因通常是连接串里没有密码。

解决方式：

- 前端填写密码
- 或设置 `DB_QUERY_POSTGRES_PASSWORD`
- 或在连接串里直接写入密码，例如：

```text
postgres://postgres:postgres@localhost:5432/postgres
```

***

### 2. 自然语言生成 SQL 不准确

可能原因：

- Schema 元数据不完整
- 目标数据库方言没有完全适配
- LLM 返回了不符合预期的 SQL

建议：

- 先确认 PostgreSQL 元数据已刷新
- 确保 schema 中列名和关系信息完整
- 使用更明确的自然语言描述

***

### 3. 编辑器里看不到生成 SQL

请确认：

- 后端 `/query/natural` 请求成功返回
- 页面没有显示校验失败或执行失败
- 浏览器控制台和网络请求没有异常

***

## 开发说明

### 后端

后端实现了：

- SQLite 持久化
- PostgreSQL 元数据采集
- SQL 只读校验
- 默认 `LIMIT` 限制
- LLM 自然语言转 SQL
- 真实查询执行

### 前端

前端实现了：

- 数据库连接管理
- 当前数据库选择
- Schema 浏览
- SQL 编辑器
- 手写查询执行
- 自然语言输入与生成
- 查询结果表格展示

***

## 许可证

本项目采用 Apache-2.0

***

## 项目名说明

- 英文名：**QueryForge**
- 中文名：**表语通**

这两个名字适合用于 GitHub 仓库、README 标题、产品介绍和演示页面。
