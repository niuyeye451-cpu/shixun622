# 实体 ID 分配报告

## 1. 分配规则

- ID 前缀按实体类型语义命名，避免视觉混淆
- 同类型内按**名称排序**后顺序分配，保证可复现
- 格式：`前缀 + 5位数字`（如 D00001）

| 实体类型 | ID前缀 | 含义 | 数量 |
|----------|--------|------|------|
| Disease | D | — | 8807 |
| Symptom | S | — | 5995 |
| Drug | G | — | 3828 |
| Check | C | — | 3353 |
| Department | P | — | 54 |
| CureWay | W | — | 544 |
| Food | F | — | 4868 |
| Producer | M | — | 17201 |

## 2. 分配结果

| 实体类型 | 实体数 | 带别名 | 最高频次 |
|----------|--------|--------|---------|
| Disease | 8807 | 1275 | 291 |
| Symptom | 5995 | 13 | 1001 |
| Drug | 3828 | 3 | 708 |
| Check | 3353 | 0 | 2127 |
| Department | 54 | 0 | 2385 |
| CureWay | 544 | 0 | 6905 |
| Food | 4868 | 0 | 2753 |
| Producer | 17201 | 0 | 305 |

## 3. 跨类型同名冲突（消歧线索）

共发现 **681** 个同名实体出现在多个类型中，需在图谱建模时消歧：

| 实体名称 | 出现的类型 |
|----------|-----------|
| β-氨基酸尿 | Disease、Symptom |
| 一氧化碳中毒 | Disease、Symptom |
| 三七胶囊 | Drug、Producer |
| 三尖瓣狭窄 | Disease、Symptom |
| 三维鱼肝油乳 | Drug、Producer |
| 三黄片 | Drug、Producer |
| 上消化道出血 | Disease、Symptom |
| 上睑下垂 | Disease、Symptom |
| 下颌后缩 | Disease、Symptom |
| 不孕不育 | Department、Disease |
| 丙硫氧嘧啶片 | Drug、Producer |
| 丧偶后适应性障碍 | Disease、Symptom |
| 中性胰岛素注射液 | Drug、Producer |
| 中暑 | Disease、Symptom |
| 丹杞颗粒 | Drug、Producer |
| 丹毒 | Disease、Symptom |
| 乌洛托品溶液 | Drug、Producer |
| 乙酰谷酰胺注射液 | Drug、Producer |
| 书写痉挛 | Disease、Symptom |
| 乳头内陷 | Disease、Symptom |
| 乳头溢液 | Disease、Symptom |
| 乳头皲裂 | Disease、Symptom |
| 乳房疼痛 | Disease、Symptom |
| 乳房肿块 | Disease、Symptom |
| 乳癖消片 | Drug、Producer |
| 乳癖消胶囊 | Drug、Producer |
| 乳突炎 | Disease、Symptom |
| 乳糜尿 | Check、Disease、Symptom |
| 乳糜泻 | Disease、Symptom |
| 乳糜胸 | Disease、Symptom |
| ... | 共 681 个 |

## 4. 增强版三元组

- 原始三元组：459387 条
- 成功映射 ID：459387 条 (100.00%)
- 未映射（实体不在词典中）：0 条

**用途**：图谱组可直接用 `head_id`/`tail_id` 做节点主键入库，无需自行维护名称→ID映射。

## 5. 使用方式

- **图谱组建库**：用 ID 作为 Neo4j 节点主键，`name` 作为普通属性
- **实体消歧**：跨类型同名冲突清单（第3节）需人工/规则确认归属
- **重要性排序**：`freq` 字段表示实体被引用次数，可用于推荐/排序
- **同义词召回**：`alias` 字段可挂到节点上，查询时 `WHERE x IN n.alias`