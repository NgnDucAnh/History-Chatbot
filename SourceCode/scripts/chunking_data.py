import os
import json
from langchain_text_splitters import RecursiveCharacterTextSplitter

def process_and_chunk_all_txt_files():
    text_splitter = RecursiveCharacterTextSplitter(
        separators=["\n\n", "\n", ".", " "], 
        chunk_size=800,       
        chunk_overlap=150,   
        length_function=len
    )

    all_chunks = []
    chunk_counter = 0

    print("Đang quét các file dữ liệu...")
    for filename in os.listdir('.'):
        if filename.endswith('.txt'):
            print(f"Đang xử lý file: {filename}")
            
            with open(filename, 'r', encoding='utf-8') as f:
                document_text = f.read()

            if not document_text.strip():
                print(f"  -> File {filename} trống, bỏ qua.")
                continue

            chunks = text_splitter.split_text(document_text)
            
            for chunk in chunks:
                chunk_counter += 1
                all_chunks.append({
                    "chunk_id": chunk_counter,
                    "source": filename,
                    "text": chunk
                })

    output_file = 'processed_chunks.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_chunks, f, ensure_ascii=False, indent=4)

    print("-" * 40)
    print(f"HOÀN THÀNH! Đã cắt được tổng cộng {chunk_counter} đoạn (chunks).")
    print(f"Toàn bộ dữ liệu đã được lưu gọn gàng vào file: {output_file}")

if __name__ == "__main__":
    process_and_chunk_all_txt_files()