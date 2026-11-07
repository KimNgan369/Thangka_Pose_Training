"""Fine-tune ConvNeXt for the existing two-level posture task.

Train-only balanced sampling, full-body input, blank-L2 masking, resumable AdamW.
Historical test is read only after a validation-selected candidate passes gates.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import time

import numpy as np
import torch
from torch import nn
from torch.nn import functional as F
from torchvision.models import convnext_tiny
from sklearn.model_selection import StratifiedGroupKFold

from quality_v2 import (ROOT, BASE, read_json, write_json, utilities, normalized_batch,
                        extract_features, member_list, add_labels, select_gate,
                        crossfit_gate, apply_gate, promote_allowed)


class PostureConvNeXt(nn.Module):
    def __init__(self, pretrained=False):
        super().__init__()
        self.backbone = convnext_tiny(weights=None, stochastic_depth_prob=.1)
        if pretrained:
            path = ROOT / 'pretrained/convnext_tiny-983f1562.pth'
            if not hashlib.sha256(path.read_bytes()).hexdigest().startswith('983f1562'):
                raise ValueError('Invalid pretrained checkpoint hash')
            self.backbone.load_state_dict(torch.load(path, map_location='cpu', weights_only=True))
        self.backbone.classifier[2] = nn.Identity()
        self.dropout = nn.Dropout(.2)
        self.l1 = nn.Linear(768, 4)
        self.l2 = nn.Linear(768, 11)
        self.evidence = nn.Linear(768, 2)

    def forward(self, x):
        f = self.dropout(self.backbone(x))
        return self.l1(f), self.l2(f), self.evidence(f)


def outputs_from_model(model, pixels, rows, indices, device='cuda'):
    model.eval()
    values = [[], [], []]
    with torch.inference_mode():
        for start in range(0, len(pixels), 4):
            with torch.autocast(device_type=device, enabled=device == 'cuda'):
                out = model(normalized_batch(pixels[start:start+4], device))
            for destination, source in zip(values, out):
                destination.append(source.float().cpu().numpy())
    raw = dict(zip(('l1_logits', 'l2_logits', 'l2_evidence_logits'), [np.concatenate(v) for v in values]))
    # Parent mass from the globally trained leaves supplements the separate L1 head.
    p1 = torch.softmax(torch.tensor(raw['l1_logits']), 1).numpy()
    leaves = torch.softmax(torch.tensor(raw['l2_logits']), 1).numpy()
    parent = np.zeros_like(p1)
    for c, code in enumerate(indices['l2_codes']):
        parent[:, indices['l1_to_idx'][indices['l2_parent'][code]]] += leaves[:, c]
    raw['l1_logits'] = np.log(np.clip(.5*p1 + .5*parent, 1e-12, 1))
    return add_labels(raw, rows, indices) if rows is not None else raw


def cached_pixels(split):
    manifest = ROOT / 'data/classification_manifest.csv'
    with manifest.open(encoding='utf-8-sig', newline='') as stream:
        rows = [r for r in csv.DictReader(stream) if r['split'] == split]
    provenance = dict(version=1, split=split, views=4 if split=='train' else 1,
                      manifest=hashlib.sha256(manifest.read_bytes()).hexdigest(), ids=[r['instance_id'] for r in rows])
    signature = hashlib.sha256(json.dumps(provenance, sort_keys=True).encode()).hexdigest()[:12]
    path = ROOT / 'cache/quality_v2/features' / f'{split}_pixels_{signature}.npy'
    return np.load(path, mmap_mode='r')


def train_one(run, seed, epochs, ns, snapshot, indices, smoke=False):
    target = run / f'convnext_tiny_seed{seed}'
    target.mkdir(parents=True, exist_ok=True)
    signature = dict(seed=seed, epochs=epochs, smoke=smoke, batch=2, accumulation=8,
                     manifest=hashlib.sha256((ROOT/'data/classification_manifest.csv').read_bytes()).hexdigest(),
                     source=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    if (target/'complete.json').exists():
        if read_json(target/'complete.json')['signature'] != signature:
            raise RuntimeError('Training signature changed')
        return dict(np.load(target/'validation_outputs.npz'))
    torch.manual_seed(seed); np.random.seed(seed)
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    model = PostureConvNeXt(pretrained=True).to(device)
    optimizer = torch.optim.AdamW([
        dict(params=model.backbone.parameters(), lr=2e-5),
        dict(params=list(model.l1.parameters())+list(model.l2.parameters())+list(model.evidence.parameters()), lr=3e-4)
    ], weight_decay=.001)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs, eta_min=1e-6)
    scaler = torch.amp.GradScaler('cuda', enabled=device=='cuda')
    rows = [r for r in snapshot['rows'] if r['split']=='train']
    val_rows = [r for r in snapshot['rows'] if r['split']=='val']
    train_pixels, val_pixels = cached_pixels('train'), cached_pixels('val')
    labels = add_labels({}, rows, indices)
    y1 = torch.tensor(labels['y1'], dtype=torch.long, device=device)
    y2 = torch.tensor(labels['y2'], dtype=torch.long, device=device)
    known = labels['y2'] >= 0
    counts = np.bincount(labels['y2'][known], minlength=11)
    probabilities = np.zeros(len(rows))
    probabilities[known] = 1/np.sqrt(counts[labels['y2'][known]])
    probabilities[known] *= .8/probabilities[known].sum()
    probabilities[~known] = .2/(~known).sum()
    state_path = target/'last_training_state.pt'
    history, best, waits, start_epoch = [], -1., 0, 1
    if state_path.exists():
        state = torch.load(state_path, map_location=device, weights_only=False)
        if state['signature'] != signature:
            raise RuntimeError('Resume settings/source mismatch')
        model.load_state_dict(state['model']); optimizer.load_state_dict(state['optimizer'])
        scheduler.load_state_dict(state['scheduler']); scaler.load_state_dict(state['scaler'])
        history, best, waits = state['history'], state['best'], state['waits']
        start_epoch = state['epoch']+1
        torch.set_rng_state(state['rng'].cpu())
        if device=='cuda': torch.cuda.set_rng_state_all([x.cpu() for x in state['cuda_rng']])
        del state
    for epoch in range(start_epoch, epochs+1):
        if epoch > 24 and waits >= 16:
            break
        begin = time.monotonic()
        model.train()
        for p in model.backbone.parameters(): p.requires_grad = smoke or epoch > 3
        if epoch <= 10 and not smoke:
            for p in model.backbone.features[:4].parameters(): p.requires_grad = False
        if epoch <= 3 and not smoke: model.backbone.eval()
        rng = np.random.default_rng(seed+epoch)
        sample = rng.choice(len(rows), size=32 if smoke else len(rows), replace=True, p=probabilities)
        views = rng.integers(0, 4, size=len(sample))
        total, batches = 0., int(np.ceil(len(sample)/2))
        optimizer.zero_grad(set_to_none=True)
        for step in range(batches):
            batch_indices = sample[step*2:step*2+2]
            pixel_indices = batch_indices + views[step*2:step*2+2]*len(rows)
            x = normalized_batch(train_pixels[pixel_indices], device)
            gold1, gold2 = y1[batch_indices], y2[batch_indices]
            mask = gold2 >= 0
            with torch.autocast(device_type=device, enabled=device=='cuda'):
                z1, z2, ze = model(x)
                parent_loss = F.cross_entropy(z1.float(), gold1, label_smoothing=.03)
                leaf_loss = F.cross_entropy(z2.float()[mask], gold2[mask], label_smoothing=.03) if mask.any() else z2.sum()*0
                branch_loss = ns['hierarchical_l2_loss'](z2.float(), gold1, gold2, indices, label_smoothing=.03)
                evidence_loss = F.cross_entropy(ze.float(), mask.long())
                loss = parent_loss + leaf_loss + .5*branch_loss + .5*evidence_loss
            group_size = min(8, batches-(step//8)*8)
            scaler.scale(loss/group_size).backward()
            if (step+1)%8 == 0 or step+1 == batches:
                scaler.unscale_(optimizer); torch.nn.utils.clip_grad_norm_(model.parameters(), 3.)
                scaler.step(optimizer); scaler.update(); optimizer.zero_grad(set_to_none=True)
            total += float(loss.detach())
            if (step+1)%100 == 0:
                print(f'ConvNeXt {seed} epoch {epoch}, batch {step+1}/{batches}', flush=True)
        out = outputs_from_model(model, val_pixels, val_rows, indices, device)
        score = ns['quality_selection_score'](out, indices)
        quality = ns['metrics_from_outputs'](out, indices)
        if score > best + 1e-6:
            best, waits = score, 0
            torch.save({k: v.detach().cpu() for k,v in model.state_dict().items()}, target/'best_model.pt')
            np.savez_compressed(target/'validation_outputs.npz', **out)
        else:
            waits += 1
        scheduler.step()
        record = dict(epoch=epoch, loss=total/batches, score=score, best=best,
                      l1_accuracy=quality['l1']['accuracy'], l1_macro_f1=quality['l1']['macro_f1'],
                      seconds=time.monotonic()-begin)
        history.append(record)
        write_json(target/'history.json', history)
        temporary = target/'last_training_state.tmp'
        torch.save(dict(signature=signature, model=model.state_dict(), optimizer=optimizer.state_dict(),
                        scheduler=scheduler.state_dict(), scaler=scaler.state_dict(), epoch=epoch,
                        best=best, waits=waits, history=history, rng=torch.get_rng_state(),
                        cuda_rng=torch.cuda.get_rng_state_all() if device=='cuda' else []), temporary)
        temporary.replace(state_path)
        write_json(ROOT/'outputs/quality_convnext_status.json', dict(state='training', run=str(run), seed=seed, **record))
        print(json.dumps(dict(seed=seed, **record)), flush=True)
    write_json(target/'complete.json', dict(signature=signature, epochs=len(history), best=best))
    del model, optimizer, scaler
    if device=='cuda': torch.cuda.empty_cache()
    return dict(np.load(target/'validation_outputs.npz'))


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--smoke', action='store_true')
    parser.add_argument('--epochs', type=int, default=60)
    parser.add_argument('--seeds', type=int, nargs='+', default=[20261103, 20261113])
    parser.add_argument('--run-dir', type=Path, default=ROOT/'outputs/quality_v2/20261103_convnext')
    args = parser.parse_args(argv)
    torch.set_num_threads(4)
    ns = utilities(); snapshot = ns['load_snapshot'](); ns['audit_snapshot'](snapshot)
    indices = ns['class_index_maps'](snapshot['ontology'])
    run = args.run_dir.resolve(); run.mkdir(parents=True, exist_ok=True)
    if args.smoke:
        train_one(run, args.seeds[0], 1, ns, snapshot, indices, smoke=True)
        write_json(ROOT/'outputs/quality_convnext_status.json',dict(state='smoke_completed',run=str(run)))
        print('Smoke complete; not a quality result.'); return
    protocol = dict(architecture='convnext_tiny', seeds=args.seeds, epochs=args.epochs,
                    loss='L1 + global L2 + .5 conditional L2 + .5 evidence; blank L2 masked',
                    data='same fixed train/val/test; train-only sqrt inverse-frequency sampler; 384 full body',
                    gate_min_precision=.925, promotion='same constraints as quality_v2, no test selection',
                    ensemble_weights=[0., .25, .5], ensemble='all declared seeds equally weighted')
    if (run/'protocol.json').exists() and read_json(run/'protocol.json') != protocol:
        raise RuntimeError('Protocol mismatch')
    write_json(run/'protocol.json', protocol)
    (run/'quality_convnext_source.py').write_bytes(Path(__file__).read_bytes())
    print('FULL TRAINING', str(run), json.dumps(protocol), flush=True)
    validation = [train_one(run, seed, args.epochs, ns, snapshot, indices) for seed in args.seeds]
    # Compare the fixed multiseed ensemble, not a cherry-picked seed.
    new_out = ns['average_hierarchical_outputs'](validation, indices)
    members, summary = member_list()
    val_rows = [r for r in snapshot['rows'] if r['split']=='val']
    _, raw = extract_features(val_rows, members, ns, ROOT/'cache/quality_v2/features', 'val')
    original_members = summary['image_selection']['members']
    def baseline_outputs(raw, rows):
        outputs=[]
        for m in original_members:
            i = next(i for i,x in enumerate(members) if (x['architecture'],x['seed'])==(m['architecture'],m['seed']))
            outputs.append(ns['apply_temperatures'](add_labels(raw[i], rows, indices), m['temperatures']))
        return ns['average_hierarchical_outputs'](outputs, indices)
    old_out = baseline_outputs(raw, val_rows)
    old_gate = read_json(BASE/'deployment/selection.json')['selected']
    base_metrics = apply_gate(old_out, indices, old_gate)[0]
    folds = list(StratifiedGroupKFold(n_splits=3, shuffle=True, random_state=20261103).split(
        np.zeros(len(val_rows)), [r['level_2_code'] or 'blank' for r in val_rows], [r['artifact_id'] for r in val_rows]))
    trials=[]
    for weight in protocol['ensemble_weights']:
        out = ns['average_hierarchical_outputs']([new_out, old_out], indices, [1-weight, weight])
        gate, metrics = select_gate(out, indices, .925)
        crossfit = crossfit_gate(out, indices, folds, .925)
        trials.append(dict(name=f'convnext_ensemble_baseline{weight}', baseline_weight=weight, gate=gate,
                           validation=metrics, crossfit=crossfit, eligible=promote_allowed(metrics,crossfit,base_metrics)))
    write_json(run/'validation_trials.json', trials)
    eligible=[t for t in trials if t['eligible']]
    chosen=max(eligible,key=lambda t:(t['crossfit']['macro_f1'],t['validation']['macro_f1'])) if eligible else None
    selection=dict(chosen=chosen,promoted=False,status='selected' if chosen else 'no_candidate_passed',
                   baseline_validation=base_metrics,test_used_for_selection=False)
    write_json(run/'selection.json',selection)
    if chosen:
        test_rows=[r for r in snapshot['rows'] if r['split']=='test']
        _, raw=extract_features(test_rows,members,ns,ROOT/'cache/quality_v2/features','test')
        old_test=baseline_outputs(raw,test_rows)
        predictions=[]
        for seed in args.seeds:
            model=PostureConvNeXt().cuda()
            model.load_state_dict(torch.load(run/f'convnext_tiny_seed{seed}/best_model.pt',weights_only=True))
            predictions.append(outputs_from_model(model,cached_pixels('test'),test_rows,indices))
            del model; torch.cuda.empty_cache()
        new_test=ns['average_hierarchical_outputs'](predictions,indices)
        w=chosen['baseline_weight']
        out=ns['average_hierarchical_outputs']([new_test,old_test],indices,[1-w,w])
        metrics,_=apply_gate(out,indices,chosen['gate'])
        write_json(run/'test_metrics.json',metrics)
        write_json(run/'baseline_test_metrics.json',apply_gate(old_test,indices,old_gate)[0])
        gate=chosen['gate']
        ns['save_test_predictions'](run/'test_predictions.csv',snapshot['rows'],out,indices,
            gate['l2_threshold'],gate['l1_threshold'],None,gate['evidence_threshold'],gate['class_thresholds'])
        with (run/'per_class_end_to_end.csv').open('w',encoding='utf-8-sig',newline='') as stream:
            writer=csv.DictWriter(stream,fieldnames=list(metrics['per_class'][0]));writer.writeheader();writer.writerows(metrics['per_class'])
    write_json(ROOT/'outputs/quality_convnext_status.json',dict(state='completed',run=str(run),selected=chosen['name'] if chosen else None))
    print('COMPLETED',json.dumps(selection,ensure_ascii=False),flush=True)


if __name__=='__main__':
    main()
