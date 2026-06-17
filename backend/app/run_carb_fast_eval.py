# -*- coding: utf-8 -*-
# backend/app/run_carb_fast_eval.py
import os
import sys
import time
import types
import pandas as pd

# =========================================================================
# 🛡️ PHÂN HỆ VÁ LỖI PHỤ THUỘC TỐI THƯỢNG (PURE SYS MOCKING)
# =========================================================================
mock_vertex_mod = types.ModuleType("langchain_community.chat_models.vertexai")
class ChatVertexAI:
    def __init__(self, *args, **kwargs): pass
mock_vertex_mod.ChatVertexAI = ChatVertexAI
sys.modules["langchain_community.chat_models.vertexai"] = mock_vertex_mod

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)
if CURRENT_DIR not in sys.path: sys.path.append(CURRENT_DIR)
if PARENT_DIR not in sys.path: sys.path.append(PARENT_DIR)

from datasets import Dataset
from ragas import evaluate
from ragas.metrics import faithfulness
from langchain_groq import ChatGroq
from langchain_core.rate_limiters import InMemoryRateLimiter

from app.eval_dataset import EVAL_DATA
from app.services.retrieval import RetrievalService

def run_pure_carb_evaluation():
    # 🎯 ÉP CỨNG CHUỖI KEY MỚI VÀO MÔI TRƯỜNG CHẠY HỆ THỐNG
    os.environ["GROQ_API_KEY"] = "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"

    print("\n🚀 [NGR-Engine] KHỞI CHẠY TIẾN TRÌNH KIỂM TOÁN CARBOHYDRATE MỚI TINH...")
    print("="*70)

    rag_service = RetrievalService()
    full_test_suite = EVAL_DATA
    total_questions = len(full_test_suite)
    print(f"✅ Đã nạp thành công bộ test đồ án gồm: {total_questions} câu hỏi.")

    questions = []
    contexts_list = []
    answers = []
    ground_truths = []

    # Kiểm soát tốc độ quét cuốn chiếu để bảo vệ cổng mạng vật lý 7687
    BATCH_SIZE = 4
    SLEEP_DURATION = 6
    start_time = time.time()

    for idx, item in enumerate(full_test_suite):
        q = item["question"]
        gt = item["ground_truth"]

        print(f" └─ Đang xử lý câu hỏi [{idx+1}/{total_questions}]: '{q}'")

        try:
            raw_context = rag_service._get_expanded_graph_context(q)
            contexts = [raw_context] if raw_context else ["🚨 ĐỒ THỊ TRỐNG (KHÔNG KHỚP THỰC THỂ) 🚨"]
            actual_answer = rag_service.answer_question(q)

            questions.append(q)
            contexts_list.append(contexts)
            answers.append(actual_answer)
            ground_truths.append(gt)

        except Exception as e:
            print(f" ⚠️ Bỏ qua câu hỏi thứ {idx+1} do lỗi: {str(e)}")
            continue

        if (idx + 1) % BATCH_SIZE == 0 and (idx + 1) < total_questions:
            print(f"☕ Hoàn thành lô [{idx+1}/{total_questions}]. Nghỉ {SLEEP_DURATION} giây cho hệ thống hồi sức...")
            time.sleep(SLEEP_DURATION)

    print("\n📦 Đóng gói dữ liệu bốc từ Đồ thị sang HuggingFace Dataset...")
    dataset_dict = {
        "question": questions,
        "contexts": contexts_list,
        "answer": answers,
        "ground_truth": ground_truths
    }
    hf_dataset = Dataset.from_dict(dataset_dict)

    print("\n⚖️ [Ragas Judge] Thiết lập giám khảo Llama 8B kèm bộ hãm phanh TPM...")
    GROQ_API_KEY = "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"

    # Hãm phanh 10 giây/câu để tài khoản Free an toàn tuyệt đối
    rate_limiter = InMemoryRateLimiter(
        requests_per_second=0.1,
        check_every_n_seconds=0.1,
        max_bucket_size=2
    )

    judge_llm = ChatGroq(
        groq_api_key=GROQ_API_KEY,
        model_name="llama-3.1-8b-instant",
        temperature=0.0,
        rate_limiter=rate_limiter
    )

    metrics = [faithfulness]

    print("⏳ Thầy cô giám khảo AI đang thực thi thuật toán chấm điểm...")
    try:
        results = evaluate(
            dataset=hf_dataset,
            metrics=metrics,
            llm=judge_llm
        )
    except Exception as e:
        print(f"🚨 Ragas Judge đứt quãng: {e}. Tự động xuất file cứu hộ dữ liệu thô!")
        pd.DataFrame(dataset_dict).to_csv(os.path.join(CURRENT_DIR, "cuu_ho_carb_raw_data.csv"), index=False, encoding="utf-8-sig")
        return

    print("\n" + "="*70)
    print(f"📈 KẾT QUẢ THỰC NGHIỆM ĐỊNH LƯỢNG CARBOHYDRATE CUỐI CÙNG:")
    print("="*70)
    df_report = results.to_pandas()

    if "faithfulness" in df_report.columns:
        df_report["faithfulness"] = (df_report["faithfulness"] * 100).round(2)

    # 🎯 VÁ AN TOÀN: In toàn bộ bảng kết quả mà không cần chỉ định tên cột cũ
    print("\n📝 Cấu trúc bảng điểm thực nghiệm ghi nhận:")
    print(df_report.head(15))

    print("\n📊 ĐIỂM SỐ TRUNG BÌNH TOÀN DIỆN NGR-ENGINE:")
    if "faithfulness" in df_report.columns:
        print(f" └─ Độ trung thực định lượng Carbohydrate: {df_report['faithfulness'].mean().round(2)}%")

    output_path = os.path.join(CURRENT_DIR, f"bao_cao_carb_hoan_chinh_{len(questions)}_cau.csv")
    df_report.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"\n🎉 THÀNH CÔNG RỰC RỠ! File báo cáo thực nghiệm đã lưu tại: {output_path}")

if __name__ == "__main__":
    run_pure_carb_evaluation()