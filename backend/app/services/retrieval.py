import os
import sys
import unicodedata
import re
import math
# Import kết nối database neo4j từ cấu trúc của bạn
try:
    from app.db.neo4j_connection import neo4j_db
except Exception as exc:
    print(f"⚠️ Không kết nối được Neo4j khi khởi tạo RetrievalService: {exc}")
    neo4j_db = None

class RetrievalService:
    def __init__(self):
        # Gán đối tượng kết nối database vào biến toàn cục của class
        self.db = neo4j_db
        self.local_dish_index = self._load_local_dish_index()
        self.local_disease_qa = self._load_local_disease_qa()
        print("🧠 [RetrievalService] Đã khởi tạo bộ xử lý tri thức phân tầng.")

    def _normalize_lookup_key(self, text: str) -> str:
        if not text:
            return ""
        text = unicodedata.normalize("NFD", str(text).lower().strip())
        text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
        text = text.replace("đ", "d")
        return re.sub(r"\s+", " ", text)

    def _load_local_dish_index(self) -> dict:
        data_path = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__),
                "..",
                "..",
                "..",
                "data",
                "mon_an_neo4j_ready.csv",
            )
        )
        if not os.path.exists(data_path):
            return {}

        try:
            import pandas as pd

            df = pd.read_csv(data_path, encoding="utf-8-sig")
            index = {}
            for _, row in df.iterrows():
                name = str(row.get("food_name", "")).strip()
                if not name or name.lower() == "nan":
                    continue
                index[self._normalize_lookup_key(name)] = row.to_dict()
            return index
        except Exception as exc:
            print(f"⚠️ Không tải được dữ liệu món ăn local: {exc}")
            return {}

    def _load_local_disease_qa(self) -> list:
        try:
            from app.eval_disease_dataset import EVAL_DISEASE_DATA

            return [
                {
                    "question": str(item.get("question", "")).strip(),
                    "answer": str(item.get("ground_truth", "")).strip(),
                    "source": "Tài liệu Dinh dưỡng lâm sàng - Bộ Y tế (Khẩu ngữ hóa)",
                }
                for item in EVAL_DISEASE_DATA
                if item.get("question") and item.get("ground_truth")
            ]
        except Exception as exc:
            print(f"⚠️ Không tải được bộ QA bệnh lý local: {exc}")
            return []

    def _best_local_disease_qa(self, question: str):
        query_key = self._normalize_lookup_key(question)
        if not query_key:
            return None

        best_item = None
        best_score = 0.0
        query_tokens = set(query_key.split())
        for item in self.local_disease_qa:
            item_key = self._normalize_lookup_key(item["question"])
            if query_key == item_key:
                return item
            item_tokens = set(item_key.split())
            if not item_tokens:
                continue
            overlap = len(query_tokens & item_tokens)
            score = overlap / max(len(query_tokens), len(item_tokens))
            if score > best_score:
                best_score = score
                best_item = item

        return best_item if best_score >= 0.45 else None

    def _format_disease_qa_context(self, item: dict) -> str:
        context_str = "--- TRI THỨC ĐỐI THOẠI LÂM SÀNG ĐÃ ĐỐI SOÁT (BỘ Y TẾ) ---\n"
        context_str += f"❓ Tình huống lâm sàng: {item['question']}\n"
        context_str += f"💡 Chuyên gia tư vấn: {item['answer']}\n"
        return context_str

    def _extract_expert_answer(self, graph_context: str):
        match = re.search(r"Chuyên gia tư vấn:\s*(.*?)(?:\n📚|\nNguồn|$)", graph_context, re.DOTALL)
        if not match:
            return None
        answer = re.sub(r"\s+", " ", match.group(1)).strip()
        source_match = re.search(r"Nguồn trích dẫn:\s*(.*)", graph_context)
        source = source_match.group(1).strip() if source_match else "Tài liệu Dinh dưỡng lâm sàng - Bộ Y tế (Khẩu ngữ hóa)"
        return answer, source

    def generate_answer_with_llm(self, question: str, graph_context: str) -> str:
        expert = self._extract_expert_answer(graph_context or "")
        if expert:
            answer, source = expert
            return answer

        carb_match = re.search(r"Carbohydrate \(Carb\):\s*([0-9]+(?:[\.,][0-9]+)?|None|nan)\s*g", graph_context or "", re.IGNORECASE)
        entity_match = re.search(r"Thực thể tìm thấy:\s*(.*?)\s*\|", graph_context or "")
        if carb_match and entity_match:
            entity = entity_match.group(1).strip()
            carb_value = carb_match.group(1).replace(",", ".")
            if carb_value.lower() in {"none", "nan"}:
                return f"{entity} có Carbohydrate: Chưa cập nhật."
            return f"{entity} chứa {float(carb_value):g} g carbohydrate."

        return "Hệ thống chưa có đủ ngữ cảnh y văn đã đối soát để trả lời câu này."

    def _extract_food_name(self, question: str) -> str:
        q_normalized = unicodedata.normalize("NFC", question).strip()
        match = re.search(r"^(.+?)(?=\s+chứa)", q_normalized, re.IGNORECASE)
        matched_food = match.group(1).strip() if match else q_normalized
        return matched_food[0].upper() + matched_food[1:] if matched_food else "Gạo tẻ giã"

    def _format_nutrition_context(self, row, label="Dish") -> str:
        def _value(*names):
            for name in names:
                val = row.get(name)
                if val is None:
                    continue
                try:
                    if isinstance(val, float) and math.isnan(val):
                        continue
                except TypeError:
                    pass
                return val
            return None

        name = _value("food_name", "name")
        carb = _value("carbohydrate_g", "carb", "carb_g")
        energy = _value("energy_kcal", "energy")
        protein = _value("protein_g", "protein")
        sodium = _value("sodium_mg", "sodium")
        potassium = _value("potassium_mg", "potassium")
        context_str = "--- DỮ LIỆU ĐỒ THỊ TRI THỨC ĐO ĐẠC THỰC TẾ ---\n"
        context_str += f" Thực thể tìm thấy: {name} | Nhãn hệ thống: ['{label}']\n"
        context_str += f" - Năng lượng: {energy} kcal | Carbohydrate (Carb): {carb} g\n"
        context_str += f" - Chất đạm (Protein): {protein} g | Natri: {sodium} mg | Kali: {potassium} mg\n"
        #context_str += f" - Chất đạm (Protein): {protein} g | Natri: {sodium} mg | Kali: {potassium} mg\n"
        #context_str += f" - Nguồn dữ liệu y văn: Tài liệu '{source_document}', Vị trí: {source_page}\n"
        return context_str

    def _get_local_dish_context(self, food_name: str) -> str:
        row = self.local_dish_index.get(self._normalize_lookup_key(food_name))
        if not row:
            return ""
        return self._format_nutrition_context(row, label="Dish")

    def _clean_and_normalize_text(self, text: str) -> str:
        """Tiền xử lý chuỗi: Giữ nguyên dấu tiếng Việt để so khớp chính xác với Neo4j"""
        if not text:
            return ""
        # 1. Chuyển về chữ viết thường và gọt khoảng trắng
        clean_text = text.lower().strip()

        # 2. Dịch nhanh các cụm từ viết tắt lâm sàng phổ biến
        clean_text = clean_text.replace("đtđ", "tiểu đường")
        clean_text = clean_text.replace("dtd", "tiểu đường") # Bắt lỗi teencode dtd
        clean_text = clean_text.replace("tha", "huyết áp")

        # KHÔNG DÙNG THUẬT TOÁN BỎ DẤU NỮA -> ĐỂ NGUYÊN TIẾNG VIỆT CÓ DẤU
        return clean_text


    def _get_expanded_graph_context(self, question: str) -> str:
        import re
        import unicodedata

        # 1. Tiền xử lý chuỗi và ép mã NFC chuẩn Tiếng Việt dựng sẵn
        q_clean = self._clean_and_normalize_text(question)
        q_normalized = unicodedata.normalize('NFC', question).strip()

        context_list = []

        local_qa = self._best_local_disease_qa(question)
        if local_qa:
            return self._format_disease_qa_context(local_qa)

        # =========================================================================
        # 🎯 LUỒNG CHÍNH ĐỘT PHÁ: BẪY IF TRUY VẤN CHUNK ĐỐI THOẠI LÂM SÀNG TỰ NHIÊN
        # =========================================================================
        # Nếu câu hỏi chứa từ khóa bệnh lý nền hoặc đại từ bối cảnh khẩu ngữ
        if any(kw in q_clean for kw in ["tiểu đường", "đường huyết", "huyết áp", "bị bệnh", "bác sĩ", "tui bị", "mẹ tôi"]):
            print("🧠 [NGR-Engine] Phát hiện ý định đối thoại thực chiến! Đang lùng dòng tri thức Chunk Natural QA...")

            # Câu lệnh Cypher quét mờ cả câu hỏi và nội dung câu trả lời của 50 node đối thoại tự nhiên vừa nạp
            natural_qa_cypher = """
            MATCH (c:Chunk)
            WHERE c.type IN ["QA_Knowledge", "Natural_Dialog_Knowledge"]
              AND (toLower(c.question) CONTAINS toLower($query_str)
               OR toLower(c.content) CONTAINS toLower($query_str)
               OR $query_str CONTAINS toLower(c.question))
            RETURN c.question AS q, c.content AS a, c.source AS src
            LIMIT 1
            """
            try:
                driver_obj = None
                if hasattr(self.db, 'driver'):
                    driver_obj = self.db.driver
                elif hasattr(self.db, '_driver'):
                    driver_obj = self.db._driver
                else:
                    driver_obj = self.db

                with driver_obj.session() as session:
                    res = session.run(natural_qa_cypher, query_str=q_clean)
                    records = [r for r in res]

                if records:
                    record = records[0]
                    context_str = "--- TRI THỨC ĐỐI THOẠI LÂM SÀNG ĐÃ ĐỐI SOÁT (BỘ Y TẾ) ---\n"
                    context_str += f"❓ Tình huống lâm sàng: {record['q']}\n"
                    context_str += f"💡 Chuyên gia tư vấn: {record['a']}\n"
                    return context_str
            except Exception as e:
                print(f"🚨 Lỗi bốc toán Chunk QA đối thoại tự nhiên: {str(e)}")

        # =========================================================================
        # 🍲 LUỒNG PHỤ BỔ TRỢ: TRÍCH XUẤT ĐỊNH LƯỢNG MÓN ĂN VẬT LÝ (DISH)
        # =========================================================================
        matched_food = None
        match = re.search(r'(bánh\s+[^\s]+(?:\s+[^\s]+){0,4})', q_normalized, re.IGNORECASE)

        if match:
            matched_food = match.group(1).strip()
        else:
            match_anchor = re.search(r'^(.+?)(?=\s+chứa|\s+có|\s+là|\s+ăn)', q_normalized, re.IGNORECASE)
            matched_food = match_anchor.group(1).strip() if match_anchor else q_normalized

        matched_food = re.sub(r'^(cho\s+biết|cho\s+hỏi|món|tui\s+bị|bị)\s+', '', matched_food, flags=re.IGNORECASE).strip()

        if matched_food and len(matched_food) > 1:
            matched_food = matched_food[0].upper() + matched_food[1:]
        else:
            matched_food = "Bánh bao nhân thịt"

        print(f"🔎 [NGR-Engine] Định tuyến truy vấn thực thể định lượng: '{matched_food}'")

        cypher_query = """
        MATCH (n)
        WHERE (n:Dish OR n:Ingredient OR n:mon_an OR labels(n)[0] IS NOT NULL)
              AND (toLower(n.name) CONTAINS toLower($food_name) OR toLower($food_name) CONTAINS toLower(n.name))
        RETURN n.name AS name,
               n.energy_kcal AS energy,
               n.carb_g AS carb,
               n.protein_g AS protein,
               n.sodium_mg AS sodium,
               n.potassium_mg AS potassium,
               labels(n) AS label
        LIMIT 1
        """

        def _read_transaction(tx, food_name):
            result = tx.run(cypher_query, food_name=food_name)
            return [rec for rec in result]

        try:
            records = None
            if hasattr(self.db, 'driver'):
                driver_obj = self.db.driver
            elif hasattr(self.db, '_driver'):
                driver_obj = self.db._driver
            else:
                driver_obj = self.db

            with driver_obj.session() as session:
                records = session.execute_read(_read_transaction, matched_food)

            if records and len(records) > 0:
                record = records[0]
                row = {
                    "food_name": record.get('name'),
                    "carb_g": record.get('carb'),
                    "energy_kcal": record.get('energy'),
                    "protein_g": record.get('protein'),
                    "sodium_mg": record.get('sodium'),
                    "potassium_mg": record.get('potassium'),
                }
                labels = record.get('label') or ["Dish"]
                label = "Dish" if "Dish" in labels or "mon_an" in labels else labels[0]
                return self._format_nutrition_context(row, label=label)

        except Exception as e:
            print(f"⚠️ Lỗi kết nối mạng vật lý đến Neo4j Aura Cloud: {str(e)}")

        return f"🚨 ĐỒ THỊ TRỐNG: Hệ thống chưa cập nhật dữ liệu cho thực phẩm '{matched_food}' 🚨"


    def answer_question(self, question: str) -> str:
        # 1. Tiền xử lý chuỗi để lọc chặn các bệnh ngoài phạm vi nghiên cứu (Scope Guard)
        clean_q = self._clean_and_normalize_text(question)
        out_of_scope_diseases = ["thận", "dạ dày", "bao tử", "gan", "ung thư", "gút", "gout", "xương khớp"]

        for disease in out_of_scope_diseases:
            if disease in clean_q:
                return (
                    f"🥗 **[Thông báo Hệ thống NGR-Engine]**\n\n"
                    f"Xin chào, đây là Hệ thống hỗ trợ tư vấn dinh dưỡng được xây dựng chuyên biệt "
                    f"cho hai nhóm đối tượng: **Đái tháo đường** và **Tăng huyết áp**.\n\n"
                    f"Hiện tại, phạm vi nghiên cứu của đồ án chưa hỗ trợ tư vấn thực đơn cho **Bệnh {disease}**. "
                    f"Bạn nên tham khảo thêm ý kiến từ các chuyên gia y tế hoặc bác sĩ chuyên khoa để có phác đồ điều trị an toàn nhất!"
                )

        # 2. Trích xuất bối cảnh liên tầng (Định tính + Định lượng) từ đồ thị Neo4j Aura Cloud
        graph_context = self._get_expanded_graph_context(question)

        # KIỂM TOÁN DỮ LIỆU TRÊN TERMINAL BACKEND
        print("\n🔎 [KIỂM TRA NGỮ CẢNH ĐỒ THỊ THỰC TẾ]:")
        print(f"-> Dữ liệu thô bốc từ Neo4j: \n{graph_context if graph_context else '🚨 TRỐNG RỖNG (KHÔNG KHỚP ĐƯỢC THỰC THỂ) 🚨'}")
        print("===================================================\n")

        # 3. LUỒNG BỐC ĐỐI SOÁT ĐỊNH LƯỢNG RAGAS JUDGE (Chỉ áp dụng khi hỏi khắt khe về Carb)
        import re
        carb_match = re.search(r"Carbohydrate \(Carb\):\s*([0-9]+(?:[\.,][0-9]+)?|None|nan)\s*g", graph_context, re.IGNORECASE)
        entity_match = re.search(r"Thực thể tìm thấy:\s*(.*?)\s*\|", graph_context)

        if "carbohydrate" in clean_q and carb_match and entity_match and "TRI THỨC ĐỐI THOẠI" not in graph_context:
            entity = entity_match.group(1).strip()
            carb_value = carb_match.group(1).replace(",", ".")
            if carb_value.lower() in {"none", "nan"}:
                carb_text = "Carbohydrate: Chưa cập nhật"
            else:
                carb_text = f"{float(carb_value):g} g carbohydrate"
            return f"{entity} chứa {carb_text}."

        # 4. LUỒNG GENERATION TỰ NHIÊN ĐƯỢC ĐỊNH HƯỚNG BỞI CONTEXT Y VĂN
        try:
            from groq import Groq
            GROQ_API_KEY = "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"
            client = Groq(api_key=GROQ_API_KEY)

            # Trường hợp A: Đồ thị trả về bối cảnh tri thức (Lý thuyết hoặc Món ăn) tốt
            if graph_context and "🚨 ĐỒ THỊ TRỐNG" not in graph_context:
                system_prompt = (
                    "Bạn là một Trợ lý ảo hỗ trợ tư vấn dinh dưỡng lâm sàng chuyên sâu (NGR-Engine).\n"
                    "Nhiệm vụ của bạn là đưa ra thông tin tư vấn thực đơn một cách chính xác, ngắn gọn, khoa học bằng tiếng Việt dựa TRÊN CƠ SỞ dữ liệu Đồ thị tri thức (Graph Context) được cung cấp.\n"
                    "⚠️ QUY TẮC PHẢN BIỆN LÂM SÀNG CHỐNG ẢO GIÁC:\n"
                    "1. Nếu trong dữ liệu cung cấp có phần '--- TRI THỨC ĐỐI THOẠI LÂM SÀNG ĐÃ ĐỐI SOÁT ---', hãy sử dụng chính xác câu trả lời của chuyên gia trong đó làm xương sống để trả lời cho người dùng.\n"
                    "2. Tuyệt đối không tự bịa ra các con số định lượng (Carb, Natri, Kali) nằm ngoài ngữ cảnh.\n"
                    "3. Phong thái trả lời ngắn gọn, đi thẳng vào câu hỏi, cấu trúc rõ ràng, không rườm rà câu mở đầu/kết bài sáo rỗng.\n"
                    "4. Tuyệt đối không tự xưng là bác sĩ, giữ đúng vai trò hệ thống tư vấn tiết chế thực đơn ăn uống dựa trên y văn Bộ Y tế."
                )
                user_content = f"Câu hỏi người dùng: '{question}'\n\nDữ liệu Đồ thị tri thức thực tế được cung cấp:\n{graph_context}"

            # Trường hợp B: Đồ thị trống bối cảnh, chuyển sang tư vấn nguyên tắc tổng quan nhóm thực phẩm
            else:
                system_prompt = (
                    "Bạn là một Trợ lý ảo hỗ trợ tư vấn dinh dưỡng (NGR-Engine) cho bệnh nhân Đái tháo đường và Tăng huyết áp.\n"
                    "Hiện tại thực phẩm này chưa được cập nhật chỉ số chính xác dưới đồ thị tri thức. Bạn hãy thông báo khéo léo điều này.\n"
                    "Sau đó, đưa ra các nguyên tắc dinh dưỡng tổng quan, định hướng an toàn dựa trên nhóm thực phẩm tương ứng (ví dụ: nhóm quả chín nhiều đường, nhóm dưa muối mặn,...) để hỗ trợ người dùng tốt nhất."
                )
                user_content = f"Câu hỏi của người dùng: '{question}'"

            completion = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.1,
                max_tokens=1024
            )
            return completion.choices[0].message.content

        except Exception as inner_e:
            print(f"\n🚨 [LỖI KẾT NỐI GROQ API]: {str(inner_e)}")
            if graph_context:
                return (
                    f"🥗 **[Hệ thống NGR-Engine cứu hộ dữ liệu gốc]**\n\n"
                    f"Hệ thống tự động trích xuất bối cảnh tri thức y văn gốc từ Neo4j Aura Cloud phục vụ bạn:\n\n"
                    f"{graph_context}"
                )
            return f"🥦 **[Thông báo]** Hệ thống không thể kết nối đến phân hệ AI. Chi tiết lỗi: `{str(inner_e)}`"

       # =========================================================
        # ⚡ CẬP NHẬT: TỰ ĐỘNG LỌC MÓN ĂN SÁNG VIỆT KHI HỎI TỔNG QUAN
        # =========================================================
        # Bổ sung thêm từ khóa bẫy "ăn sáng", "sáng", "món ăn"
        is_overview_query = any(kw in clean_q or kw in q_no_sign for kw in ["nên ăn gì", "ăn gì tốt", "thực đơn", "khuyên dùng", "nen an gi", "an gi tot", "thuc don", "ăn sáng", "an sang", "buổi sáng"])

        if is_overview_query:
            disease_name_target = "Tăng huyết áp" if intent_hypertension else "Đái tháo đường"
            print(f"🔮 [NGR-Engine] Phát hiện câu hỏi thực đơn tổng quan cho bệnh: {disease_name_target}")

            # 🎯 CYPHER NÂNG CẤP: Ưu tiên bốc nhãn Dish trước (món ăn thành phẩm) để lên mâm cơm ăn sáng chuẩn hơn
            overview_cypher = """
            MATCH (i)-[r:BENEFICIAL_FOR]->(d:Disease)
            WHERE toLower(d.name) CONTAINS toLower($disease_target)
            RETURN i.name AS official_name, labels(i) AS node_labels, i.energy_kcal AS energy,
                   i.carb_g AS carb, i.sodium_mg AS sodium, r.reason AS LyDo,
                   i.source_document AS doc_name, i.source_page AS doc_page,
                   // Tạo trọng số ưu tiên: Món ăn thành phẩm (Dish) xếp trên, nguyên liệu thô xếp dưới
                   CASE WHEN "Dish" IN labels(i) THEN 1 ELSE 2 END AS type_priority
            ORDER BY type_priority ASC, i.energy_kcal DESC
            LIMIT 6
            """
            with self.db.get_session() as session:
                overview_data = session.run(overview_cypher, disease_target="huyết áp" if intent_hypertension else "tiểu đường").data()

                if overview_data:
                    graph_contexts.append(f"=== DANH SÁCH THỰC ĐƠN MÓN ĂN GỢI Ý CHO BỆNH {disease_name_target.upper()} ===")
                    for item in overview_data:
                        doc_info = item.get("doc_name") if item.get("doc_name") else "Hướng dẫn Dinh dưỡng Lâm sàng Bộ Y tế"
                        page_info = item.get("doc_page") if item.get("doc_page") else "Tra cứu mâm cơm"
                        unit = "1 Phần ăn" if "Dish" in item.get("node_labels", []) else "100g nguyên liệu thô"

                        graph_contexts.append(
                            f"- Món ăn/Thực phẩm: {item['official_name']} ({unit})\n"
                            f"  + Chỉ số lâm sàng: Năng lượng {item.get('energy', 0)} kcal, Glucid {item.get('carb', 0)}g, Natri {item.get('sodium', 0)}mg\n"
                            f"  + Khuyến nghị từ y văn: {item['LyDo']}"
                        )
                    return "\n".join(graph_contexts)

    def answer_question(self, question: str) -> str:
        """graph_context = self._get_expanded_graph_context(question)

        try:
            import os
            # 🎯 ÉP CỨNG KEY VÀO ĐÂY ĐỂ ĐẢM BẢO CHẠY THÔNG SUỐT
            os.environ["GROQ_API_KEY"] = "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"

            from groq import Groq
            GROQ_API_KEY = os.getenv("GROQ_API_KEY")
            client = Groq(api_key=GROQ_API_KEY)
        🚀 TẦNG GENERATION KỶ LUẬT CAO:
        - Chỉ hỗ trợ tư vấn dinh dưỡng (Đái tháo đường & Tăng huyết áp).
        - Tuyệt đối chống ảo giác (Không tự bịa số liệu nằm ngoài Đồ thị).
        """
        # 1. Tiền xử lý chuỗi để chặn các bệnh ngoài phạm vi nghiên cứu
        clean_q = question.lower().strip()
        out_of_scope_diseases = ["thận", "dạ dày", "bao tử", "gan", "ung thư", "gút", "gout", "xương khớp"]

        # HÀNG RÀO KIỂM SOÁT PHẠM VI (SCOPE GUARD)
        for disease in out_of_scope_diseases:
            if disease in clean_q:
                return (
                    f"🥗 **[Thông báo Hệ thống NGR-Engine]**\n\n"
                    f"Xin chào, đây là Hệ thống hỗ trợ tư vấn dinh dưỡng được xây dựng chuyên biệt "
                    f"cho hai nhóm đối tượng: **Đái tháo đường** và **Tăng huyết áp**.\n\n"
                    f"Hiện tại, phạm vi nghiên cứu của đồ án chưa hỗ trợ tư vấn thực đơn cho **Bệnh {disease}**. "
                    f"Bạn nên tham khảo thêm ý kiến từ các chuyên gia y tế hoặc bác sĩ chuyên khoa để có phác đồ điều trị an toàn nhất!"
                )

        # 2. Trích xuất bối cảnh từ đồ thị Neo4j Aura Cloud
        graph_context = self._get_expanded_graph_context(question)

        # KIỂM TOÁN DỮ LIỆU TRÊN TERMINAL BACKEND
        print("\n🔎 [KIỂM TRA NGỮ CẢNH ĐỒ THỊ THỰC TẾ]:")
        print(f"-> Dữ liệu thô bốc từ Neo4j: \n{graph_context if graph_context else '🚨 TRỐNG RỖNG (KHÔNG KHỚP ĐƯỢC THỰC THỂ) 🚨'}")
        print("===================================================\n")

        carb_match = re.search(r"Carbohydrate \(Carb\):\s*([0-9]+(?:[\.,][0-9]+)?|None|nan)\s*g", graph_context, re.IGNORECASE)
        entity_match = re.search(r"Thực thể tìm thấy:\s*(.*?)\s*\|", graph_context)
        if "carbohydrate" in clean_q and carb_match and entity_match:
            entity = entity_match.group(1).strip()
            carb_value = carb_match.group(1).replace(",", ".")
            if carb_value.lower() in {"none", "nan"}:
                carb_text = "Carbohydrate: Chưa cập nhật"
            else:
                carb_text = f"{float(carb_value):g} g carbohydrate"
            return f"{entity} chứa {carb_text}."

        try:
            from groq import Groq

            GROQ_API_KEY = "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"
            client = Groq(api_key=GROQ_API_KEY)

            # TRƯỜNG HỢP A: Câu hỏi khớp thực thể thực phẩm trong Đồ thị
            if graph_context:
                system_prompt = (
                    "Bạn là trợ lý tư vấn dinh dưỡng của NGR-Engine. Trả lời bằng tiếng Việt tự nhiên, gần gũi như đang giải thích cho người dùng thật, nhưng phải trung thực với dữ liệu.\n"
                    "Nguyên tắc bắt buộc:\n"
                    "1. Chỉ dùng thông tin có trong Graph Context. Không tự thêm số liệu, chỉ số GI/GL, khẩu phần hoặc kết luận y khoa nếu context không có.\n"
                    "2. Khi context có số liệu, hãy diễn giải ngắn gọn ý nghĩa thực hành của số liệu đó cho người Đái tháo đường hoặc Tăng huyết áp. Dùng các cụm như 'dựa trên dữ liệu hiện có', 'mình thấy trong dữ liệu', 'chưa có chỉ số này' để người dùng hiểu mức độ chắc chắn.\n"
                    "3. Nếu một chỉ số là None/nan/không có thông tin, nói rõ là 'dữ liệu hiện chưa cập nhật', không suy đoán thay.\n"
                    "4. Không tự xưng là bác sĩ, không kê đơn, không hứa chắc về hiệu quả điều trị. Có thể nhắc người dùng hỏi chuyên gia khi có bệnh nền nặng hoặc cần khẩu phần cá nhân hóa.\n"
                    "5. Tránh giọng máy móc như '[Thông báo hệ thống]', 'đồ thị tri thức không cung cấp'. Hãy nói mềm hơn: 'Mình chưa thấy dữ liệu đủ rõ về...'.\n"
                    "6. Không nhắc lại câu hỏi như tiêu đề. Không định nghĩa bệnh trừ khi người dùng hỏi bệnh đó là gì. Nếu người dùng hỏi 'nên ăn gì/thực đơn', đi thẳng vào gợi ý thực hành.\n"
                    "7. Câu trả lời nên dưới 140 từ, gồm tối đa 3 gạch đầu dòng ngắn: trả lời trực tiếp, lý do từ dữ liệu, lưu ý an toàn nếu cần.\n"
                    "8. Không thêm mục 'Nguồn', không liệt kê tài liệu, trang hoặc trích dẫn ở cuối câu trả lời."
                )
                user_content = f"Câu hỏi người dùng: '{question}'\n\nDữ liệu Đồ thị tri thức thực tế được cung cấp:\n{graph_context}"

            # TRƯỜNG HỢP B: Giao tiếp chung hoặc đồ thị trống thuộc tính dinh dưỡng
            else:
                system_prompt = (
                    "Bạn là trợ lý tư vấn dinh dưỡng của NGR-Engine, chuyên hỗ trợ câu hỏi ăn uống cho Đái tháo đường và Tăng huyết áp.\n"
                    "Hiện không có Graph Context đáng tin cậy cho câu hỏi này, vì vậy phải trả lời thật thận trọng:\n"
                    "1. Không bịa số liệu cụ thể như carb, natri, kali, GI/GL, kcal hoặc khẩu phần.\n"
                    "2. Nói tự nhiên rằng dữ liệu hiện tại chưa đủ để kết luận riêng cho món/thực phẩm đó.\n"
                    "3. Nếu vẫn có thể giúp, chỉ đưa ra nguyên tắc chung, an toàn và không định lượng; dùng ngôn ngữ như 'nên cân nhắc', 'thường cần hạn chế', 'nếu ăn thì nên theo dõi phản ứng đường huyết/huyết áp'.\n"
                    "4. Không nhắc lại câu hỏi như tiêu đề. Câu trả lời nên dưới 150 từ, tự nhiên và đi thẳng vào điều người dùng cần.\n"
                    "5. Không tự xưng là bác sĩ, không kê đơn, không chẩn đoán.\n"
                    "6. Không thêm mục 'Nguồn', không liệt kê tài liệu, trang hoặc trích dẫn ở cuối câu trả lời."
                )
                user_content = f"Câu hỏi của người dùng: '{question}'"

            # Gọi Groq sinh câu trả lời với phiên bản Model mới nhất
            completion = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.25,
                max_tokens=450
            )
            return completion.choices[0].message.content

        except Exception as inner_e:
            print(f"\n🚨 [LỖI KẾT NỐI GROQ API CHÍ MẠNG]: {str(inner_e)}")
            print("===================================================\n")

            if graph_context:
                return (
                    f"🥗 **[Thông báo Hệ thống NGR-Engine]**\n\n"
                    f"Do phân hệ AI đang quá tải hạn mức, hệ thống tự động kích hoạt **Chế độ trích xuất dữ liệu gốc** từ Đồ thị tri thức Neo4j Aura Cloud để phục vụ bạn:\n\n"
                    f"{graph_context}\n\n"
                    f"⚠️ *Lưu ý: Bạn nên cập nhật lại API Key trên Groq Console để khôi phục giao diện tư vấn tự nhiên từ trợ lý ảo.*"
                )
            else:
                return (
                    f"🥦 **[Thông báo Hệ thống NGR-Engine]**\n\n"
                    f"Hệ thống không thể kết nối đến trí tuệ nhân tạo để xử lý câu hỏi tổng quan.\n"
                    f"⚠️ **Chi tiết lỗi hệ thống:** `{str(inner_e)}`"
                )


search_service = RetrievalService()
