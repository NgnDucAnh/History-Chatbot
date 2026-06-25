import json
import os
from openai import OpenAI
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

URI = os.getenv("NEO4J_URI")
USER = os.getenv("NEO4J_USERNAME")
PWD = os.getenv("NEO4J_PASSWORD")
driver = GraphDatabase.driver(URI, auth=(USER, PWD))

def get_embedding(text):
    """Hàm biến văn bản tiếng Việt thành mảng 1536 con số"""
    response = client.embeddings.create(
        input=text,
        model="text-embedding-3-small" 
    )
    return response.data[0].embedding

def import_chunks_to_neo4j():
    with open('processed_chunks.json', 'r', encoding='utf-8') as f:
        chunks = json.load(f)

    with driver.session() as session:
        print("Đang thiết lập cấu trúc Vector Index trên Neo4j...")
        session.run("""
            CREATE VECTOR INDEX chunk_vector IF NOT EXISTS
            FOR (c:Chunk) ON (c.embedding)
            OPTIONS {indexConfig: {
              `vector.dimensions`: 1536,
              `vector.similarity_function`: 'cosine'
            }}
        """)
        
        print(f"Tổng số chunks cần đẩy: {len(chunks)}")
        print(" Bắt đầu nạp đạn Vector...\n")

        for i, chunk in enumerate(chunks):
            chunk_id = chunk.get('chunk_id')
            text = chunk.get('text')

            print(f"--- Đang nhúng Vector cho Chunk {chunk_id} ({i+1}/{len(chunks)}) ---")
            
            try:
                vector_data = get_embedding(text)
                
                session.run("""
                    MERGE (c:Chunk {id: $chunk_id})
                    SET c.text = $text, c.embedding = $embedding
                """, chunk_id=chunk_id, text=text, embedding=vector_data)
                
            except Exception as e:
                print(f"Lỗi ở chunk {chunk_id}: {e}")

        print("\n HOÀN TẤT! Đã đẩy thành công toàn bộ Vector lên Database!")

if __name__ == "__main__":
    import_chunks_to_neo4j()
    driver.close()