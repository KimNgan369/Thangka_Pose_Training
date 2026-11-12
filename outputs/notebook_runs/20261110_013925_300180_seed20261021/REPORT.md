# Kết quả thực nghiệm phân tích tư thế Thangka

Run: 20261110_013925_300180_seed20261021  
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
- L1 accuracy: 0.8800.
- L1 macro-F1: 0.8308.
- Hiệu chỉnh độ tin cậy L1 (ECE / Brier): 0.0462 / 0.1625.
- Ngưỡng từ chối L1: 0.0000.
- L1 selective coverage/accuracy: 1.0000 / 0.8800.
- Tỷ lệ Không xác định: 0.0000.
- L2 oracle macro-F1: 0.7487.
- L2 exact trên toàn bộ mẫu có gold L2: 0.3689.
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

- Chênh lệch L1 accuracy hướng ảnh trừ hướng keypoint: 0.0238.
- Bootstrap 95% CI: [-0.03200000000000003, 0.08799999999999997].
- Nhánh ảnh sử dụng: fresh_run_all; checkpoint và ngưỡng từ validation được ghi ở image_classifier/selection.json.
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
    "evidence_threshold": 0.5,
    "class_thresholds": {
      "C2.1": 0.9079823350900244,
      "C2.2": 1.0001,
      "C2.3": 0.5008228120062537,
      "C2.4": 1.0001,
      "C2.5": 1.0001,
      "C2.6": 0.46299196499547285,
      "C2.7": 1.0001,
      "C2.8": 0.0,
      "C2.9": 1.0001,
      "C2.10": 1.0001,
      "C2.11": 0.0
    },
    "l1_choice": {
      "threshold": 0.0,
      "accepted": 136,
      "rejected": 0,
      "coverage": 1.0,
      "selective_accuracy": 0.9191176470588235,
      "selective_risk": 0.08088235294117652,
      "accuracy_95ci_wilson": [
        0.8609695547552825,
        0.9542385092256787
      ],
      "selection_rule": "maximum validation coverage subject to accepted L1 accuracy >= 0.90"
    },
    "threshold_choice": {
      "evidence_threshold": 0.5,
      "per_class": {
        "C2.1": {
          "threshold": 0.9079823350900244,
          "accepted": 22,
          "correct": 22,
          "precision": 1.0,
          "recall": 0.5365853658536586,
          "support": 41,
          "precision_95ci_wilson": [
            0.8513404742740388,
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
          "threshold": 0.5008228120062537,
          "accepted": 14,
          "correct": 13,
          "precision": 0.9285714285714286,
          "recall": 0.6842105263157895,
          "support": 19,
          "precision_95ci_wilson": [
            0.6853073044604219,
            0.9872781138877085
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
          "threshold": 0.46299196499547285,
          "accepted": 4,
          "correct": 4,
          "precision": 1.0,
          "recall": 0.8,
          "support": 5,
          "precision_95ci_wilson": [
            0.5100999795960008,
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
          "threshold": 0.0,
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
          "accepted": 5,
          "correct": 5,
          "precision": 1.0,
          "recall": 0.8333333333333334,
          "support": 6,
          "precision_95ci_wilson": [
            0.5655085052479191,
            1.0
          ]
        }
      },
      "macro_recall": 0.3503753841366165,
      "accepted": 48,
      "selection_rule": "maximize macro L2 recall; each accepted class requires >=3 validation predictions, precision >=0.90, zero blank-L2 acceptances",
      "warning": "Empirical validation targets, not a guarantee; inspect small support and Wilson intervals.",
      "calibration": "per_class",
      "branch_validation": {
        "l1_accuracy": 0.9191176470588235,
        "l1_macro_f1": 0.8868943107969445,
        "l1_confusion_matrix": [
          [
            87,
            0,
            1,
            0
          ],
          [
            0,
            12,
            4,
            0
          ],
          [
            4,
            2,
            19,
            0
          ],
          [
            0,
            0,
            0,
            7
          ]
        ],
        "l1_selective_accuracy": 0.9191176470588235,
        "l1_coverage": 1.0,
        "macro_f1": 0.4176651631197086,
        "macro_recall": 0.37648611551050576,
        "precision": 0.9302325581395349,
        "blank_acceptance": 0.03333333333333333,
        "exact_recall": 0.37735849056603776,
        "accepted": 43,
        "correct": 40,
        "nonzero_classes": 6,
        "per_class": [
          {
            "code": "C2.1",
            "support": 41,
            "predicted": 22,
            "correct": 22,
            "precision": 1.0,
            "recall": 0.5365853658536586,
            "f1": 0.6984126984126984
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
            "predicted": 5,
            "correct": 4,
            "precision": 0.8,
            "recall": 0.8,
            "f1": 0.8
          },
          {
            "code": "C2.7",
            "support": 7,
            "predicted": 6,
            "correct": 4,
            "precision": 0.6666666666666666,
            "recall": 0.5714285714285714,
            "f1": 0.6153846153846154
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
            "predicted": 2,
            "correct": 2,
            "precision": 1.0,
            "recall": 0.4,
            "f1": 0.5714285714285714
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
            "predicted": 5,
            "correct": 5,
            "precision": 1.0,
            "recall": 0.8333333333333334,
            "f1": 0.9090909090909091
          }
        ]
      },
      "branch_crossfit": {
        "l1_accuracy": 0.9191176470588235,
        "l1_macro_f1": 0.8868943107969445,
        "l1_confusion_matrix": [
          [
            87,
            0,
            1,
            0
          ],
          [
            0,
            12,
            4,
            0
          ],
          [
            4,
            2,
            19,
            0
          ],
          [
            0,
            0,
            0,
            7
          ]
        ],
        "l1_selective_accuracy": 0.9191176470588235,
        "l1_coverage": 1.0,
        "macro_f1": 0.3591659986916904,
        "macro_recall": 0.31310649128364143,
        "precision": 0.8571428571428571,
        "blank_acceptance": 0.1,
        "exact_recall": 0.39622641509433965,
        "accepted": 49,
        "correct": 42,
        "nonzero_classes": 6,
        "per_class": [
          {
            "code": "C2.1",
            "support": 41,
            "predicted": 28,
            "correct": 26,
            "precision": 0.9285714285714286,
            "recall": 0.6341463414634146,
            "f1": 0.7536231884057971
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
            "predicted": 3,
            "correct": 2,
            "precision": 0.6666666666666666,
            "recall": 0.10526315789473684,
            "f1": 0.18181818181818182
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
            "predicted": 5,
            "correct": 4,
            "precision": 0.8,
            "recall": 0.8,
            "f1": 0.8
          },
          {
            "code": "C2.7",
            "support": 7,
            "predicted": 6,
            "correct": 4,
            "precision": 0.6666666666666666,
            "recall": 0.5714285714285714,
            "f1": 0.6153846153846154
          },
          {
            "code": "C2.8",
            "support": 3,
            "predicted": 2,
            "correct": 2,
            "precision": 1.0,
            "recall": 0.6666666666666666,
            "f1": 0.8
          },
          {
            "code": "C2.9",
            "support": 5,
            "predicted": 1,
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
    "quality": {
      "score": 0.6381867592289852,
      "l1_accuracy": 0.9191176470588235,
      "l2_precision": 0.9791666666666666,
      "blank_acceptance": 0.0,
      "l1_macro_f1": 0.8868943107969445,
      "l2_end_to_end_macro_f1": 0.38947920766102584,
      "per_class": [
        {
          "code": "C2.1",
          "support": 41,
          "predicted": 22,
          "correct": 22,
          "precision": 1.0,
          "recall": 0.5365853658536586,
          "f1": 0.6984126984126985
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
          "predicted": 14,
          "correct": 13,
          "precision": 0.9285714285714286,
          "recall": 0.6842105263157895,
          "f1": 0.7878787878787878
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
          "predicted": 4,
          "correct": 4,
          "precision": 1.0,
          "recall": 0.8,
          "f1": 0.888888888888889
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
          "predicted": 5,
          "correct": 5,
          "precision": 1.0,
          "recall": 0.8333333333333334,
          "f1": 0.9090909090909091
        }
      ]
    },
    "selection_guard": {
      "anchor": 4,
      "eligible": [
        4
      ],
      "checks": {
        "0": {
          "l1_macro_f1": false,
          "l1_accuracy": false,
          "l2_macro_f1": false,
          "l2_precision": true,
          "blank_acceptance": true
        },
        "1": {
          "l1_macro_f1": false,
          "l1_accuracy": false,
          "l2_macro_f1": false,
          "l2_precision": true,
          "blank_acceptance": true
        },
        "2": {
          "l1_macro_f1": false,
          "l1_accuracy": false,
          "l2_macro_f1": false,
          "l2_precision": true,
          "blank_acceptance": true
        },
        "3": {
          "l1_macro_f1": false,
          "l1_accuracy": false,
          "l2_macro_f1": false,
          "l2_precision": true,
          "blank_acceptance": true
        },
        "4": {
          "l1_macro_f1": true,
          "l1_accuracy": true,
          "l2_macro_f1": true,
          "l2_precision": true,
          "blank_acceptance": true
        }
      },
      "selection_split": "val",
      "test_used": false
    }
  },
  "test": {
    "l1_accuracy": 0.88,
    "l1_macro_f1": 0.8308074534161491,
    "l1_ece": 0.04619847502856779,
    "l1_brier": 0.1625068402747945,
    "l1_selective_coverage": 1.0,
    "l1_selective_accuracy": 0.88,
    "unknown_rate": 0.0,
    "l2_oracle_accuracy": 0.8058252427184466,
    "l2_oracle_macro_f1": 0.7486621963894691,
    "l2_coverage": 0.39805825242718446,
    "l2_selective_accuracy": 0.926829268292683,
    "l2_exact_over_all": 0.36893203883495146,
    "l2_blank_abstention": 0.9090909090909091,
    "l2_evidence_accuracy": 0.88
  }
}