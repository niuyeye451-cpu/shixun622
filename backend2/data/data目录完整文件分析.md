# data 目录完整文件分析

> **目的**：说明 data 目录下每个文件/文件夹的作用
> **目录位置**：`D:\PythonProject\data\`

---

## 一、目录结构总览

```
data/
├── QASystemOnMedicalKG/     开源原始仓库（数据源 + 参考代码）
├── output/                  你的产出目录（验收交付物）
├── preprocess.py            数据预处理脚本
├── build_synonym.py         同义词挖掘脚本
├── assign_entity_id.py      实体ID分配脚本
├── reorganize_output.py     目录重组脚本
```

---

## 二、QASystemOnMedicalKG/ —— 开源原始仓库

> **来源**：https://github.com/liuhuanyong/QASystemOnMedicalKG
> **作用**：提供原始数据 + 参考代码（你不需要重写这些，只需理解）

### 2.1 核心数据文件

#### data/medical.json（45MB）⭐ 最重要

**内容**：
- 8808 条疾病记录（JSONL 格式）
- 每条记录包含 22 个字段（疾病名、症状、药品、科室、检查等）

**对项目的作用**：
- 是你整个项目的**数据源头**
- 所有 output 文件都是从这里加工出来的

**你做了什么**：
- 克隆仓库获取此文件
- 用 preprocess.py 清洗生成 medical_clean.json
- 提取三元组生成 triplets.csv
- 提取实体生成 entity_dict/

**与 output 的关系**：
```
原始：QASystemOnMedicalKG/data/medical.json（脏数据）
  ↓ preprocess.py
清洗：output/核心数据/medical_clean.json（干净数据）
```

---

### 2.2 dict/ —— 原始实体词典

> 这些是仓库作者导出的，你 output/实体词典/ 里的文件与其对应

| 文件 | 内容 | 与你的产出关系 |
|------|------|--------------|
| disease.txt | 8807 个疾病 | 与你的 Disease.txt 相同 |
| symptom.txt | 5998 个症状 | 与你的 Symptom.txt 相同 |
| drug.txt | 3828 个药品 | 与你的 Drug.txt 相同 |
| check.txt | 3353 个检查 | 与你的 Check.txt 相同 |
| department.txt | 54 个科室 | 与你的 Department.txt 相同 |
| food.txt | 4868 个食物 | 与你的 Food.txt 相同 |
| producer.txt | 17201 个厂商 | 与你的 Producer.txt 相同 |
| deny.txt | 否定词词典 | **你没用**，问答组可能用到 |

**deny.txt 的作用**：
- 包含否定词如"不"、"没有"、"无"
- 用于处理否定类问题："感冒不吃什么？"

**你额外做了什么**：
- 拆分 Food 为 宜吃食物.txt / 忌吃食物.txt / 推荐食谱.txt
- 原仓库没有区分食物的宜忌属性

---

### 2.3 prepare_data/ —— 数据构建脚本

> 这些脚本是仓库作者用来生成 medical.json 的，你**不需要运行**（已无法运行）

#### data_spider.py（6.5KB）

**内容**：爬取寻医问药网的爬虫脚本

**作用**：
- 原始数据来源：http://jib.xywy.com（寻医问药网）
- 爬取疾病各页面（简介/病因/症状/检查/治疗/饮食/药品）
- 存入 MongoDB

**为什么你不需要运行**：
- xywy.com 网站已改版，XPath 不再匹配
- `urllib` + `gbk` 解码已过时
- MongoDB 需要本地安装
- **你直接用现成的 medical.json 即可**

---

#### build_data.py（5.4KB）

**内容**：从 MongoDB 原始数据 → medical.json

**作用**：
- 定义了字段名映射（中文键名 → 英文键名）
- 这就是为什么 medical.json 用英文键名的原因

**关键代码**：
```python
self.key_dict = {
    '医保疾病': 'yibao_status',
    '患病比例': 'get_prob',
    '就诊科室': 'cure_department',
    '症状': 'symptom',
    '检查': 'check',
    ...
}
```

**对你的意义**：
- 解释了"科室在哪"—— `cure_department` 就是科室
- 解释了"检查在哪"—— `check` 就是检查项目

---

#### max_cut.py（3.9KB）

**内容**：基于词典的最大前向/后向切分算法

**作用**：
- 用于并发症字段 `acompany` 的分词
- 原数据可能是"支气管炎、肺炎"连在一起，需切分

---

### 2.4 核心问答代码（你参考用，不直接用）

#### build_medicalgraph.py（12KB）

**内容**：medical.json → Neo4j 图谱的入库脚本

**作用**：
- 定义了 8 类节点类型（Disease/Symptom/Drug...）
- 定义了 11 类关系类型（has_symptom/need_check...）
- 用 py2neo 逐条 create 入库

**对你的意义**：
- 是你写 data_entity_mapping.md 的参考依据
- 但图谱组不应直接用此脚本（效率低，逐条 create）

**更好的做法**：
- 用你的 triplets_with_id.csv + LOAD CSV（批量导入快 100 倍）

---

#### question_classifier.py（11KB）

**内容**：问句意图分类

**作用**：
- 判断用户问的是"症状"、"药品"、"科室"、"检查"还是"饮食"
- 用规则匹配（如"吃什么药"→药品意图）

**给谁参考**：
- 问答组——理解如何做意图分类

---

#### question_parser.py（8.6KB）

**内容**：问句解析 → Cypher 查询语句

**作用**：
- 从用户问题中提取实体（疾病名、症状名等）
- 生成对应的 Cypher 查询语句

**给谁参考**：
- 问答组——理解如何生成 Cypher

---

#### answer_search.py（6.4KB）

**内容**：执行 Cypher 查询 + 组织答案

**作用**：
- 连接 Neo4j 执行查询
- 将结果组织成自然语言回答

---

#### chatbot_graph.py（1.2KB）

**内容**：问答系统主入口

**作用**：
- 整合 classifier + parser + answer_search
- 提供问答流程 demo

---

### 2.5 文档与图片

#### README.md（21KB）

**内容**：项目说明文档

**作用**：
- 说明项目结构、数据来源、使用方法
- 你理解项目的入口文档

---

#### document/ 和 img/

| 文件 | 内容 | 作用 |
|------|------|------|
| chat1.png / chat2.png | 问答系统截图 | 展示系统效果 |
| kg_route.png | 知识图谱架构图 | 展示图谱结构 |
| qa_route.png | 问答流程图 | 展示问答流程 |
| graph_summary.png | 图谱统计图 | 展示数据规模 |
| 刘焕勇-20181004-kg_route.pptx | 项目演示 PPT | 答辩参考 |
| wechat.jpg | 作者微信二维码 | 联系原作者 |

---

## 三、你的脚本文件

### 3.1 preprocess.py（16KB）⭐ 核心脚本

**内容**：数据预处理 6 步流程

**做了什么**：
```
原始 medical.json
  ↓ Step 1: JSONL 解析
  ↓ Step 2: 疾病去重
  ↓ Step 3: 空值处理
  ↓ Step 4: 文本清洗（去乱码/噪声）
  ↓ Step 5: 数值标准化（百分比/价格/周期）
  ↓ Step 6: drug_detail 拆分
