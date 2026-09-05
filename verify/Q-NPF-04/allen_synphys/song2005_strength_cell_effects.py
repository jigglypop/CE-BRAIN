"""기록 안의 송신·수신 세포 효과를 제거한 상호연결 강도 대비."""
import json
from pathlib import Path
import numpy as np
from population_reciprocity import sha
from superficial_ee_eligibility import save

HERE=Path(__file__).resolve().parent
ip=HERE/'song2005_inventory_result.json';source=json.loads(ip.read_text())
save('song2005_strength_cell_effects_contract.json',{
    'question':'상호연결의 log EPSP 강도 차이는 기록별 송신·수신 세포 효과를 제거해도 식별되는가?',
    'data':'기존931 검출 연결; 같은 기록의 세포 ID만 비교; 연결 유무는 고정',
    'models':['record_intercept','sender','receiver','sender_receiver'],
    'method':'각 기록에서 nuisance 열공간에 상호연결 indicator와 log(amplitude_mV)를 투영해 잔차화; beta=sum(r_indicator*r_logamp)/sum(r_indicator^2)',
    'gate':'SVD rank cutoff1e-10; indicator잔차제곱합>1e-10일 때 정보 있음; 직교성과 독립lstsq 잔차 일치',
    'interpretation':'exp(beta)는 조건부 log강도 대비; 인과/검출편향 제거 아님; 모형별 정보가 있는 표본이 달라 직접 같은 효과로 취급하지 않음',
    'inference':'표준오차/p값 없음; 같은 동물 상관 미확인; 식별 불가를 효과0으로 바꾸지 않음',
    'input_sha256':sha(ip),'code_sha256':sha(Path(__file__))})
outputs={}
for model in ('record_intercept','sender','receiver','sender_receiver'):
    records=[];numerator=denominator=0.
    for row in source['records']:
        edges=row['edges']
        if not edges:continue
        keys={(e['pre'],e['post']) for e in edges}
        y=np.log([e['amplitude_V']*1000 for e in edges])
        z=np.array([(e['post'],e['pre']) in keys for e in edges],float)
        columns=[np.ones(len(edges))]
        if model in ('sender','sender_receiver'):
            columns.extend(np.array([e['pre']==v for e in edges],float) for v in sorted({e['pre'] for e in edges}))
        if model in ('receiver','sender_receiver'):
            columns.extend(np.array([e['post']==v for e in edges],float) for v in sorted({e['post'] for e in edges}))
        x=np.column_stack(columns);u,s,_=np.linalg.svd(x,full_matrices=False);rank=int(sum(s>1e-10));q=u[:,:rank]
        rz=z-q@(q.T@z);ry=y-q@(q.T@y)
        assert np.max(abs(x.T@rz))<1e-9
        assert np.allclose(rz,z-x@np.linalg.lstsq(x,z,rcond=1e-10)[0],atol=1e-10)
        assert np.allclose(ry,y-x@np.linalg.lstsq(x,y,rcond=1e-10)[0],atol=1e-10)
        info=float(rz@rz);cross=float(rz@ry)
        if info<=1e-10:continue
        numerator+=cross;denominator+=info
        records.append({'row':row['row'],'date':row['date'],'edges':len(edges),'nuisance_rank':rank,
                        'information':info,'cross_product':cross,'record_beta':cross/info})
    beta=numerator/denominator if denominator>1e-10 else None
    outputs[model]={'informative_records':len(records),'informative_dates':len({r['date'] for r in records}),
                    'information_sum':denominator,'beta':beta,'exp_beta':float(np.exp(beta)) if beta is not None else None,
                    'positive_record_contrasts':sum(r['record_beta']>0 for r in records),'records':records}
result={'contract_sha256':sha(HERE/'song2005_strength_cell_effects_contract.json'),
        'models':outputs,'verification':'PASS: SVD projection orthogonality and independent least-squares projections agree'}
save('song2005_strength_cell_effects_result.json',result)
print(json.dumps({k:{a:b for a,b in v.items() if a!='records'} for k,v in outputs.items()},indent=2))
