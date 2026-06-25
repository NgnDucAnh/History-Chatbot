import fitz  # Tên khi import của thư viện PyMuPDF
import re

def convert_pdf_to_clean_txt(pdf_path, output_txt_path):
    print(f"Đang đọc file PDF: {pdf_path} ...")
    
    try:
        doc = fitz.open(pdf_path)
        full_text = []

        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text = page.get_text()
            
            text = text.replace("Dit document is beschikbaar op", "")
            text = text.replace("studeersnel", "")
            text = text.replace("Scan to open on Studeersnel", "")
            text = text.replace("Studocu is not sponsored or endorsed by any college or university", "")
            
            text = re.sub(r'Downloaded by.*\(nguyenducanh277@gmail\.com\)', '', text)
            
            if text.strip():
                full_text.append(text)

        final_text = '\n\n'.join(full_text)
        
        final_text = re.sub(r'\n{3,}', '\n\n', final_text)

        with open(output_txt_path, 'w', encoding='utf-8') as f:
            f.write(final_text)

        print(f"THÀNH CÔNG! Đã chuyển đổi và dọn sạch rác PDF thành file: {output_txt_path}")
        
    except Exception as e:
        print(f"Lỗi khi xử lý PDF: {e}")

if __name__ == "__main__":
    input_pdf = "Việt Nam giai đoạn 54-75.pdf" 
    output_txt = "tai_lieu_dh_kinh_te_giai_doan_54_75.txt"
    
    convert_pdf_to_clean_txt(input_pdf, output_txt)