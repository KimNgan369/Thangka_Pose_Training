# Kết quả thực nghiệm phân tích tư thế Thangka

Run: 20261109_232255_seed20261021  
Chế độ: full (smoke chỉ kiểm tra thực thi, không phải kết quả mô hình cuối)  
Seeds ảnh thực tế: [20261103, 20261113, 20261021, 20261031, 20261107]  
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

- Kiến trúc: convnext_branches_baseline0.5.
- L1 accuracy: 0.8880.
- L1 macro-F1: 0.8386.
- Hiệu chỉnh độ tin cậy L1 (ECE / Brier): 0.0693 / 0.1402.
- Ngưỡng từ chối L1: 0.0000.
- L1 selective coverage/accuracy: 1.0000 / 0.8880.
- Tỷ lệ Không xác định: 0.0000.
- L2 oracle macro-F1: 0.7250.
- L2 exact trên toàn bộ mẫu có gold L2: 0.5340.
- Tỷ lệ fallback trên mẫu người gán nhãn để trống L2: 1.0000.

## Pose và phân loại từ keypoint dự đoán

- Pose PCK@0.05 bbox diagonal: 0.7862.
- Mean bbox IoU: 0.8538573000002392.
- Mean OKS: 0.8852506298351936.
- Classifier keypoint: logistic_C0.1.
- L1 accuracy: 0.8560.
- L1 macro-F1: 0.8091.
- Hiệu chỉnh độ tin cậy L1 (ECE / Brier): 0.0502 / 0.2227.
- Ngưỡng từ chối L1: 0.5992.
- L1 selective coverage/accuracy: 0.8640 / 0.9074.
- Tỷ lệ Không xác định: 0.1360.
- L2 oracle macro-F1: 0.6690.
- L2 exact trên toàn bộ mẫu có gold L2: 0.0971.
- Tỷ lệ fallback trên mẫu người gán nhãn để trống L2: 0.9545.
- Accuracy bộ kiểm tra đủ bằng chứng L2: 0.7920.

## So sánh và giới hạn

- Chênh lệch L1 accuracy hướng ảnh trừ hướng keypoint: 0.0324.
- Bootstrap 95% CI: [-0.03199999999999992, 0.09600000000000009].
- Nhánh ảnh sử dụng: historical_convnext_branches; checkpoint và ngưỡng từ validation được ghi ở image_classifier/selection.json.
- Mô hình keypoint dùng đặc trưng hình học chuẩn hóa, classifier L2 riêng theo nhánh và bộ kiểm tra đủ bằng chứng L2.
- Ngưỡng L2 theo bốn nhánh L1 của ứng viên lịch sử đã khóa trên validation và kiểm tra qua ba fold theo hiện vật; train_new dùng bộ chọn ngưỡng riêng.
- Tổ hợp ResNet18 lịch sử được temperature scaling; ngưỡng theo nhánh của ứng viên được chọn trên validation.
- Chế độ train_new dùng loss effective; chế độ historical_convnext_branches dùng checkpoint ảnh cũ, không huấn luyện lại ảnh.
- Ensemble nhiều seed; không suy rộng quá phạm vi snapshot hoặc coi test đã xem là đánh giá độc lập mới.
- Các lớp L2 support nhỏ phải được báo cùng support và confusion matrix.
- Không xác định là từ chối do bằng chứng yếu theo validation; chưa thể diễn giải như bộ phát hiện OOD vì chưa có tập âm/OOD.
- Dữ liệu và trọng số chỉ dùng nội bộ theo metadata quyền sử dụng.


## Đầu ra triển khai

