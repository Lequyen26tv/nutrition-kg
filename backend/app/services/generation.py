import os
import sys
import requests
import re # Đảm bảo đã import thư viện regex

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(os.path.dirname(CURRENT_DIR))

if BACKEND_DIR not in sys.path:
    sys.path.append(BACKEND_DIR)

from app.services.retrieval import retrieval_service


class NutritionGenerationService:
    def __init__(self):
        self.api_key = os.getenv("LLM_API_KEY", "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")
        self.api_url = os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1/chat/completions")
        self.model_name = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
        self.retrieval = retrieval_service

        # 🛡️ Danh sách từ khóa thuốc
        self.drug_keywords = [
            'thuốc', 'insulin', 'metformin', 'amlodipin', 'losartan', 'glucophage',
            'viên nén', 'kê đơn', 'biệt dược', 'tiêm', 'dược phẩm', 'uống liều'
        ]
        # Danh sách bệnh ngoài phạm vi
        self.unsupported_diseases = [
            'dạ dày', 'gút', 'gout', 'gan', 'thận', 'ung thư', 'xương khớp',
            'ho', 'sốt', 'cảm cúm', 'đau đầu', 'covid'
        ]

    def _clean_and_normalize_text(self, text: str) -> str:
        """ Bộ tiền xử lý dọn dẹp viết tắt (Đưa lên làm lõi chung) """
        t = text.lower()
        abbreviations = {
            r'\btha\b': 'tăng huyết áp',
            r'\bha\b': 'huyết áp',
            r'\bđtđ\b': 'đái tháo đường',
            r'\bdc\b': 'được',
            r'\bkh\b': 'không',
            r'\bbx\b': 'bác sĩ'
        }
        for pattern, replacement in abbreviations.items():
            t = re.sub(pattern, replacement, t)
        return t

    def _apply_clinical_guardrails(self, q_clean: str):
        # (Giữ nguyên phần quét từ khóa thuốc drug_keywords ở trên...)

        # Cấu hình bộ từ khóa mục tiêu mở rộng cho lá chắn
        diabetes_keywords = ["tiểu đường", "đái tháo đường", "đường huyết", "tăng đường", "hạ đường", "lượng đường"]
        hypertension_keywords = ["huyết áp", "tăng huyết áp", "cao huyết áp", "lên máu", "hạ huyết áp", "áp huyết"]

        has_target_disease = any(kw in q_clean for kw in diabetes_keywords) or any(kw in q_clean for kw in hypertension_keywords)

        if not has_target_disease:
            for disease in self.unsupported_diseases:
                if re.search(rf'\b{disease}\b', q_clean):
                    return (
                        "ℹ️ **THÔNG BÁO PHẠM VI HỆ THỐNG:**\n"
                        f"Hệ thống hiện tại chỉ hỗ trợ tư vấn chuyên sâu cho hai bệnh lý nền: "
                        "**Đái tháo đường** và **Tăng huyết áp**.\n\n"
                        f"Câu hỏi của bạn chứa từ khóa liên quan đến ({disease}), nằm ngoài phạm vi tri thức lâm sàng hiện tại."
                    )
        return None

    def generate_answer(self, question: str) -> str:
        # BƯỚC CHỐT: Chuẩn hóa text ngay khi tiếp nhận đầu vào
        q_clean = self._clean_and_normalize_text(question)

        # Kích hoạt lá chắn dựa trên chuỗi sạch
        guardrail_violation_msg = self._apply_clinical_guardrails(q_clean)
        if guardrail_violation_msg:
            print("🛡️ [Guardrail] Chặn đứng câu hỏi vi phạm quy tắc an toàn.")
            return guardrail_violation_msg

        # Luồng RAG tiếp tục chạy bình thường nếu an toàn
        retrieved_context = self.retrieval.hybrid_graph_rag_search(q_clean)

        system_prompt = """
        Bạn là một Chuyên gia Dinh dưỡng Lâm sàng cấp cao. Sử dụng bối cảnh đồ thị tri thức
        và y văn Bộ Y tế được cung cấp để tư vấn chế độ ăn tiết chế phù hợp cho bệnh nhân.
        """

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Câu hỏi: {question}\n\nNgữ cảnh:\n{retrieved_context}"}
            ],
            "temperature": 0.1,
            "max_tokens": 1200
        }

        try:
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=30)
            if response.status_code == 200:
                return response.json()['choices'][0]['message']['content']
            return f"⚠️ Lỗi kết nối LLM (Mã lỗi {response.status_code})"
        except Exception as e:
            return f"❌ Sự cố kết nối: {str(e)}"