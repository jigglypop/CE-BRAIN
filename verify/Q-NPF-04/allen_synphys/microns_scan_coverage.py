"""고정 16개 스캔의 반응 분석·비교 불가·중복·시간축을 통합 점검한다."""
import json
from pathlib import Path
import numpy as np
from population_reciprocity import ROOT,sha
from superficial_ee_eligibility import save

HERE=Path(__file__).resolve().parent


def read(name):
    return json.loads((HERE/name).read_text(encoding='utf-8'))


def main():
    single={
        (4,7):('microns_first_trial_level_result.json','microns_repeat_response_acquisition.json'),
        (5,3):('microns_trial_level_result.json','microns_next_repeats_acquisition.json'),
        (5,6):('microns_third_trial_level_result.json','microns_third_repeats_acquisition.json'),
        (5,7):('microns_fourth_trial_level_result.json','microns_fourth_repeats_acquisition.json'),
        (6,2):('microns_fifth_trial_level_result.json','microns_fifth_repeats_acquisition.json'),
        (6,4):('microns_sixth_trial_level_result.json','microns_sixth_repeats_acquisition.json'),
        (6,6):('microns_seventh_trial_level_result.json','microns_seventh_repeats_acquisition.json'),
        (6,7):('microns_eighth_trial_level_result.json','microns_eighth_repeats_acquisition.json'),
        (7,3):('microns_ninth_trial_level_result.json','microns_ninth_repeats_acquisition.json'),
        (7,4):('microns_tenth_trial_level_result.json','microns_tenth_repeats_acquisition.json'),
        (8,5):('microns_eleventh_trial_level_result.json','microns_eleventh_repeats_acquisition.json'),
        (9,6):('microns_last_trial_level_result.json','microns_last_repeats_acquisition.json')}
    multiple={(9,3):'microns_multi93',(9,4):'microns_multi94'}
    unsupported={(7,5),(8,7)}
    targets=read('microns_all_scan_targets_result.json')['targets']
    support=read('microns_remaining_support_result.json')['scans']
    scans=sorted({(t['session'],t['scan_idx']) for t in targets})
    assert set(scans)==set(single)|set(multiple)|unsupported and len(scans)==16
    rows=[];covered=set();all_ids={t['nucleus_id'] for t in targets}
    for session,scan in scans:
        key=(session,scan);ts=[t for t in targets if (t['session'],t['scan_idx'])==key]
        nuclei={t['nucleus_id'] for t in ts};base=dict(session=session,scan_idx=scan,nuclei=len(nuclei),registered_units=len(ts))
        if key in unsupported:
            s=next(s for s in support if (s['session'],s['scan_idx'])==key)
            assert s['status']=='NO_MATCHED_CONTRAST_SUPPORT' and s['singleton_matched_strata']==0
            rows.append(dict(**base,status='CONTRAST_UNDEFINED',source='microns_remaining_support_result.json',source_sha256=sha(HERE/'microns_remaining_support_result.json')))
            continue
        covered|=nuclei
        if key in single:
            resultfile,receiptfile=single[key];rr=read(resultfile)['results']
            rr=[r for r in rr if not r.get('exclude_disputed',False) and r['subset'] in ('all10','first5','last5')]
            cases=[dict(timing=r['timing'],subset=r['subset'],assignment_index=0,total=r['total_matched'],trial_mean=r['trial_mean_component'],within=r['within_trial_component']) for r in rr]
            assignment_count=1
        else:
            prefix=multiple[key];resultfile=prefix+'_analysis_result.json';receiptfile=prefix+'_repeats_acquisition.json'
            result=read(resultfile);cases=result['results'];assignment_count=len(result['assignments'])
            assert set(result['nuclei'])==nuclei
            assert sha(HERE/(prefix+'_analysis_draws.npz'))==result['draws_sha256']
        assert len(cases)==6*assignment_count
        path=ROOT/f'data/external/microns_functional_nwb/scan_{session}_{scan}_repeated_clips.npz'
        digest=sha(path);assert digest==read(receiptfile)['artifact_sha256']
        with np.load(path) as data:
            assert set(data['unit_ids'].tolist())=={t['unit_id'] for t in ts}
            relative=data['relative_time'];assert relative[0]==.5 and relative[-1]<9.5 and (np.diff(relative)>0).all()
            assert len(data['conditions'])==6 and data['trial_starts'].shape==(6,10)
        summaries=[]
        for timing in ('common_frame','positive_delay_sensitivity'):
            for subset in ('all10','first5','last5'):
                group=[r for r in cases if r['timing']==timing and r['subset']==subset]
                assert len(group)==assignment_count and len({r['assignment_index'] for r in group})==assignment_count
                assert all(abs(r['total']-r['trial_mean']-r['within'])<1e-12 for r in group)
                summaries.append(dict(timing=timing,subset=subset,
                    ranges={name:[min(r[name] for r in group),max(r[name] for r in group)] for name in ('total','trial_mean','within')},
                    positives={name:sum(r[name]>0 for r in group) for name in ('total','trial_mean','within')}))
        rows.append(dict(**base,status='RESPONSE_ANALYZED',assignment_count=assignment_count,source=resultfile,source_sha256=sha(HERE/resultfile),
            input_sha256=digest,samples_per_trial=len(relative),relative_step_seconds=float(np.median(np.diff(relative))),summaries=summaries))
    aggregate={}
    for timing in ('common_frame','positive_delay_sensitivity'):
        selected=[next(s for s in r['summaries'] if s['timing']==timing and s['subset']=='all10') for r in rows if r['status']=='RESPONSE_ANALYZED']
        aggregate[timing]={name:dict(all_assignments_positive=sum(s['ranges'][name][0]>0 for s in selected),all_assignments_negative=sum(s['ranges'][name][1]<0 for s in selected),includes_zero_or_mixed=sum(s['ranges'][name][0]<=0<=s['ranges'][name][1] for s in selected)) for name in ('total','within')}
    save('microns_scan_coverage_result.json',dict(scans=rows,scans_listed=16,scans_analyzed=len(single)+len(multiple),undefined_scans=len(unsupported),
        unique_nuclei_listed=len(all_ids),unique_nuclei_with_response=len(covered),uncovered_nuclei=sorted(all_ids-covered),
        all10_scan_direction_counts=aggregate,code_sha256=sha(Path(__file__)),
        limits='Descriptive scope completion only, not scientific closure. Same animal, overlapping nuclei, scan-specific clocks/populations/weights. No pooled p-value. First-scan disputed exclusion and scan5/3 omission sensitivities remain in original sources.'))
    print('COVERAGE',len(single)+len(multiple),'undefined',len(unsupported),'response nuclei',len(covered),'listed nuclei',len(all_ids))
    print(json.dumps(aggregate,indent=2))


if __name__=='__main__':main()
