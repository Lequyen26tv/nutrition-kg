import os
import sys
import re
import pickle
import numpy as np
import faiss
from PyPDF2 import PdfReader
from docx import Document
from sentence_transformers import SentenceTransformer

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(os.path.dirname(CURRENT_DIR))
if BACKEND_DIR not in sys.path:
    sys.path.append(BACKEND_DIR)

from app.db.neo4j_connection import neo4j_db
DATA_DIR = os.path.join(os.path.dirname(BACKEND_DIR), "data")
INDEX_PATH = os.path.join(DATA_DIR, "vector_db.index")
METADATA_PATH = os.path.join(DATA_DIR, "metadata.pkl")

class MedicalTextIngestionService:
    def __init__(self):
        print("-> Đang nạp mô hình nhúng văn bản y khoa multilingual-e5-base...")
        self.model = SentenceTransformer('intfloat/multilingual-e5-base')
        self.db = neo4j_db
        self.forbidden_keywords = ['thuốc', 'insulin', 'metformin', 'amlodipin', 'viên nén', 'biệt dược', 'tiêm', 'kê đơn']

    def contains_medication(self, text):
        text_for_check = text.lower().replace("không dùng thuốc", "an_toan_tiet_che").replace("không điều trị bằng thuốc", "an_toan_tiet_che")
        for kw in self.forbidden_keywords:
            if re.search(r'\b' + re.escape(kw) + r'\b', text_for_check): return True
        return False

    def read_pdf(self, file_path):
        text = ""
        reader = PdfReader(file_path)
        for page in reader.pages:
            content = page.extract_text()
            if content: text += content + "\n"
        return text

    def read_docx(self, file_path):
        doc = Document(file_path)
        return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])

    def chunk_text(self, text, chunk_size=800, overlap=100):
        text = re.sub(r'\s+', ' ', text).strip()
        sentences = re.split(r'(?<=[.!?])\s+', text)
        chunks, current_chunk = [], ""
        for sentence in sentences:
            if len(current_chunk) + len(sentence) <= chunk_size: current_chunk += sentence + " "
            else:
                if current_chunk.strip(): chunks.append(current_chunk.strip())
                current_chunk = sentence + " "
        if current_chunk.strip(): chunks.append(current_chunk.strip())
        return chunks

    def process_and_ingest(self):
        print("🚀 [Script 3] Khởi động luồng quét tệp y văn động từ thư mục data...")
        all_files = os.listdir(DATA_DIR)
        files_to_process = []
        for f_name in all_files:
            f_lower = f_name.lower()
            if "huong dan" in f_lower and f_lower.endswith(".pdf"): files_to_process.append({"name": f_name, "type": "pdf", "disease_id": "both"})
            elif "che_do_dinh_duong" in f_lower and f_lower.endswith(".pdf"): files_to_process.append({"name": f_name, "type": "pdf", "disease_id": "disease_dtd"})
            elif "tha" in f_lower and f_lower.endswith(".docx"): files_to_process.append({"name": f_name, "type": "docx", "disease_id": "disease_tha"})
            elif "dtd" in f_lower and f_lower.endswith(".docx"): files_to_process.append({"name": f_name, "type": "docx", "disease_id": "disease_dtd"})
            elif "tang huyet ap" in f_lower and f_lower.endswith(".docx"): files_to_process.append({"name": f_name, "type": "docx", "disease_id": "disease_tha"})

        print(f"📋 Tìm thấy {len(files_to_process)} tệp tài liệu y văn phù hợp.")
        all_chunks_metadata, all_embeddings = [], []

        with self.db.get_session() as session:
            for f_info in files_to_process:
                file_path = os.path.join(DATA_DIR, f_info["name"])
                print(f"📖 Đang bóc tách chữ từ tệp: {f_info['name']}")
                session.run("MATCH (c:Chunk {source: $source}) DETACH DELETE c", source=f_info["name"])

                raw_text = self.read_pdf(file_path) if f_info["type"] == "pdf" else self.read_docx(file_path)
                raw_chunks = self.chunk_text(raw_text)

                file_valid_count = 0
                for chunk_text in raw_chunks:
                    if self.contains_medication(chunk_text): continue
                    chunk_id = f"chunk_{f_info['name'].replace(' ', '_')}_{file_valid_count}"
                    file_valid_count += 1

                    session.run("MERGE (c:Chunk {id: $chunk_id}) SET c.content = $content, c.source = $source", chunk_id=chunk_id, content=chunk_text, source=f_info["name"])

                    if f_info["disease_id"] in ["disease_dtd", "both"]:
                        session.run("MATCH (c:Chunk {id: $chunk_id}), (d:Disease {id: 'disease_dtd'}) MERGE (c)-[:KIE_THUC_VE]->(d)", chunk_id=chunk_id)
                    if f_info["disease_id"] in ["disease_tha", "both"]:
                        session.run("MATCH (c:Chunk {id: $chunk_id}), (d:Disease {id: 'disease_tha'}) MERGE (c)-[:KIE_THUC_VE]->(d)", chunk_id=chunk_id)

                    all_chunks_metadata.append({"id": chunk_id, "content": chunk_text, "metadata": {"source": f_info["name"], "type": "Medical_Literature"}})
                    all_embeddings.append(self.model.encode(f"passage: {chunk_text}"))
                print(f"   ➔ Trích xuất thành công {file_valid_count} đoạn y văn sạch.")

        if all_embeddings:
            embeddings_np = np.array(all_embeddings).astype('float32')
            index = faiss.IndexFlatL2(embeddings_np.shape[1])
            index.add(embeddings_np)
            faiss.write_index(index, INDEX_PATH)
            with open(METADATA_PATH, "wb") as f: pickle.dump(all_chunks_metadata, f)
            print("🎯 [SUCCESS - SCRIPT 3] Đã lập chỉ mục Vector FAISS và nạp cấu trúc y văn!")

if __name__ == "__main__":
    MedicalTextIngestionService().process_and_ingest()