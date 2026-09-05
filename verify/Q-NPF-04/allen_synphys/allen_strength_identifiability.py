"""Allen E-E 연결의 양방향 검사·진폭 가용성과 강도 대비 식별성."""
import json
import sqlite3
from collections import Counter,defaultdict
from pathlib import Path
import numpy as np
from population_reciprocity import DB,sha
from superficial_ee_eligibility import save

HERE=Path(__file__).resolve().parent
assert sha(DB)=='7372499fdd874f057565080d5769baaf2659ef39d9f3bc3c7147dd1e1c280a53'
save('allen_strength_identifiability_contract.json',{
    'question':'보유 Allen E-E 기록은 상호연결 강도와 송신·수신 세포 효과를 분리할 관측 구조를 제공하는가?',
    'primary':'mouse VisP ex/ex target_layer 양쪽2,2/3,3; 양방향has_synapse비결측 및 n_ex_test_spikes>10',
    'secondary':'별도 가용성 조사로 mouse VisP ex/ex 모든층; 상층 재현으로 합치지 않음; 효과값 선택 없음',
    'amplitude':'synapse.psp_amplitude 유한 양수이고 synapse_type ex인 검출 연결; 누락/비양수별도 집계',
    'reciprocity':'표지는 pair.has_synapse에서 결정; 반대방향 진폭 누락을 비연결로 바꾸지 않음',
    'endpoint':'모집단·진폭 분모; 기록별 송신수신 nuisance rank와 reciprocal indicator 잔차제곱합',
    'gate':'synapse pair_id 유일; 기존상층190dyads/25positive directions와 일치; SVD와lstsq 일치',
    'limits':'가용성/식별성 조사; 진폭생성QC와 검출편향은 별도 검토 필요; 생물효과 추정 없음',
    'db_sha256':sha(DB),'code_sha256':sha(Path(__file__))})
with sqlite3.connect(DB.as_uri()+'?mode=ro',uri=True) as db:
    db.row_factory=sqlite3.Row
    rows=[dict(r) for r in db.execute('''select p.id,p.experiment_id,p.pre_cell_id,p.post_cell_id,p.has_synapse,p.n_ex_test_spikes,
      a.target_layer as pre_layer,b.target_layer as post_layer
      from pair p join cell a on a.id=p.pre_cell_id join cell b on b.id=p.post_cell_id
      join experiment e on e.id=p.experiment_id join slice s on s.id=e.slice_id
      where s.species='mouse' and e.target_region='VisP' and a.cell_class_nonsynaptic='ex' and b.cell_class_nonsynaptic='ex' ''')]
    synapses=[dict(r) for r in db.execute('select pair_id,synapse_type,psp_amplitude from synapse')]
syn={r['pair_id']:r for r in synapses};assert len(syn)==len(synapses)
results={}
for scope in ('upper_layers','all_layers_separate_inventory'):
    selected=[r for r in rows if scope!='upper_layers' or (r['pre_layer'] in ('2','2/3','3') and r['post_layer'] in ('2','2/3','3'))]
    lookup={(r['experiment_id'],r['pre_cell_id'],r['post_cell_id']):r for r in selected};assert len(lookup)==len(selected)
    counts=Counter();experiments=defaultdict(list)
    for r in selected:
        reverse=lookup.get((r['experiment_id'],r['post_cell_id'],r['pre_cell_id']))
        if reverse is None or any(v['has_synapse'] is None or v['n_ex_test_spikes'] is None or v['n_ex_test_spikes']<=10 for v in (r,reverse)):continue
        counts['qualified_directions']+=1
        if r['has_synapse']!=1:continue
        counts['positive_directions']+=1;s=syn.get(r['id'])
        if s is None:counts['missing_synapse_row']+=1;continue
        if s['synapse_type']!='ex':counts['non_ex_synapse_type']+=1;continue
        value=s['psp_amplitude']
        if value is None or not np.isfinite(value):counts['missing_or_nonfinite_amplitude']+=1;continue
        if value<=0:counts['nonpositive_amplitude']+=1;continue
        counts['usable_amplitude_directions']+=1
        experiments[r['experiment_id']].append((r['pre_cell_id'],r['post_cell_id'],reverse['has_synapse']))
    records=[]
    for eid,edges in sorted(experiments.items()):
        nodes=sorted({v for e in edges for v in e[:2]});x=np.zeros((len(edges),2*len(nodes)))
        for k,(a,b,_) in enumerate(edges):x[k,nodes.index(a)]=1;x[k,len(nodes)+nodes.index(b)]=1
        z=np.array([e[2] for e in edges],float);u,s,_=np.linalg.svd(x,full_matrices=False);rank=int(sum(s>1e-10))
        rz=z-u[:,:rank]@(u[:,:rank].T@z);info=float(rz@rz)
        assert np.allclose(rz,z-x@np.linalg.lstsq(x,z,rcond=1e-10)[0],atol=1e-10)
        records.append({'experiment_id':eid,'usable_directions':len(edges),'rank':rank,'information':info,'identifiable':info>1e-10})
    if scope=='upper_layers':assert counts['qualified_directions']==380 and counts['positive_directions']==25
    results[scope]={'counts':dict(counts),'experiments_with_amplitudes':len(records),
                    'identifiable_experiments':sum(r['identifiable'] for r in records),'records':records}
save('allen_strength_identifiability_result.json',{'contract_sha256':sha(HERE/'allen_strength_identifiability_contract.json'),
    'scopes':results,'verification':'PASS: primary denominator and independent projections'})
print(json.dumps({k:{a:b for a,b in v.items() if a!='records'} for k,v in results.items()},indent=2))
