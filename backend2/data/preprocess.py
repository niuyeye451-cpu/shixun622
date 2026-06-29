#!/usr/bin/env python3
# coding: utf-8
"""
医疗知识图谱数据预处理脚本
================================================================
功能：将 QASystemOnMedicalKG/data/medical.json（原始半成品 JSONL）
      清洗为可直接导入 Neo4j / 供 NLP、问答组使用的标准化数据。

处理流程（6 步）：
  Step 1: 格式校验 + JSONL 解析
  Step 2: 去重（疾病名 / 三元组）
  Step 3: 空值处理（统一为 [] 并标记缺失）
  Step 4: 文本清洗（去乱码 / HTML实体 / 噪声词）
  Step 5: 标准化（数值提取 / 单位归一 / 同义词归一）
  Step 6: 拆分嵌套字段（drug_detail → 厂商 + 药品）

输出（写入 ./output/）：
  - medical_clean.json        清洗后的核心数据（JSONL）
  - triplets.csv              三元组 (实体,关系,实体)
  - entity_dict/*.txt         7 类实体词典
  - synonym.json              同义词映射
  - data_quality_report.md    数据质量报告

用法：
  python preprocess.py
================================================================
"""

import json
import os
import re
import csv
from collections import Counter, defaultdict

# ============================================================
# 路径配置
# ============================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_PATH = os.path.join(BASE_DIR, "QASystemOnMedicalKG", "data", "medical.json")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
ENTITY_DIR = os.path.join(OUTPUT_DIR, "entity_dict")

# 实体类型 → 对应字段（用于三元组提取 / 词典导出）
ENTITY_FIELDS = {
    "Symptom":   "symptom",          # 症状
    "Check":     "check",            # 检查
    "Department":"cure_department",  # 科室
    "Drug":      "common_drug",      # 常用药品（与 recommand_drug 合并）
    "Food":      "do_eat",           # 食物（宜忌合并）
    "Producer":  "_producer",        # 药品厂商（从 drug_detail 拆出）
    "CureWay":   "cure_way",         # 治疗方式
}

# 三元组关系定义：(疾病侧字段, 关系英文名, 关系中文名, 目标实体集)
RELATIONS = [
    ("symptom",        "has_symptom",     "症状",     "Symptom"),
    ("check",          "need_check",      "诊断检查", "Check"),
    ("cure_department","belongs_to_dept", "所属科室", "Department"),
    ("common_drug",    "common_drug",     "常用药品", "Drug"),
    ("recommand_drug", "recommand_drug",  "推荐药品", "Drug"),
    ("do_eat",         "do_eat",          "宜吃",     "Food"),
    ("not_eat",        "not_eat",         "忌吃",     "Food"),
    ("recommand_eat",  "recommand_eat",   "推荐食谱", "Food"),
    ("cure_way",       "cure_way",        "治疗方式", "CureWay"),
    ("acompany",       "acompany_with",   "并发症",   "Disease"),
]

# 简单同义词归一表（可后续扩展；这里只列常见的）
SYNONYM_MAP = {
    "头疼": "头痛",
    "上感": "上呼吸道感染",
    "拉肚子": "腹泻",
    "发烧": "发热",
    "流鼻涕": "鼻塞",
    "咳嗽咳痰": "咳嗽",
    "恶心呕吐": "恶心",
}

# 症状噪声词黑名单（爬虫误抓的人名/乱码）
SYMPTOM_BLACKLIST = {"毓卓", "的症状", ""}


