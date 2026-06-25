import json
import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

URI = os.getenv("NEO4J_URI")
USER = os.getenv("NEO4J_USERNAME")
PWD = os.getenv("NEO4J_PASSWORD")

class HistoryGraphImporter:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def import_data(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            data_list = json.load(f)

        with self.driver.session() as session:
            for item in data_list:
                chunk_id = item['chunk_id']
                graph_data = item['graph_data']
                
                print(f"Đang đưa dữ liệu từ Chunk {chunk_id} lên Neo4j...")
                session.execute_write(self._create_graph, graph_data)

    @staticmethod
    def _create_graph(tx, data):
        for node in data.get('nodes', []):
            tx.run("""
                MERGE (n:Entity {id: $id})
                SET n.type = $type, n.name = $id
            """, id=node['id'], type=node['type'])

        for edge in data.get('edges', []):
            rel_type = edge['relation'].upper().replace(" ", "_").replace(",", "").replace("-", "_")
            
            query = f"""
                MATCH (a:Entity {{id: $source}})
                MATCH (b:Entity {{id: $target}})
                MERGE (a)-[r:`{rel_type}`]->(b)
            """
            tx.run(query, source=edge['source'], target=edge['target'])

if __name__ == "__main__":
    importer = HistoryGraphImporter(URI, USER, PWD)
    try:
        importer.import_data('extracted_graph_data.json')
        print("\n Đã đẩy toàn bộ dữ liệu lịch sử lên Đồ thị tri thức thành công!")
    except Exception as e:
        print(f" Lỗi: {e}")
    finally:
        importer.close()