# Cải thiện các nhãn tư thế khó

Bản sửa tập trung vào C2.3 (ngồi một chân co, một chân thả), C2.5 (quỳ/ngồi trên gót), C2.11 (nằm nghiêng), C2.10 (động/múa) và C2.7 (đứng lệch trọng tâm). Không đổi nhãn đã duyệt hoặc chuyển ảnh validation/test sang train.

Tình trạng ngày 01/11/2026 (UTC+7): 9 kiểm thử hồi quy đạt; lượt tích hợp `20261031_174225_seed20261021_integration_smoke` đã hoàn tất với hai kiến trúc, hai epoch ngắn gồm head và toàn backbone, đánh giá và demo. Kiểm tra tái sử dụng checkpoint hoàn tất và từ chối cấu hình không khớp cũng đạt. Đợt chính thức `20261031_174634_seed20261021` đã hoàn tất lúc 00:53 ngày 01/11/2026. Checkpoint ảnh, keypoint và pose cùng ngưỡng validation được lưu dưới thư mục run.

Sau khi mở lại notebook hoặc khởi động kernel mới, **chỉ chạy cell Demo ngay dưới tiêu đề “Demo nhanh sau khi mở lại notebook”**. Cell tự nạp run đầy đủ mới nhất bằng `saved_demo.py`, kiểm tra manifest/schema, dựng giao diện chọn ảnh và định nghĩa lại `run_demo(...)`. Không cần chạy lại huấn luyện hay các cell đánh giá. Đã kiểm tra trong kernel mới: kết quả dự đoán khớp bản ghi test đã lưu và không tạo run huấn luyện mới.

## Nguyên nhân đã xác định từ mã và lần chạy trước

- Lần chạy `20261031_153809_seed20261021` có ngưỡng L2 nhánh ảnh là `1.0001`, nên nhánh này không thể trả bất kỳ nhãn chi tiết nào. Nhánh ảnh chưa có head học bằng chứng L2, trong khi dữ liệu có 144 ảnh được duyệt để trống L2.
- Demo cố định dùng keypoint, không dùng kết quả so sánh với nhánh ảnh để chọn đầu ra.
- Mã cũ mở block cuối, tối đa 20 epoch; lớp ngồi phổ biến chiếm nhiều dữ liệu. C2.5 có 23 ảnh train; C2.11 và C2.10 mỗi lớp 29 ảnh; C2.7 có 35 ảnh; C2.3 có 82 ảnh.
- `IMAGE_SIZE` bị gán lại 224 trong cell tiện ích. Hàm resize dùng `thumbnail`, nên ảnh nhỏ không được phóng lên. Augmentation affine sau khi pad có thể cắt phần cơ thể sát biên.
- Chọn checkpoint dựa nhiều vào L2 khi được cung cấp L1 đúng (oracle) chưa phản ánh lỗi thực tế như quỳ thành đứng.
- Đặc trưng góc keypoint trước đây đo trên x/y chuẩn hóa riêng theo chiều rộng/cao. Bản mới đưa tỷ lệ crop vào cả train và demo, khôi phục hệ tọa độ đồng tỷ lệ trước khi tính hình học; quan trọng với nhân vật nằm ngang.

## Thay đổi huấn luyện

| Thành phần | Cấu hình mới |
|---|---|
| Nhánh ảnh | ResNet-18 và MobileNetV2, mỗi mạng 3 seed |
| Đầu vào | 384 × 384, giữ tỷ lệ toàn thân, xoay canvas có mở rộng trước khi resize |
| Lịch học | Tối đa 100 epoch/mô hình, ít nhất 30 epoch trước early stopping, patience 20 |
| Fine-tune | 5 epoch học head; mở block trên; từ epoch 16 mở toàn backbone |
| Batch | 4 ảnh, tích lũy 4 bước, mixed precision, clipping gradient, giữ thống kê BatchNorm |
| Loss | L1 + L2 theo nhánh + 0.5 joint L1–L2 + 0.5 bằng chứng L2 |
| Lớp hiếm | Trọng số nghịch căn tần suất tính từ train; bỏ tăng bản sao riêng C2.2 |
| Keypoint | Logistic regression ở 3 mức regularization, random forest và extra trees; jitter và phản chiếu đúng cặp khớp trái/phải |
| Checkpoint | 35% L1 macro-F1, 40% L2 end-to-end macro-F1, 15% L2 oracle macro-F1, 10% macro-F1 bằng chứng |

Loss joint truyền lỗi nhãn chi tiết về cả L1. Vì vậy ảnh quỳ không chỉ dạy phân biệt các kiểu ngồi mà còn giúp sửa nhánh ngồi/đứng/chuyển động. Nhãn L2 trống không tham gia loss nhãn chi tiết; chúng chỉ giám sát L1 và head bằng chứng.

So sánh ensemble từng kiến trúc và ensemble chung bằng validation; không chọn một seed may mắn rồi bỏ các seed còn lại. Demo tiếp tục so sánh ảnh, keypoint và ba tỷ lệ kết hợp trung gian trên validation. Trộn xác suất joint rồi khôi phục xác suất có điều kiện, bảo đảm quan hệ cha–con. Nếu thiếu pose, dùng xác suất ảnh; đường này được áp dụng giống nhau ở đánh giá và demo.

