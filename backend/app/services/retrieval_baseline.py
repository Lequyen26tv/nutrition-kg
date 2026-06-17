import os
from urllib import response
from groq import Groq
from app.evaluator.api_manager import GroqAPIManager

class RetrievalService:

    def __init__(self):
        self.api = GroqAPIManager()

        self.model = "llama-3.1-8b-instant"
        
    
    def _get_expanded_graph_context(self, question):
        # Baseline không dùng Neo4j
        return ""

    def answer_question(self, question):

        system_prompt = """
Bạn là chuyên gia tư vấn dinh dưỡng.

Trả lời bằng kiến thức chung của bạn.

Không sử dụng dữ liệu Neo4j.

Không nhắc tới Graph Context.

Nếu không chắc chắn hãy trả lời thận trọng.

Trả lời bằng tiếng Việt.
"""

        response = self._call(

    [

        {

            "role":"system",

            "content":system_prompt

        },

        {

            "role":"user",

            "content":question

        }

    ]

)

        return response.choices[0].message.content
    def _call(self, messages):

        last_error = None

        for i in range(self.api.count()):

            key = self.api.next_key()

            try:

                client = Groq(api_key=key)

                response = client.chat.completions.create(

                    model=self.model,

                    temperature=0.2,

                    messages=messages

                )

                return response

            except Exception as e:

                print(e)

                last_error = e

        raise RuntimeError(last_error)
        