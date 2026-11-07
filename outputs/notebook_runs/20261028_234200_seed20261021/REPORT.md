# Kết quả thực nghiệm phân tích tư thế Thangka

Run: 20261028_234200_seed20261021  
Dataset: thangka_pose_v1.1.0_dacntt_2026-10-20  
Seed: 20261021

## Kiểm tra dữ liệu

- Tổng số mẫu: 873.
- Split train/validation/test: {'val': 136, 'train': 612, 'test': 125}.
- Mẫu đủ 17 keypoint: 612.
- Rò rỉ artifact giữa split: 0 nhóm.
- Rò rỉ ảnh trùng hash giữa split: 0 nhóm.

## Độ đồng thuận

- Cặp nhãn độc lập của Ngan và My: 873.
- Kappa nhãn phân cấp: 0.9652.
- Kappa L1: 1.0000.

## Phân loại trực tiếp từ ảnh

- Kiến trúc: resnet18.
- L1 accuracy: 0.8720.
- L1 macro-F1: 0.8149.
- Hiệu chỉnh độ tin cậy L1 (ECE / Brier): 0.0484 / 0.1886.
- Ngưỡng từ chối L1: 0.5698.
- L1 selective coverage/accuracy: 0.9200 / 0.9217.
- Tỷ lệ Không xác định: 0.0800.
- L2 oracle macro-F1: 0.6236.
- L2 exact trên toàn bộ mẫu có gold L2: 0.0000.
- Tỷ lệ fallback trên mẫu người gán nhãn để trống L2: 1.0000.

## Pose và phân loại từ keypoint dự đoán

- Pose PCK@0.05 bbox diagonal: 0.8372.
- Mean bbox IoU: 0.892391237359342.
- Mean OKS: 0.8032537567795781.
- Classifier keypoint: random_forest.
- L1 accuracy: 0.8640.
- L1 macro-F1: 0.7986.
- Hiệu chỉnh độ tin cậy L1 (ECE / Brier): 0.0667 / 0.2000.
- Ngưỡng từ chối L1: 0.5101.
- L1 selective coverage/accuracy: 0.9040 / 0.9115.
- Tỷ lệ Không xác định: 0.0960.
- L2 oracle macro-F1: 0.6699.
- L2 exact trên toàn bộ mẫu có gold L2: 0.4854.
- Tỷ lệ fallback trên mẫu người gán nhãn để trống L2: 0.8636.
- Accuracy bộ kiểm tra đủ bằng chứng L2: 0.8480.

## So sánh và giới hạn

- Chênh lệch L1 accuracy hướng ảnh trừ hướng keypoint: 0.0083.
- Bootstrap 95% CI: [-0.05600000000000005, 0.07200000000000006].
- Mô hình ảnh dùng fine-tuning hai giai đoạn, trọng số lớp trì hoãn và loss L2 theo từng nhánh L1.
- Mô hình keypoint dùng đặc trưng hình học chuẩn hóa, classifier L2 riêng theo nhánh và bộ kiểm tra đủ bằng chứng L2.
- C2.2 dùng tăng cường keypoint có kiểm soát, trọng số vừa phải và ngưỡng riêng chọn trên validation.
- Xác suất được temperature scaling trên validation trước khi chọn ngưỡng từ chối.
- Đây là baseline một seed; không suy rộng quá phạm vi snapshot.
- Các lớp L2 support nhỏ phải được báo cùng support và confusion matrix.
- Không xác định là từ chối do bằng chứng yếu theo validation; chưa thể diễn giải như bộ phát hiện OOD vì chưa có tập âm/OOD.
- Dữ liệu và trọng số chỉ dùng nội bộ theo metadata quyền sử dụng.
