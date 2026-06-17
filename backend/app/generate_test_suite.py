# -*- coding: utf-8 -*-

import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

csv_path = os.path.abspath(
    os.path.join(
        BASE_DIR,
        "..",
        "..",
        "data",
        "ingredients.csv"
    )
)

print("CSV_PATH =", csv_path)

if not os.path.exists(csv_path):
    print("Không tìm thấy file CSV!")
    exit()

df = pd.read_csv(csv_path)

print("Số nguyên liệu:", len(df))

eval_data = []

for _, row in df.iterrows():

    if "ingredient_name" not in df.columns:
        continue

    if "carb_g" not in df.columns:
        continue

    name = str(row["ingredient_name"]).strip()
    carb = row["carb_g"]

    eval_data.append({
        "question": f"{name} chứa bao nhiêu carbohydrate?",
        "ground_truth": f"{carb} g carbohydrate"
    })

output_file = os.path.join(
    BASE_DIR,
    "eval_dataset.py"
)

with open(output_file, "w", encoding="utf-8") as f:

    f.write("# -*- coding: utf-8 -*-\n\n")
    f.write("EVAL_DATA = [\n")

    for item in eval_data:

        f.write("    {\n")
        f.write(f'        "question": "{item["question"]}",\n')
        f.write(f'        "ground_truth": "{item["ground_truth"]}"\n')
        f.write("    },\n")

    f.write("]\n")

print("Hoàn thành!")
print("Tổng số câu hỏi:", len(eval_data))
print("File xuất:", output_file)