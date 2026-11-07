# Kết quả cải thiện phân loại tư thế

Run: `20261103_convnext_branches`. Ngày lập: 03/11/2026.

Giữ nguyên 612 mẫu train, 136 validation, 125 test; giữ quan hệ L1–L2 và cơ chế từ chối theo đề tài.

Các vòng học lại phần phân loại trên đặc trưng cũ không đạt tất cả điều kiện nên không thay bản demo. Vòng ConvNeXt tinh chỉnh trực tiếp hai mạng từ trọng số ImageNet, lấy mẫu cân bằng hơn giữa các lớp trong train. Mẫu L2 trống chỉ học nhóm L1 và bằng chứng, không bị ép vào nhãn chi tiết.

Ứng viên chọn bằng validation: `convnext_branches_baseline0.5`.

**Trạng thái demo: chưa kích hoạt; giữ mô hình đang dùng.**

| Chỉ số validation | Mốc | Ứng viên |
|---|---:|---:|
| Accuracy L1 | 0.8971 | 0.9191 |
| Macro-F1 L1 | 0.8638 | 0.8971 |
| Macro-F1 L2 toàn quy trình | 0.3334 | 0.5600 |
| Macro-recall L2 | 0.2782 | 0.4876 |
| Precision L2 gộp | 0.9744 | 0.9538 |
| Tỷ lệ trả L2 trên mẫu trống | 0.0000 | 0.0333 |

Kiểm định ngưỡng qua ba fold theo hiện vật: macro-F1 0.5474, precision 0.9118, tỷ lệ trả L2 trên mẫu trống 0.0333.

## Kiểm tra trên test lịch sử

| Chỉ số | Mốc | Ứng viên |
|---|---:|---:|
| Accuracy L1 | 0.9040 | 0.8880 |
| Macro-F1 L1 | 0.8546 | 0.8386 |
| Macro-F1 L2 toàn quy trình | 0.2268 | 0.4369 |
| Tỷ lệ trả đúng L2 trên mẫu có L2 | 0.3204 | 0.5340 |
| Precision L2 gộp | 0.8462 | 0.8333 |
| Tỷ lệ trả L2 trên mẫu trống | 0.0909 | 0.0000 |
| Số lớp có ít nhất một mẫu L2 đúng | 4.0000 | 9.0000 |

| Lớp | Nhãn | Số mẫu | Đúng trước | Đúng sau | Precision sau | Recall sau | F1 sau |
|---|---|---:|---:|---:|---:|---:|---:|
| C2.1 | Ngồi bắt chéo khóa kín | 37 | 18 | 31 | 0.9688 | 0.8378 | 0.8986 |
| C2.2 | Ngồi bắt chéo không khóa kín | 4 | 0 | 0 | 0.0000 | 0.0000 | 0.0000 |
| C2.3 | Ngồi một chân co, một chân thả | 17 | 7 | 7 | 0.7778 | 0.4118 | 0.5385 |
| C2.4 | Ngồi hai chân thả | 6 | 0 | 1 | 1.0000 | 0.1667 | 0.2857 |
| C2.5 | Quỳ/ngồi trên gót | 6 | 0 | 1 | 1.0000 | 0.1667 | 0.2857 |
| C2.6 | Đứng thẳng, hai chân trụ | 3 | 1 | 3 | 0.5000 | 1.0000 | 0.6667 |
| C2.7 | Đứng lệch trọng tâm | 7 | 0 | 3 | 0.5000 | 0.4286 | 0.4615 |
| C2.8 | Một chân trụ, chân kia co/nâng | 3 | 0 | 1 | 0.5000 | 0.3333 | 0.4000 |
| C2.9 | Bước/chuyển hướng | 8 | 0 | 3 | 0.7500 | 0.3750 | 0.5000 |
| C2.10 | Động/múa | 4 | 0 | 0 | 0.0000 | 0.0000 | 0.0000 |
| C2.11 | Nằm nghiêng | 8 | 7 | 5 | 1.0000 | 0.6250 | 0.7692 |

Các lớp chưa trả đúng L2 trên test: C2.2 (Ngồi bắt chéo không khóa kín), C2.10 (Động/múa).

### Phân tích vị trí phát sinh lỗi

