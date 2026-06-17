# -*- coding: utf-8 -*-

import json
import os
import pandas as pd


class ReportExporter:

    def __init__(self):

        self.output_dir = "reports"

        os.makedirs(
            self.output_dir,
            exist_ok=True
        )

    def export(
        self,
        rows
    ):

        df = pd.DataFrame(rows)

        csv_path = os.path.join(
            self.output_dir,
            "evaluation.csv"
        )

        df.to_csv(

            csv_path,

            index=False,

            encoding="utf-8-sig"

        )

        summary = {

            "samples": len(df),

            "overall_score":
                round(df["overall_score"].mean(),4),

            "similarity":
                round(df["similarity"].mean(),4),

            "faithfulness":
                round(df["faithfulness"].mean(),2),

            "completeness":
                round(df["completeness"].mean(),2),

            "medical_safety":
                round(df["medical_safety"].mean(),2),

            "hallucination":
                round(df["hallucination"].mean(),2),

            "fluency":
                round(df["fluency"].mean(),2)

        }

        json_path = os.path.join(

            self.output_dir,

            "summary.json"

        )

        with open(

            json_path,

            "w",

            encoding="utf8"

        ) as f:

            json.dump(

                summary,

                f,

                indent=4,

                ensure_ascii=False

            )

        return csv_path, json_path