medical_clean.json + triplets.csv + entity_dict/
```

**对项目的作用**：
- 将脏数据变成干净数据
- 是所有后续工作的基础

**复用性**：
- 如果数据源更新，重新运行此脚本即可
- 模块化设计，易于维护

---

### 3.2 build_synonym.py（15KB）

**内容**：同义词挖掘脚本

**做了什么**：
```
疾病 desc 字段
  ↓ 触发词匹配（又称/简称/俗称/又名/也叫）
  ↓ 噪声过滤（句子片段/触发词残留）
  ↓ 多别名切分（顿号分隔）
  ↓ 补充症状口语 + 药品别名
synonym_full.json + synonym_alias.json
```

**对项目的作用**：
- 提升问答召回率（用户输入"头疼"能识别为"头痛")
- 文档明确要求"同义词扩展"

**复用性**：
- 如果数据源更新，重新运行此脚本即可

---

### 3.3 assign_entity_id.py（11KB）

**内容**：实体 ID 分配脚本

**做了什么**：
```
8 类实体词典
  ↓ 按名称排序分配 ID（D00001/S00001...）
  ↓ 记录别名 + 频次
  ↓ 检测跨类型同名冲突
entity_id_map.json + triplets_with_id.csv
```

**对项目的作用**：
- 提供稳定的节点主键（Neo4j 不应用 name 做主键）
- 提供消歧线索（681 个跨类型冲突）
- 提供频次信息（可用于推荐排序）

**复用性**：
- 如果数据源更新，重新运行此脚本即可

---

### 3.4 reorganize_output.py（6.9KB）

**内容**：目录重组脚本

**做了什么**：
```
output/（混乱结构）
  ↓ 创建中文文件夹（核心数据/实体词典/同义词表/ID映射/数据报告）
  ↓ 移动文件到对应文件夹
  ↓ 拆分 Food.txt 为 宜吃/忌吃/推荐食谱
  ↓ 生成目录说明.txt
