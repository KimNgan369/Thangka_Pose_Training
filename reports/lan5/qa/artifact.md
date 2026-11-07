# Báo cáo tiến độ lần 5

## Tài liệu tham chiếu

- Tệp: `I:\nam4\phan tich anh phat giao\report-chốt\tuần 5-6-7-lần 4\52300129_52300131_BaoCaoTienDo_Lan4_PhanTichTuTheThangka_CapNhat_20261010_rev6.docx`
- SHA-256: `2c5752c2a5fbbd3e22899de11a75c418ae090c392c6d6a2ed7cfab8cf314daf9`
- Một section, khổ Letter 8,50 × 11,00 inch, lề trái/phải 0,82/0,78 inch, lề trên/dưới 0,75/0,72 inch.
- 29 ảnh kiểm tra tham chiếu có trong `qa/ref-*.png`; package inventory gốc nằm ở `qa/package_inventory.json`.

## Quy ước được giữ

- Dùng trang bìa, hệ chữ Times New Roman, phần đầu trang/cuối trang, section và các thành phần nhận diện từ báo cáo lần 4.
- Nội dung sau đoạn bìa được thay bằng cấu trúc báo cáo lần 5; bảng số liệu dùng kiểu bảng và đường viền của tài liệu tham chiếu.
- Chú thích ảnh và bảng dùng trường Word `SEQ`; danh mục hình và bảng dùng trường `TOC` theo nhãn tương ứng. `w:updateFields` bật để Word bổ sung số trang khi mở hoặc cập nhật trường.
- 37 hình, 27 bảng. Mười hai thẻ demo lấy từ kết quả suy luận đã lưu; mười sáu ảnh đánh giá pose của lượt chạy chính đều được thể hiện trong 13 hình chi tiết; 12 hình tổng hợp khác nằm trong phần nội dung chính.

## Kiểm tra cuối

- `qa/finalize.py` xác nhận package DOCX hợp lệ, số trường chú thích đúng, nội dung danh mục có đủ 37 hình và 27 bảng, mỗi hình có nhận xét đi kèm, 12 mã ca demo hiện diện và các package part không chỉnh sửa khớp tài liệu tham chiếu.
- Renderer của Documents không chạy được vì môi trường không có `soffice.exe`. Word COM trong phiên trước báo lỗi logon session; vì vậy bản mới chưa được kiểm tra bằng ảnh trang cuối. Các thẻ demo và hình ghép được kiểm tra trực tiếp dưới dạng ảnh nguồn.
