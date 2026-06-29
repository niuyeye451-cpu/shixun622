import sqlite3
import json
import os
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple, Any


class BaseGraphDatabase(ABC):

    @abstractmethod
    def execute(self, query: str, params: Any = None) -> List[Dict]:
        pass

    @abstractmethod
    def create_node(self, node_id: str, name: str, label: str, properties: Dict = None):
        pass

    @abstractmethod
    def create_relation(self, rel_id: str, source_id: str, target_id: str,
                        relation_type: str, relation_name: str = '', properties: Dict = None):
        pass

    @abstractmethod
    def get_node_by_id(self, node_id: str) -> Optional[Dict]:
        pass

    @abstractmethod
    def get_node_by_name(self, name: str, label: str = None) -> Optional[Dict]:
        pass

    @abstractmethod
    def search_nodes(self, keyword: str, label: str = None, limit: int = 10) -> List[Dict]:
        pass

    @abstractmethod
    def get_nodes_by_label(self, label: str, limit: int = 100) -> List[Dict]:
        pass

    @abstractmethod
    def get_relations_by_node(self, node_id: str, relation_type: str = None) -> List[Dict]:
        pass

    @abstractmethod
    def get_graph_by_disease(self, disease_name: str, max_depth: int = 2) -> Dict:
        pass

    @abstractmethod
    def get_node_relations(self, node_id: str) -> List[Dict]:
        pass

    @abstractmethod
    def get_path_between_nodes(self, source_id: str, target_id: str, max_depth: int = 3) -> List[List[Dict]]:
        pass

    @abstractmethod
    def get_statistics(self) -> Dict:
        pass

    @abstractmethod
    def clear_database(self):
        pass

    @abstractmethod
    def get_all_labels(self) -> List[str]:
        pass

    @abstractmethod
    def get_all_relation_types(self) -> List[str]:
        pass


