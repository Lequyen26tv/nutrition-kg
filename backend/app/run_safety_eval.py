# -*- coding: utf-8 -*-
"""
Evaluate grounded clinical dialogue answers without relying on an external LLM judge.
The faithfulness score measures whether the answer stays inside the retrieved,
source-checked clinical QA context.
"""

import os
import re
import sys

import pandas as pd

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)
if CURRENT_DIR not in sys.path:
    sys.path.append(CURRENT_DIR)
if PARENT_DIR not in sys.path:
    sys.path.append(PARENT_DIR)

from app.eval_disease_dataset import EVAL_DISEASE_DATA
from app.services.retrieval import search_service


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "").lower()).strip()


def _extract_expert_answer(context: str) -> str:
    match = re.search(
        r"Chuyên gia tư vấn:\s*(.*?)(?:\n📚|\nNguồn|$)",
        str(context or ""),
        re.DOTALL,
    )
    if not match:
        return ""
    return re.sub(r"\s+", " ", match.group(1)).strip()


def _score_faithfulness(answer: str, context: str) -> float:
    expert_answer = _extract_expert_answer(context)
    if not expert_answer:
        return 0.0

    answer_core = re.sub(r"📚.*", "", str(answer or ""), flags=re.DOTALL).strip()
    answer_norm = _normalize_text(answer_core)
    expert_norm = _normalize_text(expert_answer)

    if not answer_norm:
        return 0.0
    if answer_norm == expert_norm or answer_norm in expert_norm or expert_norm in answer_norm:
        return 100.0

    answer_tokens = set(answer_norm.split())
    expert_tokens = set(expert_norm.split())
    if not answer_tokens:
        return 0.0
    return round(100.0 * len(answer_tokens & expert_tokens) / len(answer_tokens), 2)


def _score_answer_relevance(answer: str, ground_truth: str) -> float:
    answer_tokens = set(_normalize_text(answer).split())
    truth_tokens = set(_normalize_text(ground_truth).split())
    if not answer_tokens or not truth_tokens:
        return 0.0
    return round(100.0 * len(answer_tokens & truth_tokens) / len(truth_tokens), 2)


def run_natural_dialogue_evaluation():
    print("\n🚀 [NGR-Engine] ĐÁNH GIÁ ĐỐI THOẠI TỰ NHIÊN & AN TOÀN BỆNH LÝ...")
    print("=" * 85)

    rows = []
    for idx, item in enumerate(EVAL_DISEASE_DATA):
        question = item["question"]
        ground_truth = item["ground_truth"]
        print(f"🧠 Đang xử lý câu [{idx + 1}/{len(EVAL_DISEASE_DATA)}]: '{question}'")

        context = search_service._get_expanded_graph_context(question)
        answer = search_service.generate_answer_with_llm(question, context)

        rows.append(
            {
                "question": question,
                "contexts": [context],
                "answer": answer,
                "ground_truth": ground_truth,
                "faithfulness": _score_faithfulness(answer, context),
                "answer_relevance": _score_answer_relevance(answer, ground_truth),
            }
        )

    df_res = pd.DataFrame(rows)

    print("\n📊 KẾT QUẢ ĐÁNH GIÁ TIẾN TRÌNH ĐỐI THOẠI THỰC CHIẾN:")
    print("-" * 65)
    print(f"  └─ Độ trung thực y văn chống ảo giác (Faithfulness): {df_res['faithfulness'].mean():.2f}%")
    print(f"  └─ Độ liên quan câu trả lời thực tế (Answer Relevance): {df_res['answer_relevance'].mean():.2f}%")
    print("-" * 65)

    report_path = os.path.abspath(
        os.path.join(CURRENT_DIR, "..", "report_disease_safety.csv")
    )
    df_res.to_csv(report_path, index=False, encoding="utf-8-sig")
    print(f"✅ Đã xuất bản file báo cáo kết quả thực nghiệm tại: {report_path}")


if __name__ == "__main__":
    run_natural_dialogue_evaluation()
