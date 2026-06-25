import json
from google import genai
from google.genai import types
import time


extraction_prompt = """
Bạn là một chuyên gia về Lịch sử Việt Nam và Đồ thị tri thức (Knowledge Graph).
Nhiệm vụ của bạn là đọc đoạn văn bản sau và trích xuất các Thực thể (Nodes) và Mối quan hệ (Edges).

QUY TẮC TRÍCH XUẤT:
1. Thực thể (Nodes): Chỉ lấy Nhân vật, Địa danh, Tổ chức, Sự kiện, Vũ khí.
2. Mối quan hệ (Edges): Phải có hướng (Từ Node A -> Node B) và mô tả hành động.
3. CẤU TRÚC JSON YÊU CẦU:
{
  "nodes": [
    {"id": "Tên thực thể", "type": "Person/Location/Organization/Event"}
  ],
  "edges": [
    {"source": "Tên thực thể A", "target": "Tên thực thể B", "relation": "LOẠI_QUAN_HỆ"}
  ]
}

Đoạn văn bản cần xử lý:
"[TEXT_PLACEHOLDER]"
"""

def extract_graph_from_chunks():
    with open('processed_chunks.json', 'r', encoding='utf-8') as f:
        chunks = json.load(f)
        
    print(f"Tổng số chunks cần xử lý: {len(chunks)}")
    print("Bắt đầu cắm máy chạy trích xuất toàn bộ dữ liệu...\n")

    extracted_graphs = []

    for i in range(len(chunks)):
        chunk_text = chunks[i]['text']
        print(f"--- Đang xử lý Chunk {i+1}/{len(chunks)} ---")
        
        prompt = extraction_prompt.replace("[TEXT_PLACEHOLDER]", chunk_text)
        
        try:
            response = client.models.generate_content(
                model='gemini-flash-latest',
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                )
            )
            
            result = response.text.strip()
            
            extracted_graphs.append({
                "chunk_id": chunks[i]['chunk_id'],
                "source": chunks[i]['source'],
                "graph_data": json.loads(result)
            })
            
            print(f"Thành công chunk {i+1}!")
            
            if (i + 1) % 10 == 0:
                with open('extracted_graph_data_backup.json', 'w', encoding='utf-8') as backup_file:
                    json.dump(extracted_graphs, backup_file, ensure_ascii=False, indent=4)
                print(f"Đã tự động sao lưu an toàn tới chunk {i+1}...")
            
            time.sleep(3) 
            
        except Exception as e:
            print(f"Lỗi ở chunk {i+1}: {e}")
            if 'response' in locals() and hasattr(response, 'text'):
                 print(f"Dữ liệu rác gây lỗi: {response.text}")

    with open('extracted_graph_data.json', 'w', encoding='utf-8') as f:
        json.dump(extracted_graphs, f, ensure_ascii=False, indent=4)
        
    print("\n HOÀN THÀNH XUẤT SẮC! Toàn bộ đồ thị đã được lưu vào 'extracted_graph_data.json'!")

if __name__ == "__main__":
    extract_graph_from_chunks()