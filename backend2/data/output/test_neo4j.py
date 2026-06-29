#!/usr/bin/env python3
# coding: utf-8
"""
Neo4j连接测试脚本
"""

import json
import os
from neo4j import GraphDatabase

NEO4J_CONFIG = {
    "uri": "bolt://localhost:7687",
    "user": "neo4j",
    "password": "12345678"
}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)

# 测试连接
driver = GraphDatabase.driver(NEO4J_CONFIG["uri"], auth=(NEO4J_CONFIG["user"], NEO4J_CONFIG["password"]))

with driver.session() as session:
    # 测试查询
    result = session.run("RETURN 1 as test")
    print("Neo4j连接测试成功:", result.single()["test"])

driver.close()
print("测试完成")