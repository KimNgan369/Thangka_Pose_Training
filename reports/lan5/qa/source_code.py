from pathlib import Path
from datetime import datetime, timezone
from collections import Counter, defaultdict
import csv, gc, hashlib, json, math, os, platform, random, shutil, sys, time, warnings

def find_project_root():
    start = Path.cwd().resolve()
    candidates = []
    for base in [start, *start.parents]:
        candidates.extend([base, base / "Thangka_Pose_Training"])
    seen = set()
    for candidate in candidates:
        candidate = candidate.resolve()
        if candidate in seen:
            continue
        seen.add(candidate)
        if (candidate / "Thangka_Pose_Training.ipynb").is_file() and (candidate / "data").exists():
            return candidate
    raise FileNotFoundError("Không tìm thấy thư mục Thangka_Pose_Training chứa notebook và data.")

ROOT = find_project_root()
DATA_DIR = (ROOT / "data").resolve()
RATINGS_DIR = ROOT / "ratings"
OUTPUTS_DIR = ROOT / "outputs"
PRETRAINED_DIR = ROOT / "pretrained"
CACHE_DIR = ROOT / "cache"

SEED = 20261021
IMAGE_SIZE = 384
IMAGE_BATCH_SIZE = 4
IMAGE_MAX_EPOCHS = 100
IMAGE_PATIENCE = 20
IMAGE_HEAD_ONLY_EPOCHS = 5
IMAGE_DROPOUT = 0.30
IMAGE_LABEL_SMOOTHING = 0.05
# Moderate inverse-frequency weighting: rare classes count more without letting a few samples dominate.
CLASS_WEIGHT_POWER = 0.5
POSE_IMAGE_SIZE = 416
POSE_BATCH_SIZE = 2
POSE_INFERENCE_BATCH_SIZE = 1
POSE_EPOCHS = 50
POSE_PATIENCE = 10
# Pre-declared validation operating point: seek >=90% accuracy while retaining >=50% coverage.
# If validation cannot meet it, l1_rejection_curve records and uses a transparent fallback rule.
L1_TARGET_SELECTIVE_ACCURACY = 0.90
L1_MIN_COVERAGE = 0.50
L1_MIN_ACCEPTED = 30
# L2 is emitted only when validation supports both label confidence and sufficient visual evidence.
L2_TARGET_PRECISION = 0.90
L2_MAX_BLANK_ACCEPTANCE = 0.10
L2_MIN_COVERAGE = 0.25
# Use train-only inverse-frequency weights for all classes; no extra C2.2 copies.
RARE_L2_WEIGHT_BOOSTS = {}
C2_2_EXTRA_KEYPOINT_COPIES = 0
REUSE_EXISTING = True
# Image models train in each new run; use run_training.py --resume to continue an interrupted run.
# Rare posture labels belong to the classifier; do not retrain pose estimation unless its own metrics require it.
FORCE_RETRAIN_POSE = False

RUN_ID = datetime.now().strftime("%Y%m%d_%H%M%S") + f"_seed{SEED}"
RUN_ROOT = OUTPUTS_DIR / "notebook_runs" / RUN_ID
RUN_ROOT.mkdir(parents=True, exist_ok=False)

required_paths = [
    DATA_DIR / "classification_manifest.csv",
    DATA_DIR / "keypoints_coco.json",
    DATA_DIR / "ontology.json",
]
missing_data = [str(p) for p in required_paths if not p.is_file()]
if missing_data:
    raise FileNotFoundError("Thiếu dữ liệu bắt buộc:\n" + "\n".join(missing_data))

print("Thư mục dự án:", ROOT)
print("Snapshot dữ liệu:", DATA_DIR)
print("Run mới:", RUN_ROOT)

# Predeclared experiment settings. No test score enters model or threshold selection.
IMAGE_SEEDS = [20261021, 20261031, 20261107]
IMAGE_ARCHITECTURES = ["resnet18", "mobilenet_v2"]
IMAGE_ACCUMULATION_STEPS = 4
IMAGE_MIN_EPOCHS = 30
IMAGE_FULL_FINETUNE_START = 16
TRAIN_MAX_BATCHES = None  # Integration runner may cap this; full training always uses all train rows.
RUN_MODE = "full"
MODEL_SCHEMA = 4
TARGET_L2_CODES = ["C2.3", "C2.5", "C2.11", "C2.10", "C2.7"]


required_imports = {
    "numpy": "numpy",
    "pandas": "pandas",
    "PIL": "Pillow",
    "matplotlib": "matplotlib",
    "sklearn": "scikit-learn",
    "joblib": "joblib",
    "openpyxl": "openpyxl",
    "torch": "torch",
    "torchvision": "torchvision",
    "ultralytics": "ultralytics",
    "yaml": "PyYAML",
}
missing_packages = []
for module_name, package_name in required_imports.items():
    try:
        __import__(module_name)
    except Exception:
        missing_packages.append(package_name)
