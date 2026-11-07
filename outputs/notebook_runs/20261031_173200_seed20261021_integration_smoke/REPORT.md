# Kết quả thực nghiệm phân tích tư thế Thangka

Run: 20261031_173200_seed20261021_integration_smoke  
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
- L1 accuracy: 0.6320.
- L1 macro-F1: 0.1936.
- Hiệu chỉnh độ tin cậy L1 (ECE / Brier): 0.0651 / 0.5322.
- Ngưỡng từ chối L1: 0.4769.
- L1 selective coverage/accuracy: 1.0000 / 0.6320.
- Tỷ lệ Không xác định: 0.0000.
- L2 oracle macro-F1: 0.3163.
- L2 exact trên toàn bộ mẫu có gold L2: 0.0000.
- Tỷ lệ fallback trên mẫu người gán nhãn để trống L2: 1.0000.

## Pose và phân loại từ keypoint dự đoán

- Pose PCK@0.05 bbox diagonal: 0.7819.
- Mean bbox IoU: 0.8538573000002392.
- Mean OKS: 0.7549004311546911.
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

- Chênh lệch L1 accuracy hướng ảnh trừ hướng keypoint: -0.2167.
- Bootstrap 95% CI: [-0.31199999999999994, -0.128].
- Mô hình ảnh dùng fine-tuning hai giai đoạn, trọng số lớp trì hoãn và loss L2 theo từng nhánh L1.
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
    "image_weight": 0.25,
    "l1_threshold": 0.5295,
    "l2_threshold": 0.0,
    "evidence_threshold": 0.5,
    "class_thresholds": {
      "C2.1": 0.7871467851768987,
      "C2.2": 1.0001,
      "C2.3": 1.0001,
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
      "threshold": 0.5295,
      "accepted": 115,
      "rejected": 21,
      "coverage": 0.8455882352941176,
      "selective_accuracy": 0.9130434782608695,
      "selective_risk": 0.08695652173913049,
      "accuracy_95ci_wilson": [
        0.8473013610685256,
        0.952082019835131
      ],
      "selection_rule": "maximum validation coverage subject to accepted L1 accuracy >= 0.90"
    },
    "threshold_choice": {
      "evidence_threshold": 0.5,
      "per_class": {
        "C2.1": {
          "threshold": 0.7871467851768987,
          "accepted": 13,
          "correct": 13,
          "precision": 1.0,
          "recall": 0.3170731707317073,
          "support": 41,
          "precision_95ci_wilson": [
            0.7718981569447083,
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
          "threshold": 1.0001,
          "accepted": 0,
          "correct": 0,
          "precision": 0.0,
          "recall": 0.0,
          "support": 19,
          "precision_95ci_wilson": null
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
          "accepted": 4,
          "correct": 4,
          "precision": 1.0,
          "recall": 0.6666666666666666,
          "support": 6,
          "precision_95ci_wilson": [
            0.5100999795960008,
            1.0
          ]
        }
      },
      "macro_recall": 0.08943089430894308,
      "accepted": 17,
      "selection_rule": "maximize macro L2 recall; each accepted class requires >=3 validation predictions, precision >=0.90, zero blank-L2 acceptances",
      "warning": "Empirical validation targets, not a guarantee; inspect small support and Wilson intervals."
    },
    "quality": {
      "score": 0.47536200338721346,
      "l1_macro_f1": 0.8342256902761105,
      "l2_end_to_end_macro_f1": 0.11649831649831649,
      "per_class": [
        {
          "code": "C2.1",
          "support": 41,
          "predicted": 13,
          "correct": 13,
          "precision": 1.0,
          "recall": 0.3170731707317073,
          "f1": 0.48148148148148145
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
          "predicted": 0,
          "correct": 0,
          "precision": 0.0,
          "recall": 0.0,
          "f1": 0.0
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
          "predicted": 4,
          "correct": 4,
          "precision": 1.0,
          "recall": 0.6666666666666666,
          "f1": 0.8
        }
      ]
    }
  },
  "test": {
    "l1_accuracy": 0.84,
    "l1_macro_f1": 0.7832914857978543,
    "l1_ece": 0.09455295079291551,
    "l1_brier": 0.2364484440730779,
    "l1_selective_coverage": 0.864,
    "l1_selective_accuracy": 0.8796296296296297,
    "unknown_rate": 0.136,
    "l2_oracle_accuracy": 0.7378640776699029,
    "l2_oracle_macro_f1": 0.6273195200596541,
    "l2_coverage": 0.1553398058252427,
    "l2_selective_accuracy": 1.0,
    "l2_exact_over_all": 0.1553398058252427,
    "l2_blank_abstention": 0.9545454545454546,
    "l2_evidence_accuracy": 0.84
  }
}