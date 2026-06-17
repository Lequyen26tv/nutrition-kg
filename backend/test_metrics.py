import app.evaluator.metrics as metrics
from app.evaluator.metrics import *

print("similarity" in globals())
print(globals().keys())
print(metrics.__file__)
print(dir(metrics))

answer = """
Người đái tháo đường có thể ăn chuối với lượng vừa phải.
"""

ground_truth = """
Có thể ăn chuối với lượng vừa phải.
"""

context = """
Chuối

GI 51

Đái tháo đường

Carbohydrate
"""

print("Similarity:", similarity(answer, ground_truth))

print("Exact:", exact_match(answer, ground_truth))

print("Keyword:",
      keyword_hit(answer,
      ["chuối","đái tháo đường"]))

print("Entity:",
      entity_hit(answer,
      ["Chuối"]))

print("Disease:",
      disease_hit(answer,
      "Đái tháo đường"))

print("Context:",
      context_hit(answer,
      context))

print("Triple:",
      triple_hit(
          context,
          ["Chuối","GI 51"]
      ))