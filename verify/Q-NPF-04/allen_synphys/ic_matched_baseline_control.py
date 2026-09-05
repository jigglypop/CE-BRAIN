"""추가 20개 시행에서 동일 창의 notebook 기준선 대조와 사건 파형을 비교한다."""
import argparse
import json
from pathlib import Path
import numpy as np
from reference_spike_audit import sha

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
CONTRACT=HERE/'ic_matched_baseline_contract.json'
OUTPUT=HERE/'ic_matched_baseline_result.json'
SOURCES={name:HERE/filename for name,filename in {
    'responses':'ic_extension_first_result.json','inventory':'ic_extended_inventory_result.json',
    'full_records':'ic_full_recording_qc_result.json','baseline':'ic_baseline_endpoint_result.json'}.items()}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--verify',action='store_true');args=parser.parse_args()
    centers=(.100+.025*np.arange(17)).tolist()
    spec=dict(scope='post-result diagnostic of sweeps37..56, one experiment; not blinded confirmation or randomized sham',
        question='Is the fixed first-pulse positive-minus-negative contrast distinguishable descriptively from matched baseline-window changes?',
        control_centers_s=centers,control='17 fixed centers in notebook initial quiet interval, same pre spike fractional lag added; no voltage-based exclusion',
        windows='response[2,8)ms minus[-8,-3)ms, same 100kHz interpolation; baseline controls use identical windows',
        summary='actual minus mean of 17 controls per sweep; mean, median, signs, ranges; chronological groups of5; no p-values',
        waveform='1ms bins from-8 to12ms, each event baseline-subtracted with[-8,-3)ms; averages only, no peak picking',
        limitations='Notebook-defined baseline, not command-verified across every channel; temporal drift, spontaneous activity, cross-talk and source QC mismatch remain; controls not independent biological samples',
        source_sha256={k:sha(p) for k,p in SOURCES.items()},code_sha256=sha(Path(__file__)),
        prior_response_check_tolerance_uV=1e-5)
    if CONTRACT.exists():assert spec==json.loads(CONTRACT.read_text(encoding='utf-8'))
    elif args.verify:raise RuntimeError('계약 없음')
    else:
        with CONTRACT.open('x',encoding='utf-8') as stream:json.dump(spec,stream,ensure_ascii=False,indent=2)
    sources={k:json.loads(p.read_text(encoding='utf-8')) for k,p in SOURCES.items()}
    records=sources['responses']['analysis']['records'];assert [r['sweep'] for r in records]==list(range(37,57))
    rows=[];actual_waves=[];control_waves=[]
    for old in records:
        sw=old['sweep'];sweep=next(s for s in sources['inventory']['selected'] if s['sweep']==sw)
        lag=old['spikes'][0]['max_slope_time'];fs=sweep['nodes']['pre']['rate']
        actual_center=round(sweep['onset_times_s'][0]*fs)/fs+lag
        event_centers=[actual_center]+[c+lag for c in centers]
        target_values={};target_waves={}
        for target in ('positive','negative'):
            receipt=next(r for r in sources['full_records']['analysis']['records'] if r['sweep']==sw and r['target']==target)
            path=ROOT/receipt['array_path'];assert sha(path)==receipt['array_sha256']
            with np.load(path,allow_pickle=False) as data:v=data['voltage']
            t=np.arange(len(v))/fs
            quiet=next(r for r in sources['baseline']['records'] if r['sweep']==sw and r['target']==target)['corrected_regions_s'][0]
            assert all(quiet[0]<=c-.008 and c+.012<=quiet[1] for c in event_centers[1:])
            values=[];waves=[]
            for center in event_centers:
                def mean(lo,hi):return float(np.interp(center+np.arange(lo,hi,1/fs),t,v).mean())
                base=mean(-.008,-.003)
                values.append((mean(.002,.008)-base)*1e6)
                waves.append([(mean(k/1000,(k+1)/1000)-base)*1e6 for k in range(-8,12)])
            assert abs(values[0]-old['responses'][target]['voltage_change_uV'])<1e-5
            target_values[target]=values;target_waves[target]=waves
        contrasts=np.array(target_values['positive'])-np.array(target_values['negative'])
        row=dict(sweep=sw,actual_uV=float(contrasts[0]),control_uV=contrasts[1:].tolist(),
            control_mean_uV=float(contrasts[1:].mean()),adjusted_uV=float(contrasts[0]-contrasts[1:].mean()),
            actual_inside_control_range=bool(contrasts[1:].min()<=contrasts[0]<=contrasts[1:].max()),
            target_responses_uV=target_values)
        rows.append(row)
        difference=np.array(target_waves['positive'])-np.array(target_waves['negative'])
        actual_waves.append(difference[0]);control_waves.append(difference[1:].mean(axis=0))
    def stats(values):
        v=np.array(values)
        return dict(mean=float(v.mean()),median=float(np.median(v)),minimum=float(v.min()),maximum=float(v.max()),
                    positive=int((v>0).sum()),negative=int((v<0).sum()))
    summary={key:stats([r[key] for r in rows]) for key in ('actual_uV','control_mean_uV','adjusted_uV')}
    summary['actual_inside_own_control_range']=sum(r['actual_inside_control_range'] for r in rows)
    summary['chronological_groups']=[dict(sweeps=list(range(lo,lo+5)),adjusted_mean_uV=float(np.mean([r['adjusted_uV'] for r in rows if lo<=r['sweep']<lo+5]))) for lo in (37,42,47,52)]
    result=dict(contract_sha256=sha(CONTRACT),rows=rows,summary=summary,
        waveform=dict(bin_centers_ms=(np.arange(-8,12)+.5).tolist(),
                      actual_difference_mean_uV=np.mean(actual_waves,axis=0).tolist(),
                      control_difference_mean_uV=np.mean(control_waves,axis=0).tolist()))
    if args.verify:
        assert result==json.loads(OUTPUT.read_text(encoding='utf-8'));print('MATCHED_BASELINE_REPRODUCED_OFFLINE')
    else:
        with OUTPUT.open('x',encoding='utf-8') as stream:json.dump(result,stream,ensure_ascii=False,indent=2,allow_nan=False)
    print(json.dumps(summary,indent=2))


if __name__=='__main__':main()
