import json
import csv
import os
import sys
import sqlite3
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def log_print(message):
    print(message)


def import_entity_nodes(db_path):
    entity_map_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'data', 'output', 'ID映射', 'entity_id_map.json'
    )
    
    with open(entity_map_path, 'r', encoding='utf-8') as f:
        entity_map = json.load(f)
    
    log_print(f'[加载] entity_id_map.json')
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    total_count = 0
    batch_size = 5000
    batch = []
    
    for label, entities in entity_map.items():
        if label == '_meta':
            continue
        
        count = 0
        for name, data in entities.items():
            entity_id = data.get('id', '')
            properties = json.dumps({
                'alias': data.get('alias', []),
                'freq': data.get('freq', 0)
            })
            batch.append((entity_id, name, label, properties))
            count += 1
            total_count += 1
            
            if len(batch) >= batch_size:
                cursor.executemany(
                    'INSERT OR REPLACE INTO nodes (id, name, label, properties) VALUES (?, ?, ?, ?)',
                    batch
                )
                conn.commit()
                batch = []
        
        if batch:
            cursor.executemany(
                'INSERT OR REPLACE INTO nodes (id, name, label, properties) VALUES (?, ?, ?, ?)',
                batch
            )
            conn.commit()
            batch = []
        
        log_print(f'[创建] {label}节点: {count}个')
    
    conn.close()
    log_print(f'[完成] 共创建 {total_count} 个节点')
    return total_count


