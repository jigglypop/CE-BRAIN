"""허용 그래프를 직접 열거해 상호 연결 수의 가능한 범위와 정확한 빈도를 검증한다."""
import itertools
import json
from collections import Counter
from fractions import Fraction
from pathlib import Path
from reference_spike_audit import sha

HERE=Path(__file__).resolve().parent
SOURCE=HERE/'reciprocity_fixed_degrees_result.json'
OUTPUT=HERE/'reciprocity_exact_support_result.json'


def distribution(row):
    n=len(row['cell_ids']);masks=row['allowed_destination_masks'];out=row['outgoing']
    found=Counter()
    def visit(i,remaining,chosen,reciprocal):
        if i==n:
            if not any(remaining):found[reciprocal]+=1
            return
        choices=[j for j in range(n) if masks[i]&(1<<j) and remaining[j]>0]
        for selected in itertools.combinations(choices,out[i]):
            next_remaining=list(remaining)
            for j in selected:next_remaining[j]-=1
            if any(next_remaining[j]>sum(bool(masks[k]&(1<<j)) for k in range(i+1,n)) for j in range(n)):continue
            added=sum(j<i and bool(chosen[j]&(1<<i)) for j in selected)
            visit(i+1,next_remaining,chosen+[sum(1<<j for j in selected)],reciprocal+added)
    visit(0,row['incoming'],[],0)
    return found


def main():
    source=json.loads(SOURCE.read_text(encoding='utf-8'));rows=[]
    for row in source['analysis']['per_experiment']:
        counts=distribution(row);total=sum(counts.values())
        assert total==row['admissible_graphs']
        assert Fraction(sum(k*v for k,v in counts.items()),total)==Fraction(row['expected_numerator'],row['expected_denominator'])
        assert row['observed_reciprocal'] in counts
        rows.append(dict(experiment_id=row['experiment_id'],species=row['species'],slice_id=row['slice_id'],
            dyads=row['dyads'],observed=row['observed_reciprocal'],expected=row['expected_reciprocal'],
            histogram={str(k):v for k,v in sorted(counts.items())},reciprocity_variable=len(counts)>1))
    summaries={}
    for species in sorted(set(r['species'] for r in rows)):
        selected=[r for r in rows if r['species']==species];variable=[r for r in selected if r['reciprocity_variable']]
        summaries[species]=dict(experiments=len(selected),reciprocity_variable_experiments=len(variable),
            variable_slices=len(set(r['slice_id'] for r in variable)),variable_dyads=sum(r['dyads'] for r in variable),
            observed_in_variable=sum(r['observed'] for r in variable),expected_in_variable=sum(r['expected'] for r in variable),
            fixed_statistic_experiments=len(selected)-len(variable),
            fixed_observed=sum(r['observed'] for r in selected if not r['reciprocity_variable']))
    result=dict(source_sha256=sha(SOURCE),code_sha256=sha(Path(__file__)),
        scope='exact support audit, not additional biological observations; no independent-slice joint null assumed',
        total_enumerated_graphs=sum(sum(r['histogram'].values()) for r in rows),summaries=summaries,per_experiment=rows)
    if OUTPUT.exists():
        assert result==json.loads(OUTPUT.read_text(encoding='utf-8'));print('EXACT_SUPPORT_REPRODUCED')
    else:
        with OUTPUT.open('x',encoding='utf-8') as stream:json.dump(result,stream,indent=2)
    print(json.dumps(summaries,indent=2))


if __name__=='__main__':main()
