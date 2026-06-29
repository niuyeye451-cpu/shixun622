#!/usr/bin/env python3
# coding: utf-8
"""
实体 ID 分配脚本
================================================================
任务目标（项目文档依据）：
  - "实体消歧和同义词处理"：需要稳定唯一 ID 作为消歧基础
  - "保证实体名称一致"：同一实体在不同字段写法不一，需用 ID 统一引用
  - 图谱节点主键：Neo4j 不应用 name 做主键，需稳定 ID

功能：
  1. 读取清洗后的 8 类实体，为每个实体分配稳定唯一 ID
     Disease: D00001~  Symptom: S00001~  Drug: G00001~
     Check: C00001~  Department: P00001~  CureWay: W00001~
     Food: F00001~  Producer: M00001~
  2. ID 分配顺序确定性（按名称排序），保证可复现
  3. 记录每个实体的别名（来自 synonym）、出现频次（消歧线索）
  4. 生成「增强版三元组」（实体名→实体ID），供图谱组直接用
  5. 输出跨类型同名冲突清单（同名实体出现在不同类型 = 歧义线索）

输出（写入 ./output/）：
  - entity_id_map.json          {实体类型: {实体名: {id, alias, freq}}}
  - triplets_with_id.csv        增强版三元组（用 ID 替代名称）
  - entity_id_report.md         ID 分配报告
================================================================
"""

import json
import os
import csv
from collections import defaultdict, Counter

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
ENTITY_DIR = os.path.join(OUTPUT_DIR, "entity_dict")
CLEAN_PATH = os.path.join(OUTPUT_DIR, "medical_clean.json")
TRIPLET_PATH = os.path.join(OUTPUT_DIR, "triplets.csv")
SYNONYM_PATH = os.path.join(OUTPUT_DIR, "synonym_full.json")

# 实体类型 → ID 前缀（前缀选用语义首字母，避免视觉混淆）
ID_PREFIX = {
    "Disease":    "D",   # Disease
    "Symptom":    "S",   # Symptom
    "Drug":       "G",   # druG（D 已被 Disease 占用）
    "Check":      "C",   # Check
    "Department": "P",   # dePartment（D 占用）
    "CureWay":    "W",   # Way
    "Food":       "F",   # Food
    "Producer":   "M",   # Manufacturer
}

# 三元组里 head/tail 对应的实体类型
# head 固定是 Disease；tail 按关系类型不同
REL_TAIL_TYPE = {
    "has_symptom":     "Symptom",
    "need_check":      "Check",
    "belongs_to_dept": "Department",
    "common_drug":     "Drug",
    "recommand_drug":  "Drug",
    "do_eat":          "Food",
    "not_eat":         "Food",
    "recommand_eat":   "Food",
    "cure_way":        "CureWay",
    "acompany_with":   "Disease",
    "produced_by":     "Producer",
}


def load_entities():
    """从 entity_dict 读取 8 类实体（已去重）"""
    entities = {}
    for etype, prefix in ID_PREFIX.items():
        path = os.path.join(ENTITY_DIR, f"{etype}.txt")
        names = []
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                names = sorted(set(line.strip() for line in f if line.strip()))
        entities[etype] = names
    return entities


