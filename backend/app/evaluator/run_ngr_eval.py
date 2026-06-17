# -*- coding: utf-8 -*-

import os
from pathlib import Path
from dotenv import load_dotenv

# =====================================================
# Load .env
# =====================================================

BASE_DIR = Path(__file__).resolve().parents[2]
ENV_PATH = BASE_DIR / ".env"

print("BASE_DIR :", BASE_DIR)
print("ENV_PATH :", ENV_PATH)

load_dotenv(dotenv_path=ENV_PATH)


# =====================================================
# Import sau khi load env
# =====================================================

from app.services.retrieval import RetrievalService
from app.eval_disease_dataset import EVAL_DISEASE_DATA
from app.evaluator.llm_judge import LLMJudge
from app.evaluator.scorer import NGRScorer
from app.evaluator.report import ReportExporter

# =====================================================
# Init
# =====================================================

judge = LLMJudge()

retrieval = RetrievalService()

scorer = NGRScorer()

report = ReportExporter()

rows = []

print("=" * 60)
print("NGR-EVAL")
print("=" * 60)

# =====================================================
# Evaluation
# =====================================================

for idx, item in enumerate(EVAL_DISEASE_DATA):

    question = item["question"]
    ground_truth = item["ground_truth"]

    print(f"\n[{idx + 1}/{len(EVAL_DISEASE_DATA)}] {question}")

    try:

        context = retrieval._get_expanded_graph_context(
            question
        )

        answer = retrieval.answer_question(
            question
        )

        llm_result = judge.evaluate(
            question,
            ground_truth,
            context,
            answer
        )

        score = scorer.score(
            llm_result,
            answer,
            ground_truth
        )

        score["question"] = question
        score["ground_truth"] = ground_truth
        score["answer"] = answer

        rows.append(score)

        print("✓ Done")

    except Exception as e:

        print("✗ ERROR:", e)

# =====================================================
# Export
# =====================================================

csv_path, json_path = report.export(rows)

print("\n")
print("=" * 60)
print("ĐÁNH GIÁ HOÀN THÀNH")
print("=" * 60)

print("CSV  :", csv_path)
print("JSON :", json_path)