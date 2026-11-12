# Thangka Pose Training

Chỉ mở **`Thangka_Pose_Training.ipynb`**, chọn kernel Python có PyTorch CUDA, lưu rồi **Restart Kernel → Run All**. Toàn bộ code nằm trong notebook; không cần chạy file Python riêng.

Mặc định `IMAGE_PIPELINE_MODE = "convnext_l2_refinement"`: **huấn luyện hai ConvNeXt cải tiến** từ checkpoint lịch sử, thêm đầu L2 riêng theo nhóm L1. Mỗi seed chạy tối đa 40 epoch, có dừng sớm; học đầu mới trước rồi tinh chỉnh khối cuối với learning rate nhỏ. Dùng trọng số lớp tính từ train, EMA và suy luận trên toàn ảnh gốc/lật ngang. Ngưỡng và hai mức pha xác suất L2 (25%, 50%) được chọn trên validation, có kiểm tra qua ba fold theo nhóm hiện vật. L1/bằng chứng L2 dùng nhánh ảnh lịch sử. Nếu ứng viên không đạt ràng buộc, chọn lại đối chứng 55/103; chưa bảo đảm lần chạy mới sẽ vượt mốc này.

Muốn chỉ nạp mô hình ảnh lịch sử, đặt `IMAGE_PIPELINE_MODE = "historical_convnext_branches"`. Chế độ `"train_new"` chạy quy trình chín mô hình ảnh cũ. Notebook vẫn dùng pose đã lưu nếu hợp lệ. Chạy lại cell huấn luyện trong cùng kernel tiếp tục trạng thái đã lưu; **Restart Kernel → Run All tạo một run mới**.

Nhánh keypoint bật `KEYPOINT_CONTROLLED_ROUND = True` và `KEYPOINT_NONLINEAR_REFINEMENT = True`: thêm SVM RBF C=1, C=4 và cây boosting trên đặc trưng hình học, giữ L1/bằng chứng của đối chứng cho ba ứng viên mới. SVM hiệu chỉnh xác suất bằng các fold train theo nhóm hiện vật; ảnh gốc và augmentation không tách sang hai fold. Mục tiêu precision khi chọn ngưỡng gộp là 95%, khớp ràng buộc của vòng kiểm soát. Chỉ nhận ứng viên vượt điều kiện trên validation và dự đoán ngoài fold; nếu không đạt, giữ đối chứng. Đây là kiểm tra chéo bước hiệu chỉnh, không phải nested cross-validation toàn bộ chọn mô hình.

Trong thư mục run mới:

- `image_classifier/refinement/`: checkpoint và lịch sử hai seed, `protocol.json`, `controlled_round.json`, `validation_comparison.csv`, `test_comparison.csv`, `test_per_class.csv`, dự đoán và chỉ số đối chứng lịch sử.
- `keypoint_classifier/`: checkpoint đối chứng/mô hình chọn, `nonlinear_training_audit.json`, `controlled_round.json`, các bảng so sánh validation/test và chi tiết từng lớp.
- `figures/`: biểu đồ huấn luyện ConvNeXt, so sánh vòng kiểm soát và các biểu đồ của toàn quy trình.

Test được đọc sau khi khóa lựa chọn. Test lịch sử đã được xem trong các vòng trước; cần tập độc lập mới để kết luận tổng quát hóa. Đặt `KEYPOINT_NONLINEAR_REFINEMENT = False` để bỏ ba bộ phân loại mới, hoặc `KEYPOINT_CONTROLLED_ROUND = False` để dùng quy trình keypoint đối chứng.

- `data/`, `ratings/`: dữ liệu và đánh giá nhãn phục vụ đề tài.
- `pretrained/`, `cache/`: trọng số khởi tạo và bộ nhớ đệm.
- `outputs/notebook_runs/`: mỗi lần chạy tạo một thư mục kết quả mới. Giữ cả thư mục để đánh giá sau.
- `outputs/baseline_archive_20261109/`: bản sao lưu độc lập đã kiểm tra SHA-256 của mô hình, kết quả cũ và notebook trước chỉnh sửa.
- Các kết quả lịch sử trong `outputs/` và báo cáo cũ trong `reports/` được giữ nguyên.

Dữ liệu, manifest và trọng số chỉ dùng nghiên cứu nội bộ theo metadata quyền sử dụng; không phát hành công khai. Giữ repository ở chế độ riêng tư.
