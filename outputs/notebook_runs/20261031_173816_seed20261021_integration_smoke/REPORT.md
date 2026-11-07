# Kết quả thực nghiệm phân tích tư thế Thangka

Run: 20261031_173816_seed20261021_integration_smoke  
Chế độ: smoke (smoke chỉ kiểm tra thực thi, không phải kết quả mô hình cuối)  
Seeds ảnh thực tế: [20261021]  
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
- L1 accuracy: 0.3200.
- L1 macro-F1: 0.2666.
- Hiệu chỉnh độ tin cậy L1 (ECE / Brier): 0.0461 / 0.7160.
- Ngưỡng từ chối L1: 0.2845.
- L1 selective coverage/accuracy: 0.9120 / 0.3333.
- Tỷ lệ Không xác định: 0.0880.
- L2 oracle macro-F1: 0.2919.
- L2 exact trên toàn bộ mẫu có gold L2: 0.0291.
- Tỷ lệ fallback trên mẫu người gán nhãn để trống L2: 0.9545.

## Pose và phân loại từ keypoint dự đoán

- Pose PCK@0.05 bbox diagonal: 0.7862.
- Mean bbox IoU: 0.8538573000002392.
- Mean OKS: 0.8852506298351936.
- Classifier keypoint: logistic_C0.1.
- L1 accuracy: 0.8480.
- L1 macro-F1: 0.8005.
- Hiệu chỉnh độ tin cậy L1 (ECE / Brier): 0.0484 / 0.2318.
- Ngưỡng từ chối L1: 0.6429.
- L1 selective coverage/accuracy: 0.8320 / 0.9038.
- Tỷ lệ Không xác định: 0.1680.
- L2 oracle macro-F1: 0.6694.
- L2 exact trên toàn bộ mẫu có gold L2: 0.1165.
- Tỷ lệ fallback trên mẫu người gán nhãn để trống L2: 0.9545.
- Accuracy bộ kiểm tra đủ bằng chứng L2: 0.8080.

## So sánh và giới hạn

- Chênh lệch L1 accuracy hướng ảnh trừ hướng keypoint: -0.5278.
- Bootstrap 95% CI: [-0.632, -0.42400000000000004].
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
    "image_weight": 0.5,
    "l1_threshold": 0.4279,
    "l2_threshold": 0.0,
    "evidence_threshold": 0.75,
    "class_thresholds": {
      "C2.1": 0.45900359904450727,
      "C2.2": 1.0001,
      "C2.3": 0.33325594374621537,
      "C2.4": 1.0001,
      "C2.5": 1.0001,
      "C2.6": 1.0001,
      "C2.7": 1.0001,
      "C2.8": 1.0001,
      "C2.9": 1.0001,
      "C2.10": 1.0001,
      "C2.11": 0.0
    },
    "l1_choice": {
      "threshold": 0.4279,
      "accepted": 121,
      "rejected": 15,
      "coverage": 0.8897058823529411,
      "selective_accuracy": 0.9008264462809917,
      "selective_risk": 0.09917355371900827,
      "accuracy_95ci_wilson": [
        0.8346292610982092,
        0.9423553337804208
      ],
      "selection_rule": "maximum validation coverage subject to accepted L1 accuracy >= 0.90"
    },
    "threshold_choice": {
      "evidence_threshold": 0.75,
      "per_class": {
        "C2.1": {
          "threshold": 0.45900359904450727,
          "accepted": 22,
          "correct": 21,
          "precision": 0.9545454545454546,
          "recall": 0.5121951219512195,
          "support": 41,
          "precision_95ci_wilson": [
            0.7820151050048196,
            0.9919307806988522
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
          "threshold": 0.33325594374621537,
          "accepted": 9,
          "correct": 9,
          "precision": 1.0,
          "recall": 0.47368421052631576,
          "support": 19,
          "precision_95ci_wilson": [
            0.7008472464490407,
            1.0
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
          "threshold": 1.0001,
          "accepted": 0,
          "correct": 0,
          "precision": 0.0,
          "recall": 0.0,
          "support": 5,
          "precision_95ci_wilson": null
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
          "threshold": 1.0001,
          "accepted": 0,
          "correct": 0,
          "precision": 0.0,
          "recall": 0.0,
          "support": 3,
          "precision_95ci_wilson": null
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
          "accepted": 3,
          "correct": 3,
          "precision": 1.0,
          "recall": 0.5,
          "support": 6,
          "precision_95ci_wilson": [
            0.43849391955098227,
            1.0
          ]
        }
      },
      "macro_recall": 0.13507993931613957,
      "accepted": 34,
      "selection_rule": "maximize macro L2 recall; each accepted class requires >=3 validation predictions, precision >=0.90, zero blank-L2 acceptances",
      "warning": "Empirical validation targets, not a guarantee; inspect small support and Wilson intervals."
    },
    "quality": {
      "score": 0.5062256493506494,
      "l1_macro_f1": 0.8327976190476191,
      "l2_end_to_end_macro_f1": 0.17965367965367965,
      "per_class": [
        {
          "code": "C2.1",
          "support": 41,
          "predicted": 22,
          "correct": 21,
          "precision": 0.9545454545454546,
          "recall": 0.5121951219512195,
          "f1": 0.6666666666666667
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
          "correct": 9,
          "precision": 1.0,
          "recall": 0.47368421052631576,
          "f1": 0.6428571428571429
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
          "predicted": 0,
          "correct": 0,
          "precision": 0.0,
          "recall": 0.0,
          "f1": 0.0
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
          "predicted": 0,
          "correct": 0,
          "precision": 0.0,
          "recall": 0.0,
          "f1": 0.0
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
          "predicted": 3,
          "correct": 3,
          "precision": 1.0,
          "recall": 0.5,
          "f1": 0.6666666666666666
        }
      ]
    }
  },
  "test": {
    "l1_accuracy": 0.848,
    "l1_macro_f1": 0.7975649084185423,
    "l1_ece": 0.287683914403703,
    "l1_brier": 0.3441514895566743,
    "l1_selective_coverage": 0.84,
    "l1_selective_accuracy": 0.8952380952380953,
    "unknown_rate": 0.16000000000000003,
    "l2_oracle_accuracy": 0.7572815533980582,
    "l2_oracle_macro_f1": 0.6694414673024298,
    "l2_coverage": 0.34951456310679613,
    "l2_selective_accuracy": 0.9444444444444444,
    "l2_exact_over_all": 0.3300970873786408,
    "l2_blank_abstention": 0.9090909090909091,
    "l2_evidence_accuracy": 0.848
  }
}