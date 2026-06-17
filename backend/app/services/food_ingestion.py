import os
import sys
import pandas as pd

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(os.path.dirname(CURRENT_DIR))
if BACKEND_DIR not in sys.path:
    sys.path.append(BACKEND_DIR)

from app.db.neo4j_connection import neo4j_db
DATA_DIR = os.path.join(os.path.dirname(BACKEND_DIR), "data")

class AdvancedFoodIngestionService:
    def __init__(self):
        self.db = neo4j_db
        self.nutrient_map = {
            "Calories": {"id": "energy_kcal", "name": "Năng lượng"},
            "Carbohydrates": {"id": "carb_g", "name": "Glucid (Carbohydrate)"},
            "Protein": {"id": "protein_g", "name": "Chất đạm (Protein)"},
            "Fat": {"id": "fat_g", "name": "Chất béo (Fat)"},
            "Sodium Content": {"id": "sodium_mg", "name": "Natri (Sodium)"},
            "Potassium Content": {"id": "potassium_mg", "name": "Kali (Potassium)"},
            "Magnesium Content": {"id": "magnesium_mg", "name": "Magie (Magnesium)"},
            "Calcium Content": {"id": "calcium_mg", "name": "Canxi (Calcium)"},
            "Fiber Content": {"id": "fiber_g", "name": "Chất xơ (Fiber)"}
        }

    def clean_value(self, val):
        if pd.isna(val): return None
        try:
            num = float(str(val).strip().replace(',', '.'))
            return None if num == 0 or num == 0.0 else num
        except (ValueError, TypeError): return None

    def execute_ingestion(self):
        file_path = os.path.join(DATA_DIR, "pred_food_translated_full_vi.csv")
        print(f"🚀 [Script 2] Bắt đầu nạp 502 thực phẩm Ontology vào Cloud Aura từ: {file_path}")

        df = None
        for enc in ['utf-8', 'utf-8-sig', 'Windows-1258', 'latin-1']:
            try:
                df = pd.read_csv(file_path, encoding=enc)
                print(f"✅ Đọc thành công file 502 món bằng bảng mã: {enc}")
                break
            except: continue
        if df is None: raise UnicodeDecodeError("❌ Thất bại khi giải mã file CSV 502 món ăn.")

        with self.db.get_session() as session:
            print("-> Khởi tạo hệ thống Node Dưỡng chất lõi...")
            for col_name, info in self.nutrient_map.items():
                session.run("MERGE (n:Nutrient {id: $id}) SET n.name = $name", id=info["id"], name=info["name"])

        success_count, batch_size, current_batch = 0, 50, []

        for idx, row in df.iterrows():
            food_name = str(row.get('Food Name')).strip()
            if not food_name or food_name.lower() in ['nan', 'none']: continue
            current_batch.append((idx, row, food_name))

            if len(current_batch) == batch_size or idx == len(df) - 1:
                with self.db.get_session() as session:
                    for b_idx, b_row, b_name in current_batch:
                        food_id = f"food_new_{b_idx}"
                        gi_val = self.clean_value(b_row.get('Glycemic Index'))

                        # 1. Tạo node Ingredient tích hợp chỉ số GI
                        session.run("MERGE (i:Ingredient {id: $id}) SET i.name = $name, i.glycemic_index = $gi", id=food_id, name=b_name, gi=gi_val)

                        # 2. Tạo liên kết thực thể chất động (Property-to-Node)
                        for col_name, info in self.nutrient_map.items():
                            c_val = self.clean_value(b_row.get(col_name))
                            if c_val is not None:
                                session.run("""
                                    MATCH (i:Ingredient {id: $ing_id}) MATCH (n:Nutrient {id: $nut_id})
                                    MERGE (i)-[r:HAS_NUTRIENT]->(n) SET r.value = $val
                                """, ing_id=food_id, nut_id=info["id"], val=c_val)

                        # 3. Tạo định hướng bệnh lý dựa trên nhãn lâm sàng của file chuyên gia
                        diabetes_suit = str(b_row.get('Suitable for Diabetes')).strip().lower()
                        bp_suit = int(b_row.get('Suitable for Blood Pressure', 1))

                        if diabetes_suit in ['0', 'no']:
                            session.run("MATCH (i:Ingredient {id: $id}), (d:Disease {id: 'disease_dtd'}) MERGE (i)-[:RESTRICTED_FOR {reason: 'Chỉ số lâm sàng không phù hợp cho người đái tháo đường'}]->(d)", id=food_id)
                        else:
                            session.run("MATCH (i:Ingredient {id: $id}), (d:Disease {id: 'disease_dtd'}) MERGE (i)-[:BENEFICIAL_FOR {reason: 'Chỉ số lâm sàng an toàn cho người đái tháo đường'}]->(d)", id=food_id)

                        if bp_suit == 0:
                            session.run("MATCH (i:Ingredient {id: $id}), (d:Disease {id: 'disease_tha'}) MERGE (i)-[:RESTRICTED_FOR {reason: 'Không phù hợp cho người tăng huyết áp'}]->(d)", id=food_id)
                        else:
                            session.run("MATCH (i:Ingredient {id: $id}), (d:Disease {id: 'disease_tha'}) MERGE (i)-[:BENEFICIAL_FOR {reason: 'An toàn cho người tăng huyết áp'}]->(d)", id=food_id)
                        success_count += 1
                print(f"   📦 Đã đẩy thành công cụm dữ liệu: {success_count}/502 món...")
                current_batch = []
        print(f"🎯 [SUCCESS - SCRIPT 2] Hoàn thành viên mãn nâng cấp Ontology cho 502 món ăn!")

if __name__ == "__main__":
    service = AdvancedFoodIngestionService()
    try: service.execute_ingestion()
    except Exception as e: print(f"❌ Lỗi: {e}")
    finally:
        try: service.db.close()
        except: pass