## Ngưỡng đầu ra

Mỗi lớp L2 có ngưỡng riêng. Một lớp chỉ được nhận nếu có ít nhất 3 dự đoán validation được chấp nhận, precision thực nghiệm ít nhất 90%, và không nhận nhầm ảnh L2 trống trong validation. Chọn ngưỡng bằng chứng chung theo macro recall để lớp phổ biến không quyết định hết kết quả. Lớp thiếu bằng chứng vẫn fallback L1; không hạ precision mục tiêu để ép hiển thị L2.

Đây là mục tiêu thực nghiệm trên validation, không phải bảo đảm độ chính xác 90% ngoài thực tế. File selection ghi support và khoảng tin cậy Wilson. Với 3–7 ảnh validation ở nhiều lớp, khoảng bất định vẫn lớn.

## Đánh giá và bám sát đề tài

Giữ hai hướng so sánh chính trên cùng split 612 train / 136 validation / 125 test. Kappa, confusion matrix, macro-F1, PCK, OKS và bbox IoU vẫn được báo cáo. Không thêm nhận diện nhân vật, diễn giải tôn giáo hay hình thể 3D.

Phép đo PCK/OKS được sửa sang tọa độ pixel để không làm biến dạng khoảng cách ở ảnh ngang. OKS dùng hệ số COCO `(2 * sigma)^2`, với diện tích bbox làm đại diện diện tích đối tượng. Đây là **metric schema 2**; không so trực tiếp số đo tự tính mới với số đo normalized-space cũ để tuyên bố pose đã tốt lên. YOLO pose checkpoint được giữ nguyên; có thêm chẩn đoán chân theo lớp trước khi quyết định cần một thí nghiệm pose mới.

Các artifact quan trọng trong mỗi run:

- `image_classifier/*/history.json`: lịch học từng mô hình.
- `image_classifier/*/last_training_state.pt`: trạng thái tiếp tục gồm optimizer, scheduler và RNG.
- `deployment/selection.json`: cấu hình chọn trên validation, ghi trước khi đánh giá đầu ra triển khai trên test.
- `deployment/per_class_end_to_end.csv`: tính cả các trường hợp fallback/mất nhãn vì sai L1.
- `deployment/target_labels_vs_previous.csv`: so đúng 5 lớp mục tiêu với demo keypoint của lần chạy trước.
- `deployment/target_cases_vs_previous.csv`: đối chiếu từng trường hợp, giữ nguyên instance và gold label.
- `deployment/target_validation_cases.csv`: quyết định và lý do ngưỡng của các ảnh validation thuộc lớp mục tiêu.
- `pose_estimator/geometry_by_class.csv`: PCK toàn thân và hông–gối–cổ chân theo split/lớp.
- `SUMMARY.json`, `REPORT.md`, `source_notebook.ipynb`: kết quả và mã của run.

Test lịch sử đã được xem ở các vòng phát triển trước. Kết quả mới là so sánh trên benchmark hiện có; muốn kết luận tổng quát hóa cần một bộ ảnh độc lập mới. Validation đang kiêm chọn checkpoint, hiệu chuẩn và chọn ngưỡng; chưa có nested cross-validation toàn pipeline. Các giới hạn này được ghi trong notebook, không biến số đo validation thành cam kết chất lượng.

## Cách chạy

Mã học, đánh giá và demo nằm trong `Thangka_Pose_Training.ipynb`. Có thể dùng Restart → Run All, hoặc chạy nền qua cùng mã bằng:

```powershell
& 'C:\Users\ADMIN\AppData\Local\Programs\Python\Python310\python.exe' -u run_training.py
```

Tiếp tục một run bị gián đoạn bằng `--resume 'outputs\notebook_runs\TEN_RUN'`. Chỉ tiếp tục khi notebook, manifest và cấu hình khớp; không trộn checkpoint khác cấu hình. Mô hình đã hoàn tất được tái sử dụng, mô hình đang học tiếp tục từ epoch đã lưu. Chạy kiểm tra bằng `--smoke` dùng một seed mỗi kiến trúc, hai epoch ngắn để kiểm tra cả head và toàn backbone; **không dùng kết quả smoke làm kết quả nghiên cứu**.

Trạng thái tiến trình chính ở `outputs/quality_training_status.json`; log của phiên chạy nền ở `outputs/quality_training.log` và `outputs/quality_training.stderr.log`. Khi `state` là `completed`, xem các bảng trong run tương ứng để kết luận từng lớp có cải thiện hay không. Việc sửa code hoặc hoàn tất smoke chưa chứng minh mô hình mới tốt hơn.

## Nguồn đối chiếu phương pháp

- [PyTorch về transfer learning và fine-tuning](https://docs.pytorch.org/tutorials/beginner/transfer_learning_tutorial.html).
- [Mã COCOeval chính thức cho OKS](https://github.com/cocodataset/cocoapi/blob/master/PythonAPI/pycocotools/cocoeval.py).
- [scikit-learn về đánh giá chéo theo nhóm và giới hạn lựa chọn mô hình](https://scikit-learn.org/stable/modules/cross_validation.html).
