#!/usr/bin/env python3
# coding: utf-8
"""
Neo4j知识图谱数据导入脚本
将data/output中的数据导入到Neo4j数据库
"""

import json
import csv
import os
import sys
from collections import defaultdict
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "neo4j_import.log")

def log_print(message):
    print(message)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}\n")


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data", "output")

ID_PREFIX_TO_LABEL = {
    "D": "Disease",
    "S": "Symptom",
    "G": "Drug",
    "C": "Check",
    "P": "Department",
    "W": "CureWay",
    "F": "Food",
    "R": "Recipe",
    "M": "Producer"
}

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

    def __init__(self, uri, user, password, database="neo4j"):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.database = database
        log_print(f"[连接] Neo4j数据库: {uri}")
        self._test_connection()

    def _test_connection(self):
        try:
            with self.driver.session(database=self.database) as session:
                result = session.run("RETURN 1 as test")
                result.single()
                log_print("[验证] 数据库连接成功")
        except Exception as e:
            log_print(f"[错误] 数据库连接失败: {e}")
            raise

    def close(self):
        self.driver.close()

    def create_indexes(self):
        log_print("[索引] 创建索引...")
        with self.driver.session(database=self.database) as session:
            for label in set(ID_PREFIX_TO_LABEL.values()):
                try:
                    session.run(f"CREATE INDEX {label.lower()}_id IF NOT EXISTS FOR (n:{label}) ON (n.id)")
                    session.run(f"CREATE INDEX {label.lower()}_name IF NOT EXISTS FOR (n:{label}) ON (n.name)")
                    log_print(f"  - {label} 索引创建完成")
                except Exception as e:
                    log_print(f"  - {label} 索引跳过: {e}")
        log_print("[索引] 索引创建完成")

    def clear_database(self):
        log_print("[清空] 正在清空数据库...")
        with self.driver.session(database=self.database) as session:
            session.run("MATCH (n) DETACH DELETE n")
        log_print("[清空] 数据库已清空")

    def create_nodes(self):
        entity_map_path = os.path.join(DATA_DIR, "ID映射", "entity_id_map.json")
        with open(entity_map_path, "r", encoding="utf-8") as f:
            entity_map = json.load(f)

        log_print(f"[加载] entity_id_map.json")

        total_count = 0

        with self.driver.session(database=self.database) as session:
            for entity_type, entities in entity_map.items():
                if entity_type == "_meta":
                    continue

                label = entity_type
                count = 0
                batch = []

                for name, data in entities.items():
                    entity_id = data.get("id", "")
                    alias = data.get("alias", [])
                    freq = data.get("freq", 0)

                    batch.append({
                        "id": entity_id,
                        "name": name,
                        "alias": alias,
                        "freq": freq
                    })
                    count += 1
                    total_count += 1

                    if len(batch) >= 1000:
                        self._batch_create_nodes(session, label, batch)
                        batch = []

                if batch:
                    self._batch_create_nodes(session, label, batch)

                log_print(f"[创建] {label}节点: {count}个")

        log_print(f"[完成] 共创建 {total_count} 个节点")
        return total_count

    def _batch_create_nodes(self, session, label, batch):
        session.run(
            f"UNWIND $batch AS item "
            f"MERGE (n:{label} {{id: item.id}}) "
            f"SET n.name = item.name, n.alias = item.alias, n.freq = item.freq",
            batch=batch
        )

    def create_relations(self):
        triplets_path = os.path.join(DATA_DIR, "核心数据", "triplets_with_id.csv")

        log_print(f"[加载] triplets_with_id.csv")

        total_count = 0
        relation_stats = defaultdict(int)
        batch = []

        with self.driver.session(database=self.database) as session:
            with open(triplets_path, "r", encoding="utf-8-sig", newline='') as f:
                reader = csv.DictReader(f)

                for row in reader:
                    head_id = row["head_id"]
                    head_name = row["head_name"]
                    relation = row["relation"]
                    relation_cn = row["relation_cn"]
                    tail_id = row["tail_id"]
                    tail_name = row["tail_name"]

                    tail_prefix = tail_id[0] if tail_id else ""
                    tail_label = ID_PREFIX_TO_LABEL.get(tail_prefix, "Entity")

                    neo4j_relation = RELATION_MAP.get(relation, relation.upper())

                    batch.append({
                        "head_id": head_id,
                        "tail_id": tail_id,
                        "tail_label": tail_label,
                        "relation": neo4j_relation,
                        "relation_cn": relation_cn
                    })

                    relation_stats[relation] += 1
                    total_count += 1

                    if len(batch) >= 2000:
                        self._batch_create_relations(session, batch)
                        batch = []

                    if total_count % 50000 == 0:
                        log_print(f"[进度] 已创建 {total_count} 条关系...")

            if batch:
                self._batch_create_relations(session, batch)

        log_print(f"\n[统计] 各类型关系数量:")
        for rel, count in sorted(relation_stats.items(), key=lambda x: x[1], reverse=True):
            log_print(f"  {rel}: {count}条")

        log_print(f"[完成] 共创建 {total_count} 条关系")
        return total_count

    def _batch_create_relations(self, session, batch):
        for item in batch:
            try:
                session.run(
                    f"MATCH (h:Disease {{id: $head_id}}) "
                    f"MATCH (t:{item['tail_label']} {{id: $tail_id}}) "
                    f"MERGE (h)-[r:{item['relation']}]->(t) "
                    f"SET r.name_cn = $relation_cn",
                    head_id=item["head_id"],
                    tail_id=item["tail_id"],
                    relation_cn=item["relation_cn"]
                )
            except Exception as e:
                pass

    def add_disease_attributes(self):
        medical_path = os.path.join(DATA_DIR, "核心数据", "medical_clean.json")

        log_print(f"[加载] medical_clean.json")

        total_count = 0
        batch = []

        with self.driver.session(database=self.database) as session:
            with open(medical_path, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        disease = json.loads(line.strip())
                        name = disease.get("name", "")

                        if not name:
                            continue

                        attrs = {
                            "name": name,
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

                        batch.append(attrs)
                        total_count += 1

                        if len(batch) >= 500:
                            self._batch_update_disease_attrs(session, batch)
                            batch = []

                        if total_count % 2000 == 0:
                            log_print(f"[进度] 已处理 {total_count} 个疾病属性...")

                    except json.JSONDecodeError:
                        pass

            if batch:
                self._batch_update_disease_attrs(session, batch)

        log_print(f"[完成] 共更新 {total_count} 个疾病节点属性")
        return total_count

    def _sanitize(self, val):
        """Flatten complex types to JSON strings so Neo4j accepts them."""
        if isinstance(val, (dict, list)):
            return json.dumps(val, ensure_ascii=False)
        return val

    def _batch_update_disease_attrs(self, session, batch):
        for item in batch:
            item["cure_department"] = self._sanitize(item.get("cure_department", []))
            item["category"] = self._sanitize(item.get("category", []))
            item["cost_money"] = self._sanitize(item.get("cost_money", []))
            item["cure_lasttime"] = self._sanitize(item.get("cure_lasttime", ""))
            item["get_prob"] = self._sanitize(item.get("get_prob", 0))
        session.run(
            "UNWIND $batch AS item "
            "MATCH (d:Disease {name: item.name}) "
            "SET d.desc = item.desc, "
            "    d.cause = item.cause, "
            "    d.prevent = item.prevent, "
            "    d.cure_department = item.cure_department, "
            "    d.category = item.category, "
            "    d.cured_prob = item.cured_prob, "
            "    d.get_prob = item.get_prob, "
            "    d.cost_money = item.cost_money, "
            "    d.cure_lasttime = item.cure_lasttime, "
            "    d.yibao_status = item.yibao_status, "
            "    d.get_way = item.get_way, "
            "    d.easy_get = item.easy_get",
            batch=batch
        )

    def verify_import(self):
        log_print(f"\n[验证] 导入结果统计:")

        with self.driver.session(database=self.database) as session:
            result = session.run("MATCH (n) RETURN count(n) as total")
            total_nodes = result.single()["total"]
            log_print(f"  节点总数: {total_nodes}")

            result = session.run(
                "MATCH (n) "
                "RETURN labels(n)[0] as label, count(n) as count "
                "ORDER BY count DESC"
            )
            log_print(f"\n  各类节点数量:")
            for record in result:
                log_print(f"    {record['label']}: {record['count']}个")

            result = session.run("MATCH ()-[r]->() RETURN count(r) as total")
            total_rels = result.single()["total"]
            log_print(f"\n  关系总数: {total_rels}")

            result = session.run(
                "MATCH ()-[r]->() "
                "RETURN type(r) as type, count(r) as count "
                "ORDER BY count DESC"
            )
            log_print(f"\n  各类关系数量:")
            for record in result:
                log_print(f"    {record['type']}: {record['count']}条")

            result = session.run(
                "MATCH (d:Disease {name: '感冒'})-[:HAS_SYMPTOM]->(s:Symptom) "
                "RETURN s.name as symptom LIMIT 5"
            )
            log_print(f"\n  示例查询: 感冒的症状")
            symptoms = [r["symptom"] for r in result]
            log_print(f"    {', '.join(symptoms)}")


def main():
    log_print("=" * 60)
    log_print("Neo4j知识图谱数据导入")
    log_print("=" * 60)

    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "neo4j")
    database = os.getenv("NEO4J_DATABASE", "neo4j")

    log_print(f"\n[配置]")
    log_print(f"  URI: {uri}")
    log_print(f"  用户: {user}")
    log_print(f"  数据库: {database}")

    try:
        importer = Neo4jImporter(uri, user, password, database)

        log_print("\n[步骤0] 创建索引...")
        importer.create_indexes()

        log_print("\n[步骤1] 创建节点...")
        importer.create_nodes()

        log_print("\n[步骤2] 创建关系...")
        importer.create_relations()

        log_print("\n[步骤3] 添加疾病属性...")
        importer.add_disease_attributes()

        log_print("\n[步骤4] 验证导入结果...")
        importer.verify_import()

        importer.close()

        log_print("\n" + "=" * 60)
        log_print("全部导入完成！")
        log_print("=" * 60)

        log_print("\n[下一步]")
        log_print("  1. 修改 .env 中 GRAPH_BACKEND=neo4j")
        log_print("  2. 启动后端服务: python main.py")
        log_print("  3. 访问 http://localhost:8000/docs 查看API文档")
        log_print("  4. 在Neo4j Browser中执行查询验证:")
        log_print("     MATCH (d:Disease {name: '感冒'})-[r]->(n) RETURN d, r, n")

    except Exception as e:
        log_print(f"\n[错误] {e}")
        log_print("[排查]")
        log_print("  1. Neo4j是否已启动? 访问 http://localhost:7474 检查")
        log_print("  2. 连接地址是否正确? 当前: " + uri)
        log_print("  3. 用户名密码是否正确?")
        log_print("  4. neo4j Python驱动是否已安装? pip install neo4j")
        sys.exit(1)


if __name__ == "__main__":
    main()
