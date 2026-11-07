# Baseline results — internal course use

Run: `20261021_formal_baseline_seed20261021`  
Snapshot: `thangka_pose_v1.1.0_dacntt_2026-10-20`  
Manifest SHA-256: `2ec24fef466d2dc56a079d6495fb398384b263f1670eeacd939a256c1bd8e0c3`

## Protocol

The snapshot audit passed: 873 approved, human-verified records; supplied group-isolated train/validation/test split (612/136/125); 729 L2 labels and 144 intentionally blank L2 labels. Crops and label-parent consistency were checked. L1 loss uses all eligible records; blank L2 labels are masked, not imputed.

ImageNet-pretrained ResNet-18 and MobileNetV2 were fine-tuned with the same seed, crop size (224×224), light affine augmentation, square-root inverse-frequency class weights, AdamW and early stopping. Architecture selection used only the validation mean of L1 macro-F1 and oracle-conditional L2 macro-F1. ResNet-18 was selected at epoch 7 with 0.7857; MobileNetV2 selected epoch 11 with 0.7851. The difference is negligible and does not establish ResNet-18 as generally superior.

The L2 fallback threshold was selected from validation only. Blank L2 annotations were treated as examples where the output should remain at L1. The operating rule maximized labeled-L2 coverage subject to at least 0.80 validation precision, minimum 30% coverage and at least 15 accepted labeled examples. The selected threshold was 0.9504: 43/106 labeled-L2 examples received a specific leaf (40.6% coverage; 39/43 correct, 90.7%); 5/30 blank-L2 examples received a leaf. The 0.80 precision target is an explicit operating-point choice for this baseline, not a threshold prescribed by the thesis; report it as such.

## Final held-out test metrics

| Measure | Result | 95% Wilson interval | Interpretation |
|---|---:|---:|---|
| L1 accuracy | 105/125 = 84.0% | 76.6–89.4% | End-to-end four-way L1 classification |
| L1 macro-F1 | 0.789 | — | Equal weight per L1 class |
| L2 oracle accuracy | 78/103 = 75.7% | 66.6–83.0% | L2 with the gold L1 branch supplied; not end-to-end |
| L2 oracle macro-F1 | 0.611 | — | Conditional fine-label metric; support is highly uneven |
| End-to-end accepted L2 coverage | 39/103 = 37.9% | — | Fraction of test examples with a gold L2 receiving a specific leaf |
| End-to-end exact accuracy among accepted L2 | 37/39 = 94.9% | 83.1–98.6% | Selective accuracy; excludes 64 L1 fallbacks |
| Exact leaf correct over all gold-L2 examples | 37/103 = 35.9% | 27.3–45.5% | Counts fallback as not providing an exact leaf |
| Blank-L2 test rows returned at L1 | 18/22 = 81.8% | — | 4/22 blank rows still received a leaf; correctness cannot be scored without a gold L2 |

L2 per-class support and oracle F1:

| Class | n | F1 |
|---|---:|---:|
| C2.1 | 37 | 0.878 |
| C2.2 | 4 | 0.000 |
| C2.3 | 17 | 0.686 |
| C2.4 | 6 | 0.667 |
| C2.5 | 6 | 0.444 |
| C2.6 | 3 | 0.667 |
| C2.7 | 7 | 0.769 |
| C2.8 | 3 | 0.500 |
| C2.9 | 8 | 0.778 |
| C2.10 | 4 | 0.333 |
| C2.11 | 8 | 1.000 |

See `test_confusion_matrices.png`, `validation_risk_coverage.png`, `test_metrics.json`, and `test_predictions.csv` for the full diagnostics.

## Limits and audit notes

- This is one fixed group-isolated split and one seed, not a multi-seed or cross-validation estimate. Several L2 test supports are only 3–4 images; their class-level scores are not stable enough for broad claims.
- A preliminary test evaluation was run before the validation-only fallback calibration was revised to treat blank L2 labels as abstention examples. The reported metrics use the final validation-selected threshold (0.9504); no model or threshold choice was made from the preliminary test numbers. For strict external confirmation, preserve a new sealed test set or have an independent evaluator run the final checkpoint.
- C1.5 is not trained/calibrated: this snapshot has no labeled out-of-domain rejection examples.
- This run trains image-based hierarchical classification only; it does not fine-tune a keypoint detector. A geometry/keypoint model would be a separate experiment and should not be evaluated with ground-truth keypoints as if they were predicted inputs.
- Dataset metadata limits use to internal, noncommercial course training/reporting and disallows public release of raw images, dataset, or weights. Some provenance/rights notes also request permission before ML training; resolve that source-specific notice before broader use, and keep this checkpoint private.
- Training was executed through the reusable Python module in this run. The notebook was syntax-checked but this environment did not have Jupyter installed; opening/running the notebook requires the environment in `requirements.txt` (and a compatible CUDA PyTorch build to use the RTX 3050).