{
  "selection": {
    "image_weight": 1.0,
    "l1_threshold": 0.0,
    "l2_threshold": 0.0,
    "evidence_threshold": 0.85,
    "class_thresholds": {
      "C2.1": 0.6500000000000001,
      "C2.2": 0.6500000000000001,
      "C2.3": 0.6500000000000001,
      "C2.4": 0.6500000000000001,
      "C2.5": 0.6500000000000001,
      "C2.6": 0.1,
      "C2.7": 0.1,
      "C2.8": 0.1,
      "C2.9": 0.5000000000000001,
      "C2.10": 0.5000000000000001,
      "C2.11": 0.1
    },
    "l1_choice": {
      "threshold": 0.0,
      "selection_rule": "frozen 2026-11-03 validation gate"
    },
    "threshold_choice": {
      "calibration": "four_parent_branches",
      "branch_thresholds": {
        "C1.1": 0.6500000000000001,
        "C1.2": 0.1,
        "C1.3": 0.5000000000000001,
        "C1.4": 0.1
      },
      "selection_rule": "frozen 2026-11-03 validation gate"
    },
    "quality": {
      "score": 0.7285830354559448,
      "l1_accuracy": 0.9191176470588235,
      "l2_precision": 0.9538461538461539,
      "blank_acceptance": 0.03333333333333333,
      "l1_macro_f1": 0.8971200154112888,
      "l2_end_to_end_macro_f1": 0.5600460555006009,
      "per_class": [
        {
          "code": "C2.1",
          "support": 41,
          "predicted": 33,
          "correct": 33,
          "precision": 1.0,
          "recall": 0.8048780487804879,
          "f1": 0.8918918918918919
        },
        {
          "code": "C2.2",
          "support": 4,
          "predicted": 0,
          "correct": 0,
          "precision": 0.0,
          "recall": 0.0,
          "f1": 0.0
        },
        {
          "code": "C2.3",
          "support": 19,
          "predicted": 9,
          "correct": 8,
          "precision": 0.8888888888888888,
          "recall": 0.42105263157894735,
          "f1": 0.5714285714285714
        },
        {
          "code": "C2.4",
          "support": 4,
          "predicted": 0,
          "correct": 0,
          "precision": 0.0,
          "recall": 0.0,
          "f1": 0.0
        },
        {
          "code": "C2.5",
          "support": 6,
          "predicted": 1,
          "correct": 1,
          "precision": 1.0,
          "recall": 0.16666666666666666,
          "f1": 0.2857142857142857
        },
        {
          "code": "C2.6",
          "support": 5,
          "predicted": 5,
          "correct": 4,
          "precision": 0.8,
          "recall": 0.8,
          "f1": 0.8000000000000002
        },
        {
          "code": "C2.7",
          "support": 7,
          "predicted": 5,
          "correct": 4,
          "precision": 0.8,
          "recall": 0.5714285714285714,
          "f1": 0.6666666666666666
        },
        {
          "code": "C2.8",
          "support": 3,
          "predicted": 3,
          "correct": 3,
          "precision": 1.0,
          "recall": 1.0,
          "f1": 1.0
        },
        {
          "code": "C2.9",
          "support": 5,
          "predicted": 3,
          "correct": 3,
          "precision": 1.0,
          "recall": 0.6,
          "f1": 0.7499999999999999
        },
        {
          "code": "C2.10",
          "support": 6,
          "predicted": 1,
          "correct": 1,
          "precision": 1.0,
          "recall": 0.16666666666666666,
          "f1": 0.2857142857142857
        },
        {
          "code": "C2.11",
          "support": 6,
          "predicted": 5,
          "correct": 5,
          "precision": 1.0,
          "recall": 0.8333333333333334,
          "f1": 0.9090909090909091
        }
      ]
    },
    "selection_guard": {
      "selection_split": "historical_val",
      "test_used": false,
      "user_selected_frozen_candidate": "convnext_branches_baseline0.5"
    },
    "source": "historical_convnext_branches"
  },
  "test": {
    "l1_accuracy": 0.888,
    "l1_macro_f1": 0.8385968852949985,
    "l1_ece": 0.06930560362025141,
    "l1_brier": 0.1402499669351618,
    "l1_selective_coverage": 1.0,
    "l1_selective_accuracy": 0.888,
    "unknown_rate": 0.0,
    "l2_oracle_accuracy": 0.7864077669902912,
    "l2_oracle_macro_f1": 0.7250265816055289,
    "l2_coverage": 0.6407766990291263,
    "l2_selective_accuracy": 0.8333333333333334,
    "l2_exact_over_all": 0.5339805825242718,
    "l2_blank_abstention": 1.0,
    "l2_evidence_accuracy": 0.864
  }
}