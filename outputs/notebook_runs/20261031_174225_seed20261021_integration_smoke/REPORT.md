# Kết quả thực nghiệm phân tích tư thế Thangka

Run: 20261031_174225_seed20261021_integration_smoke  
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

- Chênh lệch L1 accuracy hướng ảnh trừ hướng keypoint: -0.5360.
- Bootstrap 95% CI: [-0.64, -0.432].
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
    "l1_threshold": 0.4418,
    "l2_threshold": 0.0,
    "evidence_threshold": 0.75,
    "class_thresholds": {
      "C2.1": 0.44561318347900897,
      "C2.2": 1.0001,
      "C2.3": 0.3328738806221688,
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
      "threshold": 0.4418,
      "accepted": 118,
      "rejected": 18,
      "coverage": 0.8676470588235294,
      "selective_accuracy": 0.9067796610169492,
      "selective_risk": 0.09322033898305082,
      "accuracy_95ci_wilson": [
        0.8407592905282243,
        0.9471489444260114
      ],
      "selection_rule": "maximum validation coverage subject to accepted L1 accuracy >= 0.90"
    },
    "threshold_choice": {
      "evidence_threshold": 0.75,
      "per_class": {
        "C2.1": {
          "threshold": 0.44561318347900897,
          "accepted": 24,
          "correct": 23,
          "precision": 0.9583333333333334,
          "recall": 0.5609756097560976,
          "support": 41,
          "precision_95ci_wilson": [
            0.7975777375115778,
            0.992606734645195
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
          "threshold": 0.3328738806221688,
          "accepted": 8,
          "correct": 8,
          "precision": 1.0,
          "recall": 0.42105263157894735,
          "support": 19,
          "precision_95ci_wilson": [
            0.6755843804891231,
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
      "macro_recall": 0.14988135527288285,
      "accepted": 36,
      "selection_rule": "maximize macro L2 recall; each accepted class requires >=3 validation predictions, precision >=0.90, zero blank-L2 acceptances",
      "warning": "Empirical validation targets, not a guarantee; inspect small support and Wilson intervals."
    },
    "quality": {
      "score": 0.511866304991305,
      "l1_macro_f1": 0.8327976190476191,
      "l2_end_to_end_macro_f1": 0.19093499093499092,
      "per_class": [
        {
          "code": "C2.1",
          "support": 41,
          "predicted": 24,
          "correct": 23,
          "precision": 0.9583333333333334,
          "recall": 0.5609756097560976,
          "f1": 0.7076923076923077
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
          "predicted": 8,
          "correct": 8,
          "precision": 1.0,
          "recall": 0.42105263157894735,
          "f1": 0.5925925925925926
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
    "l1_accuracy": 0.848,
    "l1_macro_f1": 0.7975649084185423,
    "l1_ece": 0.29378083233472235,
    "l1_brier": 0.3438863666702579,
    "l1_selective_coverage": 0.8,
    "l1_selective_accuracy": 0.93,
    "unknown_rate": 0.19999999999999996,
    "l2_oracle_accuracy": 0.7572815533980582,
    "l2_oracle_macro_f1": 0.6689823008004826,
    "l2_coverage": 0.3300970873786408,
    "l2_selective_accuracy": 0.9411764705882353,
    "l2_exact_over_all": 0.3106796116504854,
    "l2_blank_abstention": 0.9090909090909091,
    "l2_evidence_accuracy": 0.832
  }
}