Mỗi mẫu có L2 được xếp vào một trong bốn trường hợp theo thứ tự: sai nhóm L1; đúng L1 nhưng chọn sai ứng viên L2; chọn đúng ứng viên nhưng bị ngưỡng giữ lại; trả đúng L2. Các cột sau vì vậy không đếm trùng.

| Lớp | Train | Validation | Sai L1 | Sai ứng viên L2 | Đúng ứng viên nhưng bị giữ lại | Trả đúng L2 |
|---|---:|---:|---:|---:|---:|---:|
| C2.1 | 195 | 41 | 1 | 3 | 2 | 31 |
| C2.2 | 24 | 4 | 0 | 3 | 1 | 0 |
| C2.3 | 82 | 19 | 1 | 3 | 6 | 7 |
| C2.4 | 22 | 4 | 0 | 4 | 1 | 1 |
| C2.5 | 23 | 6 | 1 | 3 | 1 | 1 |
| C2.6 | 32 | 5 | 0 | 0 | 0 | 3 |
| C2.7 | 35 | 7 | 2 | 2 | 0 | 3 |
| C2.8 | 16 | 3 | 2 | 0 | 0 | 1 |
| C2.9 | 33 | 5 | 1 | 0 | 4 | 3 |
| C2.10 | 29 | 6 | 3 | 1 | 0 | 0 |
| C2.11 | 29 | 6 | 0 | 0 | 3 | 5 |

Sai L1 chặn đường tới nhãn con đúng; hạ ngưỡng L2 không sửa được lỗi này. Khi ứng viên L2 đã sai dù L1 đúng, mô hình chưa phân biệt tốt tư thế trong cùng nhóm. Khi ứng viên đúng nhưng bị giữ lại, hạn chế nằm ở độ tin cậy và cơ chế từ chối. Số liệu trên xác định vị trí lỗi trong quy trình, chưa chứng minh nguyên nhân thị giác như che khuất chân hay chất lượng ảnh; cần xem từng ảnh để kết luận những nguyên nhân đó.

Các lớp ít mẫu chỉ cung cấp ít trường hợp độc lập để học và kiểm tra. Lấy mẫu cân bằng giúp lớp hiếm xuất hiện thường xuyên hơn, nhưng không tạo thêm sự đa dạng của hiện vật. Hai mạng mới và ngưỡng theo nhánh đã tăng khả năng trả nhãn chi tiết, song chưa loại bỏ được nhầm lẫn giữa các nhóm tư thế.

Kiểm tra phát hành: không đạt. Số ảnh kiểm tra khớp suy luận từng ảnh: 0.

Ứng viên chưa được đưa vào demo: accuracy L1 giảm từ 0.9040 xuống 0.8880, precision L2 gộp thay đổi từ 0.8462 thành 0.8333. Mức tăng macro-F1 và số lớp nhận diện được chưa đủ để kết luận chất lượng tốt hơn trên mọi tiêu chí. Checkpoint mới vẫn được lưu để tái lập thí nghiệm. Không điều chỉnh lại ngưỡng theo lỗi test vừa quan sát.

## Cách diễn giải và giới hạn

Precision L2 gộp tính cả nhãn chi tiết trả sai trên mẫu L2 trống. Không so trực tiếp với selective accuracy chỉ tính trên mẫu có nhãn L2 của bảng cũ. Khi một lớp không có dự đoán, precision được quy ước là 0; điều đó khác với có dự đoán nhưng sai hết.

Ngưỡng mới kiểm soát precision gộp, không bảo đảm 90% cho từng lớp. Các lớp có ít mẫu vẫn có độ bất định lớn. Tập validation đã được dùng nhiều lần trong phát triển; cross-fitting ở đây chỉ kiểm tra ngưỡng, không phải nested cross-validation của cả quá trình học. Test cũng là benchmark lịch sử đã được xem trước; cần một tập độc lập mới để xác nhận khả năng khái quát hóa.

Bộ ước lượng keypoint và baseline keypoint được giữ để đối chiếu; lần thử này không chứng minh PCK/OKS tăng. Chỉ sử dụng các số liệu thực sự đo được để kết luận về bộ phân loại ảnh.

Xem `QUALITY_V2_PROTOCOL.md`, `protocol.json`, `validation_trials.json`, `selection.json`, checkpoint và lịch sử để truy nguyên. Chạy lại `python quality_convnext.py` với nguyên cấu hình sẽ tiếp tục hoặc dùng lại checkpoint đã hoàn thành.