def import_relationships(db_path):
    triplets_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'data', 'output', '核心数据', 'triplets_with_id.csv'
    )
    
    log_print(f'[加载] triplets_with_id.csv')
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    total_count = 0
    batch_size = 10000
    batch = []
    
    with open(triplets_path, 'r', encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            head_id = row['head_id']
            relation = row['relation']
            relation_cn = row['relation_cn']
            tail_id = row['tail_id']
            
            rel_id = f"rel_{head_id}_{relation}_{tail_id}"
            batch.append((rel_id, head_id, tail_id, relation, relation_cn, '{}'))
            
            total_count += 1
            if len(batch) >= batch_size:
                cursor.executemany(
                    'INSERT OR REPLACE INTO relationships (id, source_id, target_id, relation_type, relation_name, properties) VALUES (?, ?, ?, ?, ?, ?)',
                    batch
                )
                conn.commit()
                batch = []
                log_print(f'[进度] 已创建 {total_count} 条关系...')
    
    if batch:
        cursor.executemany(
            'INSERT OR REPLACE INTO relationships (id, source_id, target_id, relation_type, relation_name, properties) VALUES (?, ?, ?, ?, ?, ?)',
            batch
        )
        conn.commit()
    
    conn.close()
    log_print(f'[完成] 共创建 {total_count} 条关系')
    return total_count


def import_disease_attributes(db_path):
    medical_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'data', 'output', '核心数据', 'medical_clean.json'
    )
    
    log_print(f'[加载] medical_clean.json')
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    total_count = 0
    
    with open(medical_path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                disease = json.loads(line.strip())
                name = disease.get('name', '')
                if not name:
                    continue
                
                cursor.execute('SELECT id, properties FROM nodes WHERE name = ? AND label = ?', (name, 'Disease'))
                row = cursor.fetchone()
                if not row:
                    continue
                
                node_id, existing_props_str = row
                existing_props = json.loads(existing_props_str)
                
                properties = {
                    'desc': disease.get('desc', ''),
                    'cause': disease.get('cause', ''),
                    'prevent': disease.get('prevent', ''),
                    'cure_department': disease.get('cure_department', []),
                    'category': disease.get('category', []),
                    'cured_prob': disease.get('cured_prob', ''),
                    'get_prob': disease.get('get_prob', 0),
                    'cost_money': disease.get('cost_money', []),
                    'cure_lasttime': disease.get('cure_lasttime', ''),
                    'yibao_status': disease.get('yibao_status', ''),
                    'get_way': disease.get('get_way', ''),
                    'easy_get': disease.get('easy_get', '')
                }
                
                existing_props.update(properties)
                
                cursor.execute('UPDATE nodes SET properties = ? WHERE id = ?', (json.dumps(existing_props), node_id))
                
                total_count += 1
                if total_count % 2000 == 0:
                    conn.commit()
                    log_print(f'[进度] 已处理 {total_count} 个疾病属性...')
            
            except json.JSONDecodeError:
                pass
    
    conn.commit()
    conn.close()
    log_print(f'[完成] 共更新 {total_count} 个疾病节点属性')
    return total_count


def verify_import(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM nodes')
    total_nodes = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM relationships')
    total_rels = cursor.fetchone()[0]
    
    log_print(f'\n[验证] 导入结果统计:')
    log_print(f'  节点总数: {total_nodes}')
    log_print(f'  关系总数: {total_rels}')
    
    log_print(f'\n  各类节点数量:')
    cursor.execute('SELECT label, COUNT(*) FROM nodes GROUP BY label ORDER BY COUNT(*) DESC')
    for label, count in cursor.fetchall():
        log_print(f'    {label}: {count}个')
    
    log_print(f'\n  各类关系数量:')
    cursor.execute('SELECT relation_type, COUNT(*) FROM relationships GROUP BY relation_type ORDER BY COUNT(*) DESC')
    for rel_type, count in cursor.fetchall():
        log_print(f'    {rel_type}: {count}条')
    
    cursor.execute('SELECT id, properties FROM nodes WHERE name = ? AND label = ?', ('感冒', 'Disease'))
    row = cursor.fetchone()
    if row:
        node_id, props_str = row
        props = json.loads(props_str)
        log_print(f'\n  示例查询: 感冒')
        log_print(f'    ID: {node_id}')
        log_print(f'    属性: {list(props.keys())}')
        
        cursor.execute('SELECT target_id FROM relationships WHERE source_id = ? AND relation_type = ? LIMIT 5', (node_id, 'has_symptom'))
        symptom_ids = [r[0] for r in cursor.fetchall()]
        if symptom_ids:
            placeholders = ','.join('?' * len(symptom_ids))
            cursor.execute(f'SELECT name FROM nodes WHERE id IN ({placeholders})', symptom_ids)
            symptoms = [r[0] for r in cursor.fetchall()]
            log_print(f'    症状: {", ".join(symptoms)}')
    
    conn.close()


def init_tables(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS nodes (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            label TEXT NOT NULL,
            properties TEXT DEFAULT '{}',
            freq INTEGER DEFAULT 0
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS relationships (
            id TEXT PRIMARY KEY,
            source_id TEXT NOT NULL,
            target_id TEXT NOT NULL,
            relation_type TEXT NOT NULL,
            relation_name TEXT DEFAULT '',
            properties TEXT DEFAULT '{}'
        )
    ''')
    
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_nodes_label ON nodes(label)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_nodes_name ON nodes(name)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_rels_source ON relationships(source_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_rels_target ON relationships(target_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_rels_type ON relationships(relation_type)')
    
    conn.commit()
    conn.close()


def main():
    log_print('=' * 60)
    log_print('知识图谱数据导入')
    log_print('=' * 60)
    
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'db', 'graph.db')
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    log_print(f'\n[初始化] 数据库路径: {db_path}')
    init_tables(db_path)
    
    log_print('\n[步骤1] 创建节点...')
    import_entity_nodes(db_path)
    
    log_print('\n[步骤2] 创建关系...')
    import_relationships(db_path)
    
    log_print('\n[步骤3] 添加疾病属性...')
    import_disease_attributes(db_path)
    
    log_print('\n[步骤4] 验证导入结果...')
    verify_import(db_path)
    
    log_print('\n' + '=' * 60)
    log_print('全部导入完成！')
    log_print('=' * 60)


if __name__ == '__main__':
    main()