if missing_packages:
    raise RuntimeError(
        "Môi trường thiếu: " + ", ".join(missing_packages) +
        ". Cài đúng PyTorch CUDA trước, sau đó cài các gói còn lại và khởi động lại kernel."
    )

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import joblib
import torch
import torchvision
from PIL import Image
from openpyxl import load_workbook
from sklearn.base import clone
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, cohen_kappa_score, confusion_matrix, f1_score, classification_report
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from ultralytics import YOLO

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
environment = {
    "python": sys.version,
    "platform": platform.platform(),
    "torch": torch.__version__,
    "torchvision": torchvision.__version__,
    "cuda_available": torch.cuda.is_available(),
    "cuda_runtime": torch.version.cuda,
    "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
    "seed": SEED,
}
(RUN_ROOT / "environment.json").write_text(json.dumps(environment, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(environment, ensure_ascii=False, indent=2))
if DEVICE == "cpu":
    warnings.warn("Đang chạy CPU. Pose training có thể rất chậm; kết quả vẫn hợp lệ nhưng thời gian dài hơn.")


"""Reproducible training utilities for the private DACNTT Thangka dataset."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np
import torch
from PIL import Image
from torch import nn
from torch.nn import functional as F
from torch.utils.data import DataLoader, Dataset
from torchvision import models, transforms
from torchvision.transforms import InterpolationMode

PROJECT_ROOT = ROOT
DEFAULT_DATASET_ROOT = DATA_DIR
IGNORE_L2 = -100
IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD = (0.229, 0.224, 0.225)


def seed_everything(seed: int = 20261021) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def load_snapshot(dataset_root: str | Path = DEFAULT_DATASET_ROOT) -> dict[str, Any]:
    root = Path(dataset_root).expanduser().resolve()
    metadata = _read_json(root / "dataset_metadata.json")
    ontology = _read_json(root / "ontology.json")
    registry = _read_json(root / "split_registry.json")
    with (root / "classification_manifest.csv").open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    return {"root": root, "metadata": metadata, "ontology": ontology, "registry": registry, "rows": rows}


def _as_bool(value: str) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes"}


def audit_snapshot(snapshot: dict[str, Any], check_files: bool = True) -> dict[str, Any]:
    root, metadata, ontology, registry, rows = (
        snapshot["root"], snapshot["metadata"], snapshot["ontology"], snapshot["registry"], snapshot["rows"]
    )
    errors: list[str] = []
    if not metadata.get("ready_for_training"):
        errors.append("Metadata does not mark this snapshot ready_for_training.")
    if metadata.get("scope") != "approved":
        errors.append(f"Expected approved-only snapshot; got scope={metadata.get('scope')!r}.")
    if len(rows) != int(metadata.get("records", -1)):
        errors.append(f"CSV row count {len(rows)} differs from metadata record count {metadata.get('records')}.")
    if len({r["instance_id"] for r in rows}) != len(rows):
        errors.append("Duplicate instance_id values in classification_manifest.csv.")

    l1_codes = [item["code"] for item in sorted(ontology["level_1"], key=lambda item: item["index"])]
    l2_codes = [item["code"] for item in sorted(ontology["level_2"], key=lambda item: item["index"])]
    l1_to_idx = {code: i for i, code in enumerate(l1_codes)}
    l2_to_idx = {code: i for i, code in enumerate(l2_codes)}
    l2_parent = {item["code"]: item["parent"] for item in ontology["level_2"]}

    split_counts: Counter[str] = Counter()
    l1_counts: Counter[str] = Counter()
    l2_counts: Counter[str] = Counter()
    split_l2_counts: dict[str, Counter[str]] = defaultdict(Counter)
    missing_files: list[str] = []
    hash_splits: dict[str, set[str]] = defaultdict(set)
    group_splits: dict[str, set[str]] = defaultdict(set)
    assignments = registry.get("assignments", {})
    group_assignments = registry.get("group_assignments", {})

    for row in rows:
        split = row.get("split", "")
        l1 = row.get("level_1_code", "")
        l2 = row.get("level_2_code", "")
        if split not in {"train", "val", "test"}:
            errors.append(f"Invalid split {split!r} for {row.get('instance_id')}.")
        split_counts[split] += 1
        if row.get("review_status") != "approved" or not _as_bool(row.get("human_verified", "")):
            errors.append(f"Non-approved or non-human-verified record: {row.get('instance_id')}.")
        if l1 not in l1_to_idx:
            errors.append(f"Missing/unknown L1 label for {row.get('instance_id')}: {l1!r}.")
        else:
            l1_counts[l1] += 1
        if l2:
            if l2 not in l2_to_idx:
                errors.append(f"Unknown L2 label {l2!r} for {row.get('instance_id')}.")
            else:
                l2_counts[l2] += 1
                split_l2_counts[split][l2] += 1
                if l2_parent[l2] != l1:
                    errors.append(f"Ontology parent mismatch for {row.get('instance_id')}: {l1} vs {l2}.")
        if row.get("rights_status") not in {"verified", "research_only"}:
            errors.append(f"Rights status not eligible for internal training: {row.get('instance_id')}.")
        if check_files:
            crop_rel = Path(row["crop_path"])
            if crop_rel.is_absolute() or ".." in crop_rel.parts:
                errors.append(f"Unsafe crop path in manifest: {row['crop_path']}.")
            elif not (root / crop_rel).is_file():
                missing_files.append(str(crop_rel))
        for digest in (row.get("content_sha256", ""), row.get("crop_sha256", "")):
            if digest:
                hash_splits[digest].add(split)
        artifact_id = row.get("artifact_id", "")
        group_id = group_assignments.get(artifact_id, artifact_id)
        expected_split = assignments.get(group_id, assignments.get(artifact_id))
        if expected_split and expected_split != split:
            errors.append(f"Split registry mismatch for {artifact_id}: CSV={split}, registry={expected_split}.")
        group_splits[group_id].add(split)

    if missing_files:
        errors.append(f"Missing crop files: {len(missing_files)} (first: {missing_files[:5]}).")
    leaking_groups = [group for group, splits in group_splits.items() if len(splits) > 1]
    leaking_hashes = [digest for digest, splits in hash_splits.items() if len(splits) > 1]
    if leaking_groups:
        errors.append(f"Group leakage across splits: {len(leaking_groups)} groups.")
    if leaking_hashes:
        errors.append(f"Exact-image hash leakage across splits: {len(leaking_hashes)} hashes.")
    if errors:
        raise ValueError("Snapshot audit failed:\n- " + "\n- ".join(errors))

    manifest_sha256 = hashlib.sha256((root / "classification_manifest.csv").read_bytes()).hexdigest()
    return {
        "dataset_version": metadata["dataset_version"],
        "manifest_sha256": manifest_sha256,
        "records": len(rows),
        "split_counts": dict(split_counts),
        "l1_counts": dict(l1_counts),
        "l2_counts": dict(l2_counts),
        "l2_by_split": {split: dict(counts) for split, counts in split_l2_counts.items()},
        "l2_labeled": sum(1 for row in rows if row.get("level_2_code")),
        "l2_unlabeled": sum(1 for row in rows if not row.get("level_2_code")),
        "l1_codes": l1_codes,
        "l2_codes": l2_codes,
        "l2_parent": l2_parent,
        "split_group_count": len(group_splits),
        "audit_status": "passed",
    }


def class_index_maps(ontology: dict[str, Any]) -> dict[str, Any]:
    l1_codes = [item["code"] for item in sorted(ontology["level_1"], key=lambda item: item["index"])]
    l2_codes = [item["code"] for item in sorted(ontology["level_2"], key=lambda item: item["index"])]
    l1_to_idx = {code: i for i, code in enumerate(l1_codes)}
    l2_to_idx = {code: i for i, code in enumerate(l2_codes)}
    l2_parent = {item["code"]: item["parent"] for item in ontology["level_2"]}
    return {"l1_codes": l1_codes, "l2_codes": l2_codes, "l1_to_idx": l1_to_idx, "l2_to_idx": l2_to_idx, "l2_parent": l2_parent}


class ResizeWithPad:
    """Resize without distorting body proportions, then pad to a square canvas."""
    def __init__(self, size: int, fill=(255, 255, 255)):
        self.size = int(size)
        self.fill = fill

    def __call__(self, image: Image.Image) -> Image.Image:
        image = image.copy()
        ratio = self.size / max(image.size)
        image = image.resize((max(1, round(image.width * ratio)), max(1, round(image.height * ratio))), Image.Resampling.BILINEAR)
        canvas = Image.new("RGB", (self.size, self.size), self.fill)
        left = (self.size - image.width) // 2
        top = (self.size - image.height) // 2
        canvas.paste(image, (left, top))
        return canvas


class ThangkaDataset(Dataset):
    def __init__(self, rows: list[dict[str, str]], root: Path, indices: dict[str, Any], train: bool = False):
        self.rows = [row for row in rows if row["split"] == "train"] if train else list(rows)
        self.root = root
        self.indices = indices
        if train:
            self.transform = transforms.Compose([
                # Rotate on an expanded canvas BEFORE resize: never cut off feet or a reclining body.
                transforms.RandomRotation(degrees=7, expand=True, fill=(255, 255, 255)),
                ResizeWithPad(IMAGE_SIZE),
                transforms.RandomHorizontalFlip(p=0.5),
                transforms.ColorJitter(brightness=0.10, contrast=0.10, saturation=0.05, hue=0.02),
                transforms.ToTensor(), transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
            ])
        else:
            self.transform = transforms.Compose([
                ResizeWithPad(IMAGE_SIZE),
                transforms.ToTensor(), transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
            ])

    def __len__(self) -> int:
        return len(self.rows)

    def __getitem__(self, index: int):
        row = self.rows[index]
        with Image.open(self.root / row["crop_path"]) as image:
            tensor = self.transform(image.convert("RGB"))
        l1 = self.indices["l1_to_idx"][row["level_1_code"]]
        l2 = self.indices["l2_to_idx"].get(row["level_2_code"], IGNORE_L2)
        return tensor, l1, l2, index


def make_loaders(snapshot: dict[str, Any], batch_size: int = 16, seed: int = 20261021):
    indices = class_index_maps(snapshot["ontology"])
    train_rows = [r for r in snapshot["rows"] if r["split"] == "train"]
    val_rows = [r for r in snapshot["rows"] if r["split"] == "val"]
    test_rows = [r for r in snapshot["rows"] if r["split"] == "test"]
    train_ds = ThangkaDataset(train_rows, snapshot["root"], indices, train=True)
    val_ds = ThangkaDataset(val_rows, snapshot["root"], indices, train=False)
    test_ds = ThangkaDataset(test_rows, snapshot["root"], indices, train=False)
    generator = torch.Generator().manual_seed(seed)
    pin_memory = torch.cuda.is_available()
    loaders = {
        "train": DataLoader(train_ds, batch_size=batch_size, shuffle=True, num_workers=0, pin_memory=pin_memory, generator=generator),
        "val": DataLoader(val_ds, batch_size=batch_size, shuffle=False, num_workers=0, pin_memory=pin_memory),
        "test": DataLoader(test_ds, batch_size=batch_size, shuffle=False, num_workers=0, pin_memory=pin_memory),
    }
    return loaders, indices


class MultiTaskClassifier(nn.Module):
    def __init__(self, architecture: str, n_l1: int, n_l2: int, pretrained: bool = True):
        super().__init__()
        if architecture == "resnet18":
            weights = models.ResNet18_Weights.DEFAULT if pretrained else None
            backbone = models.resnet18(weights=weights)
            feature_dim = backbone.fc.in_features
            backbone.fc = nn.Identity()
        elif architecture == "mobilenet_v2":
            weights = models.MobileNet_V2_Weights.DEFAULT if pretrained else None
            legacy_cache = Path(torch.hub.get_dir()) / "checkpoints" / "mobilenet_v2-b0353104.pth"
            current_cache = Path(torch.hub.get_dir()) / "checkpoints" / "mobilenet_v2-7ebf99e0.pth"
            if pretrained and legacy_cache.is_file() and not current_cache.is_file():
                # Older official torchvision cache filename; strict loading verifies the
                # checkpoint matches this MobileNetV2 architecture before it is used.
                # The filename carries torchvision's SHA-256 prefix; verify it as well.
                cached_hash = hashlib.sha256(legacy_cache.read_bytes()).hexdigest()
                if not cached_hash.startswith("b0353104"):
                    raise ValueError(f"Unexpected MobileNetV2 cache checksum: {cached_hash}")
                backbone = models.mobilenet_v2(weights=None)
                state = torch.load(legacy_cache, map_location="cpu", weights_only=True)
                backbone.load_state_dict(state, strict=True)
            else:
                backbone = models.mobilenet_v2(weights=weights)
            feature_dim = backbone.classifier[-1].in_features
            backbone.classifier = nn.Identity()
        else:
            raise ValueError("architecture must be 'resnet18' or 'mobilenet_v2'")
        self.architecture = architecture
        self.backbone = backbone
        self.l1_head = nn.Sequential(nn.Dropout(IMAGE_DROPOUT), nn.Linear(feature_dim, n_l1))
        self.l2_head = nn.Sequential(nn.Dropout(IMAGE_DROPOUT), nn.Linear(feature_dim, n_l2))
        self.evidence_head = nn.Sequential(nn.Dropout(IMAGE_DROPOUT), nn.Linear(feature_dim, 2))

    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        features = self.backbone(x)
        return self.l1_head(features), self.l2_head(features), self.evidence_head(features)


def _balanced_weights(labels: list[int], class_count: int, device: torch.device) -> torch.Tensor:
    counts = np.bincount(np.asarray(labels, dtype=np.int64), minlength=class_count).astype(np.float64)
    if np.any(counts == 0):
        raise ValueError(f"Training split lacks one or more classes: {counts.tolist()}")
    weights = 1.0 / np.power(counts, CLASS_WEIGHT_POWER)
    weights /= weights.mean()
    return torch.tensor(weights, dtype=torch.float32, device=device)


def configure_backbone_stage(model, head_only, full=False):
    """Small batches must not overwrite pretrained BN running statistics."""
    model.backbone.eval()
    for parameter in model.backbone.parameters():
        parameter.requires_grad = False
    if head_only:
        return
    if full:
        blocks = [model.backbone]
    elif model.architecture == "resnet18":
        blocks = [model.backbone.layer3, model.backbone.layer4]
    else:
        blocks = [model.backbone.features[7:]]
    for block in blocks:
        block.train()
        for parameter in block.parameters():
            parameter.requires_grad = True
    for module in model.backbone.modules():
        if isinstance(module, nn.modules.batchnorm._BatchNorm):
            module.eval()


def hierarchical_l2_loss(
    logits: torch.Tensor, y1: torch.Tensor, y2: torch.Tensor, indices: dict[str, Any],
    class_weights: torch.Tensor | None = None, label_smoothing: float = 0.0,
) -> torch.Tensor:
    """Train L2 only against siblings under the gold L1 branch."""
    branch_losses = []
    for parent_index, parent_code in enumerate(indices["l1_codes"]):
        child_codes = [code for code in indices["l2_codes"] if indices["l2_parent"][code] == parent_code]
        child_indices = [indices["l2_to_idx"][code] for code in child_codes]
        branch_mask = (y2 != IGNORE_L2) & (y1 == parent_index)
        if not branch_mask.any() or len(child_indices) <= 1:
            continue
        local_logits = logits[branch_mask][:, child_indices]
        global_targets = y2[branch_mask]
        local_targets = torch.empty_like(global_targets)
        for local_index, global_index in enumerate(child_indices):
            local_targets[global_targets == global_index] = local_index
        local_weights = class_weights[child_indices] if class_weights is not None else None
        branch_losses.append(F.cross_entropy(
            local_logits, local_targets, weight=local_weights, label_smoothing=label_smoothing,
        ))
    return torch.stack(branch_losses).mean() if branch_losses else logits.sum() * 0.0


def fit_hierarchical_temperatures(outputs: dict[str, np.ndarray], indices: dict[str, Any]) -> dict[str, float]:
    """Fit L1 and branch-aware L2 temperature scaling on validation logits only."""
    logits1 = torch.tensor(outputs["l1_logits"], dtype=torch.float32)
    logits2 = torch.tensor(outputs["l2_logits"], dtype=torch.float32)
    y1 = torch.tensor(outputs["y1"], dtype=torch.long)
    y2 = torch.tensor(outputs["y2"], dtype=torch.long)

    def optimize(loss_builder):
        log_temperature = torch.zeros(1, requires_grad=True)
        optimizer = torch.optim.LBFGS([log_temperature], lr=0.1, max_iter=60, line_search_fn="strong_wolfe")
        def closure():
            optimizer.zero_grad()
            temperature = log_temperature.exp().clamp(0.25, 10.0)
            loss = loss_builder(temperature)
            loss.backward()
            return loss
        optimizer.step(closure)
        return float(log_temperature.detach().exp().clamp(0.25, 10.0).item())

    t1_candidate = optimize(lambda temperature: F.cross_entropy(logits1 / temperature, y1))
    before_l1 = multiclass_calibration_metrics(outputs["l1_logits"], outputs["y1"])
    after_l1 = multiclass_calibration_metrics(outputs["l1_logits"] / t1_candidate, outputs["y1"])
    before_score = before_l1["ece_10_bins"] + before_l1["multiclass_brier"]
    after_score = after_l1["ece_10_bins"] + after_l1["multiclass_brier"]
    # NLL temperature scaling can worsen ECE/Brier on a small validation set.
    # Keep identity calibration unless the declared validation calibration score improves.
    t1 = t1_candidate if after_score <= before_score else 1.0
    def l2_objective(temperature):
        return hierarchical_l2_loss(logits2 / temperature, y1, y2, indices)
    t2 = optimize(l2_objective)
    temperatures = {"l1_temperature": t1, "l2_temperature": t2}
    if "l2_evidence_logits" in outputs:
        evidence_logits = torch.tensor(outputs["l2_evidence_logits"], dtype=torch.float32)
        evidence_gold = (y2 != IGNORE_L2).long()
        temperatures["evidence_temperature"] = optimize(lambda t: F.cross_entropy(evidence_logits / t, evidence_gold))
    return temperatures


def apply_temperatures(outputs: dict[str, np.ndarray], temperatures: dict[str, float]) -> dict[str, np.ndarray]:
    calibrated = dict(outputs)
    calibrated["l1_logits"] = outputs["l1_logits"] / temperatures["l1_temperature"]
    calibrated["l2_logits"] = outputs["l2_logits"] / temperatures["l2_temperature"]
    if "l2_evidence_logits" in outputs:
        calibrated["l2_evidence_logits"] = outputs["l2_evidence_logits"] / temperatures.get("evidence_temperature", 1.0)
    return calibrated


def multiclass_calibration_metrics(logits: np.ndarray, targets: np.ndarray, bins: int = 10) -> dict[str, float]:
    probabilities = torch.softmax(torch.tensor(logits), dim=1).numpy()
    confidence = probabilities.max(axis=1)
    prediction = probabilities.argmax(axis=1)
    correct = (prediction == targets).astype(np.float64)
    ece = 0.0
    edges = np.linspace(0.0, 1.0, bins + 1)
    for lower, upper in zip(edges[:-1], edges[1:]):
        mask = (confidence > lower) & (confidence <= upper)
        if mask.any():
            ece += float(mask.mean() * abs(correct[mask].mean() - confidence[mask].mean()))
    one_hot = np.eye(probabilities.shape[1], dtype=np.float64)[targets]
    brier = float(np.mean(np.sum((probabilities - one_hot) ** 2, axis=1)))
    return {"ece_10_bins": ece, "multiclass_brier": brier}


def collect_logits(model, loader, device):
    model.eval()
    values = {key: [] for key in ("l1_logits", "l2_logits", "l2_evidence_logits", "y1", "y2", "indices")}
    with torch.inference_mode():
        for images, y1, y2, sample_indices in loader:
            logits1, logits2, evidence = model(images.to(device, non_blocking=True))
            for key, value in zip(values, (logits1, logits2, evidence, y1, y2, sample_indices)):
                values[key].append(value.detach().float().cpu().numpy() if key.endswith("logits") else value.cpu().numpy())
    return {key: np.concatenate(value) for key, value in values.items()}


def classification_metrics(y_true: np.ndarray, y_pred: np.ndarray, labels: list[int]) -> dict[str, Any]:
    matrix = np.zeros((len(labels), len(labels)), dtype=np.int64)
    label_pos = {value: i for i, value in enumerate(labels)}
    for truth, pred in zip(y_true.tolist(), y_pred.tolist()):
        if truth in label_pos and pred in label_pos:
            matrix[label_pos[truth], label_pos[pred]] += 1
    per_class = []
    for i, label in enumerate(labels):
        tp = int(matrix[i, i])
        support = int(matrix[i, :].sum())
        predicted = int(matrix[:, i].sum())
        precision = tp / predicted if predicted else 0.0
        recall = tp / support if support else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        per_class.append({"label_index": int(label), "support": support, "precision": precision, "recall": recall, "f1": f1})
    total = int(matrix.sum())
    correct = int(np.trace(matrix))
    return {
        "n": total,
        "accuracy": float(correct / total) if total else 0.0,
        "accuracy_95ci_wilson": wilson_interval(correct, total),
        "macro_f1": float(np.mean([item["f1"] for item in per_class])) if per_class else 0.0,
        "per_class": per_class,
        "confusion_matrix": matrix.tolist(),
    }


def wilson_interval(successes: int, total: int, z: float = 1.96) -> list[float] | None:
    """Two-sided 95% Wilson score interval for a binomial proportion."""
    if total <= 0:
        return None
    p = successes / total
    denominator = 1 + z * z / total
    center = (p + z * z / (2 * total)) / denominator
    half_width = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denominator
    return [max(0.0, center - half_width), min(1.0, center + half_width)]


def metrics_from_outputs(outputs: dict[str, np.ndarray], indices: dict[str, Any]) -> dict[str, Any]:
    pred_l1 = outputs["l1_logits"].argmax(axis=1)
    l1_metrics = classification_metrics(outputs["y1"], pred_l1, list(range(len(indices["l1_codes"]))))
    valid = outputs["y2"] != IGNORE_L2
    gold_l2 = outputs["y2"][valid]
    gold_l1 = outputs["y1"][valid]
    logits_l2 = outputs["l2_logits"][valid]
    pred_oracle = np.empty_like(gold_l2)
    for i, parent_idx in enumerate(gold_l1.tolist()):
        parent_code = indices["l1_codes"][parent_idx]
        child_idx = [indices["l2_to_idx"][code] for code, parent in indices["l2_parent"].items() if parent == parent_code]
        pred_oracle[i] = child_idx[int(logits_l2[i, child_idx].argmax())]
    l2_oracle = classification_metrics(gold_l2, pred_oracle, list(range(len(indices["l2_codes"]))))
    return {"l1": l1_metrics, "l2_oracle_given_gold_l1": l2_oracle}


def hierarchical_predictions(
    outputs: dict[str, np.ndarray], indices: dict[str, Any], threshold: float,
    l1_threshold: float = 0.0, evidence_ok: np.ndarray | list[bool] | None = None,
    l2_evidence_threshold: float = 0.0, class_thresholds: dict[str, float] | None = None,
) -> list[dict[str, Any]]:
    p_l1 = torch.softmax(torch.tensor(outputs["l1_logits"]), dim=1).numpy()
    logits_l2 = outputs["l2_logits"]
    if "l2_evidence_logits" in outputs:
        l2_evidence_probability = torch.softmax(torch.tensor(outputs["l2_evidence_logits"]), dim=1).numpy()[:, 1]
    else:
        l2_evidence_probability = np.ones(len(p_l1), dtype=np.float64)
    if evidence_ok is None:
        evidence_ok = np.ones(len(p_l1), dtype=bool)
    evidence_ok = np.asarray(evidence_ok, dtype=bool)
    if len(evidence_ok) != len(p_l1):
        raise ValueError("evidence_ok must have one value per prediction.")
    class_thresholds = class_thresholds or {}
    predictions = []
    for i in range(len(p_l1)):
        parent_idx = int(p_l1[i].argmax())
        parent_code = indices["l1_codes"][parent_idx]
        l1_confidence = float(p_l1[i, parent_idx])
        l1_accepted = bool(evidence_ok[i] and l1_confidence >= l1_threshold)
        child_codes = [code for code in indices["l2_codes"] if indices["l2_parent"][code] == parent_code]
        child_indices = [indices["l2_to_idx"][code] for code in child_codes]
        child_probs = torch.softmax(torch.tensor(logits_l2[i, child_indices]), dim=0).numpy()
        local_idx = int(child_probs.argmax())
        candidate_code = child_codes[local_idx]
        joint_confidence = float(l1_confidence * child_probs[local_idx])
        required_l2_confidence = float(class_thresholds.get(candidate_code, threshold))
        evidence_probability = float(l2_evidence_probability[i])
        l2_evidence_ok = evidence_probability >= l2_evidence_threshold
        l2_accepted = bool(l1_accepted and l2_evidence_ok and joint_confidence >= required_l2_confidence)
        decision_level = "l2" if l2_accepted else ("l1" if l1_accepted else "unknown")
        final_code = candidate_code if l2_accepted else (parent_code if l1_accepted else "")
        final_confidence = joint_confidence if l2_accepted else l1_confidence
        predictions.append({
            "l1_code": parent_code if l1_accepted else "",
            "l1_candidate": parent_code, "l1_confidence": l1_confidence,
            "l2_candidate": candidate_code, "l2_confidence": joint_confidence,
            "l2_required_confidence": required_l2_confidence,
            "l2_evidence_confidence": evidence_probability, "l2_evidence_ok": bool(l2_evidence_ok),
            "l2_code": candidate_code if l2_accepted else "",
            "used_l1_fallback": bool(l1_accepted and not l2_accepted),
            "is_unknown": not l1_accepted, "decision_level": decision_level,
            "final_code": final_code, "final_confidence": final_confidence,
            "evidence_ok": bool(evidence_ok[i]),
        })
    return predictions


def l1_rejection_curve(
    outputs: dict[str, np.ndarray], min_coverage: float = 0.50, min_accepted: int = 30,
    target_accuracy: float = 0.85, evidence_ok: np.ndarray | list[bool] | None = None,
):
    probabilities = torch.softmax(torch.tensor(outputs["l1_logits"]), dim=1).numpy()
    confidence = probabilities.max(axis=1)
    predicted = probabilities.argmax(axis=1)
    gold = np.asarray(outputs["y1"], dtype=np.int64)
    if evidence_ok is None:
        evidence_ok = np.ones(len(gold), dtype=bool)
    evidence_ok = np.asarray(evidence_ok, dtype=bool)
    candidates = sorted(set([0.0, 1.0] + [round(float(x), 4) for x in np.quantile(confidence, np.linspace(0, 1, 101))]))
    table = []
    for cutoff in candidates:
        accepted = evidence_ok & (confidence >= cutoff)
        accepted_count = int(accepted.sum())
        correct = int(((predicted == gold) & accepted).sum())
        coverage = accepted_count / len(gold) if len(gold) else 0.0
        accuracy = correct / accepted_count if accepted_count else 0.0
        table.append({
            "threshold": float(cutoff), "accepted": accepted_count,
            "rejected": int(len(gold) - accepted_count), "coverage": coverage,
            "selective_accuracy": accuracy, "selective_risk": 1.0 - accuracy if accepted_count else 1.0,
            "accuracy_95ci_wilson": wilson_interval(correct, accepted_count),
        })
    eligible = [row for row in table if row["coverage"] >= min_coverage and row["accepted"] >= min_accepted and row["selective_accuracy"] >= target_accuracy]
    if eligible:
        best = dict(max(eligible, key=lambda row: (row["coverage"], row["selective_accuracy"], -row["threshold"])))
        best["selection_rule"] = f"maximum validation coverage subject to accepted L1 accuracy >= {target_accuracy:.2f}"
    else:
        pool = [row for row in table if row["coverage"] >= min_coverage and row["accepted"] >= min_accepted]
        best = dict(max(pool, key=lambda row: (2 * row["coverage"] * row["selective_accuracy"] / max(row["coverage"] + row["selective_accuracy"], 1e-12), row["coverage"]))) if pool else dict(table[0])
        best["selection_rule"] = f"target accuracy {target_accuracy:.2f} not met; fallback to best harmonic mean of validation coverage and accuracy"
    return table, best


def threshold_curve(
    outputs: dict[str, np.ndarray], indices: dict[str, Any], min_coverage: float = 0.25,
    min_support: int = 15, target_precision: float = 0.90, max_blank_acceptance: float = 0.10,
    evidence_ok: np.ndarray | list[bool] | None = None, l1_threshold: float = 0.0,
):
    # Blank L2 means the human review found insufficient evidence for a detailed label.
    # It supervises an evidence gate, never a fabricated posture class.
    gold = np.asarray(outputs["y2"])
    known_mask = gold != IGNORE_L2
    blank_mask = ~known_mask
    base = hierarchical_predictions(
        outputs, indices, threshold=0.0, l1_threshold=l1_threshold, evidence_ok=evidence_ok
    )
    confidences = np.asarray([row["l2_confidence"] for row in base])
    evidence_scores = np.asarray([row["l2_evidence_confidence"] for row in base])
    candidate_codes = np.asarray([row["l2_candidate"] for row in base])
    source_ok = np.asarray([not row["is_unknown"] for row in base])
    gold_codes = np.asarray([indices["l2_codes"][int(value)] if value != IGNORE_L2 else "" for value in gold])
    confidence_candidates = sorted(set([0.0, 1.0001] + [round(float(x), 4) for x in np.quantile(confidences, np.linspace(0, 1, 41))]))
    evidence_candidates = ([0.0] if "l2_evidence_logits" not in outputs else
                           sorted(set([0.0, 1.0001] + [round(float(x), 4) for x in np.quantile(evidence_scores, np.linspace(0, 1, 21))])))
    labeled_count, blank_count = int(known_mask.sum()), int(blank_mask.sum())
    table = []
    for confidence_threshold in confidence_candidates:
        for evidence_threshold in evidence_candidates:
            accepted = source_ok & (confidences >= confidence_threshold) & (evidence_scores >= evidence_threshold)
            accepted_known = accepted & known_mask
            accepted_blank = accepted & blank_mask
            accepted_known_count = int(accepted_known.sum())
            accepted_blank_count = int(accepted_blank.sum())
            correct = accepted_known & (candidate_codes == gold_codes)
            true_positive = int(correct.sum())
            total_accepted = int(accepted.sum())
            coverage = accepted_known_count / labeled_count if labeled_count else 0.0
            blank_acceptance = accepted_blank_count / blank_count if blank_count else 0.0
            precision = true_positive / total_accepted if total_accepted else 0.0
            recall = true_positive / labeled_count if labeled_count else 0.0
            selective_accuracy = true_positive / accepted_known_count if accepted_known_count else 0.0
            selective_f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
            table.append({
                "threshold": float(confidence_threshold),
                "l2_confidence_threshold": float(confidence_threshold),
                "l2_evidence_threshold": float(evidence_threshold),
                "accepted_total": total_accepted, "accepted_on_labeled_l2": accepted_known_count,
                "accepted_on_blank_l2": accepted_blank_count, "blank_l2_acceptance_rate": blank_acceptance,
                "coverage_of_labeled_l2": coverage, "exact_accuracy_on_accepted_labeled_l2": selective_accuracy,
                "precision_including_blank_l2_abstention_examples": precision,
                "recall_of_gold_l2": recall, "selective_f1": selective_f1,
            })
    eligible = [row for row in table if row["coverage_of_labeled_l2"] >= min_coverage
                and row["accepted_on_labeled_l2"] >= min_support
                and row["precision_including_blank_l2_abstention_examples"] >= target_precision
                and row["blank_l2_acceptance_rate"] <= max_blank_acceptance]
    if eligible:
        best = dict(max(eligible, key=lambda row: (row["coverage_of_labeled_l2"], row["exact_accuracy_on_accepted_labeled_l2"], -row["accepted_on_blank_l2"])))
        best["selection_rule"] = (f"maximum validation L2 coverage subject to precision >= {target_precision:.2f} "
                                  f"and blank acceptance <= {max_blank_acceptance:.2f}")
    else:
        safe_pool = [row for row in table if row["accepted_on_labeled_l2"] >= min_support
                     and row["blank_l2_acceptance_rate"] <= max_blank_acceptance]
        best = dict(max(safe_pool, key=lambda row: (row["precision_including_blank_l2_abstention_examples"], row["coverage_of_labeled_l2"]))) if safe_pool else dict(table[-1])
        best["selection_rule"] = (f"strict target not met; safest validation fallback with blank acceptance <= "
                                  f"{max_blank_acceptance:.2f}")
    return table, best


def select_rare_class_threshold(
    outputs: dict[str, np.ndarray], indices: dict[str, Any], class_code: str,
    base_threshold: float, evidence_threshold: float = 0.0, target_precision: float = 0.75,
    min_accept: int = 2, evidence_ok: np.ndarray | list[bool] | None = None, l1_threshold: float = 0.0,
) -> dict[str, Any]:
    base = hierarchical_predictions(
        outputs, indices, threshold=0.0, l1_threshold=l1_threshold, evidence_ok=evidence_ok
    )
    gold = np.asarray(outputs["y2"])
    gold_codes = np.asarray([indices["l2_codes"][int(value)] if value != IGNORE_L2 else "" for value in gold])
    is_candidate = np.asarray([row["l2_candidate"] == class_code for row in base])
    source_ok = np.asarray([not row["is_unknown"] for row in base])
    scores = np.asarray([row["l2_confidence"] for row in base])
    evidence = np.asarray([row["l2_evidence_confidence"] for row in base])
    candidates = sorted(set([float(base_threshold), 1.0001] + [round(float(x), 4) for x in scores[is_candidate]]))
    trials = []
    for cutoff in candidates:
        accepted = source_ok & is_candidate & (scores >= cutoff) & (evidence >= evidence_threshold)
        count = int(accepted.sum())
        correct = int((accepted & (gold_codes == class_code)).sum())
        precision = correct / count if count else 0.0
        recall = correct / int((gold_codes == class_code).sum()) if np.any(gold_codes == class_code) else 0.0
        trials.append({"threshold": float(cutoff), "accepted": count, "correct": correct,
                       "precision": precision, "recall": recall})
    eligible = [row for row in trials if row["accepted"] >= min_accept and row["precision"] >= target_precision]
    if eligible:
        choice = dict(max(eligible, key=lambda row: (row["recall"], row["precision"], -row["threshold"])))
        choice["selection_rule"] = f"validation precision >= {target_precision:.2f} for {class_code}"
    else:
        choice = {"threshold": 1.0001, "accepted": 0, "correct": 0, "precision": 0.0, "recall": 0.0,
                  "selection_rule": f"insufficient validation evidence for {class_code}; always fallback to L1"}
    return choice


def fit_model(snapshot, architecture, run_dir, *, epochs=100, patience=20, batch_size=4,
              seed=20261021, backbone_lr=2e-5, head_lr=2e-4, weight_decay=5e-4):
    seed_everything(seed)
    torch.set_num_threads(max(1, min(6, os.cpu_count() or 1)))
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    signature = {"architecture": architecture, "seed": seed, "epochs": epochs, "patience": patience,
                 "batch_size": batch_size, "image_size": IMAGE_SIZE, "model_schema": MODEL_SCHEMA,
                 "backbone_lr": backbone_lr, "head_lr": head_lr, "weight_decay": weight_decay,
                 "min_epochs": IMAGE_MIN_EPOCHS, "accumulation": IMAGE_ACCUMULATION_STEPS,
                 "full_finetune_start": IMAGE_FULL_FINETUNE_START, "train_max_batches": TRAIN_MAX_BATCHES,
                 "head_only_epochs": IMAGE_HEAD_ONLY_EPOCHS,
                 "source_sha256": hashlib.sha256((ROOT / "Thangka_Pose_Training.ipynb").read_bytes()).hexdigest(),
                 "manifest_sha256": hashlib.sha256((snapshot["root"] / "classification_manifest.csv").read_bytes()).hexdigest()}
    summary_path, validation_path = run_dir / "training_summary.json", run_dir / "validation_logits.npz"
    if summary_path.is_file() and validation_path.is_file():
        cached = json.loads(summary_path.read_text(encoding="utf-8"))
        if cached.get("training_signature") != signature:
            raise RuntimeError(f"Resume settings/source mismatch: {run_dir}. Start a new run.")
        cached["validation_outputs"] = dict(np.load(validation_path))
        print(f"Reusing completed training: {run_dir.name}", flush=True)
        return cached
    loaders, indices = make_loaders(snapshot, batch_size=batch_size, seed=seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = MultiTaskClassifier(architecture, len(indices["l1_codes"]), len(indices["l2_codes"]), pretrained=True).to(device)
    train_rows = [r for r in snapshot["rows"] if r["split"] == "train"]
    l1_weights = _balanced_weights([indices["l1_to_idx"][r["level_1_code"]] for r in train_rows], len(indices["l1_codes"]), device)
    l2_weights = _balanced_weights([indices["l2_to_idx"][r["level_2_code"]] for r in train_rows if r["level_2_code"]], len(indices["l2_codes"]), device)
    evidence_weights = _balanced_weights([int(bool(r["level_2_code"])) for r in train_rows], 2, device)
    optimizer = torch.optim.AdamW([
        {"params": model.backbone.parameters(), "lr": backbone_lr},
        {"params": list(model.l1_head.parameters()) + list(model.l2_head.parameters()) + list(model.evidence_head.parameters()), "lr": head_lr},
    ], weight_decay=weight_decay)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=max(epochs, 1), eta_min=5e-7)
    scaler = torch.amp.GradScaler("cuda", enabled=device.type == "cuda")
    checkpoint = run_dir / "best_model.pt"
    history, best_score, best_epoch, waits = [], -math.inf, 0, 0
    resume_path = run_dir / "last_training_state.pt"
    start_epoch = 1
    if resume_path.is_file():
        state = torch.load(resume_path, map_location=device, weights_only=False)
        if state["signature"] != signature:
            raise RuntimeError("Resume settings/source mismatch; start a new run.")
        model.load_state_dict(state["model"])
        optimizer.load_state_dict(state["optimizer"])
        scheduler.load_state_dict(state["scheduler"])
        scaler.load_state_dict(state["scaler"])
        history, best_score, best_epoch, waits = state["history"], state["best_score"], state["best_epoch"], state["waits"]
        start_epoch = state["epoch"] + 1
        torch.set_rng_state(state["torch_rng"].cpu())
        if device.type == "cuda":
            torch.cuda.set_rng_state_all([s.cpu() for s in state["cuda_rng"]])
        np.random.set_state(state["numpy_rng"])
        random.setstate(state["python_rng"])
        loaders["train"].generator.set_state(state["loader_rng"].cpu())
        del state
    for epoch in range(start_epoch, epochs + 1):
        if epoch > IMAGE_MIN_EPOCHS and waits >= patience:
            break
        model.train()
        head_only = epoch <= IMAGE_HEAD_ONLY_EPOCHS
        full = epoch >= IMAGE_FULL_FINETUNE_START
        configure_backbone_stage(model, head_only, full=full)
        total_loss, total_examples = 0.0, 0
        optimizer.zero_grad(set_to_none=True)
        steps = len(loaders["train"])
        if TRAIN_MAX_BATCHES is not None:
            steps = min(steps, TRAIN_MAX_BATCHES)
        for step, (images, y1, y2, _) in enumerate(loaders["train"]):
            if step >= steps:
                break
            images, y1, y2 = images.to(device), y1.to(device), y2.to(device)
            with torch.autocast(device_type=device.type, enabled=device.type == "cuda"):
                z1, z2, ze = model(images)
                l1_loss = F.cross_entropy(z1.float(), y1, weight=l1_weights, label_smoothing=IMAGE_LABEL_SMOOTHING)
                l2_loss = hierarchical_l2_loss(z2.float(), y1, y2, indices, l2_weights, IMAGE_LABEL_SMOOTHING)
                known = y2 != IGNORE_L2
                joint_loss = (F.nll_loss(joint_leaf_log_probabilities(z1.float(), z2.float(), indices)[known],
                                         y2[known], weight=l2_weights) if known.any() else z2.sum() * 0.0)
                evidence_loss = F.cross_entropy(ze.float(), known.long(), weight=evidence_weights)
                loss = l1_loss + l2_loss + 0.5 * joint_loss + 0.5 * evidence_loss
            # Correct normalization also for the final incomplete accumulation group.
            group_start = (step // IMAGE_ACCUMULATION_STEPS) * IMAGE_ACCUMULATION_STEPS
            group_size = min(IMAGE_ACCUMULATION_STEPS, steps - group_start)
            scaler.scale(loss / group_size).backward()
            if (step + 1) % IMAGE_ACCUMULATION_STEPS == 0 or step + 1 == steps:
                scaler.unscale_(optimizer)
                torch.nn.utils.clip_grad_norm_(model.parameters(), 5.0)
                scaler.step(optimizer)
                scaler.update()
                optimizer.zero_grad(set_to_none=True)
            total_loss += float(loss.detach()) * len(y1)
            total_examples += len(y1)
            if (step + 1) % 40 == 0:
                print(f"{architecture} seed={seed} epoch={epoch} batch={step+1}/{steps}", flush=True)
        validation = collect_logits(model, loaders["val"], device)
        score = quality_selection_score(validation, indices)
        metrics = metrics_from_outputs(validation, indices)
        history.append({"epoch": epoch, "train_loss": total_loss / total_examples,
                        "val_l1_macro_f1": metrics["l1"]["macro_f1"],
                        "val_l2_oracle_macro_f1": metrics["l2_oracle_given_gold_l1"]["macro_f1"],
                        "selection_score": score, "training_stage": "head" if head_only else ("full" if full else "upper_blocks")})
        if score > best_score + 1e-6:
            best_score, best_epoch, waits = score, epoch, 0
            torch.save({k: v.detach().cpu() for k, v in model.state_dict().items()}, checkpoint)
        else:
            waits += 1
        scheduler.step()
        # Save optimizer, scheduler and RNG state, so an interrupted long run can continue.
        state_path = run_dir / "last_training_state.tmp"
        torch.save({"signature": signature, "model": model.state_dict(), "optimizer": optimizer.state_dict(),
                    "scheduler": scheduler.state_dict(), "scaler": scaler.state_dict(), "epoch": epoch,
                    "history": history, "best_score": best_score, "best_epoch": best_epoch, "waits": waits,
                    "torch_rng": torch.get_rng_state(), "cuda_rng": torch.cuda.get_rng_state_all() if device.type == "cuda" else [],
                    "numpy_rng": np.random.get_state(), "python_rng": random.getstate(),
                    "loader_rng": loaders["train"].generator.get_state()}, state_path)
        state_path.replace(resume_path)
        (run_dir / "history.json").write_text(json.dumps(history, indent=2), encoding="utf-8")
        print(f"{architecture} seed={seed} epoch={epoch}/{epochs} loss={history[-1]['train_loss']:.4f} val score={score:.4f} best={best_score:.4f}", flush=True)
        if epoch >= IMAGE_MIN_EPOCHS and waits >= patience:
            break
    model.load_state_dict(torch.load(checkpoint, map_location=device, weights_only=True))
    best_validation = collect_logits(model, loaders["val"], device)
    summary = {"architecture": architecture, "seed": seed, "best_epoch": best_epoch,
               "best_validation_selection_score": best_score, "epochs_completed": len(history),
               "checkpoint": str(checkpoint), "image_size": IMAGE_SIZE, "model_schema": MODEL_SCHEMA,
               "manifest_sha256": hashlib.sha256((snapshot["root"] / "classification_manifest.csv").read_bytes()).hexdigest(),
               "selection_metric": "0.35 L1 macro-F1 + 0.40 L2 end-to-end macro-F1 + 0.15 oracle L2 macro-F1 + 0.10 evidence macro-F1",
               "training": "full-body resize; joint hierarchical loss; evidence head; progressive full fine-tuning; frozen BN statistics",
               "batch_size": batch_size, "accumulation_steps": IMAGE_ACCUMULATION_STEPS,
               "history": history, "validation_outputs": best_validation, "training_signature": signature}
    np.savez_compressed(validation_path, **best_validation)
    (run_dir / "training_summary.json").write_text(json.dumps({k: v for k, v in summary.items() if k != "validation_outputs"}, ensure_ascii=False, indent=2), encoding="utf-8")
    del model, optimizer, scaler, loaders
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    return summary


def load_model(architecture: str, checkpoint: str | Path, ontology: dict[str, Any], device: str | None = None):
    indices = class_index_maps(ontology)
    device_obj = torch.device(device or ("cuda" if torch.cuda.is_available() else "cpu"))
    model = MultiTaskClassifier(architecture, len(indices["l1_codes"]), len(indices["l2_codes"]), pretrained=False)
    model.load_state_dict(torch.load(checkpoint, map_location=device_obj, weights_only=True))
    model.to(device_obj).eval()
    return model, device_obj, indices


def predict_image(model, image_path, indices, threshold, device, l1_threshold=0.0,
                  class_thresholds=None, temperatures=None, evidence_threshold=0.0):
    transform = transforms.Compose([ResizeWithPad(IMAGE_SIZE), transforms.ToTensor(), transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD)])
    with Image.open(image_path) as image:
        tensor = transform(image.convert("RGB")).unsqueeze(0).to(device)
    model.eval()
    with torch.inference_mode():
        z1, z2, ze = model(tensor)
    outputs = {"l1_logits": z1.cpu().numpy(), "l2_logits": z2.cpu().numpy(), "l2_evidence_logits": ze.cpu().numpy()}
    if temperatures:
        outputs = apply_temperatures(outputs, temperatures)
    return hierarchical_predictions(outputs, indices, threshold, l1_threshold, None, evidence_threshold, class_thresholds)[0]


def save_test_predictions(
    path: str | Path, rows: list[dict[str, str]], outputs: dict[str, np.ndarray],
    indices: dict[str, Any], threshold: float, l1_threshold: float = 0.0,
    evidence_ok: np.ndarray | list[bool] | None = None, l2_evidence_threshold: float = 0.0,
    class_thresholds: dict[str, float] | None = None,
) -> dict[str, Any]:
    rows = [row for row in rows if row["split"] == "test"]
    predictions = hierarchical_predictions(
        outputs, indices, threshold, l1_threshold, evidence_ok, l2_evidence_threshold, class_thresholds
    )
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["instance_id", "image_id", "split", "gold_l1", "pred_l1", "gold_l2", "pred_l2", "final_code", "decision_level", "is_unknown", "l1_confidence", "l2_candidate", "l2_confidence", "l2_evidence_confidence", "l2_evidence_ok", "used_l1_fallback"]
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for row, pred in zip(rows, predictions):
            writer.writerow({
                "instance_id": row["instance_id"], "image_id": row["image_id"], "split": row["split"],
                "gold_l1": row["level_1_code"], "pred_l1": pred["l1_code"], "gold_l2": row["level_2_code"],
                "pred_l2": pred["l2_code"], "final_code": pred["final_code"],
                "decision_level": pred["decision_level"], "is_unknown": pred["is_unknown"],
                "l1_confidence": pred["l1_confidence"],
                "l2_candidate": pred["l2_candidate"], "l2_confidence": pred["l2_confidence"],
                "l2_evidence_confidence": pred["l2_evidence_confidence"], "l2_evidence_ok": pred["l2_evidence_ok"],
                "used_l1_fallback": pred["used_l1_fallback"],
            })
    raw_metrics = metrics_from_outputs(outputs, indices)
    accepted_l1 = [(row, pred) for row, pred in zip(rows, predictions) if not pred["is_unknown"]]
    correct_l1 = sum(row["level_1_code"] == pred["l1_code"] for row, pred in accepted_l1)
    l1_selective = {
        "accepted": len(accepted_l1), "rejected_as_unknown": len(rows) - len(accepted_l1),
        "coverage": len(accepted_l1) / len(rows) if rows else 0.0,
        "selective_accuracy": correct_l1 / len(accepted_l1) if accepted_l1 else 0.0,
        "selective_accuracy_95ci_wilson": wilson_interval(correct_l1, len(accepted_l1)),
        "threshold": float(l1_threshold),
    }
    valid_rows = [(row, pred) for row, pred in zip(rows, predictions) if row["level_2_code"]]
    blank_rows = [(row, pred) for row, pred in zip(rows, predictions) if not row["level_2_code"]]
    accepted = [(row, pred) for row, pred in valid_rows if pred["l2_code"]]
    fallback_l1 = [(row, pred) for row, pred in valid_rows if pred["decision_level"] == "l1"]
    unknown_l1 = [(row, pred) for row, pred in valid_rows if pred["is_unknown"]]
    accepted_on_blank = [(row, pred) for row, pred in blank_rows if pred["l2_code"]]
    exact = sum(row["level_2_code"] == pred["l2_code"] for row, pred in accepted)
    gold_count, accepted_count = len(valid_rows), len(accepted)
    l2_end_to_end = {
        "n_with_gold_l2": gold_count, "accepted_leaf_predictions": accepted_count,
        "coverage": accepted_count / gold_count if gold_count else 0.0,
        "selective_accuracy": exact / accepted_count if accepted_count else 0.0,
        "selective_accuracy_95ci_wilson": wilson_interval(exact, accepted_count),
        "exact_leaf_correct_over_all_gold_l2": exact / gold_count if gold_count else 0.0,
        "exact_leaf_accuracy_95ci_wilson": wilson_interval(exact, gold_count),
        "fallback_to_l1_count_among_gold_l2": len(fallback_l1),
        "unknown_count_among_gold_l2": len(unknown_l1),
        "n_without_gold_l2": len(blank_rows),
        "accepted_leaf_predictions_on_blank_l2": len(accepted_on_blank),
        "abstention_rate_on_blank_l2": (len(blank_rows) - len(accepted_on_blank)) / len(blank_rows) if blank_rows else 0.0,
        "l2_confidence_threshold": float(threshold),
        "l2_evidence_threshold": float(l2_evidence_threshold),
        "class_specific_thresholds": dict(class_thresholds or {}),
    }
    l2_evidence_metrics = None
    if "l2_evidence_logits" in outputs:
        evidence_gold = (np.asarray(outputs["y2"]) != IGNORE_L2).astype(np.int64)
        evidence_pred = np.asarray(outputs["l2_evidence_logits"]).argmax(axis=1)
        l2_evidence_metrics = classification_metrics(evidence_gold, evidence_pred, [0, 1])
    return {
        "l1_all_test": raw_metrics["l1"],
        "l1_calibration": multiclass_calibration_metrics(outputs["l1_logits"], outputs["y1"]),
        "l1_selective_with_unknown": l1_selective,
        "l2_oracle_given_gold_l1": raw_metrics["l2_oracle_given_gold_l1"],
        "l2_evidence_classifier": l2_evidence_metrics,
        "l2_end_to_end_with_l1_fallback": l2_end_to_end,
        "test_rows": len(rows),
    }


def joint_leaf_log_probabilities(logits1, logits2, indices):
    log_parent = F.log_softmax(logits1, dim=1)
    result = torch.zeros_like(logits2)
    for p, parent in enumerate(indices["l1_codes"]):
        children = [indices["l2_to_idx"][c] for c in indices["l2_codes"] if indices["l2_parent"][c] == parent]
        result[:, children] = log_parent[:, p:p+1] + F.log_softmax(logits2[:, children], dim=1)
    return result


def quality_selection_score(outputs, indices):
    """End-to-end routing matters more than an oracle that supplies the correct L1."""
    metrics = metrics_from_outputs(outputs, indices)
    decisions = hierarchical_predictions(outputs, indices, 0.0)
    valid = outputs["y2"] != IGNORE_L2
    pred = np.array([indices["l2_to_idx"][r["l2_candidate"]] for r in decisions])
    e2e = classification_metrics(outputs["y2"][valid], pred[valid], list(range(len(indices["l2_codes"]))))
    evidence = classification_metrics((outputs["y2"] != IGNORE_L2).astype(int),
                                      outputs["l2_evidence_logits"].argmax(1), [0, 1])
    return (0.35 * metrics["l1"]["macro_f1"] + 0.40 * e2e["macro_f1"] +
            0.15 * metrics["l2_oracle_given_gold_l1"]["macro_f1"] + 0.10 * evidence["macro_f1"])


def average_hierarchical_outputs(outputs_list, indices, weights=None):
    """Average JOINT leaf mass, then recover conditional heads; preserve parent sums."""
    if not outputs_list:
        raise ValueError("No ensemble members.")
    n = len(outputs_list[0]["l1_logits"])
    if weights is None:
        weights = np.ones((len(outputs_list), n), dtype=np.float64) / len(outputs_list)
    weights = np.asarray(weights, dtype=np.float64)
    if weights.ndim == 1:
        weights = np.repeat(weights[:, None], n, axis=1)
    if weights.shape != (len(outputs_list), n) or np.any(weights < 0) or np.any(weights.sum(0) <= 0):
        raise ValueError("Invalid ensemble weights.")
    weights = weights / weights.sum(0, keepdims=True)
    p1 = np.zeros_like(outputs_list[0]["l1_logits"], dtype=np.float64)
    leaf = np.zeros_like(outputs_list[0]["l2_logits"], dtype=np.float64)
    pe = np.zeros((n, 2), dtype=np.float64)
    for w, out in zip(weights, outputs_list):
        for key in ("y1", "y2", "indices"):
            if key in outputs_list[0] and (key not in out or not np.array_equal(out[key], outputs_list[0][key])):
                raise ValueError(f"Ensemble row alignment mismatch: {key}")
        z1, z2 = torch.tensor(out["l1_logits"]), torch.tensor(out["l2_logits"])
        p1 += w[:, None] * torch.softmax(z1, 1).numpy()
        leaf += w[:, None] * joint_leaf_log_probabilities(z1, z2, indices).exp().numpy()
        pe += w[:, None] * torch.softmax(torch.tensor(out["l2_evidence_logits"]), 1).numpy()
    conditional = np.zeros_like(leaf)
    for p, parent in enumerate(indices["l1_codes"]):
        children = [indices["l2_to_idx"][c] for c in indices["l2_codes"] if indices["l2_parent"][c] == parent]
        conditional[:, children] = leaf[:, children] / np.maximum(p1[:, p:p+1], 1e-12)
    result = {k: outputs_list[0][k] for k in ("y1", "y2", "indices") if k in outputs_list[0]}
    result.update(l1_logits=np.log(np.clip(p1, 1e-12, 1)), l2_logits=np.log(np.clip(conditional, 1e-12, 1)),
                  l2_evidence_logits=np.log(np.clip(pe, 1e-12, 1)))
    return result


def select_class_operating_points(outputs, indices, l1_threshold, evidence_ok=None):
    """Do not let one weak class suppress every L2. Never relax the precision target."""
    base = hierarchical_predictions(outputs, indices, 0.0, l1_threshold, evidence_ok)
    candidate = np.array([r["l2_candidate"] for r in base])
    confidence = np.array([r["l2_confidence"] for r in base])
    evidence = np.array([r["l2_evidence_confidence"] for r in base])
    source_ok = np.array([not r["is_unknown"] for r in base])
    gold = np.array([indices["l2_codes"][v] if v != IGNORE_L2 else "" for v in outputs["y2"]])
    trials = []
    for evidence_cutoff in [0.0, 0.25, 0.5, 0.65, 0.75, 0.85, 0.9, 0.95]:
        per_class = {}
        for code in indices["l2_codes"]:
            eligible = []
            cutoffs = np.unique(np.r_[0.0, confidence[candidate == code], 1.0001])
            for cutoff in cutoffs:
                mask = source_ok & (candidate == code) & (confidence >= cutoff) & (evidence >= evidence_cutoff)
                count, correct = int(mask.sum()), int((mask & (gold == code)).sum())
                support = int((gold == code).sum())
                precision = correct / count if count else 0.0
                # Zero blank acceptances on validation per class; no silent lower-precision fallback.
                if count >= 3 and precision >= L2_TARGET_PRECISION and not np.any(mask & (gold == "")):
                    eligible.append({"threshold": float(cutoff), "accepted": count, "correct": correct,
                                     "precision": precision, "recall": correct / max(support, 1),
                                     "support": support, "precision_95ci_wilson": wilson_interval(correct, count)})
            per_class[code] = (max(eligible, key=lambda r: (r["recall"], r["precision"], -r["threshold"])) if eligible else
                               {"threshold": 1.0001, "accepted": 0, "correct": 0, "precision": 0.0, "recall": 0.0,
                                "support": int((gold == code).sum()), "precision_95ci_wilson": None})
        trials.append({"evidence_threshold": evidence_cutoff, "per_class": per_class,
                       "macro_recall": float(np.mean([v["recall"] for v in per_class.values()])),
                       "accepted": sum(v["accepted"] for v in per_class.values())})
    best = max(trials, key=lambda r: (r["macro_recall"], r["accepted"], -r["evidence_threshold"]))
    best["selection_rule"] = "maximize macro L2 recall; each accepted class requires >=3 validation predictions, precision >=0.90, zero blank-L2 acceptances"
    best["warning"] = "Empirical validation targets, not a guarantee; inspect small support and Wilson intervals."
    return 0.0, best["evidence_threshold"], {c: v["threshold"] for c, v in best["per_class"].items()}, best


def collect_image_members(members, loader, indices):
    results = []
    for member in members:
        model, device, _ = load_model(member["architecture"], member["checkpoint"], ontology, DEVICE)
        results.append(apply_temperatures(collect_logits(model, loader, device), member["temperatures"]))
        del model
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    return average_hierarchical_outputs(results, indices)


def collect_image_path(image_path, members, indices):
    transform = transforms.Compose([ResizeWithPad(IMAGE_SIZE), transforms.ToTensor(), transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD)])
    with Image.open(image_path) as image:
        tensor = transform(image.convert("RGB")).unsqueeze(0)
    results = []
    for member in members:
        model, device, _ = load_model(member["architecture"], member["checkpoint"], ontology, DEVICE)
        with torch.inference_mode():
            z1, z2, ze = model(tensor.to(device))
        outputs = {"l1_logits": z1.cpu().numpy(), "l2_logits": z2.cpu().numpy(), "l2_evidence_logits": ze.cpu().numpy()}
        results.append(apply_temperatures(outputs, member["temperatures"]))
        del model
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    return average_hierarchical_outputs(results, indices)


def fuse_outputs(image_outputs, pose_outputs, indices, image_weight, pose_detected):
    valid = np.asarray(pose_detected, dtype=bool)
    # A missing skeleton must not inject a fabricated all-zero pose prediction.
    w = np.where(valid, image_weight, 1.0)
    # Inference row labels are absent; validation/test row labels must align.
    aligned_pose = {k: v for k, v in pose_outputs.items() if k != "indices"}
    if "indices" in image_outputs:
        aligned_pose["indices"] = image_outputs["indices"]
    return average_hierarchical_outputs([image_outputs, aligned_pose], indices, np.stack([w, 1.0-w]))


def decision_quality(outputs, indices, l1_threshold, l2_threshold, evidence_threshold, class_thresholds):
    decisions = hierarchical_predictions(outputs, indices, l2_threshold, l1_threshold, None, evidence_threshold, class_thresholds)
    valid = outputs["y2"] != IGNORE_L2
    raw_metrics = metrics_from_outputs(outputs, indices)
    per_class = []
    for code in indices["l2_codes"]:
        idx = indices["l2_to_idx"][code]
        gold = valid & (outputs["y2"] == idx)
        predicted = np.array([r["final_code"] == code for r in decisions])
        tp = int((gold & predicted).sum())
        precision, recall = tp / max(int(predicted.sum()), 1), tp / max(int(gold.sum()), 1)
        per_class.append({"code": code, "support": int(gold.sum()), "predicted": int(predicted.sum()),
                          "correct": tp, "precision": precision, "recall": recall,
                          "f1": 2 * precision * recall / max(precision + recall, 1e-12)})
    l2_macro = float(np.mean([r["f1"] for r in per_class]))
    return {"score": 0.5 * raw_metrics["l1"]["macro_f1"] + 0.5 * l2_macro,
            "l1_macro_f1": raw_metrics["l1"]["macro_f1"], "l2_end_to_end_macro_f1": l2_macro, "per_class": per_class}


def pose_geometry_scores(pred, gt, bbox_norm, crop_size):
    """Use isotropic pixel coordinates; separately normalized x/y distorts reclining figures."""
    pred, gt = np.asarray(pred), np.asarray(gt)
    width, height = map(float, crop_size)
    distances = np.linalg.norm((pred[:, :2] - gt[:, :2]) * [width, height], axis=1)
    bw, bh = bbox_norm[2] * width, bbox_norm[3] * height
    visible = gt[:, 2] > 0
    hits = (distances <= 0.05 * max(math.hypot(bw, bh), 1e-8)) & visible
    sigmas = np.array([.26, .25, .25, .35, .35, .79, .79, .72, .72, .62, .62, 1.07, 1.07, .87, .87, .89, .89]) / 10.0
    # COCO uses (2*sigma)^2. Bbox area is explicitly used as the object-area proxy.
    oks = np.exp(-distances ** 2 / (2 * (2 * sigmas) ** 2 * max(bw * bh, 1e-8)))
    return hits, visible, float(oks[visible].mean()) if visible.any() else None


snapshot = load_snapshot(DATA_DIR)
audit = audit_snapshot(snapshot, check_files=True)
rows = snapshot["rows"]
ontology = snapshot["ontology"]
indices = class_index_maps(ontology)
l1_names_vi = {item["code"]: item["vi"] for item in ontology["level_1"]}
l2_names_vi = {item["code"]: item["vi"] for item in ontology["level_2"]}

assert audit["records"] == 873, audit
assert audit["split_counts"] == {"train": 612, "val": 136, "test": 125}, audit["split_counts"]
assert audit["l2_unlabeled"] == 144, audit["l2_unlabeled"]

artifact_splits = defaultdict(set)
hash_splits = defaultdict(set)
for row in rows:
    artifact_splits[row["artifact_id"]].add(row["split"])
    hash_splits[row["content_sha256"]].add(row["split"])
artifact_leaks = {k: sorted(v) for k, v in artifact_splits.items() if len(v) > 1}
exact_hash_leaks = {k: sorted(v) for k, v in hash_splits.items() if k and len(v) > 1}
assert not artifact_leaks, f"Artifact leakage: {artifact_leaks}"
assert not exact_hash_leaks, f"Exact-image leakage: {exact_hash_leaks}"

full_coco = json.loads((DATA_DIR / "keypoints_coco.json").read_text(encoding="utf-8"))
partial_coco = json.loads((DATA_DIR / "keypoints_partial_coco.json").read_text(encoding="utf-8"))
full_split_counts = Counter(image["split"] for image in full_coco["images"])
partial_split_counts = Counter(image["split"] for image in partial_coco["images"])

audit_summary = {
    "dataset_version": audit["dataset_version"],
    "records": audit["records"],
    "split_counts": audit["split_counts"],
    "l2_labeled": audit["l2_labeled"],
    "l2_unlabeled": audit["l2_unlabeled"],
    "full_keypoint_records": len(full_coco["annotations"]),
    "full_keypoint_by_split": dict(full_split_counts),
    "partial_keypoint_records": len(partial_coco["annotations"]),
    "partial_keypoint_by_split": dict(partial_split_counts),
    "artifact_leakage_groups": len(artifact_leaks),
    "exact_hash_leakage_groups": len(exact_hash_leaks),
}
(RUN_ROOT / "dataset_audit.json").write_text(json.dumps(audit_summary, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(audit_summary, ensure_ascii=False, indent=2))


fig, axes = plt.subplots(1, 3, figsize=(22, 6))
l1_counts = Counter(row["level_1_code"] for row in rows)
l2_counts = Counter(row["level_2_code"] for row in rows if row["level_2_code"])
axes[0].barh([l1_names_vi[c] for c in indices["l1_codes"]], [l1_counts[c] for c in indices["l1_codes"]], color="#2a7771")
axes[0].set_title("Phân bố L1")
axes[0].set_xlabel("Số ảnh")
axes[1].barh([l2_names_vi[c] for c in indices["l2_codes"]], [l2_counts[c] for c in indices["l2_codes"]], color="#c28b45")
axes[1].set_title("Phân bố L2 có nhãn")
axes[1].set_xlabel("Số ảnh")
split_order = ["train", "val", "test"]
axes[2].bar(split_order, [audit["split_counts"][s] for s in split_order], color="#526e9e")
axes[2].set_title("Split đóng băng theo artifact")
plt.tight_layout()
plt.show()


def read_rater_form(path):
    ws = load_workbook(path, data_only=True, read_only=False)["Form"]
    values = {}
    for row_number in range(5, ws.max_row + 1):
        image_id = ws.cell(row_number, 1).value
        label = ws.cell(row_number, 3).value
        if image_id is None and label is None:
            continue
        if image_id is None or label is None:
            raise ValueError(f"Dòng thiếu image_id hoặc label tại {path.name}:{row_number}")
        image_id, label = str(image_id).strip(), str(label).strip()
        if image_id in values:
            raise ValueError(f"Trùng image_id trong {path.name}: {image_id}")
        values[image_id] = label
    return values

ngan_path = RATINGS_DIR / "kappa_form_rater_ngan.xlsx"
my_path = RATINGS_DIR / "kappa_form_rater_my.xlsx"
if not ngan_path.is_file() or not my_path.is_file():
    raise FileNotFoundError(f"Thiếu phiếu gán nhãn: Ngan={ngan_path.is_file()}, My={my_path.is_file()}")
labels_ngan = read_rater_form(ngan_path)
labels_my = read_rater_form(my_path)
assert set(labels_ngan) == set(labels_my), "Phiếu của Ngan và My không có cùng tập image_id."
assert len(labels_ngan) == 873, len(labels_ngan)

valid_codes = set(indices["l1_codes"]) | {"C1.5"} | set(indices["l2_codes"])
invalid_ngan = sorted({v for v in labels_ngan.values() if v not in valid_codes})
invalid_my = sorted({v for v in labels_my.values() if v not in valid_codes})
assert not invalid_ngan and not invalid_my, {"Ngan": invalid_ngan, "My": invalid_my}

common_ids = sorted(labels_ngan)
y_ngan = [labels_ngan[i] for i in common_ids]
y_my = [labels_my[i] for i in common_ids]
to_l1 = lambda code: indices["l2_parent"].get(code, code)
y_ngan_l1 = [to_l1(code) for code in y_ngan]
y_my_l1 = [to_l1(code) for code in y_my]

kappa_summary = {
    "annotators": ["Ngan", "My"],
    "n_paired": len(common_ids),
    "hierarchical_exact_agreement": float(np.mean(np.array(y_ngan) == np.array(y_my))),
    "hierarchical_cohen_kappa": float(cohen_kappa_score(y_ngan, y_my)),
    "l1_agreement": float(np.mean(np.array(y_ngan_l1) == np.array(y_my_l1))),
    "l1_cohen_kappa": float(cohen_kappa_score(y_ngan_l1, y_my_l1)),
    "pairing_key": "image_id",
}
(RUN_ROOT / "inter_rater_agreement.json").write_text(json.dumps(kappa_summary, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(kappa_summary, ensure_ascii=False, indent=2))

all_codes = indices["l1_codes"] + ["C1.5"] + indices["l2_codes"]
cm = confusion_matrix(y_ngan, y_my, labels=all_codes)
fig, ax = plt.subplots(figsize=(11, 9))
ax.imshow(cm, cmap="Blues")
ax.set_xticks(range(len(all_codes)), all_codes, rotation=90)
ax.set_yticks(range(len(all_codes)), all_codes)
ax.set_xlabel("My")
ax.set_ylabel("Ngan")
ax.set_title("Đồng thuận nhãn độc lập: Ngan và My")
for i in range(len(all_codes)):
    for j in range(len(all_codes)):
        if cm[i, j]: ax.text(j, i, str(cm[i, j]), ha="center", va="center", fontsize=7)
plt.tight_layout()
plt.show()


seed_everything(SEED)
image_run_dir = RUN_ROOT / "image_classifier"
image_run_dir.mkdir(parents=True, exist_ok=True)
loaders, indices = make_loaders(snapshot, batch_size=IMAGE_BATCH_SIZE, seed=SEED)
image_trials, member_outputs, raw_member_outputs, all_members = {}, {}, {}, []
for architecture in IMAGE_ARCHITECTURES:
    for training_seed in IMAGE_SEEDS:
        name = f"{architecture}_seed{training_seed}"
        result = fit_model(snapshot, architecture, image_run_dir / name,
                           epochs=IMAGE_MAX_EPOCHS, patience=IMAGE_PATIENCE,
                           batch_size=IMAGE_BATCH_SIZE, seed=training_seed)
        raw = result["validation_outputs"]
        temperatures = fit_hierarchical_temperatures(raw, indices)
        member = {"architecture": architecture, "seed": training_seed, "checkpoint": result["checkpoint"],
                  "temperatures": temperatures, "best_epoch": result["best_epoch"]}
        all_members.append(member)
        raw_member_outputs[name] = raw
        member_outputs[name] = apply_temperatures(raw, temperatures)
        image_trials[name] = {k: v for k, v in result.items() if k not in ("validation_outputs", "history")}

# Fixed groups: no cherry-picking the best seed. Compare each architecture's three-seed
# ensemble and the equally weighted six-member ensemble, all on validation only.
image_groups = {architecture: [m for m in all_members if m["architecture"] == architecture] for architecture in IMAGE_ARCHITECTURES}
image_groups["all_architectures"] = all_members
image_group_trials = {}
for name, members in image_groups.items():
    member_names = [f"{m['architecture']}_seed{m['seed']}" for m in members]
    out = average_hierarchical_outputs([member_outputs[n] for n in member_names], indices)
    _, l1_choice = l1_rejection_curve(out, min_coverage=L1_MIN_COVERAGE, min_accepted=L1_MIN_ACCEPTED,
                                     target_accuracy=L1_TARGET_SELECTIVE_ACCURACY)
    t2, te, tc, choice = select_class_operating_points(out, indices, l1_choice["threshold"])
    quality = decision_quality(out, indices, l1_choice["threshold"], t2, te, tc)
    image_group_trials[name] = {"outputs": out, "quality": quality, "l1_choice": l1_choice,
                                "threshold": t2, "evidence_threshold": te, "class_thresholds": tc, "threshold_choice": choice}
image_architecture = max(image_group_trials, key=lambda name: image_group_trials[name]["quality"]["score"])
chosen = image_group_trials[image_architecture]
image_members = image_groups[image_architecture]
image_val_outputs = chosen["outputs"]
image_val_outputs_raw = average_hierarchical_outputs(
    [raw_member_outputs[f"{m['architecture']}_seed{m['seed']}"] for m in image_members], indices)
image_l1_curve_rows, image_l1_choice = l1_rejection_curve(
    image_val_outputs, min_coverage=L1_MIN_COVERAGE, min_accepted=L1_MIN_ACCEPTED,
    target_accuracy=L1_TARGET_SELECTIVE_ACCURACY)
image_l1_threshold = float(image_l1_choice["threshold"])
image_threshold, image_l2_evidence_threshold = chosen["threshold"], chosen["evidence_threshold"]
image_class_thresholds, threshold_choice = chosen["class_thresholds"], chosen["threshold_choice"]
image_c2_2_choice = threshold_choice["per_class"]["C2.2"]
image_temperatures = {"per_member": [m["temperatures"] for m in image_members]}
image_checkpoint = Path(image_members[0]["checkpoint"])
image_selection = {
    "source": "quality_multiseed_ensemble", "architecture": image_architecture, "model_schema": MODEL_SCHEMA,
    "image_size": IMAGE_SIZE, "members": image_members, "manifest_sha256": audit["manifest_sha256"],
    "validation_selection_score": chosen["quality"]["score"],
    "group_comparison": {k: v["quality"] for k, v in image_group_trials.items()},
    "l1_rejection_threshold": image_l1_threshold, "l1_threshold_choice": image_l1_choice,
    "threshold": image_threshold, "l2_fallback_threshold": image_threshold,
    "l2_evidence_threshold": image_l2_evidence_threshold,
    "class_specific_thresholds": image_class_thresholds, "c2_2_threshold_choice": image_c2_2_choice,
    "threshold_choice": threshold_choice, "temperature_scaling": image_temperatures,
}
(image_run_dir / "selection.json").write_text(json.dumps(image_selection, ensure_ascii=False, indent=2), encoding="utf-8")
image_test_outputs = collect_image_members(image_members, loaders["test"], indices)
image_test_metrics = save_test_predictions(image_run_dir / "test_predictions.csv", rows, image_test_outputs, indices,
                                          image_threshold, image_l1_threshold, None, image_l2_evidence_threshold, image_class_thresholds)
(image_run_dir / "test_metrics.json").write_text(json.dumps(image_test_metrics, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({"ensemble": image_architecture, "validation_score": chosen["quality"]["score"], "test": image_test_metrics}, ensure_ascii=False, indent=2))


fig, axes = plt.subplots(1, 2, figsize=(15, 6))
matrices = [image_test_metrics["l1_all_test"]["confusion_matrix"], image_test_metrics["l2_oracle_given_gold_l1"]["confusion_matrix"]]
labels = [indices["l1_codes"], indices["l2_codes"]]
titles = ["Hướng ảnh L1 end-to-end", "Hướng ảnh L2 oracle theo L1 chuẩn"]
for ax, matrix, codes, title in zip(axes, matrices, labels, titles):
    matrix = np.array(matrix)
    ax.imshow(matrix, cmap="Blues")
    ax.set_title(title); ax.set_xlabel("Dự đoán"); ax.set_ylabel("Nhãn thật")
    ax.set_xticks(range(len(codes)), codes, rotation=90); ax.set_yticks(range(len(codes)), codes)
    for i in range(len(codes)):
        for j in range(len(codes)):
            if matrix[i, j]: ax.text(j, i, str(matrix[i, j]), ha="center", va="center", fontsize=8)
plt.tight_layout()
plt.show()

image_l1_curve_df = pd.DataFrame(image_l1_curve_rows)
image_val_prob = torch.softmax(torch.tensor(image_val_outputs["l1_logits"]), dim=1).numpy()
image_val_conf = image_val_prob.max(axis=1)
image_val_correct = image_val_prob.argmax(axis=1) == image_val_outputs["y1"]
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
axes[0].plot(image_l1_curve_df["coverage"], image_l1_curve_df["selective_accuracy"], color="#2a7771", linewidth=2)
axes[0].scatter([image_l1_choice["coverage"]], [image_l1_choice["selective_accuracy"]], color="#b33a3a", s=70, label=f"Ngưỡng chọn = {image_l1_threshold:.2f}")
axes[0].axhline(L1_TARGET_SELECTIVE_ACCURACY, color="#777777", linestyle="--", label="Mục tiêu accuracy")
axes[0].set_xlabel("Coverage (tỷ lệ được phân loại)"); axes[0].set_ylabel("Accuracy trên mẫu được nhận")
axes[0].set_title("Risk–coverage L1 trên validation: hướng ảnh"); axes[0].set_xlim(0, 1); axes[0].set_ylim(0, 1.02); axes[0].legend()
axes[1].hist(image_val_conf[image_val_correct], bins=12, alpha=0.7, label="Dự đoán đúng", color="#2a7771")
axes[1].hist(image_val_conf[~image_val_correct], bins=12, alpha=0.7, label="Dự đoán sai", color="#c45a4f")
axes[1].axvline(image_l1_threshold, color="#222222", linestyle="--", label="Ngưỡng từ chối")
axes[1].set_xlabel("Độ tin cậy L1 cao nhất"); axes[1].set_ylabel("Số ảnh")
axes[1].set_title("Phân bố độ tin cậy L1 trên validation"); axes[1].legend()
plt.tight_layout()
plt.show()


def safe_stem(text):
    return "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in text)

def build_pose_dataset(data_dir, manifest_rows, coco, output_dir):
    marker = output_dir / "dataset.yaml"
    if marker.is_file() and REUSE_EXISTING:
        return marker
    if output_dir.exists():
        shutil.rmtree(output_dir)
    row_by_image = {row["image_id"]: row for row in manifest_rows}
    image_by_id = {int(image["id"]): image for image in coco["images"]}
    anns_by_image = {int(ann["image_id"]): ann for ann in coco["annotations"]}
    records = []
    for image_id, image in image_by_id.items():
        ann = anns_by_image[image_id]
        original_id = image["original_image_id"]
        if original_id not in row_by_image:
            raise KeyError(f"Không ghép được COCO image với manifest: {original_id}")
        row = row_by_image[original_id]
        split = "val" if row["split"] == "val" else row["split"]
        image_dir = output_dir / "images" / split
        label_dir = output_dir / "labels" / split
        image_dir.mkdir(parents=True, exist_ok=True)
        label_dir.mkdir(parents=True, exist_ok=True)
        source = data_dir / row["crop_path"]
        stem = safe_stem(row["instance_id"])
        destination = image_dir / (stem + source.suffix.lower())
        shutil.copy2(source, destination)
        crop_x, crop_y, crop_w, crop_h = json.loads(row["crop_extent_xywh"])
        bbox_x, bbox_y, bbox_w, bbox_h = [float(ann["bbox"][i]) for i in range(4)]
        xc = ((bbox_x - crop_x) + bbox_w / 2) / crop_w
        yc = ((bbox_y - crop_y) + bbox_h / 2) / crop_h
        bw, bh = bbox_w / crop_w, bbox_h / crop_h
        yolo_fields = [0, np.clip(xc, 0, 1), np.clip(yc, 0, 1), np.clip(bw, 1e-6, 1), np.clip(bh, 1e-6, 1)]
        adjusted_gt = []
        kp = ann["keypoints"]
        for index in range(0, len(kp), 3):
            x, y, visibility = float(kp[index]), float(kp[index + 1]), int(kp[index + 2])
            xn, yn = (x - crop_x) / crop_w, (y - crop_y) / crop_h
            if visibility > 0 and not (0 <= xn <= 1 and 0 <= yn <= 1):
                visibility = 0
            xn, yn = float(np.clip(xn, 0, 1)), float(np.clip(yn, 0, 1))
            yolo_fields.extend([xn, yn, visibility])
            adjusted_gt.append([xn, yn, visibility])
        (label_dir / (stem + ".txt")).write_text(" ".join(map(str, yolo_fields)) + "\n", encoding="utf-8")
        records.append({"image_id": original_id, "instance_id": row["instance_id"], "split": row["split"],
                        "file": str(destination), "bbox_norm": [xc, yc, bw, bh], "keypoints_norm": adjusted_gt})
    yaml_text = (
        f'path: "{output_dir.resolve().as_posix()}"\n'
        "train: images/train\nval: images/val\ntest: images/test\n"
        "kpt_shape: [17, 3]\n"
        "flip_idx: [0, 2, 1, 4, 3, 6, 5, 8, 7, 10, 9, 12, 11, 14, 13, 16, 15]\n"
        "names:\n  0: figure\n"
    )
    marker.write_text(yaml_text, encoding="utf-8")
    (output_dir / "records.json").write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    return marker

pose_dataset_dir = CACHE_DIR / "formal_pose_yolo"
pose_yaml = build_pose_dataset(DATA_DIR, rows, full_coco, pose_dataset_dir)
pose_records = json.loads((pose_dataset_dir / "records.json").read_text(encoding="utf-8"))
print("Pose records:", len(pose_records), Counter(r["split"] for r in pose_records))


import gc
pose_inference_batch_size = globals().get("POSE_INFERENCE_BATCH_SIZE", 1)
pose_run_dir = RUN_ROOT / "pose_estimator"
pose_run_dir.mkdir(parents=True, exist_ok=True)
cached_pose_checkpoint = OUTPUTS_DIR / "pose_baseline" / "best.pt"
cached_pose_config = OUTPUTS_DIR / "pose_baseline" / "config.json"
pretrained_pose = PRETRAINED_DIR / "yolo11n-pose.pt"
if not pretrained_pose.is_file():
    raise FileNotFoundError("Thiếu pretrained/yolo11n-pose.pt. Không tự tải để giữ khả năng tái lập offline.")

can_reuse_pose = False
if REUSE_EXISTING and not FORCE_RETRAIN_POSE and cached_pose_checkpoint.is_file() and cached_pose_config.is_file():
    pose_cache_config = json.loads(cached_pose_config.read_text(encoding="utf-8"))
    can_reuse_pose = pose_cache_config.get("manifest_sha256") == audit["manifest_sha256"]
if can_reuse_pose:
    pose_checkpoint = cached_pose_checkpoint
    pose_training_source = "cached_formal_pose_baseline"
else:
    base_pose_model = YOLO(str(pretrained_pose))
    pose_result = base_pose_model.train(
        data=str(pose_yaml), epochs=POSE_EPOCHS, patience=POSE_PATIENCE,
        imgsz=POSE_IMAGE_SIZE, batch=POSE_BATCH_SIZE, seed=SEED,
        project=str(pose_run_dir.resolve()), name="yolo11n_pose_formal",
        device=0 if DEVICE == "cuda" else "cpu", workers=0,
        pretrained=True, deterministic=True, exist_ok=False, verbose=True,
    )
    pose_save_dir = Path(pose_result.save_dir)
    pose_checkpoint = pose_save_dir / "weights" / "best.pt"
    if not pose_checkpoint.is_file():
        pose_checkpoint = pose_save_dir / "weights" / "last.pt"
    cached_pose_checkpoint.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(pose_checkpoint, cached_pose_checkpoint)
    cached_pose_config.write_text(json.dumps({
        "dataset_version": audit["dataset_version"],
        "manifest_sha256": audit["manifest_sha256"],
        "seed": SEED, "epochs": POSE_EPOCHS, "imgsz": POSE_IMAGE_SIZE,
        "batch": POSE_BATCH_SIZE, "base_weights": pretrained_pose.name,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    pose_checkpoint = cached_pose_checkpoint
    pose_training_source = "trained_in_notebook"

# The 4 GB GPU cannot hold the image classifier and YOLO-Pose validation
# buffers at the same time. Keep the already-evaluated image model on CPU;
# it is only used once more by the final demo.
if DEVICE == "cuda":
    gc.collect()
    torch.cuda.empty_cache()

pose_model = YOLO(str(pose_checkpoint))
pose_val_result = pose_model.val(
    project=str(pose_run_dir.resolve()), name="geometry_test", exist_ok=True,
    data=str(pose_yaml), split="test", imgsz=POSE_IMAGE_SIZE,
    batch=pose_inference_batch_size, device=0 if DEVICE == "cuda" else "cpu",
    half=DEVICE == "cuda",
    workers=0, verbose=False,
)
pose_ultralytics_metrics = {
    "training_source": pose_training_source,
    "checkpoint": str(pose_checkpoint),
    "pose_map50_95": float(getattr(pose_val_result.pose, "map", float("nan"))),
    "pose_map50": float(getattr(pose_val_result.pose, "map50", float("nan"))),
    "pose_map75": float(getattr(pose_val_result.pose, "map75", float("nan"))),
    "box_map50_95": float(getattr(pose_val_result.box, "map", float("nan"))),
}
del pose_val_result
# Validation builds an inference backend. Reload a clean checkpoint for
# feature extraction instead of moving that backend between devices.
del pose_model
gc.collect()
if DEVICE == "cuda":
    torch.cuda.empty_cache()
pose_model = YOLO(str(pose_checkpoint))
print(json.dumps(pose_ultralytics_metrics, ensure_ascii=False, indent=2))


import gc
pose_inference_batch_size = globals().get("POSE_INFERENCE_BATCH_SIZE", 1)
pose_feature_device = "cuda" if DEVICE == "cuda" else "cpu"

def _extract_pose_features_once(model, manifest_rows, batch_size, inference_device):
    # A list of paths makes this Ultralytics version decode every image up
    # front with LoadPilAndNumpy. Some source images are very large, so that
    # exhausts system RAM. Passing one path string at a time streams from disk.
    use_cuda = inference_device != "cpu"
    features, metadata = [], []
    total = len(manifest_rows)
    for index, row in enumerate(manifest_rows):
        path = str(DATA_DIR / row["crop_path"])
        results = model.predict(
            source=path, imgsz=POSE_IMAGE_SIZE, batch=1,
            device=inference_device, workers=0, half=use_cuda, max_det=1,
            verbose=False, stream=False,
        )
        if len(results) != 1:
            raise RuntimeError(f"Expected one pose result for {path}, got {len(results)}")
        result = results[0]
        feature = np.zeros(17 * 3 + 2, dtype=np.float32)
        detected = False
        if result.boxes is not None and len(result.boxes) and result.keypoints is not None:
            confs = result.boxes.conf.detach().cpu().numpy()
            best = int(np.argmax(confs))
            xy = result.keypoints.xyn[best].detach().cpu().numpy()
            if result.keypoints.conf is not None:
                kp_conf = result.keypoints.conf[best].detach().cpu().numpy()
            else:
                kp_conf = np.ones(17, dtype=np.float32)
            feature[:51] = np.column_stack([xy, kp_conf]).reshape(-1)
            feature[51] = float(confs[best])
            feature[52] = 1.0
            detected = True
            bbox_xywhn = result.boxes.xywhn[best].detach().cpu().numpy().astype(float).tolist()
        else:
            bbox_xywhn = None
        features.append(feature)
        metadata.append({"image_id": row["image_id"], "instance_id": row["instance_id"],
                         "split": row["split"], "detected": detected,
                         "bbox_xywhn": bbox_xywhn})
        del result, results
        if (index + 1) % 50 == 0 or index + 1 == total:
            print(f"Pose inference: {index + 1}/{total}")
    return np.stack(features), metadata

def extract_pose_features(model, manifest_rows, batch_size=1):
    global pose_model, pose_feature_device
    inference_device = 0 if DEVICE == "cuda" else "cpu"
    if DEVICE == "cuda":
        gc.collect()
        torch.cuda.empty_cache()
    try:
        return _extract_pose_features_once(model, manifest_rows, batch_size, inference_device)
    except RuntimeError as exc:
        if DEVICE != "cuda" or "out of memory" not in str(exc).lower():
            raise
        warnings.warn("GPU thiếu bộ nhớ khi trích keypoint; nạp lại checkpoint sạch và tiếp tục trên CPU.")
        model.predictor = None
        del model
        gc.collect()
        torch.cuda.empty_cache()
        pose_model = YOLO(str(pose_checkpoint))
        pose_feature_device = "cpu"
        return _extract_pose_features_once(pose_model, manifest_rows, 1, "cpu")

pose_feature_cache = CACHE_DIR / "predicted_pose_features.npz"
pose_metadata_cache = CACHE_DIR / "predicted_pose_metadata.json"
def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()

pose_checkpoint_sha256 = file_sha256(pose_checkpoint)
pose_cache_metadata = (json.loads(pose_metadata_cache.read_text(encoding="utf-8"))
                       if pose_metadata_cache.is_file() else {})
can_reuse_features = (
    REUSE_EXISTING and not FORCE_RETRAIN_POSE and pose_feature_cache.is_file()
    and pose_cache_metadata.get("checkpoint_sha256") == pose_checkpoint_sha256
    and pose_cache_metadata.get("manifest_sha256") == audit["manifest_sha256"]
    and pose_cache_metadata.get("record_count") == len(rows)
    and pose_cache_metadata.get("cache_schema") == 2
)
if can_reuse_features:
    pose_features = np.load(pose_feature_cache)["features"]
    pose_feature_metadata = pose_cache_metadata["records"]
else:
    # Release allocations and traceback frames left by earlier failed runs.
    for attr in ("last_traceback", "last_value", "last_type"):
        if hasattr(sys, attr):
            setattr(sys, attr, None)
    if DEVICE == "cuda":
        pose_model.predictor = None
        gc.collect()
        torch.cuda.empty_cache()
    # Running this cell again must not reuse the backend left by val() or a failed inference.
    del pose_model
    gc.collect()
    if DEVICE == "cuda":
        torch.cuda.empty_cache()
    pose_model = YOLO(str(pose_checkpoint))
    pose_features, pose_feature_metadata = extract_pose_features(
        pose_model, rows, pose_inference_batch_size
    )
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(pose_feature_cache, features=pose_features)
    pose_metadata_cache.write_text(json.dumps({
        "checkpoint_sha256": pose_checkpoint_sha256,
        "manifest_sha256": audit["manifest_sha256"],
        "record_count": len(rows),
        "cache_schema": 2,
        "records": pose_feature_metadata,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
assert len(pose_features) == len(rows)
print("Tỷ lệ phát hiện nhân vật:", np.mean([m["detected"] for m in pose_feature_metadata]))


COCO_SIGMAS = np.array([.26, .25, .25, .35, .35, .79, .79, .72, .72, .62, .62, 1.07, 1.07, .87, .87, .89, .89]) / 10.0
def bbox_iou_xywhn(a, b):
    ax, ay, aw, ah = map(float, a); bx, by, bw, bh = map(float, b)
    a_box = [ax - aw / 2, ay - ah / 2, ax + aw / 2, ay + ah / 2]
    b_box = [bx - bw / 2, by - bh / 2, bx + bw / 2, by + bh / 2]
    inter_w = max(0.0, min(a_box[2], b_box[2]) - max(a_box[0], b_box[0]))
    inter_h = max(0.0, min(a_box[3], b_box[3]) - max(a_box[1], b_box[1]))
    intersection = inter_w * inter_h
    union = aw * ah + bw * bh - intersection
    return intersection / union if union > 0 else 0.0

gt_pose_by_image = {record["image_id"]: record for record in pose_records if record["split"] == "test"}
feature_by_image = {row["image_id"]: pose_features[i] for i, row in enumerate(rows)}
metadata_by_image = {record["image_id"]: record for record in pose_feature_metadata}
pck_hits, pck_total, oks_values, bbox_ious, detected_pose_test = 0, 0, [], [], 0
for image_id, gt in gt_pose_by_image.items():
    feature = feature_by_image[image_id]
    if feature[52] > 0:
        detected_pose_test += 1
        predicted_bbox = metadata_by_image[image_id].get("bbox_xywhn")
        if predicted_bbox is not None:
            bbox_ious.append(bbox_iou_xywhn(gt["bbox_norm"], predicted_bbox))
    pred = feature[:51].reshape(17, 3)
    gt_kp = np.array(gt["keypoints_norm"], dtype=float)
    visible = gt_kp[:, 2] > 0
    if not visible.any():
        continue
    row = next(r for r in rows if r["image_id"] == image_id)
    crop_size = (float(row["crop_width"]), float(row["crop_height"]))
    hits, visible, oks = pose_geometry_scores(pred, gt_kp, gt["bbox_norm"], crop_size)
    pck_hits += int(hits.sum())
    pck_total += int(visible.sum())
    if oks is not None:
        oks_values.append(oks)

pose_geometry_metrics = {
    **pose_ultralytics_metrics,
    "test_full_keypoint_images": len(gt_pose_by_image),
    "test_detection_rate": detected_pose_test / max(len(gt_pose_by_image), 1),
    "mean_bbox_iou": float(np.mean(bbox_ious)) if bbox_ious else None,
    "pck_at_0_05_bbox_diagonal": pck_hits / max(pck_total, 1),
    "pck_visible_keypoints": pck_total,
    "mean_oks": float(np.mean(oks_values)) if oks_values else None,
    "oks_definition": "COCO (2*sigma)^2; pixel coordinates; bbox-area proxy; annotated ground-truth keypoints (v>0); metric schema 2, not comparable directly with old normalized-space scores",
}
(pose_run_dir / "test_pose_metrics.json").write_text(json.dumps(pose_geometry_metrics, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(pose_geometry_metrics, ensure_ascii=False, indent=2))
pose_plot_values = {
    "Tỷ lệ phát hiện": pose_geometry_metrics["test_detection_rate"],
    "BBox IoU": pose_geometry_metrics["mean_bbox_iou"] or 0.0,
    "PCK@0.05": pose_geometry_metrics["pck_at_0_05_bbox_diagonal"],
    "OKS": pose_geometry_metrics["mean_oks"] or 0.0,
}
fig, ax = plt.subplots(figsize=(9, 4.5))
bars = ax.bar(pose_plot_values.keys(), pose_plot_values.values(), color=["#526e9e", "#2a7771", "#c28b45", "#8b6fa8"])
ax.set_ylim(0, 1); ax.set_ylabel("Điểm"); ax.set_title("Chất lượng hình học của pose estimator trên test")
ax.bar_label(bars, labels=[f"{value:.1%}" for value in pose_plot_values.values()], padding=3)
plt.tight_layout()
plt.show()

# Per-class validation diagnostics reveal whether hip/knee/ankle geometry is the bottleneck.
pose_diagnostics = []
row_by_image = {r["image_id"]: r for r in rows}
for gt in pose_records:
    if gt["split"] not in ("val", "test"):
        continue
    row = row_by_image[gt["image_id"]]
    pred = feature_by_image[gt["image_id"]][:51].reshape(17, 3)
    hits, visible, oks = pose_geometry_scores(pred, gt["keypoints_norm"], gt["bbox_norm"],
                                             (row["crop_width"], row["crop_height"]))
    pose_diagnostics.append({"image_id": gt["image_id"], "split": gt["split"], "l2_code": row["level_2_code"],
                             "lower_body_hits": int(hits[11:17].sum()), "lower_body_support": int(visible[11:17].sum()),
                             "pck_hits": int(hits.sum()), "pck_support": int(visible.sum()), "oks_bbox_area": oks})
pd.DataFrame(pose_diagnostics).to_csv(pose_run_dir / "geometry_by_image.csv", index=False)
pose_class_rows = []
for (split, code), group in pd.DataFrame(pose_diagnostics).groupby(["split", "l2_code"]):
    pose_class_rows.append({"split": split, "l2_code": code, "images": len(group),
                           "lower_body_pck": group.lower_body_hits.sum() / max(group.lower_body_support.sum(), 1),
                           "pck": group.pck_hits.sum() / max(group.pck_support.sum(), 1)})
pd.DataFrame(pose_class_rows).to_csv(pose_run_dir / "geometry_by_class.csv", index=False)


def _joint_angle_cos(xy, confidence, first, middle, last):
    if min(confidence[first], confidence[middle], confidence[last]) < 0.05:
        return 0.0
    left = xy[first] - xy[middle]
    right = xy[last] - xy[middle]
    denominator = np.linalg.norm(left) * np.linalg.norm(right)
    return float(np.dot(left, right) / denominator) if denominator > 1e-8 else 0.0


def engineer_pose_features(raw_features):
    """Add translation/scale-invariant geometry while retaining original pose evidence."""
    raw_features = np.asarray(raw_features, dtype=np.float32)
    engineered = []
    for raw in raw_features:
        joints = raw[:51].reshape(17, 3)
        xy, confidence = joints[:, :2].copy(), joints[:, 2].copy()
        if len(raw) != 54 or not np.isfinite(raw[53]) or raw[53] <= 0:
            raise ValueError("Pose geometry requires 53 pose fields plus positive crop width/height ratio.")
        # x and y were normalized by DIFFERENT lengths. Restore isotropic geometry
        # before measuring angles; keep original normalized coordinates as separate features.
        xy[:, 0] *= raw[53]
        valid = confidence >= 0.05
        if valid[11] and valid[12]:
            center = (xy[11] + xy[12]) / 2.0
        elif valid.any():
            center = xy[valid].mean(axis=0)
        else:
            center = np.zeros(2, dtype=np.float32)
        if valid.any():
            span = xy[valid].max(axis=0) - xy[valid].min(axis=0)
            scale = max(float(np.linalg.norm(span)), 1e-3)
        else:
            scale = 1.0
        relative_xy = (xy - center) / scale
        relative_xy[~valid] = 0.0
        shoulder_mid = (xy[5] + xy[6]) / 2.0 if valid[5] and valid[6] else center
        hip_mid = (xy[11] + xy[12]) / 2.0 if valid[11] and valid[12] else center
        geometry = np.asarray([
            _joint_angle_cos(xy, confidence, 5, 11, 13),
            _joint_angle_cos(xy, confidence, 6, 12, 14),
            _joint_angle_cos(xy, confidence, 11, 13, 15),
            _joint_angle_cos(xy, confidence, 12, 14, 16),
            (shoulder_mid[0] - hip_mid[0]) / scale,
            (shoulder_mid[1] - hip_mid[1]) / scale,
            np.linalg.norm(xy[5] - xy[6]) / scale if valid[5] and valid[6] else 0.0,
            np.linalg.norm(xy[11] - xy[12]) / scale if valid[11] and valid[12] else 0.0,
            np.linalg.norm(xy[13] - xy[14]) / scale if valid[13] and valid[14] else 0.0,
            np.linalg.norm(xy[15] - xy[16]) / scale if valid[15] and valid[16] else 0.0,
            float(valid.mean()), float(confidence[valid].mean()) if valid.any() else 0.0,
        ], dtype=np.float32)
        engineered.append(np.concatenate([raw, relative_xy.reshape(-1), geometry]))
    return np.asarray(engineered, dtype=np.float32)


def augment_pose_training_data(raw_features, labels, seed, copies=1, include_original=True):
    rng = np.random.default_rng(seed)
    raw_features = np.asarray(raw_features, dtype=np.float32)
    labels = np.asarray(labels)
    feature_sets = [engineer_pose_features(raw_features)] if include_original else []
    label_sets = [labels] if include_original else []
    for _ in range(copies):
        noisy = raw_features.copy()
        joints = noisy[:, :51].reshape(-1, 17, 3)
        valid = joints[:, :, 2] >= 0.05
        jitter = rng.normal(0.0, 0.008, size=joints[:, :, :2].shape).astype(np.float32)
        joints[:, :, :2] += jitter * valid[:, :, None]
        joints[:, :, :2] = np.clip(joints[:, :, :2], 0.0, 1.0)
        # Mirror anatomy and image coordinates together; these labels are side-invariant.
        mirror = rng.random(len(joints)) < 0.5
        permutation = [0, 2, 1, 4, 3, 6, 5, 8, 7, 10, 9, 12, 11, 14, 13, 16, 15]
        reflected = joints[mirror][:, permutation, :].copy()
        reflected[:, :, 0] = np.where(reflected[:, :, 2] >= 0.05, 1.0 - reflected[:, :, 0], 0.0)
        joints[mirror] = reflected
        valid = joints[:, :, 2] >= 0.05
        drop = (rng.random(valid.shape) < 0.04) & valid
        joints[drop] = 0.0
        feature_sets.append(engineer_pose_features(noisy))
        label_sets.append(labels.copy())
    if not feature_sets:
        raise ValueError("At least one original or augmented copy is required.")
    return np.concatenate(feature_sets), np.concatenate(label_sets)


pose_classifier_features = np.column_stack([
    pose_features,
    np.asarray([float(row["crop_width"]) / float(row["crop_height"]) for row in rows], dtype=np.float32),
])
pose_geometry_features = engineer_pose_features(pose_classifier_features)
print("Số chiều đặc trưng keypoint sau chuẩn hóa hình học:", pose_geometry_features.shape[1])


def probability_matrix(model, X, codes):
    raw = model.predict_proba(X)
    if isinstance(raw, list):
        raise TypeError("Classifier phải trả một ma trận probability.")
    matrix = np.full((len(X), len(codes)), 1e-9, dtype=np.float64)
    class_to_index = {str(code): i for i, code in enumerate(model.classes_)}
    for j, code in enumerate(codes):
        key = str(code)
        if key in class_to_index:
            matrix[:, j] = raw[:, class_to_index[key]]
    matrix /= matrix.sum(axis=1, keepdims=True)
    return matrix

def outputs_from_classifiers(l1_model, l2_models, evidence_model, X, y1_codes=None, y2_codes=None):
    p1 = probability_matrix(l1_model, X, indices["l1_codes"])
    p2 = np.full((len(X), len(indices["l2_codes"])), 1e-9, dtype=np.float64)
    for parent_code in indices["l1_codes"]:
        child_codes = [code for code in indices["l2_codes"] if indices["l2_parent"][code] == parent_code]
        child_indices = [indices["l2_to_idx"][code] for code in child_codes]
        if len(child_codes) == 1:
            p2[:, child_indices[0]] = 1.0
        else:
            local = probability_matrix(l2_models[parent_code], X, child_codes)
            p2[:, child_indices] = local
    p_evidence = probability_matrix(evidence_model, X, [0, 1])
    outputs = {"l1_logits": np.log(np.clip(p1, 1e-9, 1)),
               "l2_logits": np.log(np.clip(p2, 1e-9, 1)),
               "l2_evidence_logits": np.log(np.clip(p_evidence, 1e-9, 1))}
    if y1_codes is not None:
        outputs["y1"] = np.asarray([indices["l1_to_idx"][code] for code in y1_codes], dtype=np.int64)
    if y2_codes is not None:
        outputs["y2"] = np.asarray([indices["l2_to_idx"].get(code, IGNORE_L2) for code in y2_codes], dtype=np.int64)
    return outputs

split_indices = {split: np.array([i for i, row in enumerate(rows) if row["split"] == split]) for split in ["train", "val", "test"]}
y_l1 = np.array([row["level_1_code"] for row in rows])
y_l2 = np.array([row["level_2_code"] for row in rows])
train_idx, val_idx, test_idx = split_indices["train"], split_indices["val"], split_indices["test"]
l2_train_idx = np.array([i for i in train_idx if y_l2[i]])

from sklearn.ensemble import ExtraTreesClassifier

candidates = {
    "logistic_regression": Pipeline([
        ("scale", StandardScaler()),
        ("model", LogisticRegression(max_iter=3000, random_state=SEED)),
    ]),
    "random_forest": RandomForestClassifier(
        n_estimators=500, min_samples_leaf=2,
        random_state=SEED, n_jobs=-1,
    ),
}
candidates["extra_trees"] = ExtraTreesClassifier(n_estimators=1000, min_samples_leaf=2, random_state=SEED, n_jobs=-1)
for regularization in [0.1, 10.0]:
    candidates[f"logistic_C{regularization}"] = Pipeline([
        ("scale", StandardScaler()),
        ("model", LogisticRegression(C=regularization, max_iter=5000, random_state=SEED)),
    ])

def inverse_sqrt_class_weights(y, boosts=None):
    labels, counts = np.unique(np.asarray(y), return_counts=True)
    if len(labels) == 0 or np.any(counts == 0):
        raise ValueError("Cannot compute class weights from an empty training split.")
    weights = 1.0 / np.power(counts.astype(np.float64), CLASS_WEIGHT_POWER)
    for i, label in enumerate(labels.tolist()):
        weights[i] *= float((boosts or {}).get(label, 1.0))
    weights /= weights.mean()
    return {label: float(weight) for label, weight in zip(labels.tolist(), weights)}

def fit_with_train_class_weights(estimator, X, y, boosts=None):
    model = clone(estimator)
    class_weights = inverse_sqrt_class_weights(y, boosts=boosts)
    if isinstance(model, Pipeline):
        model.set_params(model__class_weight=class_weights)
    else:
        model.set_params(class_weight=class_weights)
    model.fit(X, y)
    return model, class_weights

def fit_l2_branch_models(estimator, seed):
    branch_models, branch_weights = {}, {}
    for parent_offset, parent_code in enumerate(indices["l1_codes"]):
        child_codes = [code for code in indices["l2_codes"] if indices["l2_parent"][code] == parent_code]
        if len(child_codes) == 1:
            branch_models[parent_code] = None
            branch_weights[parent_code] = {child_codes[0]: 1.0}
            continue
        branch_indices = np.asarray([
            i for i in train_idx if y_l1[i] == parent_code and y_l2[i] in child_codes
        ], dtype=np.int64)
        branch_X, branch_y = augment_pose_training_data(
            pose_classifier_features[branch_indices], y_l2[branch_indices], seed + parent_offset + 1, copies=1,
        )
        if C2_2_EXTRA_KEYPOINT_COPIES > 0 and parent_code == "C1.1" and "C2.2" in child_codes:
            rare_indices = branch_indices[y_l2[branch_indices] == "C2.2"]
            rare_X, rare_y = augment_pose_training_data(
                pose_classifier_features[rare_indices], y_l2[rare_indices], seed + 101,
                copies=C2_2_EXTRA_KEYPOINT_COPIES, include_original=False,
            )
            branch_X = np.concatenate([branch_X, rare_X])
            branch_y = np.concatenate([branch_y, rare_y])
        branch_models[parent_code], branch_weights[parent_code] = fit_with_train_class_weights(
            estimator, branch_X, branch_y, boosts=RARE_L2_WEIGHT_BOOSTS,
        )
    return branch_models, branch_weights


l1_train_X, l1_train_y = augment_pose_training_data(
    pose_classifier_features[train_idx], y_l1[train_idx], SEED, copies=1,
)
evidence_train_X, evidence_train_y = augment_pose_training_data(
    pose_classifier_features[train_idx], (y_l2[train_idx] != "").astype(np.int64), SEED + 77, copies=1,
)
keypoint_trials = {}
for name, estimator in candidates.items():
    l1_model, l1_class_weights = fit_with_train_class_weights(estimator, l1_train_X, l1_train_y)
    l2_models, l2_class_weights = fit_l2_branch_models(estimator, SEED)
    evidence_model, evidence_class_weights = fit_with_train_class_weights(
        estimator, evidence_train_X, evidence_train_y,
    )
    val_outputs = outputs_from_classifiers(
        l1_model, l2_models, evidence_model, pose_geometry_features[val_idx], y_l1[val_idx], y_l2[val_idx]
    )
    val_metrics = metrics_from_outputs(val_outputs, indices)
    evidence_gold = (val_outputs["y2"] != IGNORE_L2).astype(np.int64)
    evidence_pred = val_outputs["l2_evidence_logits"].argmax(axis=1)
    evidence_metrics = classification_metrics(evidence_gold, evidence_pred, [0, 1])
    score = quality_selection_score(val_outputs, indices)
    keypoint_trials[name] = {"l1_model": l1_model, "l2_models": l2_models, "evidence_model": evidence_model,
                             "val_outputs": val_outputs, "val_metrics": val_metrics,
                             "evidence_metrics": evidence_metrics, "selection_score": score,
                             "class_weights": {"l1": l1_class_weights, "l2_by_parent": l2_class_weights,
                                               "l2_evidence": evidence_class_weights}}
    print(name, "validation selection score", round(score, 4))

keypoint_model_name = max(keypoint_trials, key=lambda name: keypoint_trials[name]["selection_score"])
keypoint_best = keypoint_trials[keypoint_model_name]
keypoint_temperatures = fit_hierarchical_temperatures(keypoint_best["val_outputs"], indices)
keypoint_val_outputs = apply_temperatures(keypoint_best["val_outputs"], keypoint_temperatures)
keypoint_val_pose_ok = np.asarray([m["detected"] for m in pose_feature_metadata], dtype=bool)[val_idx]
keypoint_l1_curve_rows, keypoint_l1_choice = l1_rejection_curve(
    keypoint_val_outputs, min_coverage=L1_MIN_COVERAGE, min_accepted=L1_MIN_ACCEPTED,
    target_accuracy=L1_TARGET_SELECTIVE_ACCURACY, evidence_ok=keypoint_val_pose_ok,
)
keypoint_l1_threshold = float(keypoint_l1_choice["threshold"])
kp_threshold_rows, kp_threshold_choice = threshold_curve(
    keypoint_val_outputs, indices, min_coverage=L2_MIN_COVERAGE, min_support=15,
    target_precision=L2_TARGET_PRECISION, max_blank_acceptance=L2_MAX_BLANK_ACCEPTANCE,
    evidence_ok=keypoint_val_pose_ok, l1_threshold=keypoint_l1_threshold,
)
keypoint_threshold = float(kp_threshold_choice["l2_confidence_threshold"])
keypoint_l2_evidence_threshold = float(kp_threshold_choice["l2_evidence_threshold"])
keypoint_threshold, keypoint_l2_evidence_threshold, keypoint_class_thresholds, kp_class_choice = select_class_operating_points(
    keypoint_val_outputs, indices, keypoint_l1_threshold, keypoint_val_pose_ok,
)
keypoint_c2_2_choice = kp_class_choice["per_class"]["C2.2"]
kp_threshold_choice = kp_class_choice
keypoint_test_outputs = apply_temperatures(outputs_from_classifiers(
    keypoint_best["l1_model"], keypoint_best["l2_models"], keypoint_best["evidence_model"], pose_geometry_features[test_idx],
    y_l1[test_idx], y_l2[test_idx],
), keypoint_temperatures)
keypoint_run_dir = RUN_ROOT / "keypoint_classifier"
keypoint_run_dir.mkdir(parents=True, exist_ok=True)
keypoint_test_pose_ok = np.asarray([m["detected"] for m in pose_feature_metadata], dtype=bool)[test_idx]
keypoint_test_metrics = save_test_predictions(
    keypoint_run_dir / "test_predictions.csv", rows, keypoint_test_outputs, indices,
    keypoint_threshold, keypoint_l1_threshold, keypoint_test_pose_ok,
    keypoint_l2_evidence_threshold, keypoint_class_thresholds,
)
keypoint_selection = {
    "model": keypoint_model_name,
    "class_weight_rule": f"normalized inverse-frequency power {CLASS_WEIGHT_POWER:g}, computed from train only",
    "l2_training": "separate classifier within each L1 branch",
    "feature_schema": "raw COCO-17 + crop aspect ratio + isotropic body-centered geometry + joint angles; uniform train-only jitter and anatomical reflection",
    "l2_evidence_model": "binary classifier trained from labeled-versus-blank L2 records",
    "training_class_weights": keypoint_best["class_weights"],
    "validation_selection_score": keypoint_best["selection_score"],
    "l1_rejection_threshold": keypoint_l1_threshold,
    "l1_threshold_choice": keypoint_l1_choice,
    "l2_fallback_threshold": keypoint_threshold,
    "l2_evidence_threshold": keypoint_l2_evidence_threshold,
    "class_specific_thresholds": keypoint_class_thresholds,
    "c2_2_threshold_choice": keypoint_c2_2_choice,
    "threshold_choice": kp_threshold_choice,
    "temperature_scaling": keypoint_temperatures,
}
joblib.dump({
    "model_schema": MODEL_SCHEMA, "model_name": keypoint_model_name,
    "l1_model": keypoint_best["l1_model"], "l2_models": keypoint_best["l2_models"],
    "evidence_model": keypoint_best["evidence_model"],
    "indices": indices, "temperatures": keypoint_temperatures,
    "l1_threshold": keypoint_l1_threshold, "l2_threshold": keypoint_threshold,
    "l2_evidence_threshold": keypoint_l2_evidence_threshold,
    "class_thresholds": keypoint_class_thresholds,
    "feature_dimension": int(pose_geometry_features.shape[1]),
}, keypoint_run_dir / "final_keypoint_classifier.joblib")
(keypoint_run_dir / "selection.json").write_text(json.dumps(keypoint_selection, ensure_ascii=False, indent=2), encoding="utf-8")
(keypoint_run_dir / "test_metrics.json").write_text(json.dumps(keypoint_test_metrics, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({"selection": keypoint_selection, "test": keypoint_test_metrics}, ensure_ascii=False, indent=2))

# The two required research baselines stay separately reported. Deployment is a third
# validation-selected comparison and must use exactly the same inference path as demo.
deployment_trials = []
for image_weight in [0.0, 0.25, 0.5, 0.75, 1.0]:
    mixed = fuse_outputs(image_val_outputs, keypoint_val_outputs, indices, image_weight, keypoint_val_pose_ok)
    _, l1_choice = l1_rejection_curve(mixed, min_coverage=L1_MIN_COVERAGE, min_accepted=L1_MIN_ACCEPTED,
                                     target_accuracy=L1_TARGET_SELECTIVE_ACCURACY)
    t2, te, tc, choice = select_class_operating_points(mixed, indices, l1_choice["threshold"])
    quality = decision_quality(mixed, indices, l1_choice["threshold"], t2, te, tc)
    deployment_trials.append({"image_weight": image_weight, "l1_threshold": l1_choice["threshold"],
                              "l2_threshold": t2, "evidence_threshold": te, "class_thresholds": tc,
                              "l1_choice": l1_choice, "threshold_choice": choice, "quality": quality})
deployment_selection = max(deployment_trials, key=lambda r: r["quality"]["score"])
deployment_l1_threshold = deployment_selection["l1_threshold"]
deployment_threshold = deployment_selection["l2_threshold"]
deployment_evidence_threshold = deployment_selection["evidence_threshold"]
deployment_class_thresholds = deployment_selection["class_thresholds"]
deployment_dir = RUN_ROOT / "deployment"
deployment_dir.mkdir(parents=True, exist_ok=True)
# Write the complete locked selection before evaluating its test predictions.
(deployment_dir / "selection.json").write_text(json.dumps({"selected": deployment_selection, "trials": deployment_trials,
    "image_members": image_members, "keypoint_classifier": str(keypoint_run_dir / "final_keypoint_classifier.joblib"),
    "manifest_sha256": audit["manifest_sha256"], "model_schema": MODEL_SCHEMA}, ensure_ascii=False, indent=2), encoding="utf-8")
deployment_test_outputs = fuse_outputs(image_test_outputs, keypoint_test_outputs, indices,
                                       deployment_selection["image_weight"], keypoint_test_pose_ok)
deployment_test_metrics = save_test_predictions(deployment_dir / "test_predictions.csv", rows, deployment_test_outputs,
    indices, deployment_threshold, deployment_l1_threshold, None, deployment_evidence_threshold, deployment_class_thresholds)
(deployment_dir / "test_metrics.json").write_text(json.dumps(deployment_test_metrics, ensure_ascii=False, indent=2), encoding="utf-8")
deployment_test_diagnostics = decision_quality(deployment_test_outputs, indices, deployment_l1_threshold,
    deployment_threshold, deployment_evidence_threshold, deployment_class_thresholds)
pd.DataFrame(deployment_test_diagnostics["per_class"]).to_csv(deployment_dir / "per_class_end_to_end.csv", index=False)
target_diagnostics = [r for r in deployment_test_diagnostics["per_class"] if r["code"] in TARGET_L2_CODES]
display(pd.DataFrame(target_diagnostics))
print("Trọng số nhánh ảnh được chọn trên validation:", deployment_selection["image_weight"])

# Historical comparison is descriptive only; it must never drive the selection above.
historical_path = OUTPUTS_DIR / "notebook_runs" / "20261031_153809_seed20261021" / "keypoint_classifier" / "test_predictions.csv"
if historical_path.is_file():
    old = pd.read_csv(historical_path, keep_default_na=False)
    current = pd.read_csv(deployment_dir / "test_predictions.csv", keep_default_na=False)
    paired = old.merge(current, on="instance_id", suffixes=("_old", "_new"), validate="one_to_one")
    if len(paired) != len(current) or not (paired.gold_l2_old == paired.gold_l2_new).all():
        raise RuntimeError("Historical comparison requires identical test instances and labels.")
    changes = []
    for code in TARGET_L2_CODES:
        group = paired[paired.gold_l2_new == code]
        changes.append({"code": code, "label": l2_names_vi[code], "support": len(group),
                        "old_l2_exact_recall": float((group.final_code_old == code).mean()),
                        "new_l2_exact_recall": float((group.final_code_new == code).mean()),
                        "old_wrong_or_rejected_l1": int((group.pred_l1_old != group.gold_l1_old).sum()),
                        "new_wrong_or_rejected_l1": int((group.pred_l1_new != group.gold_l1_new).sum())})
    pd.DataFrame(changes).to_csv(deployment_dir / "target_labels_vs_previous.csv", index=False, encoding="utf-8-sig")
    paired[paired.gold_l2_new.isin(TARGET_L2_CODES)].to_csv(deployment_dir / "target_cases_vs_previous.csv", index=False, encoding="utf-8-sig")

validation_decisions = hierarchical_predictions(
    fuse_outputs(image_val_outputs, keypoint_val_outputs, indices, deployment_selection["image_weight"], keypoint_val_pose_ok),
    indices, deployment_threshold, deployment_l1_threshold, None, deployment_evidence_threshold, deployment_class_thresholds)
validation_case_rows = []
for row, decision in zip([r for r in rows if r["split"] == "val"], validation_decisions):
    if row["level_2_code"] in TARGET_L2_CODES:
        validation_case_rows.append({"image_id": row["image_id"], "gold_l1": row["level_1_code"],
                                     "gold_l2": row["level_2_code"], **decision})
pd.DataFrame(validation_case_rows).to_csv(deployment_dir / "target_validation_cases.csv", index=False, encoding="utf-8-sig")


def compact_metrics(metrics):
    return {
        "l1_accuracy": metrics["l1_all_test"]["accuracy"],
        "l1_macro_f1": metrics["l1_all_test"]["macro_f1"],
        "l1_ece": metrics["l1_calibration"]["ece_10_bins"],
        "l1_brier": metrics["l1_calibration"]["multiclass_brier"],
        "l1_selective_coverage": metrics["l1_selective_with_unknown"]["coverage"],
        "l1_selective_accuracy": metrics["l1_selective_with_unknown"]["selective_accuracy"],
        "unknown_rate": 1.0 - metrics["l1_selective_with_unknown"]["coverage"],
        "l2_oracle_accuracy": metrics["l2_oracle_given_gold_l1"]["accuracy"],
        "l2_oracle_macro_f1": metrics["l2_oracle_given_gold_l1"]["macro_f1"],
        "l2_coverage": metrics["l2_end_to_end_with_l1_fallback"]["coverage"],
        "l2_selective_accuracy": metrics["l2_end_to_end_with_l1_fallback"]["selective_accuracy"],
        "l2_exact_over_all": metrics["l2_end_to_end_with_l1_fallback"]["exact_leaf_correct_over_all_gold_l2"],
        "l2_blank_abstention": metrics["l2_end_to_end_with_l1_fallback"]["abstention_rate_on_blank_l2"],
        "l2_evidence_accuracy": (metrics["l2_evidence_classifier"]["accuracy"]
                                 if metrics.get("l2_evidence_classifier") else np.nan),
    }

comparison = {
    "direct_image": compact_metrics(image_test_metrics),
    "predicted_keypoints": compact_metrics(keypoint_test_metrics),
}
comparison_df = pd.DataFrame(comparison).T
display(comparison_df.style.format("{:.3f}"))

guardrail_df = pd.DataFrame([
    {"phương_pháp": "Ảnh trực tiếp", "ngưỡng_L2": image_threshold,
     "ngưỡng_bằng_chứng": image_l2_evidence_threshold, "ngưỡng_C2.2": image_class_thresholds["C2.2"],
     "fallback_L2_trống_test": comparison["direct_image"]["l2_blank_abstention"]},
    {"phương_pháp": "Keypoint dự đoán", "ngưỡng_L2": keypoint_threshold,
     "ngưỡng_bằng_chứng": keypoint_l2_evidence_threshold, "ngưỡng_C2.2": keypoint_class_thresholds["C2.2"],
     "fallback_L2_trống_test": comparison["predicted_keypoints"]["l2_blank_abstention"]},
])
display(guardrail_df.style.format({"ngưỡng_L2": "{:.3f}", "ngưỡng_bằng_chứng": "{:.3f}",
                                  "ngưỡng_C2.2": "{:.3f}", "fallback_L2_trống_test": "{:.1%}"}))

calibration_rows = []
for method, raw_outputs, calibrated_outputs in [
    ("Ảnh trực tiếp", image_val_outputs_raw, image_val_outputs),
    ("Keypoint dự đoán", keypoint_best["val_outputs"], keypoint_val_outputs),
]:
    before = multiclass_calibration_metrics(raw_outputs["l1_logits"], raw_outputs["y1"])
    after = multiclass_calibration_metrics(calibrated_outputs["l1_logits"], calibrated_outputs["y1"])
    calibration_rows.append({"phương_pháp": method, "ECE_trước": before["ece_10_bins"],
                             "ECE_sau": after["ece_10_bins"], "Brier_trước": before["multiclass_brier"],
                             "Brier_sau": after["multiclass_brier"]})
display(pd.DataFrame(calibration_rows).style.format({"ECE_trước": "{:.3f}", "ECE_sau": "{:.3f}", "Brier_trước": "{:.3f}", "Brier_sau": "{:.3f}"}))

def reliability_points(outputs, bins=8):
    probabilities = torch.softmax(torch.tensor(outputs["l1_logits"]), dim=1).numpy()
    confidence = probabilities.max(axis=1); prediction = probabilities.argmax(axis=1)
    correct = prediction == outputs["y1"]
    xs, ys = [], []
    for lower, upper in zip(np.linspace(0, 1, bins + 1)[:-1], np.linspace(0, 1, bins + 1)[1:]):
        mask = (confidence > lower) & (confidence <= upper)
        if mask.any(): xs.append(float(confidence[mask].mean())); ys.append(float(correct[mask].mean()))
    return xs, ys
fig, axes = plt.subplots(1, 2, figsize=(12, 5))
for ax, method, raw_outputs, calibrated_outputs in [
    (axes[0], "Ảnh trực tiếp", image_val_outputs_raw, image_val_outputs),
    (axes[1], "Keypoint dự đoán", keypoint_best["val_outputs"], keypoint_val_outputs),
]:
    for outputs, label, color in [(raw_outputs, "Trước hiệu chỉnh", "#c28b45"), (calibrated_outputs, "Sau hiệu chỉnh", "#2a7771")]:
        x, y = reliability_points(outputs); ax.plot(x, y, marker="o", label=label, color=color)
    ax.plot([0, 1], [0, 1], linestyle="--", color="#777777"); ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.set_xlabel("Độ tin cậy trung bình"); ax.set_ylabel("Tỷ lệ đúng"); ax.set_title(f"Reliability L1 – {method}"); ax.legend()
plt.tight_layout(); plt.show()

# Per-class L2 support and test metrics: small support makes a class score highly uncertain.
l2_split_support = {
    split: Counter(row["level_2_code"] for row in rows if row["split"] == split and row["level_2_code"])
    for split in ("train", "val", "test")
}
image_l2_per_class = image_test_metrics["l2_oracle_given_gold_l1"]["per_class"]
keypoint_l2_per_class = keypoint_test_metrics["l2_oracle_given_gold_l1"]["per_class"]
l2_diagnostic_rows = []
for class_idx, code in enumerate(indices["l2_codes"]):
    image_item = image_l2_per_class[class_idx]
    keypoint_item = keypoint_l2_per_class[class_idx]
    l2_diagnostic_rows.append({
        "code": code, "nhan": l2_names_vi.get(code, code),
        "train_support": l2_split_support["train"][code],
        "val_support": l2_split_support["val"][code],
        "test_support": image_item["support"],
        "anh_recall_test": image_item["recall"], "anh_f1_test": image_item["f1"],
        "keypoint_recall_test": keypoint_item["recall"], "keypoint_f1_test": keypoint_item["f1"],
    })
l2_diagnostic_df = pd.DataFrame(l2_diagnostic_rows)
display(l2_diagnostic_df.style.format({"anh_recall_test": "{:.1%}", "anh_f1_test": "{:.1%}", "keypoint_recall_test": "{:.1%}", "keypoint_f1_test": "{:.1%}"}))
fig, axes = plt.subplots(1, 2, figsize=(18, 8), sharey=True)
support_plot = l2_diagnostic_df.set_index("nhan")[["train_support", "val_support", "test_support"]]
support_plot.plot(kind="barh", ax=axes[0], color=["#526e9e", "#8aa5c8", "#d49b52"])
axes[0].set_xlabel("Số ảnh có nhãn L2"); axes[0].set_title("Số mẫu từng nhãn theo split")
axes[0].legend(["Train", "Validation", "Test"])
l2_f1_plot = l2_diagnostic_df.set_index("nhan")[["anh_f1_test", "keypoint_f1_test"]]
l2_f1_plot.plot(kind="barh", ax=axes[1], color=["#2a7771", "#c28b45"])
axes[1].set_xlim(0, 1); axes[1].set_xlabel("F1 theo nhãn trên test")
axes[1].set_title("L2 theo lớp (oracle L1); đọc cùng số mẫu test"); axes[1].tick_params(axis="y", labelleft=False)
axes[1].legend(["Ảnh trực tiếp", "Keypoint"])
plt.tight_layout(); plt.show()

plot_metrics = ["l1_accuracy", "l1_macro_f1", "l2_oracle_macro_f1", "l2_exact_over_all"]
ax = comparison_df[plot_metrics].T.plot(kind="bar", figsize=(11, 5), color=["#2a7771", "#c28b45"])
ax.set_ylim(0, 1)
ax.set_ylabel("Điểm")
ax.set_title("So sánh trên cùng test đóng băng")
ax.legend(["Ảnh trực tiếp", "Keypoint dự đoán"])
plt.xticks(rotation=20, ha="right")
plt.tight_layout()
plt.show()

fig, axes = plt.subplots(1, 2, figsize=(15, 5))
for curve_rows, choice, label, color in [
    (image_l1_curve_rows, image_l1_choice, "Ảnh trực tiếp", "#2a7771"),
    (keypoint_l1_curve_rows, keypoint_l1_choice, "Keypoint dự đoán", "#c28b45"),
]:
    curve = pd.DataFrame(curve_rows)
    axes[0].plot(curve["coverage"], curve["selective_accuracy"], label=label, color=color, linewidth=2)
    axes[0].scatter([choice["coverage"]], [choice["selective_accuracy"]], color=color, s=60)
axes[0].axhline(L1_TARGET_SELECTIVE_ACCURACY, color="#777777", linestyle="--", label="Mục tiêu accuracy")
axes[0].set_xlim(0, 1); axes[0].set_ylim(0, 1.02)
axes[0].set_xlabel("Coverage"); axes[0].set_ylabel("Accuracy trên mẫu được nhận")
axes[0].set_title("So sánh risk–coverage L1 trên validation"); axes[0].legend()
def decision_proportions(outputs, l2_threshold, l1_threshold, evidence_ok=None, l2_evidence_threshold=0.0, class_thresholds=None):
    decisions = hierarchical_predictions(
        outputs, indices, l2_threshold, l1_threshold, evidence_ok, l2_evidence_threshold, class_thresholds
    )
    counts = Counter(row["decision_level"] for row in decisions)
    total = max(len(decisions), 1)
    return [counts["l2"] / total, counts["l1"] / total, counts["unknown"] / total]
decision_df = pd.DataFrame({
    "Ảnh trực tiếp": decision_proportions(image_test_outputs, image_threshold, image_l1_threshold, None, image_l2_evidence_threshold, image_class_thresholds),
    "Keypoint dự đoán": decision_proportions(keypoint_test_outputs, keypoint_threshold, keypoint_l1_threshold, keypoint_test_pose_ok, keypoint_l2_evidence_threshold, keypoint_class_thresholds),
}, index=["Nhãn chi tiết L2", "Fallback nhãn tổng quát L1", "Không xác định"]).T
decision_df.plot(kind="bar", stacked=True, ax=axes[1], color=["#2a7771", "#c28b45", "#b8b8b8"])
axes[1].set_ylim(0, 1); axes[1].set_ylabel("Tỷ lệ trên test"); axes[1].set_title("Phân bố mức quyết định cuối")
axes[1].tick_params(axis="x", rotation=0); axes[1].legend(loc="lower center", bbox_to_anchor=(0.5, -0.32), ncol=1)
plt.tight_layout()
plt.show()


def bootstrap_accuracy_difference(outputs_a, outputs_b, n_boot=2000, seed=SEED):
    rng = np.random.default_rng(seed)
    gold = np.array([indices["l1_to_idx"][row["level_1_code"]] for row in rows if row["split"] == "test"])
    pred_a = outputs_a["l1_logits"].argmax(axis=1)
    pred_b = outputs_b["l1_logits"].argmax(axis=1)
    differences = []
    for _ in range(n_boot):
        sample = rng.integers(0, len(gold), len(gold))
        differences.append(np.mean(pred_a[sample] == gold[sample]) - np.mean(pred_b[sample] == gold[sample]))
    return {"image_minus_keypoint_accuracy_difference": float(np.mean(differences)),
            "bootstrap_95ci": [float(x) for x in np.quantile(differences, [0.025, 0.975])],
            "bootstrap_resamples": n_boot}

paired_uncertainty = bootstrap_accuracy_difference(image_test_outputs, keypoint_test_outputs)
(RUN_ROOT / "paired_bootstrap.json").write_text(json.dumps(paired_uncertainty, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(paired_uncertainty, ensure_ascii=False, indent=2))


image_predictions = hierarchical_predictions(
    image_test_outputs, indices, image_threshold, image_l1_threshold, None,
    image_l2_evidence_threshold, image_class_thresholds
)
keypoint_predictions = hierarchical_predictions(
    keypoint_test_outputs, indices, keypoint_threshold, keypoint_l1_threshold, keypoint_test_pose_ok,
    keypoint_l2_evidence_threshold, keypoint_class_thresholds
)
test_rows = [row for row in rows if row["split"] == "test"]
error_rows = []
for row, image_pred, kp_pred in zip(test_rows, image_predictions, keypoint_predictions):
    if image_pred["l1_code"] != row["level_1_code"] or kp_pred["l1_code"] != row["level_1_code"]:
        error_rows.append({
            "image_id": row["image_id"], "gold_l1": row["level_1_code"],
            "image_pred_l1": image_pred["l1_code"], "keypoint_pred_l1": kp_pred["l1_code"],
            "gold_l2": row["level_2_code"], "image_pred_l2": image_pred["l2_code"],
            "keypoint_pred_l2": kp_pred["l2_code"],
            "image_unknown": image_pred["is_unknown"], "keypoint_unknown": kp_pred["is_unknown"],
            "visibility": row["visibility"],
            "annotation_confidence": row["annotation_confidence"],
        })
print("Số mẫu có ít nhất một hướng sai L1:", len(error_rows))
error_df = pd.DataFrame(error_rows)
display(error_df)


def format_prediction_vi(prediction):
    percent = 100.0 * prediction["final_confidence"]
    if prediction["is_unknown"]:
        return f"Không xác định – độ tin cậy L1 cao nhất {percent:.0f}%"
    code = prediction["final_code"]
    name = l2_names_vi[code] if prediction["decision_level"] == "l2" else l1_names_vi[code]
    return f"{name} – {percent:.0f}%"

def prediction_reason_vi(prediction):
    if prediction["is_unknown"]:
        return "Độ tin cậy tư thế tổng quát chưa đạt ngưỡng được chọn trên validation."
    if prediction["decision_level"] == "l2":
        return "Đủ bằng chứng thị giác và độ tin cậy để trả nhãn chi tiết L2."
    if not prediction["l2_evidence_ok"]:
        return "Chưa đủ bằng chứng thị giác cho L2; hệ thống giữ nhãn tổng quát L1."
    return "Độ tin cậy L2 chưa đạt ngưỡng; hệ thống giữ nhãn tổng quát L1."

def predict_posture(image_path):
    image_path = Path(image_path).expanduser().resolve()
    if not image_path.is_file():
        raise FileNotFoundError(f"Không tìm thấy ảnh demo: {image_path}")
    pose_result = pose_model.predict(
        source=str(image_path), imgsz=POSE_IMAGE_SIZE,
        device=pose_feature_device, half=pose_feature_device != "cpu", max_det=1, verbose=False,
    )[0]
    feature = np.zeros((1, 54), dtype=np.float32)
    with Image.open(image_path) as source_image:
        feature[0, 53] = source_image.width / source_image.height
    detected = False
    if pose_result.boxes is not None and len(pose_result.boxes) and pose_result.keypoints is not None:
        best = int(np.argmax(pose_result.boxes.conf.detach().cpu().numpy()))
        xy = pose_result.keypoints.xyn[best].detach().cpu().numpy()
        kp_conf = (pose_result.keypoints.conf[best].detach().cpu().numpy()
                   if pose_result.keypoints.conf is not None else np.ones(17))
        feature[0, :51] = np.column_stack([xy, kp_conf]).reshape(-1)
        feature[0, 51] = float(pose_result.boxes.conf[best])
        feature[0, 52] = 1.0
        detected = True
    geometry_feature = engineer_pose_features(feature)
    outputs = apply_temperatures(outputs_from_classifiers(
        keypoint_best["l1_model"], keypoint_best["l2_models"], keypoint_best["evidence_model"],
        geometry_feature,
    ), keypoint_temperatures)
    image_outputs = collect_image_path(image_path, image_members, indices)
    outputs = fuse_outputs(image_outputs, outputs, indices, deployment_selection["image_weight"], [detected])
    prediction = hierarchical_predictions(
        outputs, indices, deployment_threshold, deployment_l1_threshold, None,
        deployment_evidence_threshold, deployment_class_thresholds,
    )[0]
    return {
        "image_path": str(image_path), "pose_detected": detected,
        "prediction": prediction, "display_text": format_prediction_vi(prediction),
        "reason_text": prediction_reason_vi(prediction),
        "l1_probabilities": torch.softmax(torch.tensor(outputs["l1_logits"]), dim=1).numpy()[0],
        "l2_logits": outputs["l2_logits"][0], "pose_result": pose_result,
    }

# COCO-17 không có keypoint cổ. Hai cạnh tai-vai mặc định dễ gây hiểu nhầm trên tranh Thangka,
# nên phần minh họa tách khung mặt khỏi khung thân; dữ liệu keypoint dùng cho phân loại không đổi.
DEMO_SKELETON_EDGES = [
    (0, 1), (0, 2), (1, 2), (1, 3), (2, 4),  # mặt
    (5, 6), (5, 7), (7, 9), (6, 8), (8, 10),
    (5, 11), (6, 12), (11, 12), (11, 13), (13, 15), (12, 14), (14, 16),
]

def draw_demo_pose(ax, pose_result, min_keypoint_confidence=0.25):
    from matplotlib.patches import Rectangle
    image_rgb = pose_result.orig_img[..., ::-1]
    ax.imshow(image_rgb)
    if pose_result.boxes is None or len(pose_result.boxes) == 0 or pose_result.keypoints is None:
        return
    box_confidences = pose_result.boxes.conf.detach().cpu().numpy()
    best = int(np.argmax(box_confidences))
    x1, y1, x2, y2 = pose_result.boxes.xyxy[best].detach().cpu().numpy()
    ax.add_patch(Rectangle((x1, y1), x2 - x1, y2 - y1, fill=False, edgecolor="#ffd23f", linewidth=2.5))
    xy = pose_result.keypoints.xy[best].detach().cpu().numpy()
    confidence = (pose_result.keypoints.conf[best].detach().cpu().numpy()
                  if pose_result.keypoints.conf is not None else np.ones(len(xy), dtype=np.float32))
    visible = confidence >= float(min_keypoint_confidence)
    for start, end in DEMO_SKELETON_EDGES:
        if visible[start] and visible[end]:
            is_face = start <= 4 and end <= 4
            ax.plot([xy[start, 0], xy[end, 0]], [xy[start, 1], xy[end, 1]],
                    color="#23e05f" if is_face else "#20a4f3", linewidth=2.5, alpha=0.9)
    face_points = np.arange(0, 5)
    body_points = np.arange(5, 17)
    face_visible = face_points[visible[face_points]]
    body_visible = body_points[visible[body_points]]
    if len(face_visible):
        ax.scatter(xy[face_visible, 0], xy[face_visible, 1], s=55, c="#23e05f", edgecolors="white", linewidths=0.8, zorder=3)
    if len(body_visible):
        ax.scatter(xy[body_visible, 0], xy[body_visible, 1], s=55, c="#20a4f3", edgecolors="white", linewidths=0.8, zorder=3)
    ax.text(x1, max(0, y1 - 8), f"Pose {100 * box_confidences[best]:.0f}%", color="#ffe066",
            fontsize=11, fontweight="bold", bbox={"facecolor": "black", "alpha": 0.55, "pad": 3})

def show_prediction(result):
    pred = result["prediction"]
    # Tách ảnh khỏi biểu đồ để ảnh Thangka không bị co nhỏ khi trình chiếu.
    image_fig, image_ax = plt.subplots(figsize=(15, 9), dpi=120)
    draw_demo_pose(image_ax, result["pose_result"])
    image_ax.set_title(result["display_text"] + "\nKhung mặt và khung thân được tách rời; bbox/keypoint chỉ dùng để hỗ trợ", fontsize=16, fontweight="bold")
    image_ax.axis("off")
    image_fig.tight_layout()
    plt.show()
    plt.close(image_fig)
    fig, axes = plt.subplots(1, 3, figsize=(20, 6), dpi=120)
    l1_prob = result["l1_probabilities"]
    l1_labels = [l1_names_vi[code] for code in indices["l1_codes"]]
    colors = ["#2a7771" if code == pred["l1_candidate"] else "#9fbfbc" for code in indices["l1_codes"]]
    axes[0].barh(l1_labels, l1_prob, color=colors)
    axes[0].axvline(deployment_l1_threshold, color="#b33a3a", linestyle="--", label=f"Ngưỡng L1 = {deployment_l1_threshold:.2f}")
    axes[0].set_xlim(0, 1); axes[0].set_title("Độ tin cậy nhãn tổng quát L1"); axes[0].legend()
    evidence_value = pred["l2_evidence_confidence"]
    axes[1].barh(["Đủ bằng chứng L2"], [evidence_value], color="#526e9e")
    axes[1].axvline(deployment_evidence_threshold, color="#b33a3a", linestyle="--",
                    label=f"Ngưỡng bằng chứng = {deployment_evidence_threshold:.2f}")
    axes[1].set_xlim(0, 1); axes[1].set_title("Bằng chứng cho nhãn chi tiết"); axes[1].legend()
    parent = pred["l1_candidate"]
    child_codes = [code for code in indices["l2_codes"] if indices["l2_parent"][code] == parent]
    child_idx = [indices["l2_to_idx"][code] for code in child_codes]
    conditional = torch.softmax(torch.tensor(result["l2_logits"][child_idx]), dim=0).numpy()
    joint = pred["l1_confidence"] * conditional
    axes[2].barh([l2_names_vi[code] for code in child_codes], joint, color="#c28b45")
    axes[2].axvline(deployment_threshold, color="#b33a3a", linestyle="--", label=f"Ngưỡng L2 = {deployment_threshold:.2f}")
    selected_cutoff = deployment_class_thresholds[pred["l2_candidate"]]
    if selected_cutoff <= 1.0:
        axes[2].axvline(selected_cutoff, color="#7b3294", linestyle=":", label="Ngưỡng riêng nhãn ứng viên")
    else:
        axes[2].text(0.02, 0.95, "Nhãn ứng viên chưa đủ bằng chứng validation để trả L2", transform=axes[2].transAxes, va="top", fontsize=9)
    axes[2].set_xlim(0, 1); axes[2].set_title("Độ tin cậy nhãn chi tiết trong nhánh L1"); axes[2].legend()
    fig.suptitle("Căn cứ cho quyết định phân loại", fontsize=16, fontweight="bold")
    fig.tight_layout()
    plt.show()
    plt.close(fig)

def run_demo(image_path="", split="val", index=0):
    selected_row = None
    if str(image_path).strip():
        demo_path = Path(str(image_path).strip())
        source_text = f"Ảnh ngoài: {demo_path.name}"
    else:
        split_rows = [row for row in rows if row["split"] == split]
        if not split_rows:
            raise ValueError(f"Split không hợp lệ hoặc không có ảnh: {split}")
        selected_row = split_rows[int(index) % len(split_rows)]
        demo_path = DATA_DIR / selected_row["crop_path"]
        source_text = (f"Dataset {split}, ảnh gốc {Path(selected_row['image_path']).name} "
                       f"→ crop mục tiêu {Path(selected_row['crop_path']).name}")
    result = predict_posture(demo_path)
    pred = result["prediction"]
    gold_text = "Không có nhãn tham chiếu"
    if selected_row is not None:
        gold_text = l2_names_vi.get(selected_row["level_2_code"], l1_names_vi[selected_row["level_1_code"]])
    display(pd.DataFrame([{
        "Nguồn ảnh": source_text, "Nhãn tham chiếu": gold_text,
        "Kết quả hệ thống": result["display_text"],
        "Mức quyết định": pred["decision_level"].upper(),
        "Bằng chứng L2": f"{100 * pred['l2_evidence_confidence']:.0f}%",
        "Giải thích fallback": result["reason_text"],
    }]))
    show_prediction(result)
    return result

# Demo mặc định. Có thể đổi split/index hoặc truyền đường dẫn ảnh ngoài dataset.
SUPPORTED_DEMO_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}

def run_demo_batch(image_paths, max_images=None):
    from IPython.display import Markdown
    paths = [Path(path).expanduser().resolve() for path in image_paths]
    if max_images is not None:
        paths = paths[:max(1, int(max_images))]
    if not paths:
        raise ValueError("Chưa chọn ảnh hợp lệ để demo.")
    import gc
    summary_rows = []
    for number, image_path in enumerate(paths, start=1):
        display(Markdown(f"## Ảnh {number}/{len(paths)} — `{image_path.name}`"))
        try:
            result = run_demo(image_path=image_path)
            summary_rows.append({"Ảnh": image_path.name, "Kết quả": result["display_text"],
                                 "Mức quyết định": result["prediction"]["decision_level"].upper(), "Trạng thái": "Thành công"})
            del result
        except Exception as exc:
            print(type(exc).__name__ + ":", exc)
            summary_rows.append({"Ảnh": image_path.name, "Kết quả": "—", "Mức quyết định": "—", "Trạng thái": str(exc)})
        finally:
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
    display(Markdown("## Tổng hợp lô ảnh"))
    summary = pd.DataFrame(summary_rows)
    display(summary)
    return summary

def run_demo_folder(folder_path, recursive=False, max_images=20):
    folder = Path(str(folder_path).strip()).expanduser().resolve()
    if not folder.is_dir():
        raise NotADirectoryError(f"Không tìm thấy thư mục: {folder}")
    candidates = folder.rglob("*") if recursive else folder.iterdir()
    image_paths = sorted(
        (path for path in candidates if path.is_file() and path.suffix.lower() in SUPPORTED_DEMO_EXTENSIONS),
        key=lambda path: str(path).lower(),
    )
    if not image_paths:
        raise FileNotFoundError(f"Thư mục không có ảnh định dạng được hỗ trợ: {folder}")
    if len(image_paths) > int(max_images):
        print(f"Tìm thấy {len(image_paths)} ảnh; demo {int(max_images)} ảnh đầu để kiểm soát thời gian và bộ nhớ.")
    return run_demo_batch(image_paths, max_images=max_images)

def run_demo_dataset_batch(split, selected_indices, max_images=20):
    from IPython.display import Markdown
    import gc
    split_rows = [row for row in rows if row["split"] == split]
    if not split_rows:
        raise ValueError(f"Split không hợp lệ hoặc không có ảnh: {split}")
    chosen = list(selected_indices)[:max(1, int(max_images))]
    if not chosen:
        raise ValueError("Hãy chọn ít nhất một ảnh trong danh sách dataset.")
    summary_rows = []
    for number, index in enumerate(chosen, start=1):
        index = int(index) % len(split_rows)
        row = split_rows[index]
        image_name = Path(row["crop_path"]).name
        display(Markdown(f"## Ảnh dataset {number}/{len(chosen)} — `{image_name}`"))
        try:
            result = run_demo(split=split, index=index)
            gold = l2_names_vi.get(row["level_2_code"], l1_names_vi[row["level_1_code"]])
            summary_rows.append({"Ảnh": image_name, "Nhãn tham chiếu": gold,
                                 "Kết quả": result["display_text"],
                                 "Mức quyết định": result["prediction"]["decision_level"].upper(),
                                 "Trạng thái": "Thành công"})
            del result
        except Exception as exc:
            print(type(exc).__name__ + ":", exc)
            summary_rows.append({"Ảnh": image_name, "Nhãn tham chiếu": "—", "Kết quả": "—",
                                 "Mức quyết định": "—", "Trạng thái": str(exc)})
        finally:
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
    display(Markdown("## Tổng hợp các ảnh dataset đã chọn"))
    summary = pd.DataFrame(summary_rows)
    display(summary)
    return summary

def run_demo_dataset_files(selected_paths, required_split=None):
    from IPython.display import Markdown
    import gc
    lookup = {}
    for split_name in sorted({row["split"] for row in rows}):
        split_rows = [row for row in rows if row["split"] == split_name]
        for index, row in enumerate(split_rows):
            image_name = Path(row["image_path"]).name.casefold()
            lookup[(split_name, image_name)] = (split_name, index, row)
    chosen_paths = [Path(path).expanduser().resolve() for path in selected_paths]
    if not chosen_paths:
        raise ValueError("Hãy bấm 'Chọn ảnh dataset' và chọn ít nhất một ảnh.")
    summary_rows = []
    for number, image_path in enumerate(chosen_paths, start=1):
        display(Markdown(f"## Ảnh dataset {number}/{len(chosen_paths)} — `{image_path.name}`"))
        split_candidates = [required_split] if required_split else sorted({key[0] for key in lookup})
        matches = [lookup[(split_name, image_path.name.casefold())] for split_name in split_candidates
                   if (split_name, image_path.name.casefold()) in lookup]
        match = matches[0] if matches else None
        if match is None:
            message = f"Ảnh không thuộc split {required_split!r} trong DATA_DIR/images hoặc không có trong manifest."
            print("ValueError:", message)
            summary_rows.append({"Ảnh": image_path.name, "Split": "—", "Nhãn tham chiếu": "—",
                                 "Kết quả": "—", "Mức quyết định": "—", "Trạng thái": message})
            continue
        split_name, index, row = match
        try:
            result = run_demo(split=split_name, index=index)
            gold = l2_names_vi.get(row["level_2_code"], l1_names_vi[row["level_1_code"]])
            summary_rows.append({"Ảnh": image_path.name, "Split": split_name, "Nhãn tham chiếu": gold,
                                 "Kết quả": result["display_text"],
                                 "Mức quyết định": result["prediction"]["decision_level"].upper(),
                                 "Trạng thái": "Thành công"})
            del result
        except Exception as exc:
            print(type(exc).__name__ + ":", exc)
            summary_rows.append({"Ảnh": image_path.name, "Split": split_name, "Nhãn tham chiếu": "—",
                                 "Kết quả": "—", "Mức quyết định": "—", "Trạng thái": str(exc)})
        finally:
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
    display(Markdown("## Tổng hợp các ảnh dataset đã chọn"))
    summary = pd.DataFrame(summary_rows)
    display(summary)
    return summary

demo_result = None  # Chọn nguồn ảnh trong giao diện bên dưới; không tự chạy ảnh validation.
print("Dùng ảnh ngoài dataset: run_demo(r'C:\\duong_dan\\anh.jpg')")
print("Dùng mẫu khác: run_demo(split='val', index=5) hoặc run_demo(split='test', index=5)")

# Giao diện nút bấm đơn giản trong Jupyter/VS Code; vẫn dùng được run_demo nếu ipywidgets chưa cài.
try:
    import ipywidgets as widgets
    from IPython.display import clear_output
    demo_source = widgets.Dropdown(options=[("Validation", "val"), ("Test đã khóa", "test")], description="Nguồn:")
    dataset_selected_paths = []
    dataset_picker_button = widgets.Button(
        description="Chọn ảnh dataset (0)", icon="folder-open",
        layout=widgets.Layout(width="240px"),
    )
    dataset_selection_status = widgets.HTML("<i>Chưa chọn ảnh gốc thuộc split Validation.</i>")
    demo_button = widgets.Button(description="Chạy ảnh đã chọn", button_style="primary")
    demo_output = widgets.Output()

    def _prepare_split_picker_directory(split_name):
        import os
        import shutil
        picker_dir = CACHE_DIR / "dataset_file_picker" / split_name
        picker_dir.mkdir(parents=True, exist_ok=True)
        split_rows = [row for row in rows if row["split"] == split_name]
        for row in split_rows:
            source = (DATA_DIR / row["image_path"]).resolve()
            target = picker_dir / source.name
            if target.exists():
                continue
            try:
                os.link(source, target)  # hard link: không nhân đôi dung lượng ảnh
            except OSError:
                shutil.copy2(source, target)
        return picker_dir

    def _reset_dataset_selection(change):
        dataset_selected_paths.clear()
        dataset_picker_button.description = "Chọn ảnh dataset (0)"
        split_label = "Validation" if change["new"] == "val" else "Test đã khóa"
        dataset_selection_status.value = f"<i>Chưa chọn ảnh gốc thuộc split {split_label}.</i>"

    def _choose_dataset_files(_):
        root = None
        try:
            import tkinter as tk
            from tkinter import filedialog
            initial_dir = _prepare_split_picker_directory(demo_source.value)
            split_label = "Validation" if demo_source.value == "val" else "Test đã khóa"
            root = tk.Tk()
            root.withdraw()
            root.attributes("-topmost", True)
            root.update()
            chosen = filedialog.askopenfilenames(
                parent=root, title=f"Chọn ảnh gốc thuộc split {split_label}",
                initialdir=str(initial_dir),
                filetypes=[("Tệp ảnh", "*.jpg *.jpeg *.png *.webp *.bmp *.tif *.tiff"), ("Tất cả tệp", "*.*")],
            )
            if chosen:
                dataset_selected_paths[:] = list(chosen)
                dataset_picker_button.description = f"Chọn ảnh dataset ({len(chosen)})"
                preview = ", ".join(Path(path).name for path in chosen[:4])
                if len(chosen) > 4:
                    preview += f" và {len(chosen) - 4} ảnh khác"
                dataset_selection_status.value = f"<small><b>Đã chọn {split_label}:</b> {preview}</small>"
        except Exception as exc:
            with demo_output:
                print("Không mở được hộp thoại dataset:", type(exc).__name__ + ":", exc)
        finally:
            if root is not None:
                root.destroy()

    def _run_demo_button(_):
        with demo_output:
            clear_output(wait=True)
            try:
                run_demo_dataset_files(dataset_selected_paths, required_split=demo_source.value)
            except Exception as exc:
                print(type(exc).__name__ + ":", exc)
    demo_source.observe(_reset_dataset_selection, names="value")
    dataset_picker_button.on_click(_choose_dataset_files)
    demo_button.on_click(_run_demo_button)
    import uuid
    upload_picker = widgets.FileUpload(
        accept=".jpg,.jpeg,.png,.webp,.bmp,.tif,.tiff", multiple=True,
        description="Chọn nhiều ảnh", layout=widgets.Layout(width="220px"),
    )
    upload_button = widgets.Button(description="Dự đoán ảnh đã chọn", button_style="success")
    folder_box = widgets.Text(value="", placeholder=r"C:\thu_muc_anh", description="Thư mục:", layout=widgets.Layout(width="700px"))
    recursive_box = widgets.Checkbox(value=False, description="Gồm thư mục con")
    batch_limit = widgets.BoundedIntText(value=20, min=1, max=200, description="Tối đa:")
    folder_button = widgets.Button(description="Chạy cả thư mục", button_style="info")

    def _uploaded_items(value):
        if isinstance(value, dict):  # ipywidgets 7
            items = []
            for name, metadata in value.items():
                item = dict(metadata); item.setdefault("name", name); items.append(item)
            return items
        return [dict(item) for item in value]  # ipywidgets 8

    def _run_upload_button(_):
        with demo_output:
            clear_output(wait=True)
            try:
                items = _uploaded_items(upload_picker.value)
                if not items:
                    raise ValueError("Hãy bấm 'Chọn nhiều ảnh' và chọn ít nhất một tệp.")
                upload_dir = CACHE_DIR / "demo_uploads"
                upload_dir.mkdir(parents=True, exist_ok=True)
                saved_paths = []
                for item in items[:batch_limit.value]:
                    safe_name = Path(item.get("name", "image.jpg")).name
                    target = upload_dir / f"{uuid.uuid4().hex[:8]}_{safe_name}"
                    target.write_bytes(bytes(item["content"]))
                    saved_paths.append(target)
                if len(items) > batch_limit.value:
                    print(f"Đã chọn {len(items)} ảnh; demo {batch_limit.value} ảnh đầu.")
                run_demo_batch(saved_paths)
            except Exception as exc:
                print(type(exc).__name__ + ":", exc)

    def _run_folder_button(_):
        with demo_output:
            clear_output(wait=True)
            try:
                run_demo_folder(folder_box.value, recursive=recursive_box.value, max_images=batch_limit.value)
            except Exception as exc:
                print(type(exc).__name__ + ":", exc)

    upload_button.on_click(_run_upload_button)
    folder_button.on_click(_run_folder_button)
    display(widgets.VBox([
        widgets.HTML("<h3>Demo phân tích tư thế nhân vật Phật giáo</h3><p>Mỗi ảnh trả đúng một quyết định phân cấp L2 → L1 → Không xác định.</p>"),
        widgets.HTML("<b>1. Chọn một hoặc nhiều ảnh gốc có sẵn trong dataset</b> — chọn Validation/Test trước, rồi giữ Ctrl/Shift để chọn nhiều tệp. Notebook tự ánh xạ ảnh gốc sang crop nhân vật mục tiêu đúng như lúc huấn luyện."),
        demo_source, widgets.HBox([dataset_picker_button, demo_button]), dataset_selection_status,
        widgets.HTML("<b>2. Chọn một hoặc nhiều ảnh từ máy</b> — giữ Ctrl/Shift trong hộp thoại để chọn nhiều tệp."),
        widgets.HBox([upload_picker, upload_button]),
        widgets.HTML("<b>3. Chạy toàn bộ ảnh trong một thư mục</b>"),
        folder_box, widgets.HBox([recursive_box, batch_limit, folder_button]),
        demo_output,
    ]))
except ImportError:
    print("Không có ipywidgets; hãy gọi trực tiếp hàm run_demo như hướng dẫn ở trên.")


summary = {
    "run_id": RUN_ID,
    "created_at": datetime.now(timezone.utc).isoformat(),
    "dataset_audit": audit_summary,
    "inter_rater_agreement": kappa_summary,
    "image_selection": image_selection,
    "image_test": compact_metrics(image_test_metrics),
    "pose_geometry_test": pose_geometry_metrics,
    "keypoint_selection": keypoint_selection,
    "keypoint_test": compact_metrics(keypoint_test_metrics),
    "paired_uncertainty": paired_uncertainty,
    "run_mode": RUN_MODE,
    "image_seeds": IMAGE_SEEDS,
    "deployment_selection": deployment_selection,
    "deployment_test": compact_metrics(deployment_test_metrics),
    "limitations": [
        "Ensemble nhiều seed ảnh; chưa phải nested cross-validation toàn pipeline.",
        "Test lịch sử đã được xem ở các vòng phát triển trước; cần tập độc lập mới để kết luận tổng quát hóa.",
        "Một số lớp L2 chỉ có 3-4 mẫu test.",
        "Không xác định hiện là cơ chế từ chối theo validation trong phân phối; chưa có tập âm/OOD để đánh giá phát hiện ngoài phân phối.",
        "Phạm vi sử dụng nội bộ, không phát hành dữ liệu hoặc trọng số.",
    ],
}
(RUN_ROOT / "SUMMARY.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

report = f"""# Kết quả thực nghiệm phân tích tư thế Thangka

Run: {RUN_ID}  \nChế độ: {RUN_MODE} (smoke chỉ kiểm tra thực thi, không phải kết quả mô hình cuối)  \nSeeds ảnh thực tế: {IMAGE_SEEDS}  
Dataset: {audit_summary['dataset_version']}  
Seed: {SEED}

## Kiểm tra dữ liệu

- Tổng số mẫu: {audit_summary['records']}.
- Split train/validation/test: {audit_summary['split_counts']}.
- Mẫu đủ 17 keypoint: {audit_summary['full_keypoint_records']}.
- Rò rỉ artifact giữa split: {audit_summary['artifact_leakage_groups']} nhóm.
- Rò rỉ ảnh trùng hash giữa split: {audit_summary['exact_hash_leakage_groups']} nhóm.

## Độ đồng thuận

- Cặp nhãn độc lập của Ngan và My: {kappa_summary['n_paired']}.
- Kappa nhãn phân cấp: {kappa_summary['hierarchical_cohen_kappa']:.4f}.
- Kappa L1: {kappa_summary['l1_cohen_kappa']:.4f}.

## Phân loại trực tiếp từ ảnh

- Kiến trúc: {image_architecture}.
- L1 accuracy: {comparison['direct_image']['l1_accuracy']:.4f}.
- L1 macro-F1: {comparison['direct_image']['l1_macro_f1']:.4f}.
- Hiệu chỉnh độ tin cậy L1 (ECE / Brier): {comparison['direct_image']['l1_ece']:.4f} / {comparison['direct_image']['l1_brier']:.4f}.
- Ngưỡng từ chối L1: {image_l1_threshold:.4f}.
- L1 selective coverage/accuracy: {comparison['direct_image']['l1_selective_coverage']:.4f} / {comparison['direct_image']['l1_selective_accuracy']:.4f}.
- Tỷ lệ Không xác định: {comparison['direct_image']['unknown_rate']:.4f}.
- L2 oracle macro-F1: {comparison['direct_image']['l2_oracle_macro_f1']:.4f}.
- L2 exact trên toàn bộ mẫu có gold L2: {comparison['direct_image']['l2_exact_over_all']:.4f}.
- Tỷ lệ fallback trên mẫu người gán nhãn để trống L2: {comparison['direct_image']['l2_blank_abstention']:.4f}.

## Pose và phân loại từ keypoint dự đoán

- Pose PCK@0.05 bbox diagonal: {pose_geometry_metrics['pck_at_0_05_bbox_diagonal']:.4f}.
- Mean bbox IoU: {pose_geometry_metrics['mean_bbox_iou'] if pose_geometry_metrics['mean_bbox_iou'] is not None else 'n.a.'}.
- Mean OKS: {pose_geometry_metrics['mean_oks'] if pose_geometry_metrics['mean_oks'] is not None else 'n.a.'}.
- Classifier keypoint: {keypoint_model_name}.
- L1 accuracy: {comparison['predicted_keypoints']['l1_accuracy']:.4f}.
- L1 macro-F1: {comparison['predicted_keypoints']['l1_macro_f1']:.4f}.
- Hiệu chỉnh độ tin cậy L1 (ECE / Brier): {comparison['predicted_keypoints']['l1_ece']:.4f} / {comparison['predicted_keypoints']['l1_brier']:.4f}.
- Ngưỡng từ chối L1: {keypoint_l1_threshold:.4f}.
- L1 selective coverage/accuracy: {comparison['predicted_keypoints']['l1_selective_coverage']:.4f} / {comparison['predicted_keypoints']['l1_selective_accuracy']:.4f}.
- Tỷ lệ Không xác định: {comparison['predicted_keypoints']['unknown_rate']:.4f}.
- L2 oracle macro-F1: {comparison['predicted_keypoints']['l2_oracle_macro_f1']:.4f}.
- L2 exact trên toàn bộ mẫu có gold L2: {comparison['predicted_keypoints']['l2_exact_over_all']:.4f}.
- Tỷ lệ fallback trên mẫu người gán nhãn để trống L2: {comparison['predicted_keypoints']['l2_blank_abstention']:.4f}.
- Accuracy bộ kiểm tra đủ bằng chứng L2: {comparison['predicted_keypoints']['l2_evidence_accuracy']:.4f}.

## So sánh và giới hạn

- Chênh lệch L1 accuracy hướng ảnh trừ hướng keypoint: {paired_uncertainty['image_minus_keypoint_accuracy_difference']:.4f}.
- Bootstrap 95% CI: {paired_uncertainty['bootstrap_95ci']}.
- Mô hình ảnh học head, mở các block trên rồi toàn backbone; cố định thống kê BatchNorm, dùng loss phân cấp joint và head bằng chứng L2.
- Mô hình keypoint dùng đặc trưng hình học chuẩn hóa, classifier L2 riêng theo nhánh và bộ kiểm tra đủ bằng chứng L2.
- Tất cả nhãn L2 có ngưỡng riêng được chọn trên validation; báo support và khoảng tin cậy, không ép nhãn hiếm.
- Xác suất được temperature scaling trên validation trước khi chọn ngưỡng từ chối.
- Ensemble nhiều seed; không suy rộng quá phạm vi snapshot hoặc coi test đã xem là đánh giá độc lập mới.
- Các lớp L2 support nhỏ phải được báo cùng support và confusion matrix.
- Không xác định là từ chối do bằng chứng yếu theo validation; chưa thể diễn giải như bộ phát hiện OOD vì chưa có tập âm/OOD.
- Dữ liệu và trọng số chỉ dùng nội bộ theo metadata quyền sử dụng.
"""
(RUN_ROOT / "REPORT.md").write_text(report, encoding="utf-8")
print(report)
print("\nHoàn tất. Tất cả kết quả của run ở:", RUN_ROOT)

with (RUN_ROOT / "REPORT.md").open("a", encoding="utf-8") as stream:
    stream.write("\n\n## Đầu ra triển khai\n\n" + json.dumps({"selection": deployment_selection, "test": compact_metrics(deployment_test_metrics)}, ensure_ascii=False, indent=2))
