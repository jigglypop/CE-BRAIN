"""인간 피질 공개 표의 양방향 분모와 강도 식별성 감사."""
import csv
import io
import json
import zipfile
from collections import Counter,defaultdict
from pathlib import Path
import numpy as np
from population_reciprocity import ROOT,sha
from superficial_ee_eligibility import save

HERE=Path(__file__).resolve().parent
archive=ROOT/'data/external/peng2024_human/data.zip'
assert sha(archive)=='3711f8b8b911a24b0e5fd69e6e6c845f9e8601539807a9b960118c77ba5ad68d'
save('peng2024_inventory_contract.json',{
    'question':'공개 인간 ER/TR 표에서 환자별 연결 분모와 송신수신 교정 강도 대비를 복원할 수 있는가?',
    'selection':'tconnection_er/tr 및 tcell_er/tr; er_all을 추가 병합하지 않음; 코호트 분리',
    'dyads':'양방향행 존재 및 connected0/1인 쌍만; 누락은 음성 아님',
    'amplitude':'양방향 평가 쌍의 connected1이고 유한양수인 avg_psp_amplitude만 rank 조사; 단위확인 전 효과량 계산 없음',
    'gates':'방향키유일, 세포/환자/cluster 대응; reverse 표지와reciprocal 비교; SVD/lstsq 투영 일치',
    'limits':'가공자료 적격성 조사; 수술표본과 repatch/QC 영향 별도 조사 필요; 생물효과 추정 없음',
    'archive_sha256':sha(archive),'code_sha256':sha(Path(__file__))})
result={}
with zipfile.ZipFile(archive) as z:
    def read(name):return list(csv.DictReader(io.StringIO(z.read(name).decode('utf-8-sig'))))
    for cohort in ('er','tr'):
        rows=read('data/tconnection_'+cohort+'.csv');cells=read('data/tcell_'+cohort+'.csv')
        cm={c['cellid']:c for c in cells};assert len(cm)==len(cells)
        lookup={(r['clusterid'],r['cellid_pre'],r['cellid_post']):r for r in rows};assert len(lookup)==len(rows)
        counts=Counter();graphs=defaultdict(list);issues=[];patient_by_cluster={}
        for r in rows:
            pre,post=r['cellid_pre'],r['cellid_post'];assert pre!=post
            assert r['connected'] in ('0','1')
            for cell in (pre,post):
                if cell not in cm:issues.append({'issue':'missing_cell','cell':cell});continue
                assert cm[cell]['patientid']==r['patientid'] and cm[cell]['clusterid']==r['clusterid']
            patient_by_cluster[r['clusterid']]=r['patientid']
            rev=lookup.get((r['clusterid'],post,pre));counts['directed_rows']+=1
            if rev is None:counts['missing_reverse_directions']+=1;continue
            assert rev['patientid']==r['patientid']
            mutual=int(r['connected']) * int(rev['connected'])
            if int(r['reciprocal'])!=mutual:counts['reciprocal_flag_mismatch']+=1
            if pre<post:
                counts['both_assessed_dyads']+=1
                counts[['neither','one_way','mutual'][int(r['connected'])+int(rev['connected'])]]+=1
            if r['connected']=='1':
                counts['positive_directions']+=1
                value=float(r['avg_psp_amplitude'])
                if not np.isfinite(value):counts['missing_amplitude']+=1;continue
                if value<=0:counts['nonpositive_amplitude']+=1;continue
                counts['usable_amplitude_directions']+=1;graphs[r['clusterid']].append((pre,post,mutual))
        identifiable=[]
        for cluster,edges in graphs.items():
            nodes=sorted({v for e in edges for v in e[:2]});x=np.zeros((len(edges),2*len(nodes)))
            for i,(a,b,_) in enumerate(edges):x[i,nodes.index(a)]=1;x[i,len(nodes)+nodes.index(b)]=1
            flag=np.array([e[2] for e in edges],float);u,s,_=np.linalg.svd(x,full_matrices=False);rank=int(sum(s>1e-10))
            rz=flag-u[:,:rank]@(u[:,:rank].T@flag)
            assert np.allclose(rz,flag-x@np.linalg.lstsq(x,flag,rcond=1e-10)[0],atol=1e-10)
            if rz@rz>1e-10:identifiable.append({'cluster':cluster,'patient':patient_by_cluster[cluster],
                'directions':len(edges),'information':float(rz@rz)})
        result[cohort]={'counts':dict(counts),'patients':len({r['patientid'] for r in rows}),
            'clusters':len(patient_by_cluster),'cell_rows':len(cells),'issues':issues,
            'identifiable_clusters':len(identifiable),'identifiable_patients':len({r['patient'] for r in identifiable}),
            'informative_records':identifiable}
save('peng2024_inventory_result.json',{'contract_sha256':sha(HERE/'peng2024_inventory_contract.json'),'cohorts':result})
print(json.dumps(result,indent=2))
