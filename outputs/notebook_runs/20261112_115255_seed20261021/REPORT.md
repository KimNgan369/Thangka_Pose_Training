# Kết quả thực nghiệm phân tích tư thế Thangka

Run: 20261112_115255_seed20261021  
Chế độ: full (smoke chỉ kiểm tra thực thi, không phải kết quả mô hình cuối)  
Seeds ảnh thực tế: {'resnet18': [20261021, 20261031, 20261107], 'mobilenet_v2': [20261021, 20261031, 20261107], 'convnext_tiny': [20261103, 20261113]}  
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

- Kiến trúc: convnext_resnet_convweight0.25.
- L1 accuracy: 0.8880.
- L1 macro-F1: 0.8431.
- Hiệu chỉnh độ tin cậy L1 (ECE / Brier): 0.0494 / 0.1511.
- Ngưỡng từ chối L1: 0.0000.
- L1 selective coverage/accuracy: 1.0000 / 0.8880.
- Tỷ lệ Không xác định: 0.0000.
- L2 oracle macro-F1: 0.7386.
- L2 exact trên toàn bộ mẫu có gold L2: 0.5340.
- Tỷ lệ fallback trên mẫu người gán nhãn để trống L2: 0.8636.

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

- Chênh lệch L1 accuracy hướng ảnh trừ hướng keypoint: 0.0321.
- Bootstrap 95% CI: [-0.03200000000000003, 0.09599999999999997].
- Checkpoint ảnh và ngưỡng chọn trên validation được ghi ở image_classifier/selection.json.
- Mô hình keypoint dùng đặc trưng hình học chuẩn hóa, classifier L2 riêng theo nhánh và bộ kiểm tra đủ bằng chứng L2.
- Ngưỡng L2 được chọn trên validation và kiểm tra theo nhóm hiện vật.
- ConvNeXt dùng lấy mẫu cân bằng theo tần suất và hàm mất mát phân cấp.
- Các ứng viên và ngưỡng đều được chọn trước khi đánh giá test.
- Tổ hợp nhiều seed cần được kiểm tra thêm trên dữ liệu độc lập ngoài snapshot này.
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
      "C2.1": 0.7000000000000002,
      "C2.2": 0.7000000000000002,
      "C2.3": 0.7000000000000002,
      "C2.4": 0.7000000000000002,
      "C2.5": 0.7000000000000002,
      "C2.6": 0.20000000000000004,
      "C2.7": 0.20000000000000004,
      "C2.8": 0.20000000000000004,
      "C2.9": 0.6500000000000001,
      "C2.10": 0.6500000000000001,
      "C2.11": 0.1
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
          "code": "C2.1",
          "support": 41,
          "predicted": 37,
          "correct": 35,
          "precision": 0.9459459459459459,
          "recall": 0.8536585365853658,
          "f1": 0.8974358974358975,
          "threshold": 0.7000000000000002
        },
        "C2.2": {
          "code": "C2.2",
          "support": 4,
          "predicted": 0,
          "correct": 0,
          "precision": 0.0,
          "recall": 0.0,
          "f1": 0.0,
          "threshold": 0.7000000000000002
        },
        "C2.3": {
          "code": "C2.3",
          "support": 19,
          "predicted": 11,
          "correct": 10,
          "precision": 0.9090909090909091,
          "recall": 0.5263157894736842,
          "f1": 0.6666666666666666,
          "threshold": 0.7000000000000002
        },
        "C2.4": {
          "code": "C2.4",
          "support": 4,
          "predicted": 0,
          "correct": 0,
          "precision": 0.0,
          "recall": 0.0,
          "f1": 0.0,
          "threshold": 0.7000000000000002
        },
        "C2.5": {
          "code": "C2.5",
          "support": 6,
          "predicted": 1,
          "correct": 1,
          "precision": 1.0,
          "recall": 0.16666666666666666,
          "f1": 0.2857142857142857,
          "threshold": 0.7000000000000002
        },
        "C2.6": {
          "code": "C2.6",
          "support": 5,
          "predicted": 5,
          "correct": 4,
          "precision": 0.8,
          "recall": 0.8,
          "f1": 0.8,
          "threshold": 0.20000000000000004
        },
        "C2.7": {
          "code": "C2.7",
          "support": 7,
          "predicted": 5,
          "correct": 4,
          "precision": 0.8,
          "recall": 0.5714285714285714,
          "f1": 0.6666666666666666,
          "threshold": 0.20000000000000004
        },
        "C2.8": {
          "code": "C2.8",
          "support": 3,
          "predicted": 3,
          "correct": 3,
          "precision": 1.0,
          "recall": 1.0,
          "f1": 1.0,
          "threshold": 0.20000000000000004
        },
        "C2.9": {
          "code": "C2.9",
          "support": 5,
          "predicted": 2,
          "correct": 2,
          "precision": 1.0,
          "recall": 0.4,
          "f1": 0.5714285714285714,
          "threshold": 0.6500000000000001
        },
        "C2.10": {
          "code": "C2.10",
          "support": 6,
          "predicted": 0,
          "correct": 0,
          "precision": 0.0,
          "recall": 0.0,
          "f1": 0.0,
          "threshold": 0.6500000000000001
        },
        "C2.11": {
          "code": "C2.11",
          "support": 6,
          "predicted": 6,
          "correct": 6,
          "precision": 1.0,
          "recall": 1.0,
          "f1": 1.0,
          "threshold": 0.1
        }
      },
      "macro_recall": 0.3585249153926946,
      "accepted": 47,
      "selection_rule": "Compare both gates on identical artifact-held folds; maximize L2 F1 subject to precision/blank constraints.",
      "warning": "Empirical validation targets, not a guarantee; inspect small support and Wilson intervals.",
      "calibration": "parent_branches",
      "branch_validation": {
        "l1_accuracy": 0.9191176470588235,
        "l1_macro_f1": 0.8895833333333333,
        "l1_confusion_matrix": [
          [
            87,
            0,
            1,
            0
          ],
          [
            1,
            12,
            3,
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
        "macro_f1": 0.5352647352647352,
        "macro_recall": 0.48346086946857164,
        "precision": 0.9285714285714286,
        "blank_acceptance": 0.1,
        "exact_recall": 0.6132075471698113,
        "accepted": 70,
        "correct": 65,
        "nonzero_classes": 8,
        "per_class": [
          {
            "code": "C2.1",
            "support": 41,
            "predicted": 37,
            "correct": 35,
            "precision": 0.9459459459459459,
            "recall": 0.8536585365853658,
            "f1": 0.8974358974358975
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
            "predicted": 11,
            "correct": 10,
            "precision": 0.9090909090909091,
            "recall": 0.5263157894736842,
            "f1": 0.6666666666666666
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
            "f1": 0.8
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
            "predicted": 6,
            "correct": 6,
            "precision": 1.0,
            "recall": 1.0,
            "f1": 1.0
          }
        ]
      },
      "branch_crossfit": {
        "l1_accuracy": 0.9191176470588235,
        "l1_macro_f1": 0.8895833333333333,
        "l1_confusion_matrix": [
          [
            87,
            0,
            1,
            0
          ],
          [
            1,
            12,
            3,
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
        "macro_f1": 0.4546499046499047,
        "macro_recall": 0.39578825111559385,
        "precision": 0.8870967741935484,
        "blank_acceptance": 0.1,
        "exact_recall": 0.5188679245283019,
        "accepted": 62,
        "correct": 55,
        "nonzero_classes": 8,
        "per_class": [
          {
            "code": "C2.1",
            "support": 41,
            "predicted": 33,
            "correct": 32,
            "precision": 0.9696969696969697,
            "recall": 0.7804878048780488,
            "f1": 0.8648648648648649
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
            "correct": 7,
            "precision": 0.875,
            "recall": 0.3684210526315789,
            "f1": 0.5185185185185185
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
            "predicted": 1,
            "correct": 0,
            "precision": 0.0,
            "recall": 0.0,
            "f1": 0.0
          },
          {
            "code": "C2.10",
            "support": 6,
            "predicted": 2,
            "correct": 1,
            "precision": 0.5,
            "recall": 0.16666666666666666,
            "f1": 0.25
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
      },
      "class_crossfit": {
        "l1_accuracy": 0.9191176470588235,
        "l1_macro_f1": 0.8895833333333333,
        "l1_confusion_matrix": [
          [
            87,
            0,
            1,
            0
          ],
          [
            1,
            12,
            3,
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
        "macro_f1": 0.188023088023088,
        "macro_recall": 0.1570139317250999,
        "precision": 0.7948717948717948,
        "blank_acceptance": 0.13333333333333333,
        "exact_recall": 0.29245283018867924,
        "accepted": 39,
        "correct": 31,
        "nonzero_classes": 4,
        "per_class": [
          {
            "code": "C2.1",
            "support": 41,
            "predicted": 22,
            "correct": 20,
            "precision": 0.9090909090909091,
            "recall": 0.4878048780487805,
            "f1": 0.6349206349206349
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
            "predicted": 6,
            "correct": 5,
            "precision": 0.8333333333333334,
            "recall": 0.2631578947368421,
            "f1": 0.4
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
            "predicted": 3,
            "correct": 1,
            "precision": 0.3333333333333333,
            "recall": 0.14285714285714285,
            "f1": 0.2
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
            "predicted": 6,
            "correct": 5,
            "precision": 0.8333333333333334,
            "recall": 0.8333333333333334,
            "f1": 0.8333333333333334
          }
        ]
      },
      "branch_checks": {
        "validation_l2_f1": true,
        "validation_precision": true,
        "validation_blank": true,
        "crossfit_precision": true,
        "crossfit_blank": true,
        "crossfit_l2_f1": true
      },
      "limitation": "Gate crossfit only; backbones/temperatures used validation, not nested CV."
    },
    "quality": {
      "score": 0.7124240342990342,
      "l1_accuracy": 0.9191176470588235,
      "l2_precision": 0.9285714285714286,
      "blank_acceptance": 0.1,
      "l1_macro_f1": 0.8895833333333334,
      "l2_end_to_end_macro_f1": 0.5352647352647352,
      "per_class": [
        {
          "code": "C2.1",
          "support": 41,
          "predicted": 37,
          "correct": 35,
          "precision": 0.9459459459459459,
          "recall": 0.8536585365853658,
          "f1": 0.8974358974358975
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
          "predicted": 11,
          "correct": 10,
          "precision": 0.9090909090909091,
          "recall": 0.5263157894736842,
          "f1": 0.6666666666666666
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
          "predicted": 2,
          "correct": 2,
          "precision": 1.0,
          "recall": 0.4,
          "f1": 0.5714285714285715
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
    "l1_accuracy": 0.888,
    "l1_macro_f1": 0.8430555555555556,
    "l1_ece": 0.049415300921052965,
    "l1_brier": 0.15109054317431844,
    "l1_selective_coverage": 1.0,
    "l1_selective_accuracy": 0.888,
    "unknown_rate": 0.0,
    "l2_oracle_accuracy": 0.7961165048543689,
    "l2_oracle_macro_f1": 0.7385737863010591,
    "l2_coverage": 0.6310679611650486,
    "l2_selective_accuracy": 0.8461538461538461,
    "l2_exact_over_all": 0.5339805825242718,
    "l2_blank_abstention": 0.8636363636363636,
    "l2_evidence_accuracy": 0.864
  }
}