# Phân tích lỗi nhãn Level 2 trên tập test

Run: `20261112_115255_seed20261021`. Nguồn: `deployment/test_predictions.csv`, `SUMMARY.json` và `data/classification_manifest.csv`. Các nhận xét thị giác dưới đây dựa trên ảnh crop của các ví dụ nêu rõ, không suy rộng thành nguyên nhân chắc chắn cho toàn bộ tập.

## Kết quả cần diễn giải đúng

Tập test có 125 ảnh, trong đó 103 ảnh có nhãn L2 và 22 ảnh không gán L2. Mô hình ảnh được chọn cho demo đạt L1 đúng 111/125 (88,8%). Nếu cho sẵn L1 chuẩn, bộ phân loại L2 đúng 82/103 (79,6%). Trong quyết định cuối gồm dự đoán L1, kiểm tra bằng chứng và ngưỡng trả nhãn, L2 đúng 55/103 (53,4%); mô hình trả L2 trên 65/103 ảnh, trong đó 55 đúng. Với 22 ảnh L2 trống, mô hình vẫn trả nhãn chi tiết cho 3 ảnh. Vì vậy, không dùng chỉ số 79,6% để mô tả độ chính xác L2 của ứng dụng.

| Nhóm kết quả trên 103 ảnh có L2 | Số ảnh | Cách xác định |
|---|---:|---|
| Đúng L2 cuối cùng | 55 | Mã cuối trùng L2 chuẩn |
| Sai L1 | 12 | Dự đoán L1 khác L1 chuẩn, dẫn đến nhánh con sai |
| Sai ứng viên L2 | 18 | L1 đúng nhưng nhãn con có điểm cao nhất khác L2 chuẩn |
| Không qua ngưỡng L2 | 15 | Ứng viên L2 đúng nhưng chưa đủ điểm để trả nhãn chi tiết |
| Thiếu bằng chứng L2 | 3 | Ứng viên đúng nhưng bộ kiểm tra bằng chứng giữ ở L1 |

Các nhóm loại trừ nhau và cộng đúng 103 ảnh. “Không qua ngưỡng” và “thiếu bằng chứng” là lý do kỹ thuật cho quyết định L1, không tự chứng minh ảnh thiếu thông tin thị giác.

## Lớp nào đang yếu

| L2 | Ảnh train | Ảnh test | Đúng L2 cuối |
|---|---:|---:|---:|
| C2.1 | 195 | 37 | 30 |
| C2.2 | 24 | 4 | 0 |
| C2.3 | 82 | 17 | 8 |
| C2.4 | 22 | 6 | 1 |
| C2.5 | 23 | 6 | 0 |
| C2.6 | 32 | 3 | 3 |
| C2.7 | 35 | 7 | 3 |
| C2.8 | 16 | 3 | 1 |
| C2.9 | 33 | 8 | 1 |
| C2.10 | 29 | 4 | 0 |
| C2.11 | 29 | 8 | 8 |

C2.1 có 195 ảnh train, nhiều hơn hẳn các lớp C2.2, C2.4 và C2.5 (22–24 ảnh). Chênh lệch này là một nguyên nhân hợp lý khiến nhãn con ít dữ liệu khó học, nhưng số ảnh test mỗi lớp cũng rất nhỏ; các tỷ lệ 0/4 hoặc 3/3 chưa ổn định. C2.10 đặc biệt bị sai L1 ở 3/4 ảnh test, nên chỉ tăng điểm nhãn con không giải quyết được ba trường hợp đó.

## Ví dụ cần chỉ ra khi trình bày

