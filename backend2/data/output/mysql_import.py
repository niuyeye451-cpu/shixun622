#!/usr/bin/env python3
# coding: utf-8
"""
MySQL数据库创建与数据导入脚本
================================================================
功能：
  1. 创建数据库 medical_knowledge
  2. 创建同义词表（按提供的表结构）
  3. 从output数据导入同义词记录

数据库表结构：
  - 同义词表：synonyms

数据来源：
  - synonym_alias.json: 2232条别名→标准名映射
  - synonym_full.json: 用于确定entity_type
================================================================
"""

import json
import os
import pymysql
from datetime import datetime
from collections import defaultdict

# 数据库配置
DB_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "123456",  # MySQL密码
    "charset": "utf8mb4"
}

DB_NAME = "medical_knowledge"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)

# ============================================================
# 创建数据库和表
# ============================================================
def create_database():
    """创建数据库"""
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    # 创建数据库
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
    print(f"[创建] 数据库 {DB_NAME}")
    
    conn.commit()
    conn.close()


def create_tables():
    """创建同义词表"""
    conn = pymysql.connect(**DB_CONFIG, database=DB_NAME)
    cursor = conn.cursor()
    
    # 创建同义词表
    create_sql = """
    CREATE TABLE IF NOT EXISTS synonyms (
        id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY COMMENT '同义词记录唯一标识',
        colloquial_term VARCHAR(256) NOT NULL COMMENT '口语化/非标准表达',
        standard_term VARCHAR(256) NOT NULL COMMENT '标准医学术语',
        entity_type ENUM('DISEASE','SYMPTOM','DRUG','EXAMINATION','DEPARTMENT','POPULATION','OTHER') NOT NULL COMMENT '术语所属实体类型',
        synonym_type ENUM('COLLOQUIAL','ABBREVIATION','MISSPELLING','REGIONAL','ENGLISH') NOT NULL DEFAULT 'COLLOQUIAL' COMMENT '同义关系类型',
        verified TINYINT(1) DEFAULT 0 COMMENT '是否经专家审核确认',
        usage_count INT UNSIGNED DEFAULT 0 COMMENT '历史命中次数',
        source ENUM('MANUAL','IMPORT','AUTO_EXTRACT') DEFAULT 'AUTO_EXTRACT' COMMENT '数据来源',
        created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
        updated_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3) COMMENT '更新时间',
        INDEX idx_colloquial (colloquial_term),
        INDEX idx_standard (standard_term),
        INDEX idx_entity_type (entity_type)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='医学术语同义词映射表';
    """
    
    cursor.execute(create_sql)
    print(f"[创建] 表 synonyms")
    
    conn.commit()
    conn.close()


# ============================================================
# 数据准备
# ============================================================
def load_synonym_data():
    """加载同义词数据并补充entity_type"""
    
    # 1. 加载 synonym_full.json（确定entity_type）
    synonym_full_path = os.path.join(PROJECT_DIR, "output", "同义词表", "synonym_full.json")
    with open(synonym_full_path, "r", encoding="utf-8") as f:
        synonym_full = json.load(f)
    
    # 构建标准名->实体类型映射
    std_to_type = {}
    for category, data in synonym_full.items():
        if category == "_meta":
            continue
        if category == "disease":
            entity_type = "DISEASE"
        elif category == "symptom":
            entity_type = "SYMPTOM"
        elif category == "drug":
            entity_type = "DRUG"
        else:
            entity_type = "OTHER"
        
        if isinstance(data, dict):
            for std_name in data.keys():
                std_to_type[std_name] = entity_type
    
    print(f"[加载] synonym_full.json: {len(std_to_type)} 个标准名->实体类型映射")
    
    # 2. 加载 synonym_alias.json（别名->标准名）
    synonym_alias_path = os.path.join(PROJECT_DIR, "output", "同义词表", "synonym_alias.json")
    with open(synonym_alias_path, "r", encoding="utf-8") as f:
        synonym_alias = json.load(f)
    
    print(f"[加载] synonym_alias.json: {len(synonym_alias)} 条别名映射")
    
    # 3. 合成完整记录
    records = []
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    for colloquial, standard in synonym_alias.items():
        # 确定entity_type
        entity_type = std_to_type.get(standard, "OTHER")
        
        # 确定synonym_type（简单规则）
        synonym_type = "COLLOQUIAL"  # 默认口语表达
        
        # 判断是否为英文缩写
        if colloquial.isalpha() and colloquial.isupper():
            synonym_type = "ABBREVIATION"
        # 判断是否包含英文
        elif any(c.isalpha() and ord(c) < 128 for c in colloquial):
            synonym_type = "ENGLISH"
        
        records.append({
            "colloquial_term": colloquial,
            "standard_term": standard,
            "entity_type": entity_type,
            "synonym_type": synonym_type,
            "verified": 0,
            "usage_count": 0,
            "source": "AUTO_EXTRACT",
            "created_at": now,
            "updated_at": now
        })
    
    return records