class SQLiteGraphDatabase(BaseGraphDatabase):

    def __init__(self, db_path: str):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_tables()

    def _init_tables(self):
        conn = sqlite3.connect(self.db_path)
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
                properties TEXT DEFAULT '{}',
                FOREIGN KEY (source_id) REFERENCES nodes(id),
                FOREIGN KEY (target_id) REFERENCES nodes(id)
            )
        ''')

        cursor.execute('CREATE INDEX IF NOT EXISTS idx_nodes_label ON nodes(label)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_nodes_name ON nodes(name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_rels_source ON relationships(source_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_rels_target ON relationships(target_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_rels_type ON relationships(relation_type)')

        conn.commit()
        conn.close()

    def execute(self, sql: str, params: Tuple = ()) -> List[Dict]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(sql, params)
        conn.commit()
        results = cursor.fetchall()
        conn.close()
        return [dict(row) for row in results]

    def create_node(self, node_id: str, name: str, label: str, properties: Dict = None):
        props = json.dumps(properties or {})
        self.execute(
            'INSERT OR REPLACE INTO nodes (id, name, label, properties) VALUES (?, ?, ?, ?)',
            (node_id, name, label, props)
        )

    def create_relation(self, rel_id: str, source_id: str, target_id: str,
                        relation_type: str, relation_name: str = '', properties: Dict = None):
        props = json.dumps(properties or {})
        self.execute(
            'INSERT OR REPLACE INTO relationships (id, source_id, target_id, relation_type, relation_name, properties) VALUES (?, ?, ?, ?, ?, ?)',
            (rel_id, source_id, target_id, relation_type, relation_name, props)
        )

    def get_node_by_id(self, node_id: str) -> Optional[Dict]:
        results = self.execute('SELECT * FROM nodes WHERE id = ?', (node_id,))
        if results:
            node = results[0]
            node['properties'] = json.loads(node['properties'])
            return node
        return None

    def get_node_by_name(self, name: str, label: str = None) -> Optional[Dict]:
        if label:
            results = self.execute('SELECT * FROM nodes WHERE name = ? AND label = ?', (name, label))
        else:
            results = self.execute('SELECT * FROM nodes WHERE name = ?', (name,))
        if results:
            node = results[0]
            node['properties'] = json.loads(node['properties'])
            return node
        return None

    def search_nodes(self, keyword: str, label: str = None, limit: int = 10) -> List[Dict]:
        if label:
            results = self.execute(
                'SELECT * FROM nodes WHERE name LIKE ? AND label = ? LIMIT ?',
                (f'%{keyword}%', label, limit)
            )
        else:
            results = self.execute(
                'SELECT * FROM nodes WHERE name LIKE ? LIMIT ?',
                (f'%{keyword}%', limit)
            )
        for node in results:
            node['properties'] = json.loads(node['properties'])
        return results

    def get_nodes_by_label(self, label: str, limit: int = 100) -> List[Dict]:
        results = self.execute('SELECT * FROM nodes WHERE label = ? LIMIT ?', (label, limit))
        for node in results:
            node['properties'] = json.loads(node['properties'])
        return results

    def get_relations_by_node(self, node_id: str, relation_type: str = None) -> List[Dict]:
        if relation_type:
            results = self.execute(
                'SELECT * FROM relationships WHERE source_id = ? AND relation_type = ?',
                (node_id, relation_type)
            )
        else:
            results = self.execute(
                'SELECT * FROM relationships WHERE source_id = ?',
                (node_id,)
            )
        for rel in results:
            rel['properties'] = json.loads(rel['properties'])
        return results

    def get_graph_by_disease(self, disease_name: str, max_depth: int = 2) -> Dict:
        disease = self.get_node_by_name(disease_name, 'Disease')
        if not disease:
            search_results = self.search_nodes(disease_name, 'Disease', 1)
            if search_results:
                disease = search_results[0]
            else:
                return {'nodes': [], 'edges': [], 'center_node': None}

        visited = {disease['id']}
        nodes = [disease]
        edges = []
        queue = [(disease['id'], 0)]

        while queue:
            current_id, depth = queue.pop(0)
            if depth >= max_depth:
                continue

            relations = self.get_relations_by_node(current_id)
            for rel in relations:
                if rel['target_id'] not in visited:
                    target_node = self.get_node_by_id(rel['target_id'])
                    if target_node:
                        visited.add(rel['target_id'])
                        nodes.append(target_node)
                        edges.append(rel)
                        queue.append((rel['target_id'], depth + 1))

        return {
            'nodes': nodes,
            'edges': edges,
            'center_node': disease['id']
        }

    def get_node_relations(self, node_id: str) -> List[Dict]:
        results = self.execute(
            'SELECT * FROM relationships WHERE source_id = ? OR target_id = ?',
            (node_id, node_id)
        )
        for rel in results:
            rel['properties'] = json.loads(rel['properties'])
        return results

    def get_path_between_nodes(self, source_id: str, target_id: str, max_depth: int = 3) -> List[List[Dict]]:
        paths = []
        visited = {source_id}
        queue = [(source_id, [source_id])]

        while queue:
            current_id, path = queue.pop(0)
            if current_id == target_id:
                paths.append(path)
                continue
            if len(path) - 1 >= max_depth:
                continue

            relations = self.get_relations_by_node(current_id)
            for rel in relations:
                next_id = rel['target_id']
                if next_id not in visited:
                    visited.add(next_id)
                    queue.append((next_id, path + [next_id]))

        return paths

    def get_statistics(self) -> Dict:
        total_nodes = self.execute('SELECT COUNT(*) as count FROM nodes')[0]['count']
        total_rels = self.execute('SELECT COUNT(*) as count FROM relationships')[0]['count']

        label_stats = self.execute(
            'SELECT label, COUNT(*) as count FROM nodes GROUP BY label ORDER BY count DESC'
        )

        rel_type_stats = self.execute(
            'SELECT relation_type, COUNT(*) as count FROM relationships GROUP BY relation_type ORDER BY count DESC'
        )

        return {
            'total_nodes': total_nodes,
            'total_relationships': total_rels,
            'label_distribution': label_stats,
            'relation_distribution': rel_type_stats
        }

    def clear_database(self):
        self.execute('DELETE FROM relationships')
        self.execute('DELETE FROM nodes')

    def get_all_labels(self) -> List[str]:
        results = self.execute('SELECT DISTINCT label FROM nodes')
        return [r['label'] for r in results]

    def get_all_relation_types(self) -> List[str]:
        results = self.execute('SELECT DISTINCT relation_type FROM relationships')
        return [r['relation_type'] for r in results]


class Neo4jGraphDatabase(BaseGraphDatabase):

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
        "recommand_eat": "RECOMMAND_EAT",
        "produced_by": "PRODUCED_BY"
    }

    RELATION_MAP_REVERSE = {v: k for k, v in RELATION_MAP.items()}

    def __init__(self, uri: str, user: str, password: str, database: str = "neo4j"):
        from neo4j import GraphDatabase
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.database = database
        self._create_indexes()

    def _create_indexes(self):
        with self.driver.session(database=self.database) as session:
            for label in set(self.ID_PREFIX_TO_LABEL.values()):
                try:
                    session.run(f"CREATE INDEX {label.lower()}_id IF NOT EXISTS FOR (n:{label}) ON (n.id)")
                    session.run(f"CREATE INDEX {label.lower()}_name IF NOT EXISTS FOR (n:{label}) ON (n.name)")
                except Exception:
                    pass

    def close(self):
        self.driver.close()

    def _get_label_from_id(self, node_id: str) -> str:
        prefix = node_id[0] if node_id else ""
        return self.ID_PREFIX_TO_LABEL.get(prefix, "Entity")

    def _node_to_dict(self, node) -> Dict:
        props = dict(node)
        label = list(node.labels)[0] if node.labels else "Entity"
        return {
            'id': props.get('id', ''),
            'name': props.get('name', ''),
            'label': label,
            'properties': props,
            'freq': props.get('freq', 0)
        }

    def _rel_to_dict(self, rel, source_id: str = None, target_id: str = None) -> Dict:
        rel_type = rel.type
        original_type = self.RELATION_MAP_REVERSE.get(rel_type, rel_type.lower())
        props = dict(rel)
        return {
            'id': f"rel_{source_id}_{original_type}_{target_id}",
            'source_id': source_id,
            'target_id': target_id,
            'relation_type': original_type,
            'relation_name': props.get('name_cn', ''),
            'properties': props
        }

    def create_node(self, node_id: str, name: str, label: str, properties: Dict = None):
        props = properties or {}
        props_str = ", ".join([f"n.{k} = ${k}" for k in props.keys()])
        set_clause = f"SET n.name = $name, n.id = $id"
        if props_str:
            set_clause += ", " + props_str

        params = {"id": node_id, "name": name}
        params.update(props)

        with self.driver.session(database=self.database) as session:
            session.run(f"MERGE (n:{label} {{id: $id}}) {set_clause}", **params)

    def create_relation(self, rel_id: str, source_id: str, target_id: str,
                        relation_type: str, relation_name: str = '', properties: Dict = None):
        neo4j_rel = self.RELATION_MAP.get(relation_type, relation_type.upper())
        source_label = self._get_label_from_id(source_id)
        target_label = self._get_label_from_id(target_id)
        props = properties or {}
        props['name_cn'] = relation_name

        props_str = ", ".join([f"r.{k} = ${k}" for k in props.keys()])
        set_clause = f"SET {props_str}" if props_str else ""

        params = {"source_id": source_id, "target_id": target_id}
        params.update(props)

        with self.driver.session(database=self.database) as session:
            session.run(
                f"MATCH (s:{source_label} {{id: $source_id}}) "
                f"MATCH (t:{target_label} {{id: $target_id}}) "
                f"MERGE (s)-[r:{neo4j_rel}]->(t) "
                f"{set_clause}",
                **params
            )

    def get_node_by_id(self, node_id: str) -> Optional[Dict]:
        label = self._get_label_from_id(node_id)
        with self.driver.session(database=self.database) as session:
            result = session.run(
                f"MATCH (n:{label} {{id: $id}}) RETURN n",
                id=node_id
            )
            record = result.single()
            if record:
                return self._node_to_dict(record["n"])
            return None

    def get_node_by_name(self, name: str, label: str = None) -> Optional[Dict]:
        if label:
            query = f"MATCH (n:{label} {{name: $name}}) RETURN n LIMIT 1"
        else:
            query = "MATCH (n {name: $name}) RETURN n LIMIT 1"

        with self.driver.session(database=self.database) as session:
            result = session.run(query, name=name)
            record = result.single()
            if record:
                return self._node_to_dict(record["n"])
            return None

    def search_nodes(self, keyword: str, label: str = None, limit: int = 10) -> List[Dict]:
        if label:
            query = f"MATCH (n:{label}) WHERE n.name CONTAINS $keyword RETURN n LIMIT $limit"
        else:
            query = "MATCH (n) WHERE n.name CONTAINS $keyword RETURN n LIMIT $limit"

        results = []
        with self.driver.session(database=self.database) as session:
            result = session.run(query, keyword=keyword, limit=limit)
            for record in result:
                results.append(self._node_to_dict(record["n"]))
        return results

    def get_nodes_by_label(self, label: str, limit: int = 100) -> List[Dict]:
        results = []
        with self.driver.session(database=self.database) as session:
            result = session.run(
                f"MATCH (n:{label}) RETURN n LIMIT $limit",
                limit=limit
            )
            for record in result:
                results.append(self._node_to_dict(record["n"]))
        return results

    def get_relations_by_node(self, node_id: str, relation_type: str = None) -> List[Dict]:
        label = self._get_label_from_id(node_id)
        if relation_type:
            neo4j_rel = self.RELATION_MAP.get(relation_type, relation_type.upper())
            query = (
                f"MATCH (s:{label} {{id: $node_id}})-[r:{neo4j_rel}]->(t) "
                f"RETURN s, r, t"
            )
        else:
            query = (
                f"MATCH (s:{label} {{id: $node_id}})-[r]->(t) "
                f"RETURN s, r, t"
            )

        results = []
        with self.driver.session(database=self.database) as session:
            result = session.run(query, node_id=node_id)
            for record in result:
                source_id = record["s"]["id"]
                target_id = record["t"]["id"]
                results.append(self._rel_to_dict(record["r"], source_id, target_id))
        return results

    def get_graph_by_disease(self, disease_name: str, max_depth: int = 2) -> Dict:
        disease = self.get_node_by_name(disease_name, "Disease")
        if not disease:
            search_results = self.search_nodes(disease_name, "Disease", 1)
            if search_results:
                disease = search_results[0]
            else:
                return {'nodes': [], 'edges': [], 'center_node': None}

        disease_name = disease['name']

        query = (
            f"MATCH (d:Disease {{name: $name}})-[r*1..{max_depth}]->(n) "
            f"WITH DISTINCT d, n, r "
            f"MATCH (d)-[rels*1..{max_depth}]->(n) "
            f"RETURN DISTINCT d, n, rels"
        )

        nodes_dict = {}
        edges_set = set()
        edges_list = []
        center_node_id = None

        with self.driver.session(database=self.database) as session:
            result = session.run(query, name=disease_name)

            if not result.peek():
                disease = self.get_node_by_name(disease_name, "Disease")
                if not disease:
                    return {'nodes': [], 'edges': [], 'center_node': None}
                return {'nodes': [disease], 'edges': [], 'center_node': disease['id']}

            for record in result:
                d = record["d"]
                n = record["n"]
                rels = record["rels"]

                d_dict = self._node_to_dict(d)
                if d_dict['id'] not in nodes_dict:
                    nodes_dict[d_dict['id']] = d_dict
                    center_node_id = d_dict['id']

                n_dict = self._node_to_dict(n)
                if n_dict['id'] not in nodes_dict:
                    nodes_dict[n_dict['id']] = n_dict

                for i, rel in enumerate(rels):
                    source_id = list(rel.nodes)[0]["id"]
                    target_id = list(rel.nodes)[1]["id"]
                    edge_key = (source_id, target_id, rel.type)
                    if edge_key not in edges_set:
                        edges_set.add(edge_key)
                        edges_list.append(self._rel_to_dict(rel, source_id, target_id))

        return {
            'nodes': list(nodes_dict.values()),
            'edges': edges_list,
            'center_node': center_node_id
        }

    def get_node_relations(self, node_id: str) -> List[Dict]:
        label = self._get_label_from_id(node_id)
        query = (
            f"MATCH (s:{label} {{id: $node_id}})-[r_out]->(t_out) "
            f"RETURN s, r_out AS r, t_out AS t "
            f"UNION ALL "
            f"MATCH (t_in:{label} {{id: $node_id}})<-[r_in]-(s_in) "
            f"RETURN s_in AS s, r_in AS r, t_in AS t"
        )

        results = []
        with self.driver.session(database=self.database) as session:
            result = session.run(query, node_id=node_id)
            for record in result:
                source_id = record["s"]["id"]
                target_id = record["t"]["id"]
                results.append(self._rel_to_dict(record["r"], source_id, target_id))
        return results

    def get_path_between_nodes(self, source_id: str, target_id: str, max_depth: int = 3) -> List[List[Dict]]:
        source_label = self._get_label_from_id(source_id)
        target_label = self._get_label_from_id(target_id)

        query = (
            f"MATCH path = (s:{source_label} {{id: $source_id}})-[*1..{max_depth}]->(t:{target_label} {{id: $target_id}}) "
            f"RETURN nodes(path) AS path_nodes, relationships(path) AS path_rels "
            f"LIMIT 10"
        )

        paths = []
        with self.driver.session(database=self.database) as session:
            result = session.run(query, source_id=source_id, target_id=target_id)
            for record in result:
                path_nodes = [self._node_to_dict(n) for n in record["path_nodes"]]
                node_ids = [n['id'] for n in path_nodes]
                paths.append(node_ids)
        return paths

    def get_statistics(self) -> Dict:
        with self.driver.session(database=self.database) as session:
            total_nodes = session.run("MATCH (n) RETURN count(n) as count").single()["count"]
            total_rels = session.run("MATCH ()-[r]->() RETURN count(r) as count").single()["count"]

            label_result = session.run(
                "MATCH (n) "
                "RETURN labels(n)[0] as label, count(n) as count "
                "ORDER BY count DESC"
            )
            label_stats = [{"label": r["label"], "count": r["count"]} for r in label_result]

            rel_result = session.run(
                "MATCH ()-[r]->() "
                "RETURN type(r) as relation_type, count(r) as count "
                "ORDER BY count DESC"
            )
            rel_type_stats = [
                {
                    "relation_type": self.RELATION_MAP_REVERSE.get(r["relation_type"], r["relation_type"].lower()),
                    "count": r["count"]
                }
                for r in rel_result
            ]

            return {
                'total_nodes': total_nodes,
                'total_relationships': total_rels,
                'label_distribution': label_stats,
                'relation_distribution': rel_type_stats
            }

    def clear_database(self):
        with self.driver.session(database=self.database) as session:
            session.run("MATCH (n) DETACH DELETE n")

    def get_all_labels(self) -> List[str]:
        with self.driver.session(database=self.database) as session:
            result = session.run("MATCH (n) RETURN DISTINCT labels(n)[0] as label")
            return [r["label"] for r in result if r["label"]]

    def get_all_relation_types(self) -> List[str]:
        with self.driver.session(database=self.database) as session:
            result = session.run("MATCH ()-[r]->() RETURN DISTINCT type(r) as rel_type")
            return [
                self.RELATION_MAP_REVERSE.get(r["rel_type"], r["rel_type"].lower())
                for r in result
            ]

    def execute(self, cypher: str, params: Dict = None) -> List[Dict]:
        params = params or {}
        results = []
        with self.driver.session(database=self.database) as session:
            result = session.run(cypher, **params)
            for record in result:
                results.append(dict(record))
        return results


_graph_db_instance = None


def get_graph_db() -> BaseGraphDatabase:
    global _graph_db_instance
    if _graph_db_instance is None:
        graph_backend = os.getenv("GRAPH_BACKEND", "sqlite").lower()

        if graph_backend == "neo4j":
            uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
            user = os.getenv("NEO4J_USER", "neo4j")
            password = os.getenv("NEO4J_PASSWORD", "neo4j")
            database = os.getenv("NEO4J_DATABASE", "neo4j")
            _graph_db_instance = Neo4jGraphDatabase(uri, user, password, database)
        else:
            db_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                'db', 'graph.db'
            )
            _graph_db_instance = SQLiteGraphDatabase(db_path)

    return _graph_db_instance


def reset_graph_db():
    global _graph_db_instance
    if _graph_db_instance is not None and hasattr(_graph_db_instance, 'close'):
        _graph_db_instance.close()
    _graph_db_instance = None
