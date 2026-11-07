# Kết quả thực nghiệm phân tích tư thế Thangka

Run: 20261031_174634_seed20261021  
Chế độ: full (smoke chỉ kiểm tra thực thi, không phải kết quả mô hình cuối)  
Seeds ảnh thực tế: [20261021, 20261031, 20261107]  
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
- L1 accuracy: 0.9040.
- L1 macro-F1: 0.8546.
- Hiệu chỉnh độ tin cậy L1 (ECE / Brier): 0.0350 / 0.1548.
- Ngưỡng từ chối L1: 0.4267.
- L1 selective coverage/accuracy: 0.9840 / 0.9106.
- Tỷ lệ Không xác định: 0.0160.
- L2 oracle macro-F1: 0.6749.
- L2 exact trên toàn bộ mẫu có gold L2: 0.3204.
- Tỷ lệ fallback trên mẫu người gán nhãn để trống L2: 0.9091.

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

- Chênh lệch L1 accuracy hướng ảnh trừ hướng keypoint: 0.0482.
- Bootstrap 95% CI: [-0.008000000000000007, 0.11199999999999999].
- Mô hình ảnh học head, mở các block trên rồi toàn backbone; cố định thống kê BatchNorm, dùng loss phân cấp joint và head bằng chứng L2.
- Mô hình keypoint dùng đặc trưng hình học chuẩn hóa, classifier L2 riêng theo nhánh và bộ kiểm tra đủ bằng chứng L2.
- Tất cả nhãn L2 có ngưỡng riêng được chọn trên validation; báo support và khoảng tin cậy, không ép nhãn hiếm.
- Xác suất được temperature scaling trên validation trước khi chọn ngưỡng từ chối.
- Ensemble nhiều seed; không suy rộng quá phạm vi snapshot hoặc coi test đã xem là đánh giá độc lập mới.
- Các lớp L2 support nhỏ phải được báo cùng support và confusion matrix.
- Không xác định là từ chối do bằng chứng yếu theo validation; chưa thể diễn giải như bộ phát hiện OOD vì chưa có tập âm/OOD.
- Dữ liệu và trọng số chỉ dùng nội bộ theo metadata quyền sử dụng.


## Đầu ra triển khai