def load_synonyms():
    """读取同义词表 {类型: {标准名: [别名]}}"""
    if not os.path.exists(SYNONYM_PATH):
        return {}
    with open(SYNONYM_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    # 合并 disease/symptom/drug 三类
    merged = {}
    for cat in ("disease", "symptom", "drug"):
        if cat in data:
            # 类型名映射到实体类型
            type_map = {"disease": "Disease", "symptom": "Symptom", "drug": "Drug"}
            merged[type_map[cat]] = data[cat]
    return merged


def count_frequency():
    """统计每个实体名在三元组中的出现频次（消歧/重要性线索）"""
    freq = defaultdict(Counter)
    if not os.path.exists(TRIPLET_PATH):
        return freq
    with open(TRIPLET_PATH, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            tail_type = REL_TAIL_TYPE.get(row["relation"])
            if tail_type:
                freq[tail_type][row["tail"]] += 1
            freq["Disease"][row["head"]] += 1
    return freq


def assign_ids(entities, synonyms, freq):
    """为每个实体分配 ID，返回 {类型: {名称: {id, alias, freq}}}"""
    id_map = {}
    for etype, names in entities.items():
        prefix = ID_PREFIX[etype]
        syn = synonyms.get(etype, {})
        etype_freq = freq.get(etype, Counter())
        type_map = {}
        for idx, name in enumerate(names, 1):
            eid = f"{prefix}{idx:05d}"
            type_map[name] = {
                "id": eid,
                "alias": syn.get(name, []),
                "freq": etype_freq.get(name, 0),
            }
        id_map[etype] = type_map
    return id_map


def detect_cross_type_conflicts(id_map):
    """
    跨类型同名冲突检测：同一个名称出现在不同实体类型中
    （如某词既是症状又是疾病 = 潜在歧义）
    """
    name_to_types = defaultdict(set)
    for etype, mapping in id_map.items():
        for name in mapping:
            name_to_types[name].add(etype)
    conflicts = {name: sorted(ts) for name, ts in name_to_types.items() if len(ts) > 1}
    return conflicts


def build_triplets_with_id(id_map):
    """生成增强版三元组（名称 → ID）"""
    # 反向索引：{类型: {名称: id}}
    name2id = {t: {n: m["id"] for n, m in mp.items()} for t, mp in id_map.items()}

    out_path = os.path.join(OUTPUT_DIR, "triplets_with_id.csv")
    missing = 0
    total = 0
    with open(TRIPLET_PATH, "r", encoding="utf-8-sig") as fin, \
         open(out_path, "w", encoding="utf-8-sig", newline="") as fout:
        reader = csv.DictReader(fin)
        writer = csv.writer(fout)
        writer.writerow(["head_id", "head_name", "relation", "relation_cn",
                         "tail_id", "tail_name"])
        for row in reader:
            total += 1
            rel = row["relation"]
            tail_type = REL_TAIL_TYPE.get(rel)
            head_id = name2id.get("Disease", {}).get(row["head"], "")
            tail_id = ""
            if tail_type:
                tail_id = name2id.get(tail_type, {}).get(row["tail"], "")
            if not head_id or not tail_id:
                missing += 1
            writer.writerow([head_id, row["head"], rel, row["relation_cn"],
                             tail_id, row["tail"]])
    return total, missing, out_path


def gen_report(id_map, conflicts, triplet_total, triplet_missing):
    """生成 ID 分配报告"""
    lines = []
    lines.append("# 实体 ID 分配报告\n")
    lines.append("## 1. 分配规则\n")
    lines.append("- ID 前缀按实体类型语义命名，避免视觉混淆")
    lines.append("- 同类型内按**名称排序**后顺序分配，保证可复现")
    lines.append("- 格式：`前缀 + 5位数字`（如 D00001）\n")
    lines.append("| 实体类型 | ID前缀 | 含义 | 数量 |")
    lines.append("|----------|--------|------|------|")
    for etype, prefix in ID_PREFIX.items():
        lines.append(f"| {etype} | {prefix} | — | {len(id_map.get(etype,{}))} |")
    lines.append("")

    lines.append("## 2. 分配结果\n")
    lines.append("| 实体类型 | 实体数 | 带别名 | 最高频次 |")
    lines.append("|----------|--------|--------|---------|")
    for etype, mapping in id_map.items():
        with_alias = sum(1 for m in mapping.values() if m["alias"])
        max_freq = max((m["freq"] for m in mapping.values()), default=0)
        lines.append(f"| {etype} | {len(mapping)} | {with_alias} | {max_freq} |")
    lines.append("")

    lines.append("## 3. 跨类型同名冲突（消歧线索）\n")
    lines.append(f"共发现 **{len(conflicts)}** 个同名实体出现在多个类型中，"
                 "需在图谱建模时消歧：\n")
    lines.append("| 实体名称 | 出现的类型 |")
    lines.append("|----------|-----------|")
    for name, types in sorted(conflicts.items())[:30]:
        lines.append(f"| {name} | {'、'.join(types)} |")
    if len(conflicts) > 30:
        lines.append(f"| ... | 共 {len(conflicts)} 个 |")
    lines.append("")

    lines.append("## 4. 增强版三元组\n")
    lines.append(f"- 原始三元组：{triplet_total} 条")
    lines.append(f"- 成功映射 ID：{triplet_total - triplet_missing} 条 "
                 f"({(triplet_total-triplet_missing)/triplet_total*100:.2f}%)")
    lines.append(f"- 未映射（实体不在词典中）：{triplet_missing} 条\n")
    lines.append("**用途**：图谱组可直接用 `head_id`/`tail_id` 做节点主键入库，"
                 "无需自行维护名称→ID映射。\n")

    lines.append("## 5. 使用方式\n")
    lines.append("- **图谱组建库**：用 ID 作为 Neo4j 节点主键，"
                 "`name` 作为普通属性")
    lines.append("- **实体消歧**：跨类型同名冲突清单（第3节）需人工/规则确认归属")
    lines.append("- **重要性排序**：`freq` 字段表示实体被引用次数，"
                 "可用于推荐/排序")
    lines.append("- **同义词召回**：`alias` 字段可挂到节点上，"
                 "查询时 `WHERE x IN n.alias`")

    path = os.path.join(OUTPUT_DIR, "entity_id_report.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"[产物] ID分配报告 → {path}")


def main():
    print("=" * 60)
    print("实体 ID 分配")
    print("=" * 60)

    entities = load_entities()
    print("[读取] 实体类型：", {t: len(n) for t, n in entities.items()})

    synonyms = load_synonyms()
    print(f"[读取] 同义词：{sum(len(v) for v in synonyms.values())} 组")

    freq = count_frequency()
    print(f"[统计] 实体频次统计完成")

    id_map = assign_ids(entities, synonyms, freq)
    total_entities = sum(len(m) for m in id_map.values())
    print(f"[分配] 共分配 {total_entities} 个实体 ID")

    # 写 entity_id_map.json
    map_path = os.path.join(OUTPUT_DIR, "entity_id_map.json")
    with open(map_path, "w", encoding="utf-8") as f:
        json.dump(id_map, f, ensure_ascii=False, indent=2)
    print(f"[产物] entity_id_map.json → {map_path}")

    # 跨类型冲突检测
    conflicts = detect_cross_type_conflicts(id_map)
    print(f"[消歧] 跨类型同名冲突：{len(conflicts)} 个")

    # 增强版三元组
    triplet_total, triplet_missing, triplet_path = build_triplets_with_id(id_map)
    print(f"[产物] triplets_with_id.csv → {triplet_path}")
    print(f"        映射成功 {triplet_total-triplet_missing}/{triplet_total}")

    # 报告
    gen_report(id_map, conflicts, triplet_total, triplet_missing)

    print("=" * 60)
    print("完成！输出目录：", OUTPUT_DIR)
    print("=" * 60)


if __name__ == "__main__":
    main()
