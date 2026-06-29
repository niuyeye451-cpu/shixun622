# Neo4j知识图谱导入指南

## 一、环境准备

### 1.1 安装Neo4j

**Windows安装步骤：**

1. 下载Neo4j Desktop: https://neo4j.com/download/
2. 安装并启动Neo4j Desktop
3. 创建新项目，添加本地数据库
4. 启动数据库（默认端口：7687）

**或使用Neo4j Community Edition：**

```powershell
# 下载并解压Neo4j Community Edition
# 进入bin目录
neo4j.bat console
```

### 1.2 安装Python驱动

```powershell
pip install neo4j
```

---

## 二、导入脚本说明

### 2.1 脚本位置

```
output/neo4j_import.py
```

### 2.2 功能清单

| 步骤 | 功能 | 数据来源 | 数量 |
|------|------|----------|------|
| 步骤1 | 创建节点 | entity_id_map.json | 44,650个 |
| 步骤2 | 创建关系 | triplets_with_id.csv | 459,387条 |
| 步骤3 | 添加属性 | medical_clean.json | 8,807个疾病 |

### 2.3 配置修改

**修改Neo4j连接配置（neo4j_import.py 第20-24行）：**

```python
NEO4J_CONFIG = {
    "uri": "bolt://localhost:7687",  # 连接地址
    "user": "neo4j",                  # 用户名
    "password": "123456"              # 密码（请改为你的密码）
}
```

---

## 三、执行导入

### 3.1 启动Neo4j

确保Neo4j已启动并可访问：

```powershell
# 在浏览器访问
http://localhost:7474

# 或使用命令行检查
neo4j status
```

### 3.2 执行导入脚本

```powershell
cd d:\PythonProject\data\output
python neo4j_import.py
```

### 3.3 导入进度监控

脚本会实时显示进度：

```
[步骤1] 创建节点...
[创建] Disease节点: 8807个
[创建] Symptom节点: 5995个
[创建] Drug节点: 3828个
...
[完成] 共创建 44650 个节点

[步骤2] 创建关系...
[进度] 已创建 50000 条关系...
[进度] 已创建 100000 条关系...
...
[完成] 共创建 459387 条关系

[步骤3] 添加疾病属性...
[进度] 已处理 2000 个疾病属性...
...
[完成] 共更新 8807 个疾病节点属性
```

---

## 四、验证导入结果

### 4.1 脚本自动验证

脚本会自动输出统计信息：

```
节点总数: 44650
各类节点数量:
  Disease: 8807个
  Symptom: 5995个
  Drug: 3828个
  ...

关系总数: 459387
各类关系数量:
  HAS_SYMPTOM: 123456条
  COMMON_DRUG: 45678条
  ...
```

### 4.2 Neo4j Browser查询

打开Neo4j Browser（http://localhost:7474），执行以下查询：

**查询节点总数：**

```cypher
MATCH (n) RETURN count(n)
```

**查询关系总数：**

```cypher
MATCH ()-[r]->() RETURN count(r)
```

**查询感冒的症状：**

```cypher
MATCH (d:Disease {name: '感冒'})-[:HAS_SYMPTOM]->(s:Symptom)
RETURN s.name
```

**查询感冒的常用药品：**

```cypher
MATCH (d:Disease {name: '感冒'})-[:COMMON_DRUG]->(g:Drug)
RETURN g.name
```

**查询感冒的详细信息：**

```cypher
MATCH (d:Disease {name: '感冒'})
RETURN d.name, d.desc, d.cause, d.prevent, d.cure_department
```

**可视化感冒的关系图谱：**

```cypher
MATCH (d:Disease {name: '感冒'})-[r]->(n)
RETURN d, r, n
```

---

## 五、图谱结构说明

### 5.1 节点类型

| 标签 | 数量 | ID前缀 | 说明 |
|------|------|---------|------|
| Disease | 8807 | D | 疾病节点，含详细属性 |
| Symptom | 5995 | S | 症状节点 |
| Drug | 3828 | G | 药品节点 |
| Check | 3353 | C | 检查项目节点 |
| Department | 54 | P | 科室节点 |
| CureWay | 544 | W | 治疗方式节点 |
| Food | 4868 | F | 食物节点 |
| Recipe | 4504 | R | 推荐食谱节点 |
| Producer | 17201 | M | 药品厂商节点 |

### 5.2 关系类型