- `THK000423_0c26cda164_2_01`, chuẩn C2.2: mô hình chọn đúng ứng viên C2.2 nhưng độ tin cậy 32,5% dưới ngưỡng riêng 70%, nên trả L1. Ảnh cho thấy hai chân giao nhau, nhưng các đường viền chân và bệ đỡ chồng lên nhau. Đây là một giả thuyết thị giác cho việc chưa đạt độ tin cậy, cần người gán nhãn kiểm tra lại bằng ảnh gốc.
- `THK000705_01`, chuẩn C2.2: mô hình trả C2.3 với độ tin cậy 75,9%. Tư thế chân và vải trang trí quanh đầu gối, cổ chân dễ làm việc phân biệt “bắt chéo không khóa kín” với “một chân co, một chân thả” khó hơn. Đây là nhầm nhãn con, không phải lỗi L1.
- `HAR_52548545_01`, chuẩn C2.5: ứng viên C2.5 đúng, độ tin cậy 48,3% dưới ngưỡng 70%, nên trả L1. Ảnh có nhiều chi tiết tay/chân, vật trang trí và bệ đỡ; cần xem ảnh ở kích thước lớn trước khi kết luận điểm khớp hay nhãn gán là nguyên nhân chính.
- `THK000234_01`, chuẩn C2.10: mô hình trả C1.3 và ứng viên C2.9, tức L1 đúng nhưng nhầm tư thế động sang bước/chuyển hướng. Một chân co và một chân duỗi rõ, còn lửa và vải chuyển động có thể gây nhiễu ngữ cảnh. Đây là giả thuyết cần so với các ảnh C2.9 tương tự.

## Kết luận thực nghiệm

L2 fail do nhiều tầng quyết định: sai nhóm L1, nhầm giữa nhãn con, và cơ chế giữ ở L1 khi điểm chưa đạt ngưỡng. Ngưỡng giúp tránh trả L2 tùy tiện nhưng làm giảm độ bao phủ: chỉ 65/103 ảnh có nhãn L2 được trả nhãn chi tiết. Mô hình keypoint trả đúng 10/10 ảnh nó chấp nhận, nhưng chỉ chấp nhận 10/103, nên không thay thế được nhánh ảnh trong ứng dụng hiện tại.

Để kiểm chứng nguyên nhân thị giác, dùng tab phân tích lỗi chọn từng ảnh, mở lại crop mục tiêu và đối chiếu đầu gối, cổ chân, bệ đỡ, các chi bị che với hướng dẫn nhãn. Nếu bổ sung dữ liệu, đổi mô hình hoặc đổi ngưỡng sau khi xem test, cần tập đánh giá độc lập mới để xác nhận kết quả.

## Ngưỡng 60% trong giao diện local

Theo yêu cầu thử lại khả năng trả nhãn L2, `local_app.py` áp dụng ngưỡng tối đa 60% cho các lớp vốn có ngưỡng cao hơn: C2.1–C2.5 từ 70% xuống 60%, C2.9–C2.10 từ 65% xuống 60%. Các lớp còn lại và ngưỡng bằng chứng 50% giữ nguyên. Quy tắc này áp dụng cho mọi ảnh theo lớp ứng viên và điểm dự đoán; không dùng nhãn thật của ảnh để quyết định.

Tính lại trên điểm test đã lưu: đúng L2 cuối cùng là **60/103** thay vì 55/103; nhóm ứng viên đúng nhưng không qua ngưỡng còn **10** thay vì 15. Đồng thời có **4/22** ảnh L2 trống được trả nhãn chi tiết thay vì 3/22, và ba ảnh có nhãn L2 khác bị nhận thêm nhãn chi tiết sai. Vì đã xem test trước khi chỉnh ngưỡng, đây chỉ là phân tích hậu nghiệm, không thay thế kết quả đánh giá chính thức của run. Cần test độc lập mới để xác nhận hiệu quả và tỷ lệ trả nhãn sai.

Trên toàn bộ validation, ngưỡng gốc chấp nhận 70 ảnh L2, đúng 65 (precision 92,9%), và chấp nhận 3/30 ảnh L2 trống (10%). Ngưỡng tối đa 60% chấp nhận 78 ảnh, đúng 68 (precision **87,2%**), và chấp nhận 6/30 ảnh L2 trống (**20%**). Vì vậy cấu hình 60% đồng loạt không đạt mục tiêu precision ≥90% và tỷ lệ nhận nhầm L2 trống ≤10% đã đặt trong notebook. Nó chỉ phù hợp làm chế độ thử local để quan sát đánh đổi; không báo cáo như ngưỡng đã được chọn hợp lệ từ validation.
