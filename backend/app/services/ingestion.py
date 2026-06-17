import os
import sys
import pandas as pd

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(os.path.dirname(CURRENT_DIR))
if BACKEND_DIR not in sys.path:
    sys.path.append(BACKEND_DIR)

from app.db.neo4j_connection import neo4j_db
DATA_DIR = os.path.join(os.path.dirname(BACKEND_DIR), "data")

class NutritionIngestionService:
    def __init__(self):
        self.db = neo4j_db

    def clean_value(self, val):
        if pd.isna(val): return None
        value = str(val).strip().replace(',', '.')
        if value.lower() in ['', 'nan', 'none', 'n/a', 'null']: return None
        try:
            num = float(value)
            return None if num == 0 or num == 0.0 else num  # Kỷ luật y khoa: 0 -> null
        except (ValueError, TypeError): return None

    def execute_ingestion(self):
        print(f"📂 [Script 1] Đang xử lý danh mục thực phẩm nền từ: {DATA_DIR}")

        # Đọc 4 file dữ liệu gốc bằng giải pháp bảng mã an toàn
        df_ingredients = pd.read_csv(os.path.join(DATA_DIR, "ingredients.csv"), encoding='utf-8-sig')
        df_ing_import = pd.read_csv(os.path.join(DATA_DIR, "ingredients_import.csv"), encoding='utf-8-sig')
        df_dishes = pd.read_csv(os.path.join(DATA_DIR, "dishes_import.csv"), encoding='utf-8-sig')
        df_dish_ing = pd.read_csv(os.path.join(DATA_DIR, "dish_ingredients_import.csv"), encoding='utf-8-sig')

        metadata_cols = ['ingredient_id', 'ingredient_name', 'category']
        nutrient_cols = [col for col in df_ingredients.columns if col not in metadata_cols]

        with self.db.get_session() as session:
            print("-> Khởi tạo các Node Bệnh lý gốc...")
            session.run("""
                MERGE (d1:Disease {id:'disease_dtd', name:'Đái tháo đường'})
                MERGE (d2:Disease {id:'disease_tha', name:'Tăng huyết áp'})
            """)

            print("-> Nạp nguyên liệu và tự động phân nhóm Category nâng cao...")
            for _, row in df_ingredients.iterrows():
                ing_name = str(row.get('ingredient_name')).strip()
                raw_cat = row.get('category')
                cat_name = str(raw_cat).strip() if pd.notna(raw_cat) else "Chưa phân loại"

                nutrient_props = {col: self.clean_value(row.get(col)) for col in nutrient_cols if self.clean_value(row.get(col)) is not None}

                match_id = df_ing_import[df_ing_import['name'].astype(str).str.lower() == ing_name.lower()]
                ing_id = str(match_id.iloc[0]['ingredient_id']) if not match_id.empty else f"ing_{int(float(row.get('ingredient_id')))}"

                # Tạo nút nguyên liệu và nút phân nhóm thực phẩm
                session.run("MERGE (i:Ingredient {id: $id}) SET i.name = $name, i += $props", id=ing_id, name=ing_name, props=nutrient_props)
                session.run("MERGE (cat:Category {name: $cat}) WITH cat MATCH (i:Ingredient {id: $id}) MERGE (i)-[:BELONGS_TO]->(cat)", cat=cat_name, id=ing_id)

                # Thiết lập các quan hệ logic tự động dựa trên hàm lượng chất
                carb = nutrient_props.get('carb_g')
                sodium = nutrient_props.get('sodium_mg')
                if isinstance(carb, (int, float)):
                    if carb < 10: session.run("MATCH (i:Ingredient {id:$id}), (d:Disease {id:'disease_dtd'}) MERGE (i)-[:BENEFICIAL_FOR {reason: 'Glucid thấp'}]->(d)", id=ing_id)
                    elif carb > 70: session.run("MATCH (i:Ingredient {id:$id}), (d:Disease {id:'disease_dtd'}) MERGE (i)-[:RESTRICTED_FOR {reason: 'Glucid cao'}]->(d)", id=ing_id)
                if isinstance(sodium, (int, float)) and sodium > 300:
                    session.run("MATCH (i:Ingredient {id:$id}), (d:Disease {id:'disease_tha'}) MERGE (i)-[:RESTRICTED_FOR {reason: 'Natri cao'}]->(d)", id=ing_id)

            print("-> Đang lập sơ đồ danh mục các món ăn Việt Nam...")
            for _, row in df_dishes.iterrows():
                session.run("MERGE (d:Dish {id:$id}) SET d.name = $name", id=str(row['dish_id']), name=str(row['name']))

            print("-> Thiết lập các sợi liên kết thành phần món ăn...")
            for _, row in df_dish_ing.iterrows():
                session.run("""
                    MATCH (d:Dish {id:$dish_id}) MATCH (i:Ingredient {id:$ing_id})
                    MERGE (d)-[r:CONTAINS_INGREDIENT]->(i)
                    SET r.quantity = $qty, r.unit = $unit
                """, dish_id=str(row['dish_id']), ing_id=str(row['ingredient_id']), qty=self.clean_value(row.get('quantity')), unit=str(row.get('unit', 'g')))

        print("🎯 [SUCCESS - SCRIPT 1] Đã đồng bộ cấu trúc danh mục món ăn lên mây Aura!")

if __name__ == "__main__":
    NutritionIngestionService().execute_ingestion()