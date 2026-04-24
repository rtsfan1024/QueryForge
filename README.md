# QueryForge（表语通）v2.0

QueryForge（中文名：**表语通**）是一款面向数据库探索与智能查询分析的 Web 工具。v2.0 版本在原有 PostgreSQL 的基础上，进行了基于 **SOLID 原则**的底层架构重构，全面支持 **MySQL** 数据源。

本项目通过分离元数据提取（Introspection）、SQL 方言处理（Dialect）与连接管理（Connection Factory），实现了高扩展的多数据源支持。系统支持自动采集 Schema 元数据，执行带安全拦截的只读 SQL 查询，并通过自然语言生成适配不同数据库方言的 SQL (NL2SQL)。

采用前后端分离架构：

- **后端**：FastAPI + SQLite + PostgreSQL / MySQL + 驱动 (`psycopg` / `pymysql`) + `sqlglot` + OpenAI 兼容 LLM
- **前端**：React + TypeScript + Vite + Ant Design + Monaco Editor

***

## **目录**

- [核心特性](https://www.google.com/search?q=%23核心特性)
- [架构演进说明](https://www.google.com/search?q=%23架构演进说明)
- [技术栈](https://www.google.com/search?q=%23技术栈)
- [项目结构](https://www.google.com/search?q=%23项目结构)
- [快速开始](https://www.google.com/search?q=%23快速开始)
- [环境变量](https://www.google.com/search?q=%23环境变量)
- [数据库连接与使用](https://www.google.com/search?q=%23数据库连接与使用)
- [API 概览](https://www.google.com/search?q=%23api-概览)
- [测试与验收](https://www.google.com/search?q=%23测试与验收)
- [常见问题](https://www.google.com/search?q=%23常见问题)
- [开发者指南（扩展新数据库）](https://www.google.com/search?q=%23开发者指南扩展新数据库)

***

## **核心特性**

- **多数据源支持**：无缝连接 PostgreSQL 与 MySQL 数据库。
- **智能 Schema 内省 (Introspection)**：自动采集不同数据库的表、视图、列信息与基础关联关系。
- **方言自适应只读保护**：底层集成 SQL 语法树（Abstract Syntax Tree）解析，针对不同数据源严格限制仅允许 `SELECT` 操作，并自动追加对应方言的 `LIMIT 1000` 防护。
- **NL2SQL（自然语言转 SQL）**：基于目标数据库的 Schema 上下文与特定的方言 Prompt，智能生成准确的 SQL 语句。
- **连接状态持久化**：支持将异构数据库的连接配置统一保存至 SQLite，方便跨会话管理。

***

## **架构演进说明**

v2.0 版本严格践行了面向对象设计原则，为未来的横向扩展（如接入 SQLite, Oracle, ClickHouse）铺平了道路：

| **设计原则**       | **落地实践**                                                                    |
| :------------- | :-------------------------------------------------------------------------- |
| **开闭原则 (OCP)** | 引入 `IDatabaseIntrospector` / `ISQLDialect` 接口。新增数据库类型无需修改核心查询与校验逻辑。         |
| **单一职责 (SRP)** | 每种数据库的方言解析（如 `MySQLDialect`）、元数据抓取（`MySQLIntrospection`）与连接管理独立成类。          |
| **依赖倒置 (DIP)** | 核心业务服务（如 `SQLService`, `MetadataService`）仅依赖抽象接口，具体实现由工厂类（Factory）在运行时动态注入。 |

***

## **技术栈**

### **后端**

- Python 3.11+
- Web 框架：FastAPI
- 关系型持久化：SQLite (存储配置)
- 数据库驱动：`psycopg[binary]` (PostgreSQL), `pymysql` 或 `mysql-connector-python` (MySQL)
- SQL 语法解析：`sqlglot`
- LLM 交互：OpenAI Python SDK

### **前端**

- 核心框架：React + TypeScript + Vite
- UI 组件库：Ant Design
- 代码编辑器：Monaco Editor

***

## **项目结构**

Plaintext

```
~/
├─ backend/                  # FastAPI 后端
│  ├─ src/
│  │  ├─ api/                # 路由层 (dbs.py 等)
│  │  ├─ llm/                # LLM 客户端与方言特定的 Prompt 管理
│  │  ├─ models/             # 数据模型 (DatabaseType 枚举等)
│  │  ├─ repositories/       # 数据层抽象
│  │  │  ├─ introspector_interface.py    # 内省器抽象接口
│  │  │  ├─ postgres_introspection.py    # PG 内省实现
│  │  │  ├─ mysql_introspection.py       # MySQL 内省实现
│  │  │  └─ connection_factory.py        # 数据库连接工厂
│  │  └─ services/           # 核心服务逻辑
│  │     ├─ sql_dialect_interface.py     # SQL 方言抽象接口
│  │     ├─ postgres_dialect.py          # PG 方言处理器
│  │     ├─ mysql_dialect.py             # MySQL 方言处理器
│  │     └─ sql_service.py               # SQL 校验与执行服务
│  ├─ tests/                 # 单元测试与真实数据库集成测试
│  └─ pyproject.toml         # 依赖配置
├─ frontend/                 # React 前端
│  ├─ src/
│  │  ├─ components/         # DatabaseTypeLabel 等公共组件
│  │  ├─ pages/              # 包含多数据库类型选择的交互界面
│  │  └─ services/           # API 请求层
└─ README.md
```

***

## **快速开始**

### **1. 克隆项目与准备工作**

Bash

```
git clone <your-repo-url>
cd <repo-root>
```

确保本地或远程有可访问的 PostgreSQL 或 MySQL 实例。

### **2. 环境配置**

设置必要的 LLM API 密钥和数据库默认密码（参见 [环境变量](https://www.google.com/search?q=%23环境变量) 章节）。

### **3. 启动后端**

Bash

```
cd backend
pip install -r requirements.txt  # 或 poetry/pdm install
python -m uvicorn src.main:app --reload --port 8000
```

### **4. 启动前端**

Bash

```
cd frontend
npm install
npm run dev
```

访问 `http://localhost:5173` 开始使用。

***

## **环境变量**

### **后端必需 / 推荐**

- `OPENAI_BASE_URL`: OpenAI 兼容中转站地址（例：`https://api.vveai.com/v1`）
- `OPENAI_API_KEY`: 接口密钥
- `OPENAI_MODEL`: LLM 模型名（推荐：`gpt-4o`）
- `DB_QUERY_POSTGRES_PASSWORD` / `DB_QUERY_MYSQL_PASSWORD`: 默认的回退数据库密码。

### **集成测试专用**

- `DB_QUERY_POSTGRES_DSN`: `postgres://postgres:postgres@localhost:5432/postgres`
- `DB_QUERY_MYSQL_DSN`: `mysql://root:password@localhost:3306/tests`

***

## **数据库连接与使用**

在前端界面的**添加数据库**表单中，首先**选择数据库类型 (dbType)**，然后填入对应的连接信息：

### **PostgreSQL 示例**

- **类型**: PostgreSQL
- **连接名**: pg\_dev
- **连接 URL**: `postgres://postgres@localhost:5432/test`
- **密码**: (若 URL 中未带密码，需在此填写)

### **MySQL 示例**

- **类型**: MySQL
- **连接名**: mysql\_prod
- **连接 URL**: `mysql://root@localhost:3306/tests`
- **密码**: (若 URL 中未带密码，需在此填写)

### **操作流转**

1. **Schema 获取**：保存后系统自动通过 Factory 路由到对应的 Introspector 获取元数据。
2. **手写/AI 生成 SQL**：在执行面板输入 SQL 或自然语言（如：“查询近7天注册的用户数”）。
3. **安全执行**：系统将通过 `ISQLDialect` 进行方言特定的 AST 校验，确保无破坏性操作，追加 `LIMIT` 后执行并渲染数据表。

***

## **API 概览**

- `GET /api/v1/dbs` : 获取所有保存的连接列表（包含 `dbType` 标识）。
- `POST /api/v1/dbs/{name}` : 新增/更新连接配置并触发初次 Schema 抓取。
- `GET /api/v1/dbs/{name}` : 获取目标库的完整 Schema。
- `POST /api/v1/dbs/{name}/query` : 安全执行手写 SQL。
- `POST /api/v1/dbs/{name}/query/natural` : 提交自然语言，生成目标数据库方言的 SQL 并执行。

***

## **常见问题**

**1. 连接 MySQL 失败，提示驱动未找到？**

确保后端环境中安装了 `pymysql` 或 `mysql-connector-python`。在虚拟环境中执行 `pip install pymysql`。

**2. 生成的 SQL 在 MySQL 下报错？**

不同 LLM 对方言的理解存在差异。如果模型在 MySQL 模式下输出了 PostgreSQL 特有的语法（如 `ILIKE` 或 `CURRENT_DATE` 类型转换），请检查 `src/llm/client.py` 中针对 MySQL 的专用 System Prompt 是否被正确加载。

**3. “no password supplied” 或 “Access denied”**

请确保连接 URL 格式标准（包含凭证）或在前端面板显式提供了密码字段。

***

## **开发者指南（扩展新数据库）**

基于 v2.0 确立的 SOLID 架构，若需扩展支持新数据库（例如 SQLite 或 SQL Server），只需执行以下 5 步，**完全无需修改现有核心业务代码**：

1. 在 `DatabaseType` 枚举中新增类型。
2. 实现 `IDatabaseIntrospector` 接口，编写该库的 Schema 查询逻辑。
3. 实现 `ISQLDialect` 接口，定义该库的 SQL AST 解析与 `LIMIT` 注入规则。
4. 实现 `IDatabaseConnectionFactory` 接口，管理特定驱动的连接。
5. 在 `IntrospectorFactory` 与 `SQLDialectFactory` 的注册表中挂载新实现。

***

*License: Apache-2.0*
