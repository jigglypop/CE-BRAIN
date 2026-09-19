"""Source-time comparison with all earlier artifact-free target voltage available.

Sensitivity to the masked-history policy, preserving its completed artifacts.
The first command guard and each currently predicted response remain withheld.
"""
import argparse
import importlib.util
import json
import platform
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
spec = importlib.util.spec_from_file_location('masked_timing',HERE/'recovery_source_timing.py')
timing = importlib.util.module_from_spec(spec)
spec.loader.exec_module(timing)
base = timing.base


def prefix_design(raw,window):
    record = timing.observation_design(raw,window)
    left = np.asarray(raw['left_times'],float)
    available = (left+timing.DT<=-.0005+1e-12)|np.asarray(raw['valid'],bool)
    anchors = record['anchors'].copy()
    for pulse in range(12):
        mask = record['pulses']==pulse
        first = record['indices'][mask][0]
        preceding = np.flatnonzero(available[:first])
        assert len(preceding)
        anchors[mask] = preceding[-1]
        assert anchors[mask][0]<first
    record['masked_anchors'] = record['anchors'].copy()
    record['anchors'] = anchors
    record['anchor_left'] = left[anchors]
    record['baseline'] = np.asarray(raw['y'])[anchors]
    record['innovation'] = record['observed']-record['baseline']
    return record


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,default=HERE/'recovery_source_prefix_result.json')
    parser.add_argument('--array-output',type=Path,default=ROOT/'data/local/allen-synphys-analysis/recovery-source-prefix-v1/source_prefix_arrays.npz')
    args = parser.parse_args()
    if args.output.exists() or args.array_output.exists():
        raise FileExistsError('Preserve existing prefix outputs')
    masked_path = HERE/'recovery_source_timing_result.json'
    masked = json.loads(masked_path.read_text(encoding='utf-8'))
    assert base.sha(HERE/'recovery_source_timing.py')==masked['source_sha256']
    assert base.sha(ROOT/'tests/test_recovery_source_timing.py')==masked['test_sha256']
    assert base.sha(ROOT/masked['arrays']['path'])==masked['arrays']['sha256']
    raw,provenance = timing.load_records()
    provenance.update(masked_path=masked_path.relative_to(ROOT).as_posix(),masked_sha256=base.sha(masked_path),
                      masked_source_sha256=masked['source_sha256'],masked_arrays=masked['arrays'])
    arrays,models,profiles,rows,checks = {},{},[],[],[]
    for window in timing.WINDOWS:
        prepared = [prefix_design(record,window) for record in raw]
        for r in prepared:
            key = window+'_'+str(r['sweep'])+'_'+r['target']
            for field in ('indices','pulses','anchors','masked_anchors','left','anchor_left','relative_ms','observed','baseline','innovation'):
                arrays[key+'_'+field] = r[field]
            checks.append(dict(window=window,sweep=r['sweep'],target=r['target'],bins_per_pulse=r['counts'].tolist(),
                changed_anchor_pulses=int(sum(r['anchors'][r['pulses']==pulse][0]!=r['masked_anchors'][r['pulses']==pulse][0] for pulse in range(12))),
                first_anchor_right_ms=float((r['anchor_left'][0]+timing.DT)*1000),
                anchor_to_AP_ms=[float((r['spikes'][pulse]-r['anchor_left'][r['pulses']==pulse][0])*1000) for pulse in range(12)]))
        for target in base.TARGETS:
            records = [r for r in prepared if r['target']==target]
            for shift in timing.SHIFTS_MS:
                best,profile = timing.fit_models(records,shift)
                model_key = window+'_'+target+'_'+str(int(shift))
                models[model_key] = best
                profiles += [dict(target=target,window=window,**r) for r in profile]
                for r in records:
                    key = window+'_'+str(r['sweep'])+'_'+target
                    for method,model in best.items():
                        prediction = timing.predict_innovation(r,model)
                        arrays[key+'_shift'+str(int(shift))+'_'+method] = prediction
                        for region in ('initial','recovery'):
                            rows.append(dict(window=window,target=target,sweep=r['sweep'],gap_ms=r['gap_s']*1000,
                                shift_ms=shift,method=method,region=region,**timing.error_metrics(r,prediction,region)))
                print('PREFIX_FIT',model_key,json.dumps(best),flush=True)
    summary = timing.summarize(rows)
    args.array_output.parent.mkdir(parents=True,exist_ok=True)
    with args.array_output.open('xb') as stream:
        np.savez_compressed(stream,**arrays)
    design = dict(masked['design'])
    design['observation'] = ('Every actual response is forecast from the latest parent-valid target bin strictly before its first scored bin. '
        'Parent artifact masks exclude the current command through AP+2ms. Earlier scored responses may be observed for later predictions. '
        'The entire current response is withheld; no target observation inside it updates the forecast. Short/long windows share anchors.')
    design['sensitivity_reason'] = ('Masked-history diagnostics found193/516 event anchors older than20ms, up to102.095ms. '
        'This separately preserved sensitivity allows the actually available prefix; it was chosen after the masked run, not blind validation.')
    result = dict(question=masked['question'],status=masked['status'],source_sha256=base.sha(__file__),
        test_sha256=base.sha(ROOT/'tests/test_recovery_source_prefix.py'),runtime=dict(python=platform.python_version(),numpy=np.__version__),
        provenance=provenance,design=design,observation_checks=checks,models=models,actual_time_kernel_profiles=profiles,
        per_sweep=rows,summary=summary,arrays=dict(path=args.array_output.relative_to(ROOT).as_posix(),
            sha256=base.sha(args.array_output),bytes=args.array_output.stat().st_size))
    with args.output.open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(result,stream,indent=2,ensure_ascii=False,allow_nan=False)
        stream.write('\n')
    print('PREFIX_RESULT',args.output,base.sha(args.output),flush=True)
    print(json.dumps([r for r in summary if r['shift_ms']==0 and r['cohort']=='temporal'],indent=2))


if __name__=='__main__':
    main()
