# Đặc tả định dạng cho báo cáo tiến độ lần 5

- Tài liệu tham chiếu: `I:\nam4\phan tich anh phat giao\report-GK-CK\thamkhao\Huong dan trinh bay khoa luan TN, do an TN.docx`.
- SHA-256 tham chiếu: `A4967E47864E7F41F81D9B72A3DAC951C53A5952F7353405D5793DD9AC3A9E45`.
- Tài liệu có 2 section, giấy A4 dọc. Phần hướng dẫn soạn thảo nêu rõ: Times New Roman 13 pt; giãn dòng 1,5; lề trên 3,5 cm, dưới 3 cm, trái 3,5 cm, phải 2 cm; số trang ở giữa đầu trang; dòng đầu đoạn thụt một tab.
- Section đầu của tài liệu mẫu dùng chính các lề trên. Section thứ hai có lề khác do các mẫu biểu/phần minh họa; không áp dụng cho phần thân báo cáo. Bản báo cáo lần 5 hiện đã đúng A4, lề và có số trang giữa đầu trang ở section nội dung.
- Cách áp dụng: giữ bìa và cấp tiêu đề hiện hữu; đồng nhất kiểu chữ Times New Roman; đưa nội dung thân, danh mục, chú thích hình/bảng và chữ trong bảng về 13 pt; đặt giãn dòng 1,5 cho phần nội dung và bảng; thụt đầu dòng 1 tab cho đoạn văn xuôi căn đều hai lề. Giữ căn giữa và vị trí chú thích hình dưới hình, tiêu đề bảng trên bảng, danh mục hình/bảng và phân cấp tiêu đề.
- Nội dung cần bảo toàn: 2 section, 27 bảng, 37 hình minh họa trong thân bài, 12 trường hợp demo, ghi chú/nhận xét ngay dưới kết quả, bìa, trường dữ liệu, trường số trang, quan hệ ảnh và các thành phần OOXML không liên quan.
- Gói DOCX chỉ dự kiến thay đổi `word/document.xml` và `word/styles.xml`; mọi thành phần khác được kiểm tra theo mã băm.
- Hạn chế kiểm tra trực quan: `render_docx.py` không thể khởi chạy vì máy Windows không có `soffice.exe`; Word COM cũng không tạo được phiên do lỗi logon session. Ghi nhận kiểm tra cấu trúc và kiểu định dạng bằng OOXML sau khi chỉnh.
