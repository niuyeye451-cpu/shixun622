#!/usr/bin/env python3
# coding: utf-8
"""
数据合并脚本
================================================================
功能：将新爬取的数据与原始 medical.json 合并

输入：
  - 原始数据：QASystemOnMedicalKG/data/medical.json（8808条）
  - 新数据：output/新数据爬取/new_medical.json（5条）

输出：
  - 合并数据：output/新数据爬取/medical_merged.json

处理逻辑：
  1. 读取原始数据和新数据
  2. 检查新数据格式是否正确
  3. 按疾病名去重（新疾病名不在原数据中才添加）
  4. 输出合并结果

用法：python merge_data.py
================================================================
"""

import json
import os
from collections import Counter

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(os.path.dirname(BASE_DIR))

# 输入文件路径
ORIGINAL_PATH = os.path.join(PROJECT_DIR, "QASystemOnMedicalKG", "data", "medical.json")
NEW_DATA_PATH = os.path.join(BASE_DIR, "new_medical.json")
OUTPUT_PATH = os.path.join(BASE_DIR, "medical_merged.json")

# 标准字段列表（用于格式验证）
STANDARD_FIELDS = [
    'name', 'desc', 'cause', 'prevent', 'symptom', 'cure_department',
    'cure_way', 'cure_lasttime', 'cured_prob', 'get_prob', 'get_way',
    'easy_get', 'acompany', 'check', 'common_drug', 'recommand_drug',
    'drug_detail', 'do_eat', 'not_eat', 'recommand_eat', 'cost_money',
    'yibao_status', 'category', '_id'
]


def load_jsonl(path):
    """加载 JSONL 文件"""
    records = []
    if not os.path.exists(path):
        print(f"[警告] 文件不存在: {path}")
        return records
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError as e:
                    print(f"[错误] JSON 解析失败: {e}")
    return records


def validate_format(records, source_name):
    """验证数据格式"""
    print(f"\n=== {source_name} 格式验证 ===")
    print(f"记录数: {len(records)}")
    
    if not records:
        return False
    
    # 检查字段完整性
    all_fields = set()
    for r in records:
        all_fields.update(r.keys())
    
    missing = set(STANDARD_FIELDS) - all_fields
    extra = all_fields - set(STANDARD_FIELDS)
    
    print(f"标准字段: {len(STANDARD_FIELDS)}")
    print(f"实际字段: {len(all_fields)}")
    print(f"缺失字段: {missing if missing else '无'}")
    print(f"多余字段: {extra if extra else '无'}")
    
    # 检查 name 字段是否存在且非空
    valid_count = sum(1 for r in records if r.get("name") and r["name"].strip())
    print(f"有效记录（有name）: {valid_count}/{len(records)}")
    
    return valid_count > 0


def merge_data(original, new_data):
    """合并数据，按疾病名去重"""
    print(f"\n=== 合并处理 ===")
    
    # 获取原始疾病名集合
    original_names = set(r["name"] for r in original if r.get("name"))
    print(f"原始疾病数: {len(original_names)}")
    
    # 筛选新数据（只添加不存在的疾病）
    added = []
    skipped = []
    for r in new_data:
        name = r.get("name", "").strip()
        if not name:
            skipped.append(("无名称", r))
        elif name in original_names:
            skipped.append(("已存在", name))
        else:
            added.append(r)
    
    print(f"新增疾病数: {len(added)}")
    print(f"跳过记录数: {len(skipped)}")
    
    if added:
        print(f"新增疾病列表: {[r['name'] for r in added]}")
    
    if skipped:
        print(f"跳过原因统计:")
        reason_count = Counter(s[0] for s in skipped)
        for reason, cnt in reason_count.items():
            print(f"  {reason}: {cnt}")
    
    # 合并结果
    merged = original + added
    
    return merged, added, skipped


def save_jsonl(records, path):
    """保存为 JSONL 格式"""
    with open(path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"[保存] {len(records)} 条 → {path}")


def main():
    print("=" * 60)
    print("数据合并脚本")
    print("=" * 60)
    
    # 1. 加载原始数据
    print(f"\n[读取] 原始数据: {ORIGINAL_PATH}")
    original = load_jsonl(ORIGINAL_PATH)
    if not original:
        print("[错误] 原始数据加载失败")
        return
    
    # 2. 加载新数据
    print(f"\n[读取] 新数据: {NEW_DATA_PATH}")
    new_data = load_jsonl(NEW_DATA_PATH)
    if not new_data:
        print("[错误] 新数据加载失败，请先运行 medical_spider.py")
        return
    
    # 3. 验证格式
    if not validate_format(original, "原始数据"):
        print("[错误] 原始数据格式不正确")
        return
    
    if not validate_format(new_data, "新数据"):
        print("[错误] 新数据格式不正确")
        return
    
    # 4. 合并数据
    merged, added, skipped = merge_data(original, new_data)
    
    # 5. 保存合并结果
    save_jsonl(merged, OUTPUT_PATH)
    
    # 6. 生成合并报告
    report_path = os.path.join(BASE_DIR, "merge_report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# 数据合并报告\n\n")
        f.write(f"- 原始数据: {len(original)} 条\n")
        f.write(f"- 新增数据: {len(added)} 条\n")
        f.write(f"- 跳过数据: {len(skipped)} 条\n")
        f.write(f"- 合并总数: {len(merged)} 条\n\n")
        f.write("## 新增疾病列表\n\n")
        for r in added:
            f.write(f"- {r['name']}\n")
        f.write("\n## 后续步骤\n\n")
        f.write("1. 运行 `preprocess.py` 清洗合并数据\n")
        f.write("2. 运行 `build_synonym.py` 挖掘同义词\n")
        f.write("3. 运行 `assign_entity_id.py` 分配ID\n")
    
    print(f"\n[生成] 合并报告: {report_path}")
    
    print("\n" + "=" * 60)
    print("合并完成！")
    print("=" * 60)
    print(f"\n下一步：")
    print(f"  1. 复制 medical_merged.json 替换原始 medical.json")
    print(f"  2. 或直接用 medical_merged.json 运行处理脚本")


if __name__ == "__main__":
    main()