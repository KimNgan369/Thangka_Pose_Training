"""Decoupled, class-balanced posture learning with validation-only selection.

Backbones are frozen from the documented baseline (not an independent CV estimate
of the whole representation). Group cross-fitting assesses only the new gate.
No test examples are extracted until selection.json has been written.
"""
from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import json
import os
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from concurrent.futures import ThreadPoolExecutor

import joblib
import numpy as np
import torch
from PIL import Image, ImageOps, ImageEnhance
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.preprocessing import normalize
from sklearn.calibration import CalibratedClassifierCV
from threadpoolctl import threadpool_limits

from notebook_cells import get_code_cell

ROOT = Path(__file__).resolve().parent
BASE = ROOT / 'outputs/notebook_runs/20261031_174634_seed20261021'
VERSION = 1


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    temporary.replace(path)


def utilities(root=ROOT, base=BASE):
    ns = dict(ROOT=root, DATA_DIR=root / 'data', IMAGE_SIZE=384, IMAGE_DROPOUT=.3,
              CLASS_WEIGHT_POWER=.5, MODEL_SCHEMA=4, L2_TARGET_PRECISION=.9,
              DEVICE='cuda' if torch.cuda.is_available() else 'cpu')
    notebook = read_json(base / 'source_notebook.ipynb')
    exec(compile(''.join(get_code_cell(notebook, 6)['source']), '<baseline utilities>', 'exec'), ns)
    ns['ontology'] = read_json(root / 'data/ontology.json')
    return ns


def softmax(x):
    x = np.asarray(x, dtype=np.float64)
    e = np.exp(x - x.max(axis=1, keepdims=True))
    return e / e.sum(axis=1, keepdims=True)


def subset(outputs, positions):
    return {k: v[positions] for k, v in outputs.items()}


def member_list(base=BASE):
    summary = read_json(base / 'SUMMARY.json')
    members = []
    for architecture in ('resnet18', 'mobilenet_v2'):
        for seed in (20261021, 20261031, 20261107):
            checkpoint = base / 'image_classifier' / f'{architecture}_seed{seed}' / 'best_model.pt'
            if not checkpoint.is_file():
                raise FileNotFoundError(checkpoint)
            members.append(dict(architecture=architecture, seed=seed, checkpoint=str(checkpoint),
                                sha256=hashlib.sha256(checkpoint.read_bytes()).hexdigest()))
    return members, summary


def image_pixels(image, view, ns):
    # Deterministic train-only augmentation; preserve the full body and support.
    if view == 1:
        image = ImageOps.mirror(image)
    elif view == 2:
        image = ImageEnhance.Color(image.rotate(5, expand=True, fillcolor='white')).enhance(.9)
    elif view == 3:
        image = ImageOps.mirror(image.rotate(-5, expand=True, fillcolor='white'))
        image = ImageEnhance.Contrast(image).enhance(1.08)
    return np.asarray(ns['ResizeWithPad'](384)(image), dtype=np.uint8)


def normalized_batch(pixels, device):
    tensor = torch.from_numpy(np.stack(pixels)).permute(0, 3, 1, 2).to(device).float().div_(255.)
    mean = tensor.new_tensor([.485, .456, .406])[None, :, None, None]
    std = tensor.new_tensor([.229, .224, .225])[None, :, None, None]
    return (tensor - mean) / std