{
  "selection": {
    "image_weight": 1.0,
    "l1_threshold": 0.4267,
    "l2_threshold": 0.0,
    "evidence_threshold": 0.5,
    "class_thresholds": {
      "C2.1": 0.8424416506474687,
      "C2.2": 1.0001,
      "C2.3": 0.6729900438586809,
      "C2.4": 1.0001,
      "C2.5": 1.0001,
      "C2.6": 0.6059472968962741,
      "C2.7": 1.0001,
      "C2.8": 0.22926941522779,
      "C2.9": 1.0001,
      "C2.10": 1.0001,
      "C2.11": 0.0
    },
    "l1_choice": {
      "threshold": 0.4267,
      "accepted": 134,
      "rejected": 2,
      "coverage": 0.9852941176470589,
      "selective_accuracy": 0.9104477611940298,
      "selective_risk": 0.08955223880597019,
      "accuracy_95ci_wilson": [
        0.8499868912578767,
        0.948030543246656
      ],
      "selection_rule": "maximum validation coverage subject to accepted L1 accuracy >= 0.90"
    },
    "threshold_choice": {
      "evidence_threshold": 0.5,
      "per_class": {
        "C2.1": {
          "threshold": 0.8424416506474687,
          "accepted": 17,
          "correct": 17,
          "precision": 1.0,
          "recall": 0.4146341463414634,
          "support": 41,
          "precision_95ci_wilson": [
            0.8156763396284354,
            1.0
          ]
        },
        "C2.2": {
          "threshold": 1.0001,
          "accepted": 0,
          "correct": 0,
          "precision": 0.0,
          "recall": 0.0,
          "support": 4,
          "precision_95ci_wilson": null
        },
        "C2.3": {
          "threshold": 0.6729900438586809,
          "accepted": 12,
          "correct": 11,
          "precision": 0.9166666666666666,
          "recall": 0.5789473684210527,
          "support": 19,
          "precision_95ci_wilson": [
            0.6461140782014047,
            0.9851352905492264
          ]
        },
        "C2.4": {
          "threshold": 1.0001,
          "accepted": 0,
          "correct": 0,
          "precision": 0.0,
          "recall": 0.0,
          "support": 4,
          "precision_95ci_wilson": null
        },
        "C2.5": {
          "threshold": 1.0001,
          "accepted": 0,
          "correct": 0,
          "precision": 0.0,
          "recall": 0.0,
          "support": 6,
          "precision_95ci_wilson": null
        },
        "C2.6": {
          "threshold": 0.6059472968962741,
          "accepted": 3,
          "correct": 3,
          "precision": 1.0,
          "recall": 0.6,
          "support": 5,
          "precision_95ci_wilson": [
            0.43849391955098227,
            1.0
          ]
        },
        "C2.7": {
          "threshold": 1.0001,
          "accepted": 0,
          "correct": 0,
          "precision": 0.0,
          "recall": 0.0,
          "support": 7,
          "precision_95ci_wilson": null
        },
        "C2.8": {
          "threshold": 0.22926941522779,
          "accepted": 3,
          "correct": 3,
          "precision": 1.0,
          "recall": 1.0,
          "support": 3,
          "precision_95ci_wilson": [
            0.43849391955098227,
            1.0
          ]
        },
        "C2.9": {
          "threshold": 1.0001,
          "accepted": 0,
          "correct": 0,
          "precision": 0.0,
          "recall": 0.0,
          "support": 5,
          "precision_95ci_wilson": null
        },
        "C2.10": {
          "threshold": 1.0001,
          "accepted": 0,
          "correct": 0,
          "precision": 0.0,
          "recall": 0.0,
          "support": 6,
          "precision_95ci_wilson": null
        },
        "C2.11": {
          "threshold": 0.0,
          "accepted": 6,
          "correct": 6,
          "precision": 1.0,
          "recall": 1.0,
          "support": 6,
          "precision_95ci_wilson": [
            0.6096569663469354,
            0.9999999999999999
          ]
        }
      },
      "macro_recall": 0.3266892286147742,
      "accepted": 41,
      "selection_rule": "maximize macro L2 recall; each accepted class requires >=3 validation predictions, precision >=0.90, zero blank-L2 acceptances",
      "warning": "Empirical validation targets, not a guarantee; inspect small support and Wilson intervals."
    },
    "quality": {
      "score": 0.6157910874431681,
      "l1_macro_f1": 0.8637745098039216,
      "l2_end_to_end_macro_f1": 0.36780766508241475,
      "per_class": [
        {
          "code": "C2.1",
          "support": 41,
          "predicted": 17,
          "correct": 17,
          "precision": 1.0,
          "recall": 0.4146341463414634,
          "f1": 0.5862068965517241
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
          "predicted": 12,
          "correct": 11,
          "precision": 0.9166666666666666,
          "recall": 0.5789473684210527,
          "f1": 0.7096774193548387
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
          "predicted": 0,
          "correct": 0,
          "precision": 0.0,
          "recall": 0.0,
          "f1": 0.0
        },
        {
          "code": "C2.6",
          "support": 5,
          "predicted": 3,
          "correct": 3,
          "precision": 1.0,
          "recall": 0.6,
          "f1": 0.7499999999999999
        },
        {
          "code": "C2.7",
          "support": 7,
          "predicted": 0,
          "correct": 0,
          "precision": 0.0,
          "recall": 0.0,
          "f1": 0.0
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
          "predicted": 0,
          "correct": 0,
          "precision": 0.0,
          "recall": 0.0,
          "f1": 0.0
        },
        {
          "code": "C2.10",
          "support": 6,
          "predicted": 0,
          "correct": 0,
          "precision": 0.0,
          "recall": 0.0,
          "f1": 0.0
        },
        {
          "code": "C2.11",
          "support": 6,
          "predicted": 6,
          "correct": 6,
          "precision": 1.0,
          "recall": 1.0,
          "f1": 1.0
        }
      ]
    }
  },
  "test": {
    "l1_accuracy": 0.904,
    "l1_macro_f1": 0.8545879617669853,
    "l1_ece": 0.03499723704066759,
    "l1_brier": 0.15480986313430684,
    "l1_selective_coverage": 0.984,
    "l1_selective_accuracy": 0.9105691056910569,
    "unknown_rate": 0.016000000000000014,
    "l2_oracle_accuracy": 0.7766990291262136,
    "l2_oracle_macro_f1": 0.6749457322967995,
    "l2_coverage": 0.3592233009708738,
    "l2_selective_accuracy": 0.8918918918918919,
    "l2_exact_over_all": 0.32038834951456313,
    "l2_blank_abstention": 0.9090909090909091,
    "l2_evidence_accuracy": 0.88
  }
}