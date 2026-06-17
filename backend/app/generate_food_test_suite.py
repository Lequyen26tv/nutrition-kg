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
        "mon_an_neo4j_ready.csv"
    )
)

print("CSV_PATH =", csv_path)

df = pd.read_csv(csv_path)

eval_data = []

for _, row in df.iterrows():

    name = str(row["food_name"]).strip()

    carb = row["carbohydrate_g"]

    eval_data.append({
        "question":
            f"{name} chứa bao nhiêu carbohydrate?",

        "ground_truth":
            f"{carb} g carbohydrate"
    })

output_file = os.path.join(
    BASE_DIR,
    "eval_food_dataset.py"
)

with open(output_file, "w", encoding="utf-8") as f:

    f.write("# -*- coding: utf-8 -*-\n\n")
    f.write("EVAL_DATA = [\n")

    for item in eval_data:

        f.write("    {\n")
        f.write(
            f'        "question": "{item["question"]}",\n'
        )
        f.write(
            f'        "ground_truth": "{item["ground_truth"]}"\n'
        )
        f.write("    },\n")

    f.write("]\n")

print("Hoàn thành!")
print("Tạo", len(eval_data), "câu hỏi")