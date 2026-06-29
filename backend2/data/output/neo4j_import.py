#!/usr/bin/env python3
# coding: utf-8
"""
Neo4j知识图谱导入脚本
================================================================
功能：
  1. 从entity_id_map.json创建所有节点
  2. 从triplets_with_id.csv创建所有关系
  3. 从medical_clean.json添加疾病节点属性

数据来源：
  - entity_id_map.json: 44650个实体ID映射
  - triplets_with_id.csv: 459387条三元组
  - medical_clean.json: 8807条疾病完整数据
================================================================
"""

import json
import csv
import os
import sys
from neo4j import GraphDatabase
from datetime import datetime
from collections import defaultdict

# 日志文件输出
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "neo4j_import.log")

def log_print(message):
    """同时输出到控制台和日志文件"""
    print(message)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(message + "\n")

# Neo4j配置
NEO4J_CONFIG = {
    "uri": "bolt://localhost:7687",  # Neo4j连接地址
    "user": "neo4j",                  # 用户名
    "password": "12345678"              # 密码（请修改为你的密码）
}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)

# 实体类型映射（ID前缀 -> Neo4j节点标签）
ID_PREFIX_TO_LABEL = {
    "D": "Disease",       # 疾病
    "S": "Symptom",       # 症状
    "G": "Drug",          # 药品（G代表Drug）
    "C": "Check",         # 检查项目
    "P": "Department",    # 科室（P代表科室）
    "W": "CureWay",       # 治疗方式
    "F": "Food",          # 食物
    "R": "Recipe",        # 推荐食谱
    "M": "Producer"       # 药品厂商
}

# 关系类型映射（CSV关系名 -> Neo4j关系类型）
RELATION_MAP = {
    "has_symptom": "HAS_SYMPTOM",
    "acompany_with": "ACOMPANY_WITH",
    "belongs_to_dept": "BELONGS_TO_DEPT",
    "common_drug": "COMMON_DRUG",
    "recommand_drug": "RECOMMAND_DRUG",
    "cure_way": "CURE_WAY",
    "need_check": "NEED_CHECK",
    "do_eat": "DO_EAT",
    "not_eat": "NOT_EAT",
    "recommand_eat": "RECOMMAND_EAT"
}


