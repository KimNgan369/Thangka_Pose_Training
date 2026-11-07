# Thống nhất nhãn ngày 30/10/2026

Ngân và My đã đồng thuận các quyết định dưới đây. Đây là bản đính chính nhãn/mô tả cho manifest đang dùng để huấn luyện, không phải kết quả do mô hình suy ra.

| Ảnh | Tập | Quyết định |
| --- | --- | --- |
| `THK000423_0c26cda164_2` | test | Giữ `C1.1/C2.2` (ngồi bắt chéo không khóa kín); sửa mô tả cũ nói `C2.3`. |
| `THK000443_230709b76a_2` | train | Giữ `C1.1/C2.2` (ngồi bắt chéo không khóa kín); sửa mô tả cũ nói `C2.1`. |
| `THK000025` | val | Đổi `C1.1` sang `C1.3` (chuyển động); để L2 trống. Đây là ca cưỡi linh thú được hai người chỉ định rõ. |
| `THK000010`, `THK000016`, `THK000078`, `THK000787` | train | Đổi `C1.1` sang `C1.3` theo quy tắc mọi tư thế cưỡi ngựa thuộc nhãn chuyển động; để L2 trống. |

Các ảnh cưỡi ngựa khác đã là `C1.3` thì không đổi nhãn. Đề xuất `C1.1` trong ghi chú cũ của `THK000092` được quyết định này thay thế. Quy tắc mới chỉ áp dụng cho **ngựa**, cùng ca cưỡi **nai/hươu `THK000025`** được nêu đích danh; không tự động đổi ảnh cưỡi la, sư tử, hổ hoặc rồng chưa được hội đồng phân xử.

Sau đính chính, manifest có 873 bản ghi; số lượng L1 là `C1.1=544`, `C1.2=114`, `C1.3=164`, `C1.4=51`. SHA-256 của `classification_manifest.csv`: `527fd2f85fd60af921e696272ffa3bb39dbf7ee41ac1763501330603b71637`.

Các tệp `thangka_pose_v1.1.0_dacntt_2026-10-20_*.json` là bản xuất lịch sử, không chỉnh sửa. Tập `test` vẫn giữ nguyên danh sách ảnh; việc sửa mô tả của một ảnh test không được dùng để chọn mô hình hay ngưỡng. Kết quả huấn luyện/đánh giá cũ phải được xem là kết quả trên phiên bản nhãn trước khi đính chính; cần chạy lại nếu muốn báo cáo theo manifest hiện tại.
