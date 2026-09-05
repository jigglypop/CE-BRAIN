"""동일 조건 PL/NPL 기술적 비교; 조건과 세션 반복을 보존한다."""
import json
from pathlib import Path
from collections import defaultdict
import numpy as np
from population_reciprocity import sha
from superficial_ee_eligibility import save
HERE=Path(__file__).resolve().parent
def main():
    p=HERE/'icms_passive_coupling_extract_result.json'
    save('icms_passive_coupling_matched_contract.json',dict(code_sha256=sha(Path(__file__)),input_sha256=sha(p),
        method='Group by animal/session/current/channel; compare median NPL minus median PL among rows where both PC and PCnorm finite. Require at least1 unit in each label. Preserve missing groups. Report condition results and equal-condition session averages, equal-session animal averages; no pooled animal inference.',
        question='Is the within-condition PL/NPL comparison defined, and does normalization preserve its descriptive direction?',
        limits='Exploratory source-summary observation. Response-derived labels, repeated cells and shared population. No cell-type, causal or independent replication claim.'))
    groups=defaultdict(list)
    for r in json.loads(p.read_text(encoding='utf-8'))['rows']:
        groups[(r['animal'],r['session'],r['current'],r['channel'])].append(r)
    results=[]
    for key,rows in sorted(groups.items()):
        selected={label:[r for r in rows if r['label']==label and r['pc'] is not None and r['pc_norm'] is not None] for label in ('pl','npl')}
        row=dict(animal=key[0],session=key[1],current=key[2],channel=key[3],
                 all_counts={label:sum(r['label']==label for r in rows) for label in selected},finite_counts={label:len(rr) for label,rr in selected.items()})
        row['status']='DEFINED' if all(selected.values()) else 'UNDEFINED'
        if row['status']=='DEFINED':
            assert not ({r['unit'] for r in selected['pl']}&{r['unit'] for r in selected['npl']})
            row['units']={label:[r['unit'] for r in rr] for label,rr in selected.items()}
            for metric in ('pc','pc_norm'):
                values={label:float(np.median([r[metric] for r in rr])) for label,rr in selected.items()}
                row[metric]=dict(medians=values,npl_minus_pl=values['npl']-values['pl'])
        results.append(row)
    summaries=[];session_results=[]
    for animal in sorted({r['animal'] for r in results}):
        rr=[r for r in results if r['animal']==animal];defined=[r for r in rr if r['status']=='DEFINED'];sessions=[]
        for session in sorted({r['session'] for r in defined}):
            ss=[r for r in defined if r['session']==session]
            row=dict(animal=animal,session=session,conditions=len(ss),**{m:float(np.mean([r[m]['npl_minus_pl'] for r in ss])) for m in ('pc','pc_norm')})
            sessions.append(row);session_results.append(row)
        summaries.append(dict(animal=animal,total_conditions=len(rr),defined_conditions=len(defined),defined_sessions=len(sessions),
            sign_disagreement=sum(np.sign(r['pc']['npl_minus_pl'])!=np.sign(r['pc_norm']['npl_minus_pl']) for r in defined),
            animal_equal_session_mean={m:float(np.mean([r[m] for r in sessions])) if sessions else None for m in ('pc','pc_norm')},
            positive_conditions={m:sum(r[m]['npl_minus_pl']>0 for r in defined) for m in ('pc','pc_norm')}))
    save('icms_passive_coupling_matched_result.json',dict(conditions=results,sessions=session_results,animals=summaries))
    for s in summaries:print(s)
if __name__=='__main__':main()