class Neo4jImporter:
    """Neo4j数据导入器"""
    
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        log_print(f"[连接] Neo4j数据库: {uri}")
    
    def close(self):
        self.driver.close()
    
    def clear_database(self):
        """清空数据库（可选）"""
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
            log_print("[清空] 数据库已清空")
    
    # ============================================================
    # 步骤1：创建节点
    # ============================================================
    def create_nodes(self):
        """从entity_id_map.json创建所有节点"""
        
        # 加载entity_id_map.json
        entity_id_map_path = os.path.join(PROJECT_DIR, "output", "ID映射", "entity_id_map.json")
        with open(entity_id_map_path, "r", encoding="utf-8") as f:
            entity_id_map = json.load(f)
        
        log_print(f"[加载] entity_id_map.json")
        
        total_count = 0
        with self.driver.session() as session:
            for entity_type, entities in entity_id_map.items():
                if entity_type == "_meta":
                    continue
                
                # 确定Neo4j节点标签
                label = entity_type  # Disease, Symptom, Drug, etc.
                
                count = 0
                for name, data in entities.items():
                    entity_id = data.get("id", "")
                    alias = data.get("alias", [])
                    freq = data.get("freq", 0)
                    
                    # 创建节点
                    session.run(
                        f"MERGE (n:{label} {{id: $id}}) "
                        f"SET n.name = $name, n.alias = $alias, n.freq = $freq",
                        id=entity_id,
                        name=name,
                        alias=alias,
                        freq=freq
                    )
                    count += 1
                    total_count += 1
                
                log_print(f"[创建] {label}节点: {count}个")
        
        log_print(f"[完成] 共创建 {total_count} 个节点")
        return total_count
    
    # ============================================================
    # 步骤2：创建关系
    # ============================================================
    def create_relations(self):
        """从triplets_with_id.csv创建所有关系"""
        
        triplets_path = os.path.join(PROJECT_DIR, "output", "核心数据", "triplets_with_id.csv")
        
        log_print(f"[加载] triplets_with_id.csv")
        
        total_count = 0
        relation_stats = defaultdict(int)
        
        with self.driver.session() as session:
            with open(triplets_path, "r", encoding="utf-8-sig", newline='') as f:
                reader = csv.DictReader(f)
                
                # 检查列名是否存在
                if 'head_id' not in reader.fieldnames:
                    log_print(f"[错误] CSV列名不匹配，实际列名: {reader.fieldnames}")
                    return 0
                
                batch_size = 1000
                batch = []
                
                for row in reader:
                    head_id = row["head_id"]
                    head_name = row["head_name"]
                    relation = row["relation"]
                    relation_cn = row["relation_cn"]
                    tail_id = row["tail_id"]
                    tail_name = row["tail_name"]
                    
                    # 确定尾实体标签（根据ID前缀）
                    tail_prefix = tail_id[0] if tail_id else ""
                    tail_label = ID_PREFIX_TO_LABEL.get(tail_prefix, "Entity")
                    
                    # 确定Neo4j关系类型
                    neo4j_relation = RELATION_MAP.get(relation, relation.upper())
                    
                    # 创建关系
                    try:
                        session.run(
                            f"MATCH (h:Disease {{id: $head_id}}) "
                            f"MATCH (t:{tail_label} {{id: $tail_id}}) "
                            f"MERGE (h)-[r:{neo4j_relation}]->(t) "
                            f"SET r.name_cn = $relation_cn",
                            head_id=head_id,
                            tail_id=tail_id,
                            relation_cn=relation_cn
                        )
                        
                        relation_stats[relation] += 1
                        total_count += 1
                        
                        if total_count % 50000 == 0:
                            log_print(f"[进度] 已创建 {total_count} 条关系...")
                    
                    except Exception as e:
                        log_print(f"[错误] 关系创建失败: {head_name} -> {tail_name}, {e}")
        
        log_print(f"\n[统计] 各类型关系数量:")
        for rel, count in sorted(relation_stats.items(), key=lambda x: x[1], reverse=True):
            log_print(f"  {rel}: {count}条")
        
        log_print(f"[完成] 共创建 {total_count} 条关系")
        return total_count
    
    # ============================================================
    # 步骤3：添加疾病属性
    # ============================================================
    def add_disease_attributes(self):
        """从medical_clean.json添加疾病节点属性"""
        
        medical_path = os.path.join(PROJECT_DIR, "output", "核心数据", "medical_clean.json")
        
        log_print(f"[加载] medical_clean.json")
        
        total_count = 0
        
        with self.driver.session() as session:
            with open(medical_path, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        disease = json.loads(line.strip())
                        name = disease.get("name", "")
                        
                        if not name:
                            continue
                        
                        # 提取属性
                        attrs = {
                            "desc": disease.get("desc", ""),
                            "cause": disease.get("cause", ""),
                            "prevent": disease.get("prevent", ""),
                            "cure_department": disease.get("cure_department", []),
                            "category": disease.get("category", []),
                            "cured_prob": disease.get("cured_prob", ""),
                            "get_prob": disease.get("get_prob", 0),
                            "cost_money": disease.get("cost_money", []),
                            "cure_lasttime": disease.get("cure_lasttime", ""),
                            "yibao_status": disease.get("yibao_status", ""),
                            "get_way": disease.get("get_way", ""),
                            "easy_get": disease.get("easy_get", "")
                        }
                        
                        # 更新节点属性
                        session.run(
                            "MATCH (d:Disease {name: $name}) "
                            "SET d.desc = $desc, "
                            "    d.cause = $cause, "
                            "    d.prevent = $prevent, "
                            "    d.cure_department = $cure_department, "
                            "    d.category = $category, "
                            "    d.cured_prob = $cured_prob, "
                            "    d.get_prob = $get_prob, "
                            "    d.cost_money = $cost_money, "
                            "    d.cure_lasttime = $cure_lasttime, "
                            "    d.yibao_status = $yibao_status, "
                            "    d.get_way = $get_way, "
                            "    d.easy_get = $easy_get",
                            name=name,
                            **attrs
                        )
                        
                        total_count += 1
                        
                        if total_count % 2000 == 0:
                            log_print(f"[进度] 已处理 {total_count} 个疾病属性...")
                    
                    except json.JSONDecodeError as e:
                        log_print(f"[错误] JSON解析失败: {e}")
                    except Exception as e:
                        log_print(f"[错误] 属性添加失败: {e}")
        
        log_print(f"[完成] 共更新 {total_count} 个疾病节点属性")
        return total_count
    
    # ============================================================
    # 验证导入结果
    # ============================================================
    def verify_import(self):
        """验证导入结果"""
        
        log_print(f"\n[验证] 导入结果统计:")
        
        with self.driver.session() as session:
            # 统计节点总数
            result = session.run("MATCH (n) RETURN count(n) as total")
            total_nodes = result.single()["total"]
            log_print(f"  节点总数: {total_nodes}")
            
            # 统计各类节点
            result = session.run(
                "MATCH (n) "
                "RETURN labels(n)[0] as label, count(n) as count "
                "ORDER BY count DESC"
            )
            log_print(f"\n  各类节点数量:")
            for record in result:
                log_print(f"    {record['label']}: {record['count']}个")
            
            # 统计关系总数
            result = session.run("MATCH ()-[r]->() RETURN count(r) as total")
            total_rels = result.single()["total"]
            log_print(f"\n  关系总数: {total_rels}")
            
            # 统计各类关系
            result = session.run(
                "MATCH ()-[r]->() "
                "RETURN type(r) as type, count(r) as count "
                "ORDER BY count DESC"
            )
            log_print(f"\n  各类关系数量:")
            for record in result:
                log_print(f"    {record['type']}: {record['count']}条")
            
            # 查询示例：感冒的症状
            result = session.run(
                "MATCH (d:Disease {name: '感冒'})-[:HAS_SYMPTOM]->(s:Symptom) "
                "RETURN s.name as symptom LIMIT 5"
            )
            log_print(f"\n  示例查询: 感冒的症状")
            symptoms = [r["symptom"] for r in result]
            log_print(f"    {', '.join(symptoms)}")


def main():
    """主流程"""
    
    log_print("=" * 60)
    log_print("Neo4j知识图谱数据导入")
    log_print("=" * 60)
    
    # 提示
    log_print("\n[提示] 请确保:")
    log_print("  1. Neo4j已启动（默认端口: bolt://localhost:7687）")
    log_print("  2. 用户名密码正确（请在脚本中修改 NEO4J_CONFIG）")
    log_print("  3. 已安装neo4j Python驱动（pip install neo4j）")
    
    try:
        # 创建导入器
        importer = Neo4jImporter(
            NEO4J_CONFIG["uri"],
            NEO4J_CONFIG["user"],
            NEO4J_CONFIG["password"]
        )
        
        # 步骤1: 创建节点
        log_print("\n[步骤1] 创建节点...")
        importer.create_nodes()
        
        # 步骤2: 创建关系
        log_print("\n[步骤2] 创建关系...")
        importer.create_relations()
        
        # 步骤3: 添加疾病属性
        log_print("\n[步骤3] 添加疾病属性...")
        importer.add_disease_attributes()
        
        # 验证导入结果
        log_print("\n[步骤4] 验证导入结果...")
        importer.verify_import()
        
        # 关闭连接
        importer.close()
        
        log_print("\n" + "=" * 60)
        log_print("全部导入完成！")
        log_print("=" * 60)
        
        log_print("\n[下一步] 你可以在Neo4j Browser中执行查询:")
        log_print("  MATCH (d:Disease {name: '感冒'})-[:HAS_SYMPTOM]->(s) RETURN s.name")
        log_print("  MATCH (d:Disease {name: '感冒'})-[:COMMON_DRUG]->(g) RETURN g.name")
    
    except Exception as e:
        log_print(f"\n[错误] {e}")
        log_print("[提示] 请检查:")
        log_print("  1. Neo4j是否已启动")
        log_print("  2. 连接地址是否正确")
        log_print("  3. 用户名密码是否正确")
        log_print("  4. neo4j Python驱动是否已安装（pip install neo4j）")


if __name__ == "__main__":
    main()