# 医药知识图谱系统 - Neo4j可视化部署指南

## 目录
1. [环境要求](#环境要求)
2. [快速开始（SQLite版）](#快速开始sqlite版)
3. [完整部署（Neo4j版）](#完整部署neo4j版)
4. [前端可视化使用](#前端可视化使用)
5. [常见问题](#常见问题)

---

## 环境要求

- **操作系统**：Windows 10/11 或 macOS 或 Linux
- **Python**：3.9 或更高版本
- **内存**：建议 4GB 以上（Neo4j 需要）

---

## 快速开始（SQLite版）

如果你只需要使用知识图谱查询功能，不需要安装Neo4j：

### 步骤1：安装Python依赖

```bash
cd medical-system
pip install -r requirements.txt
```

### 步骤2：启动服务

```bash
python main.py
```

服务启动后访问：
- API文档：http://localhost:8000/docs
- 知识图谱可视化：http://localhost:8000/graph/graph-browser.html

> ⚠️ 注意：SQLite版直接使用`db/graph.db`文件，无需额外配置。

---

## 完整部署（Neo4j版）

### 第一部分：安装Neo4j

#### Windows系统

**方法1：通过Chocolatey安装（推荐）**
```powershell
# 安装Chocolatey（如果没有）
Set-ExecutionPolicy Bypass -Scope Process -Force
iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))

# 安装Neo4j
choco install neo4j -y
```

**方法2：手动下载安装**

1. 访问 https://neo4j.com/download-center/#community 下载Neo4j Community Edition
2. 选择Windows版本（.zip或.msi）
3. 解压到 `C:\neo4j` 或其他目录

**方法3：使用Neo4j Desktop**

1. 下载Neo4j Desktop：https://neo4j.com/download-center/#desktop
2. 安装后创建一个新的数据库
3. 记住连接地址（默认 `bolt://localhost:7687`）

#### macOS系统

```bash
# 使用Homebrew安装
brew install neo4j

# 启动Neo4j服务
brew services start neo4j
```

#### Linux系统

```bash
# 添加Neo4j仓库
wget -O - https://debian.neo4j.com/neotechnology.gpg.key | sudo apt-key add -
echo 'deb https://debian.neo4j.com stable latest' | sudo tee /etc/apt/sources.list.d/neo4j.list
sudo apt-get update
sudo apt-get install neo4j

# 启动Neo4j
neo4j start
```

### 第二部分：配置Neo4j

#### 1. 设置Neo4j密码

启动Neo4j后，访问 Neo4j Browser：http://localhost:7474

首次登录：
- 用户名：`neo4j`
- 密码：`neo4j`（首次会要求修改）

#### 2. 修改配置文件

编辑 `neo4j.conf`（位于Neo4j安装目录的conf文件夹）：

```properties
# 如果需要远程访问，取消下面这行的注释
# dbms.connector.http.address=0.0.0.0:7474
# dbms.connector.bolt.address=0.0.0.0:7687

# 设置初始密码（如果通过命令行）
dbms.security.auth_enabled=true
```

### 第三部分：导入数据

#### 1. 修改项目配置

编辑项目中的 `.env` 文件：

```env
# 切换到Neo4j后端
GRAPH_BACKEND=neo4j

# Neo4j连接配置（根据你的实际配置修改）
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=你的新密码
NEO4J_DATABASE=neo4j
```

#### 2. 执行数据导入

```bash
cd medical-system
python import_neo4j.py
```

导入过程大约需要5-10分钟，会显示进度：
```
======================================================================
Neo4j知识图谱数据导入
======================================================================
[连接] Neo4j数据库: bolt://localhost:7687
[验证] 数据库连接成功
[索引] 创建索引...
[创建] Disease节点: 8800个
[创建] Symptom节点: 9800个
...
[进度] 已创建 100000 条关系...
[完成] 共创建 459387 条关系
```

### 第四部分：启动后端服务

```bash
# 确保Neo4j正在运行
# Windows: 在服务中启动Neo4j服务
# macOS/Linux: brew services start neo4j 或 neo4j start

# 启动FastAPI服务
python main.py
```

服务启动后：
- API文档：http://localhost:8000/docs
- 知识图谱可视化：http://localhost:8000/graph/graph-browser.html
- Neo4j Browser：http://localhost:7474

---

## 前端可视化使用

### 访问可视化页面

打开浏览器访问：`http://localhost:8000/graph/graph-browser.html`

### 功能说明

| 功能 | 操作 |
|------|------|
| **查询疾病图谱** | 在左侧输入疾病名称，点击"搜索" |
| **调整深度** | 拖动"深度"滑块（1-5层） |
| **查看节点详情** | 点击图谱中的任意节点 |
| **搜索实体** | 使用下方的搜索框搜索症状、药品等 |
| **快捷查询** | 点击右侧的"感冒"、"糖尿病"等标签 |

### 界面说明

```
┌─────────────────────────────────────────────────────────────┐
│  医药知识图谱系统                           ● 已连接 NEO4J  │
├─────────────┬───────────────────────────────────────────────┤
│  图谱查询    │                                               │
│  [疾病名称] [搜索]  │                                           │
│  深度 ──●── 2      │           ┌───┐                        │
│             │           ┌───┐  │感冒│  ┌───┐                │
│  数据库统计  │          │头痛│──│    │──│咳嗽│                │
│  节点: 44650│           └───┘  └─┬─┘  └───┘                │
│  关系: 459387│                     │                         │
│             │                ┌────┴────┐                    │
│  节点图例    │               │  病毒性感冒│                   │
│  ● 疾病     │                └─────────┘                    │
│  ● 症状     │                                               │
│  ● 药品     │                                               │
│             │                                               │
│  快捷查询    │                                               │
│  [感冒][糖尿病]│                                            │
└─────────────┴───────────────────────────────────────────────┘
```

---

## API接口参考

### 知识图谱接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/v1/common/knowledge-graph/disease-graph` | GET | 获取疾病知识图谱 |
| `/api/v1/common/knowledge-graph/entities/search` | GET | 搜索实体 |
| `/api/v1/common/knowledge-graph/entities/{id}` | GET | 获取实体详情 |
| `/api/v1/common/knowledge-graph/statistics` | GET | 获取统计信息 |
| `/api/v1/common/knowledge-graph/labels` | GET | 获取所有标签类型 |
| `/api/v1/common/knowledge-graph/db-status` | GET | 数据库连接状态 |

### 大模型接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/v1/llm/query` | POST | 大模型问答 |
| `/api/v1/llm/graph-analysis` | POST | 知识图谱分析 |
| `/api/v1/llm/symptom-diagnosis` | GET | 症状诊断 |
| `/api/v1/llm/drug-recommendation` | GET | 药物推荐 |

### 示例请求

```bash
# 查询感冒的知识图谱
curl "http://localhost:8000/api/v1/common/knowledge-graph/disease-graph?disease_name=感冒&max_depth=2"

# 搜索相关实体
curl "http://localhost:8000/api/v1/common/knowledge-graph/entities/search?keyword=发烧&entity_type=symptom"

# 获取数据库状态
curl "http://localhost:8000/api/v1/common/knowledge-graph/db-status"
```

---

## 常见问题

### Q1: Neo4j启动失败，提示端口被占用

```powershell
# 检查端口占用
netstat -ano | findstr 7687
netstat -ano | findstr 7474

# 停止占用端口的进程
taskkill /PID <进程ID> /F
```

### Q2: Neo4j连接被拒绝

1. 确认Neo4j服务正在运行
2. 检查`.env`中的连接信息是否正确
3. 确认`neo4j.conf`中的连接器已启用

### Q3: 数据导入失败

1. 确保Neo4j正在运行
2. 检查`.env`中的密码是否正确
3. 查看`neo4j_import.log`日志文件

### Q4: 浏览器无法访问可视化页面

1. 确认服务正在运行
2. 访问 `http://localhost:8000/docs` 检查API是否正常
3. 检查是否有防火墙阻止

### Q5: 图谱显示为空

1. 检查数据库是否已导入数据
2. 确认`GRAPH_BACKEND`配置正确
3. 访问`/db-status`接口检查连接状态

---

## 项目文件结构

```
medical-system/
├── app/
│   ├── routes/
│   │   ├── knowledge_graph.py   # 知识图谱API
│   │   └── llm.py               # 大模型接口
│   ├── graph_db.py              # 图数据库抽象层
│   └── schemas.py                # 数据模型
├── data/
│   └── output/                   # 知识图谱数据
│       ├── ID映射/entity_id_map.json
│       └── 核心数据/triplets_with_id.csv
├── db/
│   └── graph.db                  # SQLite图数据库
├── static/
│   └── graph-browser.html        # 可视化页面
├── import_neo4j.py               # Neo4j导入脚本
├── main.py                      # FastAPI入口
├── requirements.txt             # Python依赖
└── .env                         # 配置文件
```

---

## 技术支持

如有问题，请检查：
1. Neo4j Browser是否正常访问
2. FastAPI服务日志输出
3. `neo4j_import.log` 导入日志
