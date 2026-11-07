# Thangka training dataset thangka_pose_v1.1.0_dacntt_2026-10-20

Created: 2026-10-20T17:22:58+00:00

The dated JSON exports preserve the 2026-10-20 snapshot. The working CSV manifests received an Ngân/My label-consensus amendment on 2026-10-30 (see `LABEL_CONSENSUS_20261030.md`); use the manifest SHA-256 to identify the exact revision used for a run. `artifact_id_or_manual_visual_relation_group` is the grouping key for train/validation/test splits and cross-validation folds. Use `classification_manifest.csv` for L1/L2 and `keypoints_coco.json` for full-keypoint MMPose training. `keypoints_partial_coco.json` is for masked or partial-keypoint experiments.

Technical training readiness: true

Public release readiness: false — project policy is internal/research-only and prohibits dataset publication.

Quality blockers: none

Review `quality_report.json`, provenance, rights, class support and split statistics before reporting model metrics. Top-level manifests and `research_manifest.csv` are internal-research artifacts. The `release/` manifests are intentionally empty because project policy prohibits public release. A generated split is reproducible, but small classes can still require grouped cross-validation.
