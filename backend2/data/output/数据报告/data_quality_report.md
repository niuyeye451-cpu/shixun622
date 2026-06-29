# 医疗知识图谱数据质量报告

- 来源：`QASystemOnMedicalKG/data/medical.json`
- 解析损坏行：0
- 去重移除：1
- 最终疾病数：8807

## 1. 字段覆盖率

| 字段 | 非空数 | 覆盖率 |
|------|--------|--------|
| desc | 8806 | 100.0% |
| cause | 8790 | 99.8% |
| prevent | 8770 | 99.6% |
| symptom | 8764 | 99.5% |
| check | 8803 | 100.0% |
| cure_department | 8806 | 100.0% |
| common_drug | 7644 | 86.8% |
| recommand_drug | 7644 | 86.8% |
| do_eat | 5575 | 63.3% |
| not_eat | 5575 | 63.3% |
| cured_prob | 8756 | 99.4% |

## 2. 实体规模（去重后）

| 实体类型 | 数量 |
|----------|------|
| Check | 3353 |
| CureWay | 544 |
| Department | 54 |
| Disease | 8807 |
| Drug | 3828 |
| Food | 4868 |
| Producer | 17201 |
| Symptom | 5995 |

## 3. 数据缺失情况

- 无药品信息：1163 条 (13.2%)
- 无饮食建议：3232 条 (36.7%)

## 4. 处理说明

- 文本字段：去除 HTML 实体、多余空白、控制字符
- 列表字段：去重保序、同义词归一、过滤噪声词
- 数值字段：`cured_prob`/`get_prob` 提取百分比数值；`cost_money` 提取价格区间；`cure_lasttime` 归一为结构体
- `drug_detail`：拆分为厂商(Producer)与药品(Drug)
- 疾病去重：同名保留信息最全者