def extract_features(rows, members, ns, cache_dir, split, views=1):
    """View-major order, exact instance IDs and checkpoint hashes in cache key."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    provenance = dict(version=VERSION, split=split, views=views,
                      manifest=hashlib.sha256((ROOT / 'data/classification_manifest.csv').read_bytes()).hexdigest(),
                      ids=[r['instance_id'] for r in rows])
    pixel_signature = hashlib.sha256(json.dumps(provenance, sort_keys=True).encode()).hexdigest()[:12]
    pixel_file = cache_dir / f'{split}_pixels_{pixel_signature}.npy'
    if not pixel_file.exists():
        partial = pixel_file.with_suffix('.partial.npy')
        pixels = np.lib.format.open_memmap(partial, mode='w+', dtype=np.uint8, shape=(views * len(rows), 384, 384, 3))
        def prepare(item):
            i, row = item
            with Image.open(ROOT / 'data' / row['crop_path']) as image:
                image = image.convert('RGB')
                return i, [image_pixels(image, view, ns) for view in range(views)]
        with ThreadPoolExecutor(max_workers=4) as pool:
            for start in range(0, len(rows), 16):
                for i, prepared in pool.map(prepare, list(enumerate(rows))[start:start+16]):
                    for view, pixels_view in enumerate(prepared):
                        pixels[view * len(rows) + i] = pixels_view
                if start % 64 == 0:
                    print(f'Prepare pixels {split}: {min(start+16, len(rows))}/{len(rows)}', flush=True)
        pixels.flush()
        del pixels
        partial.replace(pixel_file)
    pixels = np.load(pixel_file, mmap_mode='r')
    features, raw = [], []
    for member in members:
        signature = hashlib.sha256(json.dumps(dict(provenance, model=member['sha256']), sort_keys=True).encode()).hexdigest()
        file = cache_dir / f'{split}_{member["architecture"]}_{member["seed"]}_{signature[:12]}.npz'
        if file.exists():
            data = np.load(file)
            features.append(data['features'])
            raw.append({k: data[k] for k in ('l1_logits', 'l2_logits', 'l2_evidence_logits')})
            continue
        model, device, _ = ns['load_model'](member['architecture'], member['checkpoint'], ns['ontology'])
        arrays = {k: [] for k in ('features', 'l1_logits', 'l2_logits', 'l2_evidence_logits')}
        for start in range(0, len(pixels), 16):
            with torch.inference_mode():
                x = normalized_batch(pixels[start:start+16], device)
                f = model.backbone(x)
                for key, value in zip(arrays, (f, model.l1_head(f), model.l2_head(f), model.evidence_head(f))):
                    arrays[key].append(value.cpu().numpy())
            if start % 512 == 0:
                print(f'Extract {split} {member["architecture"]}/{member["seed"]}: {start}/{len(pixels)} on {device}', flush=True)
        data = {k: np.concatenate(v) for k, v in arrays.items()}
        np.savez_compressed(file, **data)
        features.append(data['features'])
        raw.append({k: data[k] for k in ('l1_logits', 'l2_logits', 'l2_evidence_logits')})
        del model
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        print(f'Features: {split}, {member["architecture"]}, seed {member["seed"]}, {len(data["features"])} views', flush=True)
    return features, raw


def feature_matrix(features, positions):
    # Normalize each representation separately so 1280 dimensions do not swamp 512.
    return np.concatenate([normalize(features[i]) for i in positions], axis=1) / np.sqrt(len(positions))


class BalancedHeads:
    """Learn new L1, global-leaf and evidence classifiers on frozen representations."""
    def __init__(self, kind, c, parent_indices):
        self.kind, self.c, self.parents = kind, c, np.asarray(parent_indices)

    def fit(self, x, y1, y2, groups=None):
        known = y2 >= 0
        def model(target, target_groups):
            if self.kind == 'logistic':
                return LogisticRegression(C=self.c, class_weight='balanced', max_iter=2500, solver='lbfgs')
            estimator = SVC(C=self.c, kernel='rbf', gamma='scale', class_weight='balanced', probability=False)
            if self.kind == 'calibrated_svm':
                if target_groups is None:
                    raise ValueError('Calibration requires artifact groups including augmented copies.')
                folds = list(StratifiedGroupKFold(n_splits=3, shuffle=True, random_state=20261103).split(
                    np.zeros(len(target)), target, target_groups))
                for fit, held in folds:
                    assert not set(target_groups[fit]) & set(target_groups[held])
                return CalibratedClassifierCV(estimator, method='sigmoid', cv=folds, ensemble=False, n_jobs=1)
            return estimator
        groups = np.asarray(groups) if groups is not None else None
        self.l1 = model(y1, groups).fit(x, y1)
        self.leaf = model(y2[known], groups[known] if groups is not None else None).fit(x[known], y2[known])
        self.evidence = model(known.astype(int), groups).fit(x, known.astype(int))
        assert np.array_equal(self.l1.classes_, np.arange(4))
        assert np.array_equal(self.leaf.classes_, np.arange(11))
        return self

    def probabilities(self, estimator, x):
        if hasattr(estimator, 'predict_proba'):
            return estimator.predict_proba(x)
        decision = estimator.decision_function(x)
        if decision.ndim == 1:
            decision = np.stack([-decision / 2, decision / 2], axis=1)
        # SVM scores are not calibrated probabilities; fitted gate must be assessed out of fold.
        return softmax(decision)

    def outputs(self, x):
        leaf = self.probabilities(self.leaf, x)
        parent_from_leaf = np.column_stack([leaf[:, self.parents == i].sum(axis=1) for i in range(4)])
        p1 = .5 * self.probabilities(self.l1, x) + .5 * parent_from_leaf
        return dict(l1_logits=np.log(np.clip(p1, 1e-12, 1)),
                    l2_logits=np.log(np.clip(leaf, 1e-12, 1)),
                    l2_evidence_logits=np.log(np.clip(self.probabilities(self.evidence, x), 1e-12, 1)))


def add_labels(out, rows, indices, views=1):
    out = dict(out)
    out['y1'] = np.tile([indices['l1_to_idx'][r['level_1_code']] for r in rows], views)
    out['y2'] = np.tile([indices['l2_to_idx'].get(r['level_2_code'], -100) for r in rows], views)
    out['indices'] = np.arange(len(rows) * views)
    return out


def decision_arrays(outputs, indices):
    p1 = softmax(outputs['l1_logits'])
    l1 = p1.argmax(axis=1)
    candidate, confidence = np.zeros(len(l1), dtype=int), np.zeros(len(l1))
    for parent_idx, parent in enumerate(indices['l1_codes']):
        children = np.array([indices['l2_to_idx'][c] for c in indices['l2_codes'] if indices['l2_parent'][c] == parent])
        mask = l1 == parent_idx
        conditional = softmax(outputs['l2_logits'][mask][:, children])
        candidate[mask] = children[conditional.argmax(axis=1)]
        confidence[mask] = conditional.max(axis=1) * p1[mask, parent_idx]
    return l1, candidate, confidence, p1.max(axis=1), softmax(outputs['l2_evidence_logits'])[:, 1]


def score_decisions(outputs, candidate, accepted, l1, l1_accepted):
    gold = outputs['y2']
    known = gold >= 0
    correct = accepted & (candidate == gold)
    per_class = []
    for c in range(11):
        tp, pred, support = int((correct & (gold == c)).sum()), int((accepted & (candidate == c)).sum()), int((gold == c).sum())
        precision, recall = tp / max(pred, 1), tp / max(support, 1)
        per_class.append(dict(code=f'C2.{c+1}', support=support, predicted=pred, correct=tp,
                              precision=precision, recall=recall, f1=2*tp/max(pred+support, 1)))
    return dict(l1_accuracy=float((l1 == outputs['y1']).mean()),
                l1_selective_accuracy=float(((l1 == outputs['y1']) & l1_accepted).sum()/max(l1_accepted.sum(), 1)),
                l1_coverage=float(l1_accepted.mean()),
                macro_f1=float(np.mean([c['f1'] for c in per_class])),
                macro_recall=float(np.mean([c['recall'] for c in per_class])),
                precision=float(correct.sum()/max(accepted.sum(), 1)),
                blank_acceptance=float((accepted & ~known).sum()/max((~known).sum(), 1)),
                exact_recall=float(correct.sum()/max(known.sum(), 1)),
                accepted=int(accepted.sum()), correct=int(correct.sum()),
                nonzero_classes=sum(c['correct'] > 0 for c in per_class), per_class=per_class)


def apply_gate(outputs, indices, gate):
    l1, candidate, confidence, l1_conf, evidence = decision_arrays(outputs, indices)
    l1_ok = l1_conf >= gate['l1_threshold']
    cutoffs = np.array([gate['class_thresholds'].get(f'C2.{c+1}', gate['l2_threshold']) for c in candidate])
    accepted = l1_ok & (confidence >= cutoffs) & (evidence >= gate['evidence_threshold'])
    return score_decisions(outputs, candidate, accepted, l1, l1_ok), (candidate, accepted, l1, l1_ok)


def select_gate(outputs, indices):
    """Pooled gate: avoid declaring a rare class unusable from three examples.

    Target remains >=90% pooled precision, <=10% blank acceptance. This does NOT
    promise 90% for every class. Candidate thresholds are fixed before test access.
    """
    l1, candidate, conf, l1_conf, evidence = decision_arrays(outputs, indices)
    l1_options = []
    for cutoff in (0., .4, .5, .6, .7):
        mask = l1_conf >= cutoff
        if mask.mean() >= .75 and ((l1 == outputs['y1']) & mask).sum()/max(mask.sum(), 1) >= .90:
            l1_options.append(cutoff)
    l1_cutoff = min(l1_options) if l1_options else 0.
    best = None
    for threshold in np.arange(.1, 1., .05):
        for evidence_cutoff in (0., .5, .7, .85, .95):
            accepted = (l1_conf >= l1_cutoff) & (conf >= threshold) & (evidence >= evidence_cutoff)
            metrics = score_decisions(outputs, candidate, accepted, l1, l1_conf >= l1_cutoff)
            if metrics['accepted'] >= 6 and metrics['precision'] >= .90 and metrics['blank_acceptance'] <= .10:
                ranking = (metrics['macro_f1'], metrics['macro_recall'], metrics['precision'])
                if best is None or ranking > best[0]:
                    best = (ranking, dict(l1_threshold=l1_cutoff, l2_threshold=float(threshold), evidence_threshold=evidence_cutoff,
                                          class_thresholds={f'C2.{c+1}': float(threshold) for c in range(11)}), metrics)
    if best is None:
        gate = dict(l1_threshold=l1_cutoff, l2_threshold=1.0001, evidence_threshold=0., class_thresholds={})
        return gate, apply_gate(outputs, indices, gate)[0]
    return best[1], best[2]


def crossfit_gate(outputs, indices, folds):
    collected = [np.empty(len(outputs['y1']), dtype=dtype) for dtype in (int, bool, int, bool)]
    for fit, held in folds:
        gate, _ = select_gate(subset(outputs, fit), indices)
        _, decisions = apply_gate(subset(outputs, held), indices, gate)
        for target, source in zip(collected, decisions):
            target[held] = source
    return score_decisions(outputs, *collected)


def promote_allowed(metrics, crossfit, baseline):
    """Predeclared constraints, never changed after reading test."""
    return (metrics['macro_f1'] >= baseline['macro_f1'] + .02
            and metrics['macro_recall'] > baseline['macro_recall']
            and metrics['l1_accuracy'] >= baseline['l1_accuracy'] - 1/136
            and metrics['precision'] >= max(.90, baseline['precision'] - .05)
            and metrics['blank_acceptance'] <= .10
            and crossfit['precision'] >= .85
            and crossfit['blank_acceptance'] <= .15
            and crossfit['macro_f1'] >= baseline['macro_f1']
            and metrics['nonzero_classes'] > baseline['nonzero_classes'])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-dir', type=Path)
    parser.add_argument('--extended', action='store_true', help='Train group-calibrated heads and predeclared 50/50 baseline blends')
    args = parser.parse_args()
    torch.set_num_threads(4)
    ns = utilities()
    snapshot = ns['load_snapshot']()
    audit = ns['audit_snapshot'](snapshot)
    indices = ns['class_index_maps'](snapshot['ontology'])
    members, summary = member_list()
    run = args.run_dir or ROOT / 'outputs/quality_v2' / datetime.now(ZoneInfo('Asia/Bangkok')).strftime('%Y%m%d_%H%M%S')
    run.mkdir(parents=True, exist_ok=True)
    print('RUN', run, flush=True)
    write_json(ROOT / 'outputs/quality_v2_status.json', dict(state='running', run=str(run), pid=os.getpid()))
    protocol = dict(version=VERSION, baseline=str(BASE), manifest_sha256=audit['manifest_sha256'],
                    train_views=4, groups=['resnet18', 'mobilenet_v2', 'all'],
                    classifiers={'logistic': [.1, 1., 10.], 'rbf_svm': [1., 10., 100.]},
                    selection='validation only; group-crossfit of gate; test after locked selection',
                    limitations='Frozen backbones were selected on historical validation. Gate crossfit is not nested CV of the full pipeline.',
                    promotion_rule='macro-F1 +.02; macro-recall increase; L1 accuracy lose <=1/136; pooled precision >=max(.90, baseline-.05); blank acceptance <=.10; crossfit precision >=.85, blank<=.15, F1>=baseline; more nonzero classes')
    if args.extended:
        protocol.update(groups=['resnet18', 'all'], classifiers={'logistic': [10., 100.], 'calibrated_svm': [1., 10.]},
                        baseline_blends=[0., .5], calibration='3 artifact-group folds within train; augmented views stay together')
    if (run / 'protocol.json').exists() and read_json(run / 'protocol.json') != protocol:
        raise RuntimeError('Cannot resume with a different protocol')
    write_json(run / 'protocol.json', protocol)
    (run / 'quality_v2_source.py').write_bytes(Path(__file__).read_bytes())
    rows = {split: [r for r in snapshot['rows'] if r['split'] == split] for split in ('train', 'val', 'test')}
    train_features, _ = extract_features(rows['train'], members, ns, ROOT / 'cache/quality_v2/features', 'train', 4)
    val_features, val_raw = extract_features(rows['val'], members, ns, ROOT / 'cache/quality_v2/features', 'val')
    baseline_members = summary['image_selection']['members']
    def baseline_outputs(raw, split):
        calibrated = []
        for m in baseline_members:
            pos = next(i for i, full in enumerate(members) if (m['architecture'], m['seed']) == (full['architecture'], full['seed']))
            calibrated.append(ns['apply_temperatures'](add_labels(raw[pos], rows[split], indices), m['temperatures']))
        return ns['average_hierarchical_outputs'](calibrated, indices)
    baseline_out = baseline_outputs(val_raw, 'val')
    baseline_gate = read_json(BASE / 'deployment/selection.json')['selected']
    assert baseline_gate['image_weight'] == 1., 'Baseline adapter requires image-only original deployment.'
    baseline_metrics = apply_gate(baseline_out, indices, baseline_gate)[0]
    write_json(run / 'baseline_validation.json', baseline_metrics)
    strata = [r['level_2_code'] or ('blank_' + r['level_1_code']) for r in rows['val']]
    groups = [r['artifact_id'] for r in rows['val']]
    folds = list(StratifiedGroupKFold(n_splits=3, shuffle=True, random_state=20261103).split(np.zeros(len(groups)), strata, groups))
    for fit, held in folds:
        assert not set(np.asarray(groups)[fit]) & set(np.asarray(groups)[held])
    write_json(run / 'gate_folds.json', [{k: [rows['val'][int(i)]['instance_id'] for i in v] for k, v in [('fit', fit), ('held', held)]} for fit, held in folds])
    parent_indices = [indices['l1_to_idx'][indices['l2_parent'][code]] for code in indices['l2_codes']]
    labels = add_labels({}, rows['train'], indices, 4)
    trials, candidates = [], {}
    def register(name, out, state):
        gate, metrics = select_gate(out, indices)
        crossfit = crossfit_gate(out, indices, folds)
        allowed = promote_allowed(metrics, crossfit, baseline_metrics)
        record = dict(name=name, gate=gate, validation=metrics, crossfit=crossfit, eligible=allowed)
        trials.append(record)
        candidates[name] = (out, state)
        write_json(run / 'validation_trials.json', trials)
        joblib.dump(state, run / (name + '.joblib'))
        print(f'{name}: F1={metrics["macro_f1"]:.3f}, precision={metrics["precision"]:.3f}, classes={metrics["nonzero_classes"]}, crossfit F1={crossfit["macro_f1"]:.3f}, eligible={allowed}', flush=True)
    register('baseline_rethreshold', baseline_out, dict(kind='baseline'))
    for group, positions in [('resnet18', [0, 1, 2]), ('mobilenet_v2', [3, 4, 5]), ('all', list(range(6)))]:
        if group not in protocol['groups']:
            continue
        x = feature_matrix(train_features, positions)
        xv = feature_matrix(val_features, positions)
        for kind, cs in protocol['classifiers'].items():
            for c in cs:
                name = f'{group}_{kind}_{c:g}'
                with threadpool_limits(limits=4):
                    heads = BalancedHeads(kind, c, parent_indices).fit(x, labels['y1'], labels['y2'],
                        np.tile([r['artifact_id'] for r in rows['train']], 4))
                    out = add_labels(heads.outputs(xv), rows['val'], indices)
                state = dict(kind='balanced_heads', heads=heads, positions=positions, members=members,
                             manifest_sha256=audit['manifest_sha256'], baseline=str(BASE), version=VERSION)
                register(name, out, state)
                if args.extended:
                    mixed = ns['average_hierarchical_outputs']([out, baseline_out], indices, [.5, .5])
                    register(name + '_blend', mixed, dict(state, blend_baseline=.5, baseline_members=baseline_members))
    eligible = [trial for trial in trials if trial['eligible'] and trial['name'] != 'baseline_rethreshold']
    chosen = max(eligible, key=lambda t: (t['crossfit']['macro_f1'], t['validation']['macro_f1'])) if eligible else None
    selection = dict(chosen=chosen, promoted=False, status='selected' if chosen else 'no_candidate_passed',
                     baseline_validation=baseline_metrics, test_used_for_selection=False)
    write_json(run / 'selection.json', selection)
    # Selection is now locked. Historical test is used only for a descriptive audit.
    if chosen:
        state = candidates[chosen['name']][1]
        joblib.dump(state, run / 'selected_model.joblib')
        test_features, test_raw = extract_features(rows['test'], members, ns, ROOT / 'cache/quality_v2/features', 'test')
        out = add_labels(state['heads'].outputs(feature_matrix(test_features, state['positions'])), rows['test'], indices)
        baseline_test = baseline_outputs(test_raw, 'test')
        if state.get('blend_baseline'):
            out = ns['average_hierarchical_outputs']([out, baseline_test], indices, [.5, .5])
        metrics, decisions = apply_gate(out, indices, chosen['gate'])
        write_json(run / 'test_metrics.json', metrics)
        write_json(run / 'baseline_test_metrics.json', apply_gate(baseline_test, indices, baseline_gate)[0])
        ns['save_test_predictions'](run / 'test_predictions.csv', snapshot['rows'], out, indices,
                                   chosen['gate']['l2_threshold'], chosen['gate']['l1_threshold'], None,
                                   chosen['gate']['evidence_threshold'], chosen['gate']['class_thresholds'])
        with (run / 'per_class_end_to_end.csv').open('w', encoding='utf-8-sig', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=list(metrics['per_class'][0]))
            writer.writeheader(); writer.writerows(metrics['per_class'])
        # Activation is a separate, verified operation after checking inference parity.
        print('Selected candidate saved; awaiting inference-parity verification before activation.', flush=True)
    write_json(ROOT / 'outputs/quality_v2_status.json', dict(state='completed', run=str(run), selected=chosen['name'] if chosen else None))
    print('COMPLETED', json.dumps(selection, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    # Avoid pickles referencing __main__ when the notebook loads trained heads later.
    from quality_v2 import main
    main()
