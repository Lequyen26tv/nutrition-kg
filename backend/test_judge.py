from app.evaluator.llm_judge import LLMJudge

judge = LLMJudge(
    api_key="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"
)

result = judge.evaluate(
    question="Người đái tháo đường có nên ăn chuối không?",
    ground_truth="Có thể ăn với lượng vừa phải.",
    context="Chuối có GI khoảng 51...",
    answer="Người đái tháo đường có thể ăn chuối với lượng vừa phải."
)

print(result)