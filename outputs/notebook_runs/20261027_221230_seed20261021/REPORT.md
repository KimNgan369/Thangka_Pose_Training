# Kết quả thực nghiệm phân tích tư thế Thangka

Run: 20261027_221230_seed20261021  
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
- L1 macro-F1: 0.7830.
- Ngưỡng từ chối L1: 0.6921.
- L1 selective coverage/accuracy: 0.8800 / 0.9000.
- Tỷ lệ Không xác định: 0.1200.
- L2 oracle macro-F1: 0.6527.
- L2 exact trên toàn bộ mẫu có gold L2: 0.4951.

## Pose và phân loại từ keypoint dự đoán

- Pose PCK@0.05 bbox diagonal: 0.8372.
- Mean bbox IoU: 0.892391237359342.
- Mean OKS: 0.8032537567795781.
- Classifier keypoint: random_forest.
- L1 accuracy: 0.8720.
- L1 macro-F1: 0.8145.
- Ngưỡng từ chối L1: 0.4733.
- L1 selective coverage/accuracy: 0.8640 / 0.8981.
- Tỷ lệ Không xác định: 0.1360.
- L2 oracle macro-F1: 0.5818.
- L2 exact trên toàn bộ mẫu có gold L2: 0.4660.

## So sánh và giới hạn

- Chênh lệch L1 accuracy hướng ảnh trừ hướng keypoint: -0.0327.
- Bootstrap 95% CI: [-0.09599999999999997, 0.02400000000000002].
- Đây là baseline một seed; không suy rộng quá phạm vi snapshot.
- Các lớp L2 support nhỏ phải được báo cùng support và confusion matrix.
- Không xác định là từ chối do bằng chứng yếu theo validation; chưa thể diễn giải như bộ phát hiện OOD vì chưa có tập âm/OOD.
- Dữ liệu và trọng số chỉ dùng nội bộ theo metadata quyền sử dụng.
