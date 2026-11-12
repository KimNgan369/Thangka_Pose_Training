# Thangka Pose Training

Mở **`Thangka_Pose_Training.ipynb`**, chọn kernel Python có PyTorch CUDA, lưu rồi **Restart Kernel → Run All**. Bố cục 18 mục tương tự v7; tất cả mã nằm trong notebook.

Mỗi lượt chạy huấn luyện mới 3 kiến trúc ảnh × 3 seed từ pretrained gốc ImageNet, rồi chạy cải tiến ConvNeXt L2 từ hai checkpoint vừa huấn luyện trong cùng run. Giữ loss phân cấp cân bằng lớp, EMA, TTA, chọn ngưỡng và kiểm tra theo nhóm hiện vật. YOLO Pose được huấn luyện mới từ pretrained gốc; sau đó chạy phân loại keypoint, SVM/boosting, chọn kết hợp trên validation và đánh giá test, báo cáo, demo.

Không nạp checkpoint Thangka từ các run trước. Kết quả mới ở `outputs/notebook_runs/<run_id>/`, gồm checkpoint ảnh, refinement, pose, keypoint, cache, biểu đồ, lựa chọn validation và báo cáo. `source_notebook.ipynb` chụp mã nguồn trước huấn luyện. Chạy lại một cell huấn luyện trong cùng kernel có thể tiếp tục trạng thái của chính run đó; Restart Kernel → Run All tạo run mới.

Checkpoint cũ trong `outputs/`, bản lưu `outputs/baseline_archive_20261109/` và notebook v7 được giữ nguyên. Đặc biệt, pose mới không ghi đè `outputs/pose_baseline/best.pt`. Demo nạp đúng pose và mô hình ảnh/keypoint của run được chọn; chạy riêng mục 18 để dùng lại run cũ khi cần.

Dữ liệu và trọng số chỉ dùng nghiên cứu nội bộ theo metadata quyền sử dụng. Test lịch sử đã được xem khi phát triển; cần tập độc lập mới để kết luận khả năng khái quát hóa. Không cam kết kết quả mới tốt hơn đối chứng trước khi chạy.

## Giao diện chạy local

Nhấp đúp `run_local.bat` hoặc chạy `py -3.10 local_app.py` trong thư mục này. Chờ nạp checkpoint, sau đó mở `http://127.0.0.1:7860` nếu trình duyệt không tự mở. Giao diện dùng run đầy đủ mới nhất; có thể khóa một run bằng `py -3.10 local_app.py --run-id 20261112_115255_seed20261021`. Đóng cửa sổ lệnh hoặc nhấn Ctrl+C để tắt.

Tab **Thử ảnh** nhận ảnh từ máy hoặc ảnh test đã gán nhãn. Với ảnh test, ứng dụng dùng crop nhân vật mục tiêu từ manifest để so với kết quả đã lưu. Tab **Phân tích lỗi L2 trên test** lọc các ảnh theo loại lỗi và nhãn con. Đây là công cụ suy luận và xem lại kết quả; không huấn luyện hay điều chỉnh ngưỡng trên test. Ảnh ngoài dataset không có nhãn chuẩn nên chỉ hiển thị dự đoán và căn cứ giữ ở L1.

Phân tích chi tiết lần chạy mới nhất ở `L2_ERROR_ANALYSIS.md`.
