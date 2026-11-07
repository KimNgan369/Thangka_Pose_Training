# Thí nghiệm cải thiện lớp hiếm — 03/11/2026

Mốc đối chiếu là run `20261031_174634_seed20261021`. Thí nghiệm giữ nguyên dữ liệu, nhãn và split 612/136/125. Không chuyển ảnh test sang train. Đầu ra vẫn là L2 khi đủ căn cứ, lùi về L1 hoặc không xác định theo đề tài.

## Phương pháp

Giữ bộ trích xuất đặc trưng của sáu mạng đã học, sau đó học lại bộ phân loại với trọng số cân bằng lớp. Mỗi ảnh train có bốn phiên bản: nguyên bản, phản chiếu, xoay nhẹ kết hợp thay đổi màu/độ tương phản. Giữ toàn thân và bệ đỡ; không xoay lớn làm đổi nhóm tư thế. Validation và test chỉ dùng ảnh nguyên bản.

So sánh đặc trưng ba ResNet18, ba MobileNetV2 và cả sáu mạng. Mỗi nhóm thử Logistic Regression ở C=0,1/1/10 và SVM RBF ở C=1/10/100. Học riêng nhóm L1, 11 lớp L2 và bằng chứng có/không có L2. Mẫu L2 trống không tham gia học lớp chi tiết. Xác suất nhóm cha được kết hợp với tổng xác suất các lớp con để giảm mâu thuẫn giữa hai cấp. SVM sử dụng điểm quyết định được chuẩn hóa; không coi điểm này là xác suất đã hiệu chuẩn.

Ngưỡng mới dùng bằng chứng chung trên validation, mục tiêu precision L2 gộp ít nhất 90% và tỷ lệ trả L2 trên mẫu trống không quá 10%. Không còn tự khóa một lớp chỉ vì chưa có ba dự đoán validation đúng. Điều này thay đổi mục tiêu từ precision riêng từng lớp sang precision gộp; **không có cam kết 90% cho từng lớp**. Báo cáo vẫn phải ghi từng lớp, số mẫu và các trường hợp còn sai.

## Điều kiện thay mô hình

Trước khi xem kết quả test, ứng viên phải thỏa mãn:

- Macro-F1 L2 toàn quy trình tăng ít nhất 0,02 và macro-recall tăng so với mốc.
- Accuracy L1 giảm không quá một mẫu trên 136 mẫu validation.
- Macro-F1 L1 giảm không quá 0,02; điều kiện này được bổ sung trước khi xem test ở vòng so sánh ngưỡng theo nhánh, để tránh che khuất suy giảm ở nhóm L1 ít mẫu.
- Precision L2 gộp ít nhất 90% và giảm không quá 5 điểm phần trăm so với mốc; mẫu L2 trống bị chấp nhận không quá 10%.
- Có thêm lớp nhận đúng L2.
- Qua ba fold validation tách theo hiện vật: precision L2 gộp ít nhất 85%, tỷ lệ nhận nhầm mẫu trống không quá 15%, macro-F1 không thấp hơn mốc.

Fold chỉ dùng để chọn ngưỡng trên hai phần rồi đo trên phần còn lại. Các mạng trích đặc trưng trước đó đã được chọn bằng validation lịch sử. Vì vậy, đây chưa phải nested cross-validation của toàn bộ quy trình. Test lịch sử chỉ được mở sau khi ghi lựa chọn; vẫn cần dữ liệu độc lập để khẳng định khả năng khái quát hóa.

Precision gộp trong thí nghiệm mới tính **mọi nhãn L2 đã trả**, kể cả nhãn sai trên mẫu L2 trống. Chỉ số này nghiêm hơn selective accuracy chỉ tính trên mẫu có L2 chuẩn trong một số bảng cũ. Báo cáo phải so cùng định nghĩa.

## Tệp và cách chạy

`quality_v2.py` chứa huấn luyện, kiểm định và đánh giá. `quality_v2_demo.py` nạp ứng viên đã vượt kiểm định; không huấn luyện lại. `outputs/quality_v2/` lưu mô hình và số liệu riêng. Bản demo cũ không bị thay trong quá trình thử nghiệm. Chỉ tạo `outputs/active_quality_v2.json` sau khi kiểm tra suy luận từng ảnh khớp dự đoán đã lưu.

```powershell
python quality_v2.py --run-dir outputs/quality_v2/20261103_balanced
```

Lần thử này tập trung cải thiện bộ phân loại. Bộ ước lượng điểm khớp vẫn được giữ làm mốc; không tuyên bố PCK/OKS đã cải thiện nếu chưa huấn luyện và đo lại.

## Vòng tiếp theo sau khi vòng đầu không đạt

