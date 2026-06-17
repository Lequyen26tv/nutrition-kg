# -*- coding: utf-8 -*-

from app.evaluator.metrics import (
    similarity,
    semantic_similarity,
    exact_match,
    llm_score,
    overall_score
)


class NGRScorer:

    def score(
        self,
        llm_result,
        answer,
        ground_truth
    ):

        # Lexical Similarity
        lexical_sim = similarity(
            answer,
            ground_truth
        )

        # Semantic Similarity
        semantic_sim = semantic_similarity(
            answer,
            ground_truth
        )

        # Exact Match
        em = exact_match(
            answer,
            ground_truth
        )

        # LLM Score
        llm = llm_score(
            llm_result["faithfulness"],
            llm_result["completeness"],
            llm_result["medical_safety"],
            llm_result["hallucination"],
            llm_result["fluency"]
        )

        # Có thể lấy trung bình lexical + semantic
        similarity_score = round(
            (lexical_sim + semantic_sim) / 2,
            4
        )

        # Overall
        final = overall_score(
            similarity_score,
            llm
        )

        return {

            # ---------- Similarity ----------
            "lexical_similarity": lexical_sim,

            "semantic_similarity": semantic_sim,

            "similarity": similarity_score,

            "exact_match": em,

            # ---------- LLM Judge ----------
            "faithfulness":
                llm_result["faithfulness"],

            "completeness":
                llm_result["completeness"],

            "medical_safety":
                llm_result["medical_safety"],

            "hallucination":
                llm_result["hallucination"],

            "fluency":
                llm_result["fluency"],

            # ---------- Score ----------
            "llm_score": llm,

            "overall_score": final
        }