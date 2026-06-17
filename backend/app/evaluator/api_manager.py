# -*- coding: utf-8 -*-

import os
from itertools import cycle
from pathlib import Path
from dotenv import load_dotenv
# Load .env từ thư mục backend
BASE_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = BASE_DIR / ".env"

load_dotenv(dotenv_path=ENV_FILE)

print("ENV:", ENV_FILE)
class GroqAPIManager:

    def __init__(self):

        self.keys = []

        # Đọc GROQ_API_KEY_1, GROQ_API_KEY_2, ...
        i = 1

        while True:

            key = os.getenv(f"GROQ_API_KEY_{i}")

            if not key:
                break

            key = key.strip()

            if key:
                self.keys.append(key)

            i += 1

        # Hỗ trợ key cũ
        single = os.getenv("GROQ_API_KEY")

        if single:

            single = single.strip()

            if single and single not in self.keys:
                self.keys.append(single)

        if len(self.keys) == 0:
            raise RuntimeError(
                "Không tìm thấy GROQ_API_KEY trong file .env"
            )

        print("=" * 50)
        print(f"Đã nạp {len(self.keys)} Groq API")
        print("=" * 50)

        self.pool = cycle(self.keys)

    def next_key(self):

        return next(self.pool)

    def count(self):

        return len(self.keys)
    # =====================================================
# TEST API ROTATION
# =====================================================

if __name__ == "__main__":

    api = GroqAPIManager()

    print(f"Tổng số API: {api.count()}")

    for i in range(10):
        key = api.next_key()
        print(f"API {i+1}: {key[:15]}...")