| 关系 | 说明 | 示例 |
|------|------|------|
| HAS_SYMPTOM | 疾病的症状 | (感冒)-[:HAS_SYMPTOM]->(头痛) |
| COMMON_DRUG | 常用药品 | (感冒)-[:COMMON_DRUG]->(感冒灵) |
| BELONGS_TO_DEPT | 所属科室 | (感冒)-[:BELONGS_TO_DEPT]->(内科) |
| NEED_CHECK | 诊断检查 | (感冒)-[:NEED_CHECK]->(血常规) |
| CURE_WAY | 治疗方式 | (感冒)-[:CURE_WAY]->(药物治疗) |
| DO_EAT | 宜吃食物 | (感冒)-[:DO_EAT]->(苹果) |
| NOT_EAT | 忌吃食物 | (感冒)-[:NOT_EAT]->(辣椒) |
| RECOMMAND_EAT | 推荐食谱 | (感冒)-[:RECOMMAND_EAT]->(粥) |
| ACOMPANY_WITH | 并发症 | (感冒)-[:ACOMPANY_WITH]->(肺炎) |
| RECOMMAND_DRUG | 推荐药品 | (感冒)-[:RECOMMAND_DRUG]->(布洛芬) |

### 5.3 疾病节点属性

Disease节点包含以下属性：

| 属性 | 类型 | 说明 |
|------|------|------|
| id | String | 实体唯一ID（如D00001） |
| name | String | 疾病名称 |
| alias | List | 别名列表 |
| freq | Integer | 出现频次 |
| desc | String | 疾病描述 |
| cause | String | 发病原因 |
| prevent | String | 预防措施 |
| cure_department | List | 治疗科室列表 |
| category | List | 分类列表 |
| cured_prob | String | 治愈概率 |
| get_prob | Float | 患病概率 |
| cost_money | List | 治疗费用范围 |
| cure_lasttime | String | 治疗时长 |
| yibao_status | String | 医保状态 |
| get_way | String | 传染方式 |
| easy_get | String | 易感人群 |

---

## 六、常见问题

### 6.1 连接失败

**问题：无法连接到Neo4j**

**解决方案：**
1. 检查Neo4j是否启动（http://localhost:7474）
2. 检查端口是否正确（默认7687）
3. 检查用户名密码是否正确
4. 检查防火墙设置

### 6.2 导入速度慢

**问题：导入速度太慢**

**解决方案：**
1. 增大Neo4j内存配置（neo4j.conf）
2. 使用批量导入（LOAD CSV）
3. 禁用Neo4j事务日志（仅导入时）

### 6.3 数据丢失

**问题：部分数据未导入**

**解决方案：**
1. 检查源数据文件完整性
2. 检查ID映射是否完整
3. 检查三元组ID是否匹配

---

## 七、性能优化建议

### 7.1 使用LOAD CSV（推荐）

对于大规模数据，使用Neo4j内置的LOAD CSV更快：

```cypher
// 批量创建节点
LOAD CSV WITH HEADERS FROM 'file:/triplets_with_id.csv' AS row
MERGE (d:Disease {id: row.head_id})
SET d.name = row.head_name;

// 批量创建关系
LOAD CSV WITH HEADERS FROM 'file:/triplets_with_id.csv' AS row
MATCH (d:Disease {id: row.head_id})
MATCH (t {id: row.tail_id})
MERGE (d)-[:HAS_SYMPTOM]->(t);
```

### 7.2 创建索引

在导入前创建索引可加速查询：

```cypher
CREATE INDEX disease_id IF NOT EXISTS FOR (n:Disease) ON (n.id);
CREATE INDEX disease_name IF NOT EXISTS FOR (n:Disease) ON (n.name);
CREATE INDEX symptom_id IF NOT EXISTS FOR (n:Symptom) ON (n.id);
CREATE INDEX drug_id IF NOT EXISTS FOR (n:Drug) ON (n.id);
```

---

## 八、下一步操作

### 8.1 连接问答系统

将Neo4j图谱连接到问答系统：

```python
from neo4j import GraphDatabase

def query_symptoms(disease_name):
    driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))
    with driver.session() as session:
        result = session.run(
            "MATCH (d:Disease {name: $name})-[:HAS_SYMPTOM]->(s) "
            "RETURN s.name",
            name=disease_name
        )
        return [r["s.name"] for r in result]
```

### 8.2 同义词召回

结合MySQL同义词表：

```python
# 1. 从MySQL查询同义词（synonym_alias.json已导入）
# "头疼" -> "头痛"

# 2. 用标准名查询Neo4j图谱
# MATCH (s:Symptom {name: '头痛'})<-[:HAS_SYMPTOM]-(d:Disease)
# RETURN d.name
```

---

*文档撰写：数据组*
*日期：2026-06-29*