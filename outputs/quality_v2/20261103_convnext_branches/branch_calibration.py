"""Low-dimensional hierarchical calibration: one L2 cutoff per parent branch.

Four thresholds share a pooled precision/blank constraint. This avoids fitting
eleven thresholds from tiny classes; group crossfit must still check stability.
"""
import numpy as np
from quality_v2 import decision_arrays, apply_gate, score_decisions, subset


def select_branch_gate(outputs, indices, min_precision=.925):
    l1, candidate, conf, l1_conf, evidence = decision_arrays(outputs, indices)
    gold = outputs['y2']; blank = gold < 0
    candidates_l1 = []
    for threshold in (0., .4, .5, .6, .7):
        mask = l1_conf >= threshold
        if mask.mean() >= .75 and ((l1 == outputs['y1']) & mask).sum()/max(mask.sum(),1) >= .9:
            candidates_l1.append(threshold)
    l1_threshold = min(candidates_l1) if candidates_l1 else 0.
    thresholds = np.r_[np.arange(.1, 1., .05), 1.0001]
    dims = len(thresholds)
    parents = np.array([indices['l1_to_idx'][indices['l2_parent'][c]] for c in indices['l2_codes']])
    best = None
    for evidence_threshold in (0., .5, .7, .85, .95):
        tables = []
        for parent in range(4):
            table = []
            for cutoff in thresholds:
                mask = (l1==parent) & (l1_conf>=l1_threshold) & (conf>=cutoff) & (evidence>=evidence_threshold)
                correct = mask & (candidate==gold)
                f1_sum = 0.
                for leaf in np.flatnonzero(parents==parent):
                    support = int((gold==leaf).sum())
                    count = int((mask & (candidate==leaf)).sum())
                    tp = int((correct & (gold==leaf)).sum())
                    f1_sum += 2*tp/max(support+count,1)
                table.append([int(mask.sum()),int(correct.sum()),int((mask & blank).sum()),f1_sum])
            tables.append(np.array(table))
        totals = []
        for field in range(4):
            total = 0.
            for parent in range(4):
                shape = [1]*4; shape[parent]=dims
                total = total + tables[parent][:,field].reshape(shape)
            totals.append(total)
        accepted, correct, blanks, score = totals
        precision = correct/np.maximum(accepted,1)
        valid = (accepted>=6) & (precision>=min_precision) & (blanks<=.10*max(blank.sum(),1))
        ranking = np.where(valid, score/11 + 1e-7*precision, -1.)
        flat = int(ranking.argmax())
        if ranking.flat[flat] < 0: continue
        position = np.unravel_index(flat,ranking.shape)
        if best is None or ranking.flat[flat]>best[0]:
            cutoffs = [float(thresholds[p]) for p in position]
            gate = dict(l1_threshold=l1_threshold,l2_threshold=0.,evidence_threshold=evidence_threshold,
                        class_thresholds={code:cutoffs[parents[i]] for i,code in enumerate(indices['l2_codes'])},
                        branch_thresholds=dict(zip(indices['l1_codes'],cutoffs)))
            best = (float(ranking.flat[flat]),gate)
    if best is None:
        gate = dict(l1_threshold=l1_threshold,l2_threshold=1.0001,evidence_threshold=0.,class_thresholds={})
    else: gate = best[1]
    return gate,apply_gate(outputs,indices,gate)[0]


def crossfit_branch_gate(outputs,indices,folds,min_precision=.925):
    collected=[np.empty(len(outputs['y1']),dtype=dtype) for dtype in (int,bool,int,bool)]
    for fit,held in folds:
        gate,_=select_branch_gate(subset(outputs,fit),indices,min_precision)
        _,decisions=apply_gate(subset(outputs,held),indices,gate)
        for target,source in zip(collected,decisions): target[held]=source
    return score_decisions(outputs,*collected)
