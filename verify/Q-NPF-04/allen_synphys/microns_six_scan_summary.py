"""완료한 네 스캔의 고정 성분 비교를 빠짐없이 묶는다."""
import json
from pathlib import Path
from population_reciprocity import sha
from superficial_ee_eligibility import save

HERE=Path(__file__).resolve().parent


def main():
    specs=[('4_7','microns_first_trial_level_result.json'),
           ('5_3','microns_trial_level_result.json'),
           ('5_6','microns_third_trial_level_result.json'),
           ('5_7','microns_fourth_trial_level_result.json'),
           ('6_2','microns_fifth_trial_level_result.json'),
           ('6_4','microns_sixth_trial_level_result.json')]
    rows=[];sources=[]
    for scan,name in specs:
        result=json.loads((HERE/name).read_text(encoding='utf-8'))['results']
        sources.append(dict(scan=scan,path=name,sha256=sha(HERE/name)))
        for timing in ('common_frame','positive_delay_sensitivity'):
            chosen={s:next(r for r in result if r['timing']==timing and r['subset']==s and not r.get('exclude_disputed',False)) for s in ('all10','first5','last5')}
            for r in chosen.values():
                assert abs(r['total_matched']-r['trial_mean_component']-r['within_trial_component'])<1e-12
            rows.append(dict(scan=scan,timing=timing,
                total_all10=chosen['all10']['total_matched'],
                within_all10=chosen['all10']['within_trial_component'],
                within_first5=chosen['first5']['within_trial_component'],
                within_last5=chosen['last5']['within_trial_component'],
                within_late_minus_early=chosen['last5']['within_trial_component']-chosen['first5']['within_trial_component']))
    targets=json.loads((HERE/'microns_all_scan_targets_result.json').read_text(encoding='utf-8'))['targets']
    ids={s:{t['nucleus_id'] for t in targets if f"{t['session']}_{t['scan_idx']}"==s} for s,_ in specs}
    overlaps=[dict(scan_a=a,scan_b=b,nuclei=len(ids[a]&ids[b])) for i,(a,_) in enumerate(specs) for b,_ in specs[i+1:]]
    save('microns_six_scan_summary_result.json',dict(results=rows,sources=sources,
        cells_by_scan={s:len(v) for s,v in ids.items()},unique_nuclei=len(set.union(*ids.values())),overlaps=overlaps,
        code_sha256=sha(Path(__file__)),limits='Same animal, scan-specific populations and denominators. No pooled significance test or independent animal replication. Includes all six completed ordered scans; incomplete16-scan coverage.'))
    print(json.dumps(dict(results=rows,overlaps=overlaps,unique_nuclei=len(set.union(*ids.values()))),indent=2))


if __name__=='__main__':main()
