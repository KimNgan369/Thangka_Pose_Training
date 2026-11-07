"""Predeclared comparison of global and four-branch gates after CNN training.

All selection reads validation only. Prior test results are never loaded here.
"""
from quality_v2 import *
from quality_convnext import PostureConvNeXt, cached_pixels, outputs_from_model
from branch_calibration import select_branch_gate, crossfit_branch_gate


def main():
    torch.set_num_threads(4)
    model_run=ROOT/'outputs/quality_v2/20261103_convnext'
    run=ROOT/'outputs/quality_v2/20261103_convnext_branches'
    run.mkdir(parents=True,exist_ok=True)
    protocol=read_json(model_run/'protocol.json')
    protocol.update(model_run=str(model_run.relative_to(ROOT)), calibration=['global','four_parent_branches'],
                    baseline_gate_ablation=True, prior_test_metrics_used=False)
    write_json(run/'protocol.json',protocol)
    for source in ('quality_convnext.py','quality_v2.py','branch_calibration.py','calibrate_convnext_branches.py'):
        (run/source).write_bytes((ROOT/source).read_bytes())
    ns=utilities();snapshot=ns['load_snapshot']();indices=ns['class_index_maps'](ns['ontology'])
    val_rows=[r for r in snapshot['rows'] if r['split']=='val']
    members,summary=member_list()
    _,raw=extract_features(val_rows,members,ns,ROOT/'cache/quality_v2/features','val')
    def baseline_outputs(raw,rows):
        out=[]
        for m in summary['image_selection']['members']:
            i=next(i for i,x in enumerate(members) if (x['architecture'],x['seed'])==(m['architecture'],m['seed']))
            out.append(ns['apply_temperatures'](add_labels(raw[i],rows,indices),m['temperatures']))
        return ns['average_hierarchical_outputs'](out,indices)
    old_out=baseline_outputs(raw,val_rows)
    old_gate=read_json(BASE/'deployment/selection.json')['selected']
    baseline=apply_gate(old_out,indices,old_gate)[0]
    groups=np.array([r['artifact_id'] for r in val_rows])
    folds=list(StratifiedGroupKFold(n_splits=3,shuffle=True,random_state=20261103).split(
        np.zeros(len(val_rows)),[r['level_2_code'] or 'blank' for r in val_rows],groups))
    for fit,held in folds: assert not set(groups[fit]) & set(groups[held])
    write_json(run/'gate_folds.json',[{k:[val_rows[int(i)]['instance_id'] for i in v]
               for k,v in [('fit',fit),('held',held)]} for fit,held in folds])
    validation=[]
    for seed in protocol['seeds']:
        folder=model_run/f'convnext_tiny_seed{seed}'
        complete=read_json(folder/'complete.json')
        if complete['signature']['smoke']:raise RuntimeError('Smoke weights cannot be selected')
        validation.append(dict(np.load(folder/'validation_outputs.npz')))
    new_out=ns['average_hierarchical_outputs'](validation,indices)
    trials=[]
    for weight in [0.,.25,.5,1.]:
        out=ns['average_hierarchical_outputs']([new_out,old_out],indices,[1-weight,weight])
        for style,selector,crossfitter in [('global',select_gate,crossfit_gate),('branches',select_branch_gate,crossfit_branch_gate)]:
            gate,metrics=selector(out,indices,.925)
            crossfit=crossfitter(out,indices,folds,.925)
            record=dict(name=f'convnext_{style}_baseline{weight}',baseline_weight=weight,calibration=style,
                        gate=gate,validation=metrics,crossfit=crossfit,
                        eligible=promote_allowed(metrics,crossfit,baseline))
            trials.append(record)
            print(record['name'],json.dumps({k:v for k,v in metrics.items() if k!='per_class'}),
                  'crossfit',crossfit['macro_f1'],crossfit['precision'],'eligible',record['eligible'],flush=True)
    write_json(run/'validation_trials.json',trials)
    eligible=[t for t in trials if t['eligible']]
    chosen=max(eligible,key=lambda t:(t['crossfit']['macro_f1'],t['validation']['macro_f1'])) if eligible else None
    selection=dict(chosen=chosen,promoted=False,status='selected' if chosen else 'no_candidate_passed',
                   baseline_validation=baseline,test_used_for_selection=False)
    write_json(run/'selection.json',selection)
    if chosen:
        test_rows=[r for r in snapshot['rows'] if r['split']=='test']
        _,raw=extract_features(test_rows,members,ns,ROOT/'cache/quality_v2/features','test')
        old=baseline_outputs(raw,test_rows)
        device='cuda' if torch.cuda.is_available() else 'cpu'
        predictions=[]
        for seed in protocol['seeds']:
            model=PostureConvNeXt().to(device)
            model.load_state_dict(torch.load(model_run/f'convnext_tiny_seed{seed}/best_model.pt',map_location=device,weights_only=True))
            predictions.append(outputs_from_model(model,cached_pixels('test'),test_rows,indices,device))
            del model
            if device=='cuda':torch.cuda.empty_cache()
        new=ns['average_hierarchical_outputs'](predictions,indices)
        weight=chosen['baseline_weight']
        out=ns['average_hierarchical_outputs']([new,old],indices,[1-weight,weight])
        np.savez_compressed(run/'test_outputs.npz',**out)
        metrics,_=apply_gate(out,indices,chosen['gate'])
        write_json(run/'test_metrics.json',metrics)
        write_json(run/'baseline_test_metrics.json',apply_gate(old,indices,old_gate)[0])
        gate=chosen['gate']
        ns['save_test_predictions'](run/'test_predictions.csv',snapshot['rows'],out,indices,
            gate['l2_threshold'],gate['l1_threshold'],None,gate['evidence_threshold'],gate['class_thresholds'])
        with (run/'per_class_end_to_end.csv').open('w',encoding='utf-8-sig',newline='') as stream:
            writer=csv.DictWriter(stream,fieldnames=list(metrics['per_class'][0]));writer.writeheader();writer.writerows(metrics['per_class'])
    write_json(ROOT/'outputs/quality_v2_status.json',dict(state='completed',run=str(run),selected=chosen['name'] if chosen else None))
    print('COMPLETED',chosen['name'] if chosen else 'No candidate passed',flush=True)


if __name__=='__main__':main()
