# -*- coding: utf-8 -*-

import json
import re

from groq import Groq

from app.evaluator.api_manager import GroqAPIManager


class LLMJudge:

    def __init__(self):

        self.api = GroqAPIManager()

        self.model = "llama-3.1-8b-instant"

    # =====================================================
    # Gọi Groq với cơ chế xoay vòng API
    # =====================================================

    def _call(self, prompt):

        last_error = None

        for i in range(self.api.count()):

            key = self.api.next_key()

            print(f"🔑 Sử dụng API #{i+1}")

            try:

                client = Groq(api_key=key)

                try:

                    response = client.chat.completions.create(
                        model=self.model,
                        temperature=0,
                        response_format={"type": "json_object"},
                        messages=[
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ]
                    )

                except TypeError:
                    # SDK Groq cũ
                    response = client.chat.completions.create(
                        model=self.model,
                        temperature=0,
                        messages=[
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ]
                    )

                return response

            except Exception as e:

                print(f"⚠ API #{i+1} lỗi")
                print(e)

                last_error = e

        raise RuntimeError(
            f"Tất cả API đều lỗi.\n{last_error}"
        )

    # =====================================================
    # Đánh giá
    # =====================================================

    def evaluate(

        self,

        question,

        ground_truth,

        context,

        answer

    ):

        prompt = f"""
Bạn là bác sĩ nội khoa đồng thời là chuyên gia đánh giá chatbot dinh dưỡng.

Nhiệm vụ:

Đánh giá chất lượng câu trả lời.

==============================

CÂU HỎI

{question}

==============================

GROUND TRUTH

{ground_truth}

==============================

KNOWLEDGE GRAPH CONTEXT

{context}

==============================

CHATBOT ANSWER

{answer}

==============================

Hãy chấm điểm:

1. faithfulness (0-10)

2. completeness (0-10)

3. medical_safety (0-10)

4. hallucination (0-10)

10 = hoàn toàn không bịa.

5. fluency (0-10)

==============================

Chỉ trả JSON.

{{
    "faithfulness":9,
    "completeness":8,
    "medical_safety":10,
    "hallucination":10,
    "fluency":9,
    "reason":"..."
}}

Không trả lời ngoài JSON.
"""

        response = self._call(prompt)

        content = response.choices[0].message.content.strip()

        # JSON chuẩn

        try:

            return json.loads(content)

        except Exception:

            pass

        # JSON nằm trong text

        match = re.search(
            r"\{[\s\S]*\}",
            content
        )

        if match:

            try:

                return json.loads(
                    match.group()
                )

            except Exception:

                pass

        # fallback

        return {

            "faithfulness": 0,

            "completeness": 0,

            "medical_safety": 0,

            "hallucination": 0,

            "fluency": 0,

            "reason": "Cannot parse JSON"

        }