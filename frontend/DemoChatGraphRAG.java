import javax.swing.*;
import java.awt.*;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;

public class DemoChatGraphRAG extends JFrame {

    // 1. Khai báo các thành phần giao diện cá nhân hóa cho Khóa luận
    private JTextArea txtKhungChat;    // Khung hiển thị nội dung chat
    private JTextField txtONhapCauHoi; // Ô để bệnh nhân nhập câu hỏi
    private JButton btnGui;            // Nút bấm gửi dữ liệu

    // Đường link API kết nối thẳng đến Server FastAPI (Python) đang chạy
    private static final String URL_API_BACKEND = "http://127.0.0.1:8000/api/chat";

    public DemoChatGraphRAG() {
        // Cấu hình khung giao diện chính (JFrame)
        setTitle("HỆ THỐNG TRUY XUẤT DINH DƯỠNG LÂM SÀNG - GRAPH-RAG DEMO");
        setSize(650, 500);
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setLocationRelativeTo(null); // Đặt cửa sổ hiển thị ở chính giữa màn hình

        // Thiết lập khung hiển thị cuộc hội thoại
        txtKhungChat = new JTextArea();
        txtKhungChat.setEditable(false); // Khóa không cho sửa nội dung chat cũ
        txtKhungChat.setFont(new Font("Times New Roman", Font.PLAIN, 14));
        txtKhungChat.setLineWrap(true);       // Tự động xuống dòng khi câu dài
        txtKhungChat.setWrapStyleWord(true);   // Ngắt dòng chuẩn theo từ

        // Bọc khung chat vào thanh cuộn (JScrollPane) đề phòng câu trả lời y khoa rất dài
        JScrollPane thanhCuonChat = new JScrollPane(txtKhungChat);

        // Thiết lập ô nhập câu hỏi
        txtONhapCauHoi = new JTextField();
        txtONhapCauHoi.setFont(new Font("Times New Roman", Font.PLAIN, 14));

        // Thiết lập nút Gửi màu xanh hiện đại
        btnGui = new JButton("Gửi Câu Hỏi");
        btnGui.setFont(new Font("Times New Roman", Font.BOLD, 14));
        btnGui.setBackground(new Color(0, 122, 255));
        btnGui.setForeground(Color.WHITE);

        // Bố trí các nút bấm ở thanh phía dưới giao diện
        JPanel khungPhiaDuoi = new JPanel(new BorderLayout(10, 10));
        khungPhiaDuoi.setBorder(BorderFactory.createEmptyBorder(10, 10, 10, 10));
        khungPhiaDuoi.add(txtONhapCauHoi, BorderLayout.CENTER);
        khungPhiaDuoi.add(btnGui, BorderLayout.EAST);

        // Đưa tất cả vào khung giao diện chính
        add(thanhCuonChat, BorderLayout.CENTER);
        add(khungPhiaDuoi, BorderLayout.SOUTH);

        // 2. Cài đặt sự kiện click nút Gửi hoặc gõ phím Enter
        btnGui.addActionListener(e -> kichHoatLuongKetNoiMạng());
        txtONhapCauHoi.addActionListener(e -> kichHoatLuongKetNoiMạng());
    }

    /**
     * Thuật toán điều phối luồng xử lý: Tránh đơ giao diện Swing khi chờ LLM phản hồi
     */
    private void kichHoatLuongKetNoiMạng() {
        String cauHoi = txtONhapCauHoi.getText().trim();
        if (cauHoi.isEmpty()) return; // Ô trống thì bỏ qua không xử lý

        // Hiển thị ngay câu hỏi của người dùng và trạng thái chờ lên màn hình
        txtKhungChat.append("Bệnh nhân: " + cauHoi + "\n");
        txtKhungChat.append("Hệ thống: Đang kết nối đồ thị tri thức và xử lý lâm sàng, xin chờ...\n");
        txtONhapCauHoi.setText(""); // Xóa trống ô nhập câu hỏi

        // 🌟 BẮT BUỘC TRONG SWING: Tạo một Thread (luồng) chạy ngầm độc lập
        new Thread(() -> {
            // Gọi hàm bắn API sang Python để nhận câu trả lời
            String phanHoiTuBackend = guiYeuCauToiFastAPI(cauHoi);

            // Đổ dữ liệu ngược lại màn hình giao diện một cách an toàn
            SwingUtilities.invokeLater(() -> {
                txtKhungChat.append("\n🤖 Chuyên Gia Phản Hồi (NGR-Engine):\n" + phanHoiTuBackend + "\n");
                txtKhungChat.append("----------------------------------------------------------------------------------------------------\n");
            });
        }).start();
    }

    /**
     * Hàm lõi kết nối Client-Server sử dụng thư viện HttpClient (Chuẩn từ Java 11)
     */
    private String guiYeuCauToiFastAPI(String cauHoiNguoiDung) {
        try {
            // Bước A: Mã hóa cấu trúc chuỗi JSON thô gửi đi
            String cleanQuestion = cauHoiNguoiDung.replace("\"", "\\\"");
            String jsonPayload = "{\"question\":\"" + cleanQuestion + "\"}";

            // Bước B: Khởi tạo bộ điều phối HttpClient
            HttpClient client = HttpClient.newBuilder()
                    .connectTimeout(Duration.ofSeconds(10))
                    .build();

            // Bước C: Đóng gói gói tin Request HTTP POST kèm Header JSON
            HttpRequest request = HttpRequest.newBuilder()
                    .uri(URI.create(URL_API_BACKEND))
                    .timeout(Duration.ofSeconds(50))
                    .header("Content-Type", "application/json")
                    .POST(HttpRequest.BodyPublishers.ofString(jsonPayload))
                    .build();

            // Bước D: Thực thi truyền tải gói tin qua cổng mạng và nhận kết quả
            HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());

            if (response.statusCode() == 200) {
                // Giải mã dữ liệu JSON trả về từ FastAPI
                String jsonResult = response.body();
                return giaiMaTruongAnswer(jsonResult);
            } else {
                return "⚠️ Lỗi: Máy chủ Backend báo mã lỗi HTTP " + response.statusCode();
            }

        } catch (Exception ex) {
            return "❌ Lỗi kết nối: Không thể gửi tin tới Backend FastAPI. Hãy chắc chắn Uvicorn Server đang chạy! (Chi tiết: " + ex.getMessage() + ")";
        }
    }

    /**
     * Hàm bóc tách chuỗi thủ công tốc độ cao để lấy nội dung trường "answer"
     */
    private String giaiMaTruongAnswer(String jsonTho) {
        try {
            int viTriDau = jsonTho.indexOf("\"answer\":\"") + 10;
            int viTriCuoi = jsonTho.lastIndexOf("\"}");
            if (viTriDau > 9 && viTriCuoi > viTriDau) {
                String ketQua = jsonTho.substring(viTriDau, viTriCuoi);
                // Khôi phục các ký tự đặc biệt như xuống dòng (\n) từ chuỗi JSON
                return ketQua.replace("\\n", "\n").replace("\\t", "\t").replace("\\\"", "\"");
            }
        } catch (Exception e) {
            return jsonTho;
        }
        return jsonTho;
    }

    // 3. Hàm khởi chạy ứng dụng chính
    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> {
            DemoChatGraphRAG cuaSoChat = new DemoChatGraphRAG();
            cuaSoChat.setVisible(true); // Kích hoạt hiển thị giao diện
        });
    }
}