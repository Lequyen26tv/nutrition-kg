# -*- coding: utf-8 -*-
# backend/app/run_dish_fast_eval.py
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
# 🎯 NẠP ĐẦY ĐỦ BỘ 4 THƯỚC ĐO THEO CHUẨN RAGAS V1.0 (ĐỒNG BỘ 100% ĐUÔI _RELEVANCY)
from ragas.metrics.collections import faithfulness, answer_relevancy, context_precision, context_recall
from langchain_groq import ChatGroq
from langchain_core.rate_limiters import InMemoryRateLimiter

from app.eval_disease_dataset import EVAL_DISEASE_DATA
from app.services.retrieval import RetrievalService

def run_dish_evaluation():
    # 🎯 ÉP CỨNG CHUỖI KEY MỚI VÀO MÔI TRƯỜNG CHẠY HỆ THỐNG
    os.environ["GROQ_API_KEY"] = "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"

    print("\n🚀 [NGR-Engine] KÍCH HOẠT TIẾN TRÌNH KIỂM TOÁN PHÂN HỆ ĐỐI THOẠI & AN TOÀN BỆNH LÝ...")
    print("="*75)

    rag_service = RetrievalService()
    full_test_suite = EVAL_DISEASE_DATA
    total_questions = len(full_test_suite)
    print(f"✅ Đã nạp thành công bộ test thực chiến gồm: {total_questions} câu hỏi.")

    questions = []
    contexts_list = []
    answers = []
    ground_truths = []

    BATCH_SIZE = 2
    SLEEP_DURATION = 4

    for idx, item in enumerate(full_test_suite):
        q = item["question"]
        gt = item["ground_truth"]

        print(f" └─ Đang xử lý câu hỏi thực chiến [{idx+1}/{total_questions}]: '{q}'")

        try:
            raw_context = rag_service._get_expanded_graph_context(q)
            contexts = [raw_context] if raw_context else ["🚨 ĐỒ THỊ TRỐNG (KHÔNG KHỚP TRI THỨC LÂM SÀNG) 🚨"]
            actual_answer = rag_service.answer_question(q)

            questions.append(q)
            contexts_list.append(contexts)
            answers.append(actual_answer)
            ground_truths.append(gt)

        except Exception as e:
            print(f" ⚠️ Bỏ qua câu thứ {idx+1} do nhiễu mạng hoặc lỗi cấu trúc: {str(e)}")
            continue

        if (idx + 1) % BATCH_SIZE == 0 and (idx + 1) < total_questions:
            print(f"☕ Hoàn thành lô [{idx+1}/{total_questions}]. Nghỉ {SLEEP_DURATION} giây bảo vệ connection pool...")
            time.sleep(SLEEP_DURATION)

    print("\n📦 Đóng gói dữ liệu thực nghiệm sang HuggingFace Dataset chuẩn Ragas...")
    dataset_dict = {
        "question": questions,
        "contexts": contexts_list,
        "answer": answers,
        "ground_truth": ground_truths
    }
    hf_dataset = Dataset.from_dict(dataset_dict)

    print("\n⚖️ [Ragas Judge] Thiết lập hội đồng chấm điểm Llama 3.1 8B chống bão Rate Limit...")
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

    rate_limiter = InMemoryRateLimiter(
        requests_per_second=0.5,
        check_every_n_seconds=0.1,
        max_bucket_size=3
    )

    judge_llm = ChatGroq(
        groq_api_key=GROQ_API_KEY,
        model_name="llama-3.1-8b-instant",
        max_tokens=2048,
        temperature=0.0,
        rate_limiter=rate_limiter
    )

    # 🌟 ĐÃ SỬA: Đổi answer_relevance thành answer_relevancy cho khớp hoàn toàn với gói import
    # MỚI (CHẠY PHĂM PHĂM):
    metrics = [faithfulness(), answer_relevancy(), context_precision(), context_recall()]

    print("⏳ Giám khảo AI đang thực thi thuật toán chấm điểm đối soát tri thức lâm sàng...")
    try:
        results = evaluate(
            dataset=hf_dataset,
            metrics=metrics,
            llm=judge_llm,
        )
    except Exception as e:
        print(f"🚨 Ragas Judge đứt quãng giữa chừng: {e}. Đã kích hoạt hệ thống xuất file cứu hộ dữ liệu thô!")
        pd.DataFrame(dataset_dict).to_csv(os.path.join(CURRENT_DIR, "cuu_ho_disease_raw_data.csv"), index=False, encoding="utf-8-sig")
        return

    print("\n" + "="*75)
    print(f"📈 KẾT QUẢ KIỂM TOÁN HỆ THỐNG NGR-ENGINE (TOÀN DIỆN 4 TIÊU CHÍ):")
    print("="*75)
    df_report = results.to_pandas()

    # 🌟 ĐÃ SỬA: Đồng bộ chuỗi kiểm tra tên cột của dataframe Pandas
    target_metrics = ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]
    for col in target_metrics:
        if col in df_report.columns:
            df_report[col] = (df_report[col] * 100).round(2)

    print("\n📝 Cấu trúc bảng điểm thực nghiệm ghi nhận:")
    print(df_report.head(10))

    print("\n📊 ĐIỂM SỐ TRUNG BÌNH ĐỘ CHÍNH XÁC DINH DƯỠNG LÂM SÀNG:")
    if "faithfulness" in df_report.columns:
        print(f" ├─ Độ trung thực y văn (Faithfulness): {df_report['faithfulness'].mean().round(2)}%")
    if "answer_relevancy" in df_report.columns:
        print(f" ├─ Sự liên quan câu trả lời (Answer Relevancy): {df_report['answer_relevancy'].mean().round(2)}%")
    if "context_precision" in df_report.columns:
        print(f" ├─ Độ chính xác truy xuất đồ thị (Context Precision): {df_report['context_precision'].mean().round(2)}%")
    if "context_recall" in df_report.columns:
        print(f" ├─ Độ bao phủ tri thức nguồn (Context Recall): {df_report['context_recall'].mean().round(2)}%")

    output_path = os.path.join(CURRENT_DIR, f"bao_cao_disease_hoan_chinh_{len(questions)}_cau.csv")
    df_report.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"\n🎉 THÀNH CÔNG RỰC RỠ! Toàn bộ file báo cáo đã được xuất tại: {output_path}")

if __name__ == "__main__":
    run_dish_evaluation()