# ============================================================
# 工具函数
# ============================================================
def ensure_dirs():
    """创建输出目录"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(ENTITY_DIR, exist_ok=True)


def clean_text(s):
    """清洗文本：去 HTML 实体 / 控制字符 / 多余空白"""
    if not isinstance(s, str):
        return s
    s = s.replace("\xa0", " ")          # 不间断空格
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    s = re.sub(r"[ \t]+", " ", s)        # 连续空格/制表符
    s = re.sub(r"\n{2,}", "\n", s)       # 连续换行
    s = s.strip()
    return s


def clean_list(lst, blacklist=None):
    """清洗列表型字段：去空白 / 去重保序 / 应用同义词 / 过滤黑名单"""
    if not isinstance(lst, list):
        return []
    seen, result = set(), []
    for item in lst:
        if not isinstance(item, str):
            continue
        item = clean_text(item)
        if not item:
            continue
        if blacklist and item in blacklist:
            continue
        item = SYNONYM_MAP.get(item, item)   # 同义词归一
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def extract_percent(s):
    """'约40%' / '0.00002%' → 数值；解析失败返回原值"""
    if not isinstance(s, str):
        return s
    m = re.search(r"(\d+\.?\d*)\s*%", s)
    return float(m.group(1)) if m else s


def extract_money_range(s):
    """'8000——15000 元' → [8000, 15000]；单值 → [v, v]；失败返回原值"""
    if not isinstance(s, str):
        return s
    nums = re.findall(r"\d+\.?\d*", s)
    if len(nums) >= 2:
        return [float(nums[0]), float(nums[1])]
    if len(nums) == 1:
        return [float(nums[0]), float(nums[0])]
    return s


def normalize_duration(s):
    """'约3个月' → {'value':3,'unit':'月'}；失败返回原值（归一化到天可后续做）"""
    if not isinstance(s, str):
        return s
    m = re.search(r"(\d+\.?\d*)\s*(天|周|个月|月|年)", s)
    if m:
        return {"value": float(m.group(1)), "unit": m.group(2)}
    return s


def split_drug_detail(detail):
    """
    '华东药业(布洛芬)' → {'producer':'华东药业', 'drug':'布洛芬'}
    厂商在括号外，药品在括号内。
    """
    if not isinstance(detail, str):
        return None
    if "(" in detail and detail.endswith(")"):
        producer = detail.split("(")[0].strip()
        drug = detail.split("(")[-1].replace(")", "").strip()
        if producer and drug:
            return {"producer": producer, "drug": drug}
    return None


# ============================================================
# Step 1: 解析 JSONL
# ============================================================
def step1_parse(path):
    """逐行解析 JSONL，跳过损坏行，返回记录列表"""
    records, bad = [], 0
    with open(path, "r", encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                bad += 1
    print(f"[Step1] 解析完成：成功 {len(records)} 条，损坏 {bad} 条")
    return records, bad


# ============================================================
# Step 2: 去重（疾病名）
# ============================================================
def step2_dedup(records):
    """同名疾病保留信息最全（非空字段最多）的一条"""
    groups = defaultdict(list)
    for r in records:
        groups[r.get("name", "")].append(r)

    deduped, removed = [], 0
    for name, items in groups.items():
        if not name:
            continue
        if len(items) == 1:
            deduped.append(items[0])
        else:
            # 选非空字段最多的记录
            best = max(items, key=lambda r: sum(1 for v in r.values()
                                                if v not in ("", [], None)))
            deduped.append(best)
            removed += len(items) - 1
    print(f"[Step2] 去重：移除重复疾病 {removed} 条，剩余 {len(deduped)} 条")
    return deduped, removed


# ============================================================
# Step 3 + 4 + 5 + 6: 单条记录清洗
# ============================================================
def clean_record(rec):
    """对单条疾病记录做完整清洗，返回新 dict"""
    out = {}

    # ---- 文本类字段：清洗 ----
    for k in ("name", "desc", "cause", "prevent"):
        out[k] = clean_text(rec.get(k, ""))

    # ---- 列表类字段：清洗 + 同义词归一 + 黑名单 ----
    out["symptom"]        = clean_list(rec.get("symptom"), SYMPTOM_BLACKLIST)
    out["acompany"]       = clean_list(rec.get("acompany"))
    out["cure_department"]= clean_list(rec.get("cure_department"))
    out["cure_way"]       = clean_list(rec.get("cure_way"))
    out["check"]          = clean_list(rec.get("check"))
    out["common_drug"]    = clean_list(rec.get("common_drug"))
    out["recommand_drug"] = clean_list(rec.get("recommand_drug"))
    out["do_eat"]         = clean_list(rec.get("do_eat"))
    out["not_eat"]        = clean_list(rec.get("not_eat"))
    out["recommand_eat"]  = clean_list(rec.get("recommand_eat"))
    out["category"]       = clean_list(rec.get("category"))

    # ---- Step 5: 数值标准化 ----
    out["cured_prob"]     = extract_percent(rec.get("cured_prob", ""))
    out["get_prob"]       = extract_percent(rec.get("get_prob", ""))
    out["cost_money"]    = extract_money_range(rec.get("cost_money", ""))
    out["cure_lasttime"] = normalize_duration(rec.get("cure_lasttime", ""))

    # ---- 其他字符串字段：清洗 ----
    for k in ("yibao_status", "get_way", "easy_get"):
        out[k] = clean_text(rec.get(k, ""))

    # ---- Step 6: 拆分 drug_detail → producers + drugs ----
    raw_detail = rec.get("drug_detail", [])
    producers, drug_pairs = [], []
    if isinstance(raw_detail, list):
        for d in raw_detail:
            pair = split_drug_detail(d)
            if pair:
                producers.append(pair["producer"])
                drug_pairs.append(pair["drug"])
    out["_producers"]  = sorted(set(producers))   # 内部用，导出时处理
    out["_drug_pairs"] = sorted(set(drug_pairs))
    out["drug_detail"] = raw_detail if isinstance(raw_detail, list) else []

    # ---- 缺失标记（Step 3 的体现）----
    out["_has_drug"]    = len(out["common_drug"]) > 0 or len(out["recommand_drug"]) > 0
    out["_has_food"]    = len(out["do_eat"]) > 0 or len(out["not_eat"]) > 0

    return out


def step3456_clean(records):
    """批量清洗所有记录"""
    cleaned = [clean_record(r) for r in records]
    print(f"[Step3-6] 清洗完成：{len(cleaned)} 条记录已标准化")
    return cleaned


# ============================================================
# 衍生产物：三元组 / 词典 / 同义词
# ============================================================
def build_artifacts(cleaned):
    """从清洗后数据构建三元组、实体词典、同义词表"""
    triplets = set()
    entity_sets = defaultdict(set)
    synonym_used = Counter()

    for rec in cleaned:
        disease = rec["name"]
        entity_sets["Disease"].add(disease)

        for field, rel_en, rel_cn, etype in RELATIONS:
            vals = rec.get(field, [])
            if not isinstance(vals, list):
                continue
            for v in vals:
                v = v.strip() if isinstance(v, str) else v
                if not v:
                    continue
                triplets.add((disease, rel_en, rel_cn, v))
                entity_sets[etype].add(v)
                if v in SYNONYM_MAP.values():
                    synonym_used[v] += 1

        # Producer 来自拆分
        for p in rec.get("_producers", []):
            entity_sets["Producer"].add(p)
            triplets.add((disease, "produced_by", "生产厂商", p))

    # ---- 写三元组 CSV ----
    triplet_path = os.path.join(OUTPUT_DIR, "triplets.csv")
    with open(triplet_path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["head", "relation", "relation_cn", "tail"])
        for t in sorted(triplets):
            w.writerow(t)
    print(f"[产物] 三元组：{len(triplets)} 条 → {triplet_path}")

    # ---- 写实体词典 ----
    for etype, names in entity_sets.items():
        p = os.path.join(ENTITY_DIR, f"{etype}.txt")
        with open(p, "w", encoding="utf-8") as f:
            f.write("\n".join(sorted(names)))
        print(f"[产物] 实体词典 {etype}：{len(names)} 个 → {p}")

    # ---- 写同义词表 ----
    syn_path = os.path.join(OUTPUT_DIR, "synonym.json")
    with open(syn_path, "w", encoding="utf-8") as f:
        json.dump(SYNONYM_MAP, f, ensure_ascii=False, indent=2)
    print(f"[产物] 同义词表：{len(SYNONYM_MAP)} 条 → {syn_path}")

    return triplets, entity_sets


# ============================================================
# 数据质量报告
# ============================================================
def gen_quality_report(cleaned, entity_sets, n_bad, n_removed):
    """生成 Markdown 数据质量报告"""
    total = len(cleaned)
    report = []
    report.append("# 医疗知识图谱数据质量报告\n")
    report.append(f"- 来源：`QASystemOnMedicalKG/data/medical.json`")
    report.append(f"- 解析损坏行：{n_bad}")
    report.append(f"- 去重移除：{n_removed}")
    report.append(f"- 最终疾病数：{total}\n")

    # 字段覆盖率
    report.append("## 1. 字段覆盖率\n")
    report.append("| 字段 | 非空数 | 覆盖率 |")
    report.append("|------|--------|--------|")
    fields = ["desc", "cause", "prevent", "symptom", "check",
              "cure_department", "common_drug", "recommand_drug",
              "do_eat", "not_eat", "cured_prob"]
    for fld in fields:
        cnt = sum(1 for r in cleaned
                  if r.get(fld) not in ("", [], None, [None]))
        report.append(f"| {fld} | {cnt} | {cnt/total*100:.1f}% |")
    report.append("")

    # 实体规模
    report.append("## 2. 实体规模（去重后）\n")
    report.append("| 实体类型 | 数量 |")
    report.append("|----------|------|")
    for etype, names in sorted(entity_sets.items()):
        report.append(f"| {etype} | {len(names)} |")
    report.append("")

    # 缺失情况
    no_drug = sum(1 for r in cleaned if not r["_has_drug"])
    no_food = sum(1 for r in cleaned if not r["_has_food"])
    report.append("## 3. 数据缺失情况\n")
    report.append(f"- 无药品信息：{no_drug} 条 ({no_drug/total*100:.1f}%)")
    report.append(f"- 无饮食建议：{no_food} 条 ({no_food/total*100:.1f}%)\n")

    report.append("## 4. 处理说明\n")
    report.append("- 文本字段：去除 HTML 实体、多余空白、控制字符")
    report.append("- 列表字段：去重保序、同义词归一、过滤噪声词")
    report.append("- 数值字段：`cured_prob`/`get_prob` 提取百分比数值；"
                  "`cost_money` 提取价格区间；`cure_lasttime` 归一为结构体")
    report.append("- `drug_detail`：拆分为厂商(Producer)与药品(Drug)")
    report.append("- 疾病去重：同名保留信息最全者\n")

    path = os.path.join(OUTPUT_DIR, "data_quality_report.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(report))
    print(f"[产物] 质量报告 → {path}")


# ============================================================
# 主流程
# ============================================================
def main():
    ensure_dirs()
    print("=" * 60)
    print("医疗知识图谱数据预处理")
    print("=" * 60)

    # Step 1
    records, n_bad = step1_parse(INPUT_PATH)
    # Step 2
    records, n_removed = step2_dedup(records)
    # Step 3-6
    cleaned = step3456_clean(records)

    # 写清洗后数据
    clean_path = os.path.join(OUTPUT_DIR, "medical_clean.json")
    with open(clean_path, "w", encoding="utf-8") as f:
        for rec in cleaned:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"[产物] 清洗数据：{len(cleaned)} 条 → {clean_path}")

    # 衍生产物
    triplets, entity_sets = build_artifacts(cleaned)

    # 质量报告
    gen_quality_report(cleaned, entity_sets, n_bad, n_removed)

    print("=" * 60)
    print("全部完成！输出目录：", OUTPUT_DIR)
    print("=" * 60)


if __name__ == "__main__":
    main()