output/（清晰结构）
```

**对项目的作用**：
- 让产出目录清晰易懂
- 解决 Food 实体的歧义问题

**复用性**：
- 如果产出结构需要调整，修改此脚本即可

---

## 四、output/ —— 你的产出目录

> 已在 `output文件详细说明.md` 中详细说明，此处简要列出

### 4.1 核心数据/

| 文件 | 来源脚本 | 作用 |
|------|---------|------|
| medical_clean.json | preprocess.py | 清洗后的疾病数据 |
| triplets.csv | preprocess.py | 三元组（名称版） |
| triplets_with_id.csv | assign_entity_id.py | 三元组（ID版） |

### 4.2 实体词典/

| 文件 | 来源脚本 | 作用 |
|------|---------|------|
| 8 类实体词典.txt | preprocess.py | NER 识别基础 |
| 宜吃食物.txt | reorganize_output.py | 区分宜吃属性 |
| 忌吃食物.txt | reorganize_output.py | 区分忌吃属性 |
| 推荐食谱.txt | reorganize_output.py | 区分食谱 |

### 4.3 同义词表/

| 文件 | 来源脚本 | 作用 |
|------|---------|------|
| synonym_full.json | build_synonym.py | 完整同义词词典 |
| synonym_alias.json | build_synonym.py | 别名→标准名映射 |
| synonym_report.md | build_synonym.py | 挖掘报告 |

### 4.4 ID映射/

| 文件 | 来源脚本 | 作用 |
|------|---------|------|
| entity_id_map.json | assign_entity_id.py | 44650 个实体 ID |

### 4.5 数据报告/

| 文件 | 来源 | 作用 |
|------|------|------|
| data_entity_mapping.md | 手写 | 数据-实体映射交接文档 |
| data_quality_report.md | preprocess.py | 数据质量报告 |
| entity_id_report.md | assign_entity_id.py | ID 分配报告 |
| task_summary_report.md | 手写 | 任务总结报告 |
| output文件详细说明.md | 手写 | output 文件详细说明 |

---

## 五、文件依赖关系图

```
原始数据源
  │
  ├── 寻医问药网 (http://jib.xywy.com)
  │     ↓ data_spider.py（已过时，无法运行）
  │
  ├── MongoDB 原始库
  │     ↓ build_data.py（已过时，无法运行）
  │
  └── medical.json（你直接用这个）
        │
        ├── preprocess.py ──────────────────┬── medical_clean.json
        │                                  ├── triplets.csv
        │                                  └── entity_dict/*.txt
        │
        ├── build_synonym.py ───────────────┬── synonym_full.json
        │                                  └── synonym_alias.json
        │
        ├── assign_entity_id.py ────────────┬── entity_id_map.json
        │                                  └── triplets_with_id.csv
        │
        └── reorganize_output.py ───────────┬── output/目录重组
                                           └── 宜吃/忌吃/推荐食谱.txt
```

---

## 六、哪些文件你需要保留

### 必须保留（验收交付物）

| 文件/目录 | 原因 |
|---------|------|
| output/ 全部内容 | 验收交付物 |
| preprocess.py | 可复用脚本 |
| build_synonym.py | 可复用脚本 |
| assign_entity_id.py | 可复用脚本 |
| reorganize_output.py | 可复用脚本 |
| QASystemOnMedicalKG/data/medical.json | 原始数据源证明 |

### 可以删除（不影响交付）

| 文件/目录 | 原因 |
|---------|------|
| QASystemOnMedicalKG/.git/ | Git 历史，无需保留 |
| QASystemOnMedicalKG/__pycache__/ | Python 缓存，可删除 |
| QASystemOnMedicalKG/dict/ | 你的 output/实体词典/ 已包含 |
| QASystemOnMedicalKG/prepare_data/ | 脚本已无法运行，仅供参考 |
| QASystemOnMedicalKG/document/ | 图片，答辩可不展示 |
| QASystemOnMedicalKG/img/ | 图片，答辩可不展示 |
| QASystemOnMedicalKG/*.py（问答代码） | 问答组会自己写 |

### 建议保留（答辩参考）

| 文件 | 原因 |
|------|------|
| QASystemOnMedicalKG/README.md | 说明数据来源 |
| QASystemOnMedicalKG/build_medicalgraph.py | 证明节点/关系设计来源 |

---

## 七、总结：data 目录的核心价值

| 目录/文件 | 一句话价值 |
|---------|----------|
| QASystemOnMedicalKG/data/medical.json | 原始数据源，一切工作的起点 |
| output/ | 验收交付物，证明你做了什么 |
| preprocess.py | 核心清洗脚本，可复用 |
| build_synonym.py | 同义词挖掘脚本，可复用 |
| assign_entity_id.py | ID分配脚本，可复用 |
| reorganize_output.py | 目录重组脚本，可复用 |

---

*文档撰写：数据组*
*日期：2026-06-27*