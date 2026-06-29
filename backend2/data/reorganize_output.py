#!/usr/bin/env python3
# coding: utf-8
"""
重新组织 output 目录结构
================================================================
功能：
  1. 创建中文文件夹，按数据功能分类
  2. 移动文件到对应文件夹
  3. 拆分 Food.txt 为三个文件（宜吃/忌吃/推荐食谱）

目录结构：
  output/
  ├── 核心数据/         medical_clean.json, triplets.csv, triplets_with_id.csv
  ├── 实体词典/         8类实体词典 + Food拆分文件
  ├── 同义词表/         synonym 相关文件
  ├── ID映射/           entity_id_map.json
  ├── 数据报告/         各种 report + mapping 文档
================================================================
"""

import os
import shutil
import csv
from collections import defaultdict

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

# 新目录结构（中文命名）
NEW_DIRS = {
    "核心数据": "medical_clean.json, triplets.csv, triplets_with_id.csv",
    "实体词典": "entity_dict 及拆分的 Food 文件",
    "同义词表": "synonym 相关文件",
    "ID映射": "entity_id_map.json",
    "数据报告": "各种 md 文档",
}

# 文件移动映射
FILE_MAP = {
    "核心数据": ["medical_clean.json", "triplets.csv", "triplets_with_id.csv"],
    "实体词典": [],  # 特殊处理
    "同义词表": ["synonym.json", "synonym_alias.json", "synonym_full.json", "synonym_report.md"],
    "ID映射": ["entity_id_map.json"],
    "数据报告": ["data_entity_mapping.md", "data_quality_report.md", "entity_id_report.md", "task_summary_report.md"],
}


def split_food_dict():
    """从 triplets.csv 拆分 Food 为 宜吃/忌吃/推荐食谱"""
    do_eat = set()
    not_eat = set()
    recommand_eat = set()
    
    triplet_path = os.path.join(OUTPUT_DIR, "triplets.csv")
    if not os.path.exists(triplet_path):
        print("[警告] triplets.csv 不存在，跳过 Food 拆分")
        return
    
    with open(triplet_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rel = row["relation"]
            tail = row["tail"]
            if rel == "do_eat":
                do_eat.add(tail)
            elif rel == "not_eat":
                not_eat.add(tail)
            elif rel == "recommand_eat":
                recommand_eat.add(tail)
    
    # 写入三个文件
    entity_dir = os.path.join(OUTPUT_DIR, "实体词典")
    os.makedirs(entity_dir, exist_ok=True)
    
    for name, data in [("宜吃食物.txt", do_eat), ("忌吃食物.txt", not_eat), ("推荐食谱.txt", recommand_eat)]:
        path = os.path.join(entity_dir, name)
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(sorted(data)))
        print(f"[拆分] {name}: {len(data)} 个 → {path}")
    
    return len(do_eat), len(not_eat), len(recommand_eat)


def reorganize():
    """重新组织目录结构"""
    print("=" * 60)
    print("重新组织 output 目录结构")
    print("=" * 60)
    
    # 1. 创建新目录
    for dir_name in NEW_DIRS:
        dir_path = os.path.join(OUTPUT_DIR, dir_name)
        os.makedirs(dir_path, exist_ok=True)
        print(f"[创建] {dir_name}/")
    
    # 2. 拆分 Food 词典
    do_cnt, not_cnt, rec_cnt = split_food_dict()
    
    # 3. 移动普通文件
    for dir_name, files in FILE_MAP.items():
        if not files:
            continue
        dir_path = os.path.join(OUTPUT_DIR, dir_name)
        for fn in files:
            src = os.path.join(OUTPUT_DIR, fn)
            dst = os.path.join(dir_path, fn)
            if os.path.exists(src):
                shutil.move(src, dst)
                print(f"[移动] {fn} → {dir_name}/")
    
    # 4. 处理实体词典（移动 entity_dict 内容，保留原目录结构）
    old_entity_dir = os.path.join(OUTPUT_DIR, "entity_dict")
    new_entity_dir = os.path.join(OUTPUT_DIR, "实体词典")
    
    if os.path.exists(old_entity_dir):
        for fn in os.listdir(old_entity_dir):
            src = os.path.join(old_entity_dir, fn)
            dst = os.path.join(new_entity_dir, fn)
            if os.path.exists(src) and not os.path.exists(dst):
                shutil.copy(src, dst)
        # 删除旧目录
        shutil.rmtree(old_entity_dir)
        print(f"[整理] entity_dict/ 内容已合并到 实体词典/")
    
    # 5. 删除临时文件
    temp_file = os.path.join(OUTPUT_DIR, "_mapping_stats.json")
    if os.path.exists(temp_file):
        os.remove(temp_file)
        print("[清理] _mapping_stats.json")
    
    # 6. 生成目录说明文件
    readme_path = os.path.join(OUTPUT_DIR, "目录说明.txt")
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write("output 目录结构说明\n")
        f.write("=" * 50 + "\n\n")
        f.write("核心数据/\n")
        f.write("  - medical_clean.json     清洗后的疾病数据（8807条）\n")
        f.write("  - triplets.csv           三元组（45.9万条，名称版）\n")
        f.write("  - triplets_with_id.csv   三元组（ID版，图谱组直接用）\n\n")
        f.write("实体词典/\n")
        f.write("  - Disease.txt            疾病词典（8807个）\n")
        f.write("  - Symptom.txt            症状词典（5995个）\n")
        f.write("  - Drug.txt               药品词典（3828个）\n")
        f.write("  - Check.txt              检查项目词典（3353个）\n")
        f.write("  - Department.txt         科室词典（54个）\n")
        f.write("  - CureWay.txt            治疗方式词典（544个）\n")
        f.write("  - Producer.txt           药品厂商词典（17201个）\n")
        f.write("  - Food.txt               全部食物名称（4868个）\n")
        f.write("  - 宜吃食物.txt           宜吃食物（{}个）\n".format(do_cnt))
        f.write("  - 忌吃食物.txt           忌吃食物（{}个）\n".format(not_cnt))
        f.write("  - 推荐食谱.txt           推荐食谱（{}个）\n\n".format(rec_cnt))
        f.write("同义词表/\n")
        f.write("  - synonym_full.json      完整同义词词典\n")
        f.write("  - synonym_alias.json     别名→标准名映射（问答召回用）\n")
        f.write("  - synonym_report.md      同义词挖掘报告\n\n")
        f.write("ID映射/\n")
        f.write("  - entity_id_map.json     44650个实体ID映射（节点主键）\n\n")
        f.write("数据报告/\n")
        f.write("  - data_entity_mapping.md  数据-实体映射交接文档\n")
        f.write("  - data_quality_report.md  数据质量报告\n")
        f.write("  - entity_id_report.md     实体ID分配报告\n")
        f.write("  - task_summary_report.md  任务总结报告\n")
    print(f"[生成] 目录说明.txt")
    
    print("=" * 60)
    print("完成！新目录结构：", OUTPUT_DIR)
    print("=" * 60)


if __name__ == "__main__":
    reorganize()