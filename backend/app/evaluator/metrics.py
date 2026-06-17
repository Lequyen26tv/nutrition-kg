# -*- coding: utf-8 -*-
print("===== METRICS VERSION 2 =====")
"""
NGR-Eval Metrics
Tác giả: Nutrition GraphRAG Evaluation Framework
"""

import re
from difflib import SequenceMatcher

from sentence_transformers import SentenceTransformer
import numpy as np

SEMANTIC_MODEL = SentenceTransformer(
    "paraphrase-multilingual-MiniLM-L12-v2"
)

def semantic_similarity(text1, text2):
    text1 = normalize(text1)
    text2 = normalize(text2)

    emb = SEMANTIC_MODEL.encode(
        [text1, text2],
        normalize_embeddings=True
    )

    score = np.dot(emb[0], emb[1])

    return round(float(score), 4)
# ==========================================
# Chuẩn hóa văn bản
# ==========================================

def normalize(text):

    if text is None:
        return ""

    text = str(text).lower().strip()

    text = re.sub(r"\s+", " ", text)

    return text


# ==========================================
# Similarity
# ==========================================

def similarity(text1, text2):
    print("Similarity loaded")
    text1 = normalize(text1)
    text2 = normalize(text2)

    return round(
        SequenceMatcher(None, text1, text2).ratio(),
        4
    )


# ==========================================
# Exact Match
# ==========================================

def exact_match(answer, ground_truth):

    return normalize(answer) == normalize(ground_truth)


# ==========================================
# Keyword Hit
# ==========================================

def keyword_hit(answer, keywords):

    answer = normalize(answer)

    if len(keywords) == 0:
        return 1

    hit = 0

    for kw in keywords:

        if normalize(kw) in answer:
            hit += 1

    return round(hit / len(keywords), 4)


# ==========================================
# Entity Hit
# ==========================================

def entity_hit(answer, entities):

    answer = normalize(answer)

    if len(entities) == 0:
        return 1

    hit = 0

    for e in entities:

        if normalize(e) in answer:
            hit += 1

    return round(hit / len(entities), 4)


# ==========================================
# Disease Hit
# ==========================================

def disease_hit(answer, disease):

    if disease is None:
        return 1

    answer = normalize(answer)

    return normalize(disease) in answer


# ==========================================
# Context Hit
# ==========================================

def context_hit(answer, context):

    if context is None:
        return 0

    answer = normalize(answer)

    context = normalize(context)

    words = list(set(context.split()))

    if len(words) == 0:
        return 0

    hit = 0

    for w in words:

        if w in answer:
            hit += 1

    return round(hit / len(words), 4)


# ==========================================
# Triple Hit
# ==========================================

def triple_hit(context, triples):

    """
    triples = [
        "Chuối",
        "GI 51",
        "Đái tháo đường"
    ]
    """

    if len(triples) == 0:
        return 1

    context = normalize(context)

    hit = 0

    for t in triples:

        if normalize(t) in context:
            hit += 1

    return round(hit / len(triples), 4)


# ==========================================
# Overall Retrieval Score
# ==========================================

def retrieval_score(

    entity,

    keyword,

    context,

    triple

):

    return round(

        entity * 0.30 +

        keyword * 0.25 +

        context * 0.25 +

        triple * 0.20,

        4
    )


# ==========================================
# Overall LLM Score
# ==========================================

def llm_score(

    faithfulness,

    completeness,

    medical_safety,

    hallucination,

    fluency

):

    return round(

        (

            faithfulness +

            completeness +

            medical_safety +

            hallucination +

            fluency

        ) / 50,

        4
    )


# ==========================================
# Overall Final Score
# ==========================================

def overall_score(

    retrieval,

    llm

):

    return round(

        retrieval * 0.4 +

        llm * 0.6,

        4
    )