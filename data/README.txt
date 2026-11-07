Thangka training export v2

classification_manifest.csv: complete model manifest for L1/L2 classification.
posture_labels.csv: backward-compatible copy of the classification manifest.
keypoints_coco.json: approved, full 17-keypoint records only.
keypoints_partial_coco.json: approved records with at least one keypoint.
ontology.json: label indexes, parent mapping, keypoint order and skeleton.
dataset_metadata.json: versions, preprocessing, split configuration and statistics.
quality_report.json: blockers, warnings and affected image IDs.
annotation_changes.csv and ai_evaluation.json: immutable first-AI versus final-review audit.
research_manifest.csv: approved records for internal/research-only use.
rights_research_only.csv: records limited to internal research or course use.
release/: intentionally empty manifests because project policy prohibits publication.
review_summary.csv and provenance.csv: compact review and source metadata, without raw audit history.
splits/: task-specific train/val/test lists and grouped folds.
checksums.sha256: hashes for packaged images and crops.
images/ and crops/: included according to export options.