# ============================================================
# 数据导入
# ============================================================
def import_synonyms(records):
    """导入同义词数据"""
    conn = pymysql.connect(**DB_CONFIG, database=DB_NAME)
    cursor = conn.cursor()
    
    # 清空表（可选）
    cursor.execute("TRUNCATE TABLE synonyms")
    print(f"[清空] 表 synonyms")
    
    # 批量插入
    insert_sql = """
    INSERT INTO synonyms 
    (colloquial_term, standard_term, entity_type, synonym_type, verified, usage_count, source, created_at, updated_at)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    
    batch_size = 500
    total = len(records)
    
    for i in range(0, total, batch_size):
        batch = records[i:i+batch_size]
        values = [
            (r["colloquial_term"], r["standard_term"], r["entity_type"], 
             r["synonym_type"], r["verified"], r["usage_count"], r["source"],
             r["created_at"], r["updated_at"])
            for r in batch
        ]
        cursor.executemany(insert_sql, values)
        conn.commit()
        print(f"[导入] {min(i+batch_size, total)}/{total} 条")
    
    conn.close()
    print(f"[完成] 共导入 {total} 条同义词记录")


# ============================================================
# 验证导入结果
# ============================================================
def verify_import():
    """验证导入结果"""
    conn = pymysql.connect(**DB_CONFIG, database=DB_NAME)
    cursor = conn.cursor()
    
    # 统计总数
    cursor.execute("SELECT COUNT(*) FROM synonyms")
    total = cursor.fetchone()[0]
    print(f"\n[验证] 总记录数: {total}")
    
    # 统计各实体类型
    cursor.execute("SELECT entity_type, COUNT(*) FROM synonyms GROUP BY entity_type")
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]} 条")
    
    # 统计各同义词类型
    cursor.execute("SELECT synonym_type, COUNT(*) FROM synonyms GROUP BY synonym_type")
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]} 条")
    
    # 显示示例
    cursor.execute("SELECT colloquial_term, standard_term, entity_type, synonym_type FROM synonyms LIMIT 5")
    print(f"\n[示例] 前5条记录:")
    for row in cursor.fetchall():
        print(f"  '{row[0]}' -> '{row[1]}' ({row[2]}, {row[3]})")
    
    conn.close()


# ============================================================
# 主流程
# ============================================================
def main():
    print("=" * 60)
    print("MySQL数据库创建与数据导入")
    print("=" * 60)
    
    # 提示输入密码
    print("\n[提示] 如果MySQL需要密码，请在脚本中修改 DB_CONFIG['password']")
    
    try:
        # 1. 创建数据库
        print("\n[步骤1] 创建数据库...")
        create_database()
        
        # 2. 创建表
        print("\n[步骤2] 创建表...")
        create_tables()
        
        # 3. 加载数据
        print("\n[步骤3] 加载数据...")
        records = load_synonym_data()
        
        # 4. 导入数据
        print("\n[步骤4] 导入数据...")
        import_synonyms(records)
        
        # 5. 验证
        print("\n[步骤5] 验证导入结果...")
        verify_import()
        
        print("\n" + "=" * 60)
        print("全部完成！")
        print("=" * 60)
        
    except pymysql.Error as e:
        print(f"\n[错误] MySQL错误: {e}")
        print("[提示] 请检查:")
        print("  1. MySQL是否已启动")
        print("  2. 用户名密码是否正确")
        print("  3. 是否有创建数据库的权限")
    except Exception as e:
        print(f"\n[错误] {e}")


if __name__ == "__main__":
    main()