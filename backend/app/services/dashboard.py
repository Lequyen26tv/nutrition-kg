import os
import sys

# Thiết lập hệ thống sys.path định vị cấp thư mục chuẩn xác trên Windows
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))  # app/services
SERVICES_DIR = CURRENT_DIR
APP_DIR = os.path.dirname(SERVICES_DIR)                   # app
BACKEND_DIR = os.path.dirname(APP_DIR)                   # backend
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)              # nutrition_graph_rag

if BACKEND_DIR not in sys.path:
    sys.path.append(BACKEND_DIR)

from app.db.neo4j_connection import neo4j_db


class NutritionGraphDashboardService:
    def __init__(self):
        self.db = neo4j_db

    def render_system_overview(self):
        print("\n" + "═"*65)
        print("📊 BÁO CÁO BAO QUÁT TOÀN DIỆN HỆ THỐNG ĐỒ THỊ TRI THỨC NGR")
        print("═"*65)

        with self.db.get_session() as session:
            # 1. Thống kê chi tiết các Node (Thực thể)
            print("\n1. THỐNG KÊ THỰC THỂ (NODES):")
            node_query = """
            MATCH (n)
            RETURN labels(n)[0] AS Label, count(n) AS SoLuong
            ORDER BY SoLuong DESC
            """
            nodes = session.run(node_query).data()
            total_nodes = 0

            for node in nodes:
                label = node['Label'] if node['Label'] else "Chưa định nhãn"
                print(f"   🔹 Nhãn [{label:11}]: {node['SoLuong']:4} nodes")
                total_nodes += node['SoLuong']
            print(f"   👉 TỔNG SỐ LƯỢNG THỰC THỂ: {total_nodes} nodes")

            # 2. Thống kê chi tiết mối quan hệ (Relationships)
            print("\n2. THỐNG KÊ MỐI QUAN HỆ (RELATIONSHIPS):")
            rel_query = """
            MATCH ()-[r]->()
            RETURN type(r) AS LoaiQuanHe, count(r) AS SoLuong
            ORDER BY SoLuong DESC
            """
            rels = session.run(rel_query).data()
            total_rels = 0

            for rel in rels:
                print(f"   🔸 Liên kết [:{rel['LoaiQuanHe']:19}]: {rel['SoLuong']:4} links")
                total_rels += rel['SoLuong']
            print(f"   👉 TỔNG SỐ LƯỢNG ĐƯỜNG LIÊN KẾT : {total_rels} links")

            # 3. Tính toán mật độ kết nối (Graph Density / Avg Degree)
            print("\n3. CHỈ SỐ MẬT ĐỘ PHỨC HỢP ĐỒ THỊ:")
            if total_nodes > 0:
                avg_degree = total_rels / total_nodes
                print(f"   📈 Bậc kết nối trung bình (Avg Degree): {avg_degree:.2f}")
                print(f"      -> Ý nghĩa: Trung bình một nút có {avg_degree:.1f} sợi dây liên kết bổ trợ ngữ cảnh.")
            else:
                print("   📈 Mật độ kết nối: Đồ thị trống dữ liệu.")

            # 4. Kiểm tra các thuộc tính dưỡng chất động (Dynamic Properties)
            print("\n4. DANH SÁCH DƯỠNG CHẤT ĐỘNG TRONG HỆ THỐNG:")
            prop_query = """
            MATCH (i:Ingredient)
            UNWIND keys(i) AS key
            WITH DISTINCT key
            WHERE NOT key IN ['id', 'name', 'category']
            RETURN key AS Nutrient
            ORDER BY Nutrient ASC
            """
            props = session.run(prop_query).data()
            nutrient_list = [p['Nutrient'] for p in props]
            print(f"   🧬 Số lượng chất động nhận diện thành công: {len(nutrient_list)} thuộc tính.")
            if nutrient_list:
                # In thành các dòng, mỗi dòng tối đa 4 chất cho gọn
                chunks = [nutrient_list[i:i + 4] for i in range(0, len(nutrient_list), 4)]
                for chunk in chunks:
                    print(f"      * {', '.join(chunk)}")

            # 5. Kiểm tra phòng tuyến bảo vệ dữ liệu (Constraints)
            print("\n5. TRẠNG THÁI RÀNG BUỘC BẢO VỆ (CONSTRAINTS):")
            try:
                constraints = session.run("SHOW CONSTRAINTS").data()
                if constraints:
                    print(f"   ✅ Hệ thống đã kích hoạt thành công {len(constraints)} hàng rào UNIQUE.")
                    for c in constraints:
                        print(f"      - [{c.get('name')}]: {c.get('description')}")
                else:
                    print("   ⚠️ CẢNH BÁO: Chưa cấu hình ràng buộc bảo vệ! Dữ liệu có nguy cơ bị trùng lặp.")
            except Exception as e:
                print(f"   ❌ Không thể truy xuất thông tin ràng buộc: {str(e)}")

        print("\n" + "═"*65 + "\n")


if __name__ == "__main__":
    dashboard = NutritionGraphDashboardService()
    dashboard.render_system_overview()