# Kết quả thực nghiệm phân tích tư thế Thangka

Run: 20261103_101754_seed20261021  
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
- L1 accuracy: 0.8880.
- L1 macro-F1: 0.8386.
- Hiệu chỉnh độ tin cậy L1 (ECE / Brier): 0.0516 / 0.1597.
- Ngưỡng từ chối L1: 0.0000.
- L1 selective coverage/accuracy: 1.0000 / 0.8880.
- Tỷ lệ Không xác định: 0.0000.
- L2 oracle macro-F1: 0.7672.
- L2 exact trên toàn bộ mẫu có gold L2: 0.3398.
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

- Chênh lệch L1 accuracy hướng ảnh trừ hướng keypoint: 0.0319.
- Bootstrap 95% CI: [-0.02400000000000002, 0.09599999999999997].
- Mô hình ảnh học head, mở các block trên rồi toàn backbone; cố định thống kê BatchNorm, dùng loss phân cấp joint và head bằng chứng L2.
- Mô hình keypoint dùng đặc trưng hình học chuẩn hóa, classifier L2 riêng theo nhánh và bộ kiểm tra đủ bằng chứng L2.
- So sánh ngưỡng theo lớp với ngưỡng chung theo nhánh cha trên validation; kiểm tra độ ổn định theo nhóm hiện vật, không ép nhãn hiếm.
- Xác suất được temperature scaling trên validation trước khi chọn ngưỡng từ chối.
- ConvNeXt được huấn luyện trong cùng vòng so sánh với ResNet18 và MobileNetV2; lấy mẫu cân bằng chỉ trên train, không ép mẫu L2 trống.
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
      "C2.1": 0.8477060390090492,
      "C2.2": 1.0001,
      "C2.3": 0.6694448752609096,
      "C2.4": 1.0001,
      "C2.5": 1.0001,
      "C2.6": 1.0001,
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
      "selective_accuracy": 0.9044117647058824,
      "selective_risk": 0.09558823529411764,
      "accuracy_95ci_wilson": [
        0.8433188415060294,
        0.9432854307563016
      ],
      "selection_rule": "maximum validation coverage subject to accepted L1 accuracy >= 0.90"
    },
    "threshold_choice": {
      "evidence_threshold": 0.5,
      "per_class": {
        "C2.1": {
          "threshold": 0.8477060390090492,
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
          "threshold": 0.6694448752609096,
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
      "macro_recall": 0.2721437740693196,
      "accepted": 38,
      "selection_rule": "maximize macro L2 recall; each accepted class requires >=3 validation predictions, precision >=0.90, zero blank-L2 acceptances",
      "warning": "Empirical validation targets, not a guarantee; inspect small support and Wilson intervals.",
      "calibration": "per_class",
      "branch_validation": {
        "l1_accuracy": 0.9044117647058824,
        "l1_macro_f1": 0.876969696969697,
        "l1_confusion_matrix": [
          [
            84,
            1,
            3,
            0
          ],
          [
            0,
            13,
            3,
            0
          ],
          [
            3,
            3,
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
        "l1_selective_accuracy": 0.9044117647058824,
        "l1_coverage": 1.0,
        "macro_f1": 0.3758154990549356,
        "macro_recall": 0.3017060389332533,
        "precision": 0.9259259259259259,
        "blank_acceptance": 0.1,
        "exact_recall": 0.4716981132075472,
        "accepted": 54,
        "correct": 50,
        "nonzero_classes": 7,
        "per_class": [
          {
            "code": "C2.1",
            "support": 41,
            "predicted": 30,
            "correct": 28,
            "precision": 0.9333333333333333,
            "recall": 0.6829268292682927,
            "f1": 0.7887323943661971
          },
          {
            "code": "C2.2",
            "support": 4,
            "predicted": 1,
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
            "predicted": 2,
            "correct": 2,
            "precision": 1.0,
            "recall": 0.4,
            "f1": 0.5714285714285714
          },
          {
            "code": "C2.7",
            "support": 7,
            "predicted": 1,
            "correct": 1,
            "precision": 1.0,
            "recall": 0.14285714285714285,
            "f1": 0.25
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
        "l1_accuracy": 0.9044117647058824,
        "l1_macro_f1": 0.876969696969697,
        "l1_confusion_matrix": [
          [
            84,
            1,
            3,
            0
          ],
          [
            0,
            13,
            3,
            0
          ],
          [
            3,
            3,
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
        "l1_selective_accuracy": 0.9029850746268657,
        "l1_coverage": 0.9852941176470589,
        "macro_f1": 0.3389238732522315,
        "macro_recall": 0.2992092203902217,
        "precision": 0.8113207547169812,
        "blank_acceptance": 0.16666666666666666,
        "exact_recall": 0.4056603773584906,
        "accepted": 53,
        "correct": 43,
        "nonzero_classes": 6,
        "per_class": [
          {
            "code": "C2.1",
            "support": 41,
            "predicted": 26,
            "correct": 23,
            "precision": 0.8846153846153846,
            "recall": 0.5609756097560976,
            "f1": 0.6865671641791045
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
            "correct": 3,
            "precision": 0.6,
            "recall": 0.6,
            "f1": 0.6
          },
          {
            "code": "C2.7",
            "support": 7,
            "predicted": 5,
            "correct": 3,
            "precision": 0.6,
            "recall": 0.42857142857142855,
            "f1": 0.5
          },
          {
            "code": "C2.8",
            "support": 3,
            "predicted": 1,
            "correct": 1,
            "precision": 1.0,
            "recall": 0.3333333333333333,
            "f1": 0.5
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
            "predicted": 7,
            "correct": 6,
            "precision": 0.8571428571428571,
            "recall": 1.0,
            "f1": 0.9230769230769231
          }
        ]
      }
    },
    "quality": {
      "score": 0.5882977719351468,
      "l1_macro_f1": 0.876969696969697,
      "l2_end_to_end_macro_f1": 0.2996258469005966,
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
    "l1_accuracy": 0.888,
    "l1_macro_f1": 0.8385989010989011,
    "l1_ece": 0.05157842685403176,
    "l1_brier": 0.15968637934280946,
    "l1_selective_coverage": 1.0,
    "l1_selective_accuracy": 0.888,
    "unknown_rate": 0.0,
    "l2_oracle_accuracy": 0.8155339805825242,
    "l2_oracle_macro_f1": 0.7671681680710324,
    "l2_coverage": 0.3592233009708738,
    "l2_selective_accuracy": 0.9459459459459459,
    "l2_exact_over_all": 0.33980582524271846,
    "l2_blank_abstention": 0.9545454545454546,
    "l2_evidence_accuracy": 0.88
  }
}