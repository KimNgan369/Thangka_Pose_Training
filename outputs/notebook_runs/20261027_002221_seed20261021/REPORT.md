# Kết quả thực nghiệm phân tích tư thế Thangka

Run: 20261027_002221_seed20261021  
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
- L1 accuracy: 0.8400.
- L1 macro-F1: 0.7893.
- L2 oracle macro-F1: 0.6111.
- L2 exact trên toàn bộ mẫu có gold L2: 0.3592.

## Pose và phân loại từ keypoint dự đoán

- Pose PCK@0.05 bbox diagonal: 0.8372.
- Mean bbox IoU: 0.892391237359342.
- Mean OKS: 0.8032537567795781.
- Classifier keypoint: random_forest.
- L1 accuracy: 0.8720.
- L1 macro-F1: 0.8145.
- L2 oracle macro-F1: 0.5907.
- L2 exact trên toàn bộ mẫu có gold L2: 0.4854.

## So sánh và giới hạn

- Chênh lệch L1 accuracy hướng ảnh trừ hướng keypoint: -0.0327.
- Bootstrap 95% CI: [-0.09600000000000009, 0.03200000000000003].
- Đây là baseline một seed; không suy rộng quá phạm vi snapshot.
- Các lớp L2 support nhỏ phải được báo cùng support và confusion matrix.
- C1.5 chưa được hiệu chuẩn do không có tập âm/OOD.
- Dữ liệu và trọng số chỉ dùng nội bộ theo metadata quyền sử dụng.