Run `20261103_balanced` không có ứng viên đạt đủ điều kiện validation và không mở test. Vòng `20261103_calibrated` thử Logistic Regression C=10/100 và SVM C=1/10 trên hai nhóm đặc trưng ResNet18 hoặc cả sáu mạng. SVM được hiệu chuẩn sigmoid bằng ba fold theo hiện vật trong **train**; các ảnh tăng cường giữ cùng nhóm với ảnh gốc. Mỗi cấu hình có thêm phương án trộn cố định 50/50 với dự đoán mốc. Điều kiện chất lượng không được nới lỏng. Đây là tìm kiếm bổ sung dựa trên validation, cần ghi nhận khi diễn giải độ bất định; không gọi các fold này là dữ liệu hoàn toàn độc lập với bước học đặc trưng lịch sử.

```powershell
python quality_v2.py --extended --run-dir outputs/quality_v2/20261103_calibrated
```

## Tinh chỉnh mạng ảnh mới

Hai vòng trên chưa có ứng viên đạt tất cả điều kiện; vòng thay riêng đầu L2 cũng chưa đạt. Do đó, bước tiếp theo dùng ConvNeXt-Tiny khởi tạo bằng trọng số ImageNet chính thức của Torchvision, đã kiểm tra mã băm. Chạy hai seed, tối đa 60 epoch mỗi seed; học đầu ra ở ba epoch đầu, tinh chỉnh các tầng trên từ epoch 4 và toàn mạng từ epoch 11. Dừng sớm sau ít nhất 24 epoch và 16 epoch không cải thiện. Batch 2, tích lũy 8 bước, mixed precision phù hợp GPU 4 GB.

Mỗi epoch lấy mẫu train theo tần suất lớp ở mức nghịch căn, dành 20% xác suất lấy mẫu cho các mẫu L2 trống. Không cộng thêm trọng số mất mát theo lớp để tránh nhân đôi tác động cân bằng. Hàm mất mát học L1, L2 toàn cục, L2 trong nhánh và bằng chứng L2. Ảnh L2 trống không tham gia hai thành phần phân loại L2.

Lựa chọn checkpoint dùng cùng chỉ số validation tổng hợp đã ghi trong baseline. So sánh tổ hợp đồng trọng số của hai seed và hai mức trộn với baseline (25%, 50% trọng số baseline); không chọn một seed thuận lợi sau khi xem test. Giữ nguyên tiêu chí thay mô hình. Một lượt smoke đã kiểm tra backward toàn mạng và lưu trạng thái; không dùng kết quả smoke để báo cáo chất lượng.

```powershell
python quality_convnext.py
```

Mỗi seed lưu `best_model.pt`, `last_training_state.pt`, `history.json` và đầu ra validation. Chạy lại đúng lệnh và cấu hình sẽ tiếp tục trạng thái đã lưu. Sau lựa chọn validation, test lịch sử là bước kiểm tra cuối trước khi sử dụng: nếu phát hiện suy giảm theo điều kiện đã đặt, không kích hoạt ứng viên và không dùng test để chọn lại siêu tham số. `activate_quality_v2.py` kiểm tra từng ảnh test qua đường suy luận demo rồi mới ghi con trỏ mô hình đang dùng.

Trước khi hoàn tất huấn luyện và xem test, bổ sung phép so sánh ngưỡng toàn cục với bốn ngưỡng chung theo nhánh L1. Các lớp con cùng một nhánh dùng chung ngưỡng; tổng precision yêu cầu ít nhất 92,5%, tỷ lệ nhận nhầm mẫu trống tối đa 10%. Bốn ngưỡng được chọn đồng thời để tăng macro-F1, rồi đánh giá ngoài fold theo nhóm hiện vật với cùng điều kiện thay mô hình. Cấu hình baseline với ngưỡng mới cũng được so sánh để tách ảnh hưởng của ngưỡng; nếu phương án này tốt nhất theo tiêu chí đã đặt thì giữ trọng số cũ và chỉ thay cơ chế quyết định, thay vì buộc dùng mạng mới. Khi đó phải ghi rõ tăng chất lượng đầu ra chưa phải bằng chứng trọng số học tốt hơn. Không đọc số liệu test của những cấu hình trước để chọn ngưỡng hoặc mô hình ở lượt này.

Lệnh chạy/tiếp tục toàn bộ quy trình, gồm huấn luyện, chọn ngưỡng, kiểm tra demo và cập nhật báo cáo:

```powershell
python run_quality_upgrade.py
```

Nguồn phương pháp: [PyTorch transfer learning](https://docs.pytorch.org/tutorials/beginner/transfer_learning_tutorial), [ConvNeXt-Tiny chính thức](https://docs.pytorch.org/vision/master/models/generated/torchvision.models.convnext_tiny.html).
