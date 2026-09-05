"""ER 양성 진폭의 상호연결 대비: 송신수신 효과 및 원시코드 가용성 민감도."""
import csv
import io
import json
import zipfile
from collections import defaultdict
from pathlib import Path
import numpy as np
from scipy.io import loadmat
from population_reciprocity import ROOT,sha
from superficial_ee_eligibility import save

HERE=Path(__file__).resolve().parent;archive=ROOT/'data/external/peng2024_human/data.zip'
assert sha(archive)=='3711f8b8b911a24b0e5fd69e6e6c845f9e8601539807a9b960118c77ba5ad68d'
save('peng2024_er_strength_contract.json',{
    'question':'ER 검출 연결에서 상호연결 강도 차이는 송신·수신 세포 효과를 고려해도 남는가?',
    'scope':'ER만; 저자 connected 표지와 유한양수 avg_psp_amplitude; TR 제외는 출처 미확인 때문',
    'branches':['author_published','both_raw_codes_finite'],
    'sensitivity':'두 방향 matrix.connection이 유한인 쌍만; 유한 코드가 검사완전성이나QC통과를 보장한다는 주장은 아님',
    'model':'기록별 sender+receiver 열공간에서 reciprocal indicator와 log(mV)를 잔차화; beta=sum(cross)/sum(info)',
    'comparison':'각 분기에서 정보 있는 동일 기록만 사용한 기록절편 기준선도 계산',
    'patient':'기여 환자 수·환자별 numerator/denominator; 한 환자 제외 beta 범위; p값 없음',
    'gates':'CSV/monosynaptic/환자 대응, finite진폭 원본 일치, SVD/lstsq일치, info>1e-10',
    'limits':'가공 수술표본 조건부 관측; 결측32방향·논문과1연결차이 미해결; 인과/건강한인간 일반화 아님',
    'archive_sha256':sha(archive),'code_sha256':sha(Path(__file__))})
with zipfile.ZipFile(archive) as z:
    def read(name):return list(csv.DictReader(io.StringIO(z.read('data/'+name+'_er.csv').decode('utf-8-sig'))))
    cells={r['cellid'].replace(' ',''):r for r in read('tcell')};rows=read('tconnection')
    dm={str(int(d['data_index'])):d for d in loadmat(io.BytesIO(z.read('data/data_matrix_er.mat')),simplify_cells=True)['data']}
lookup={(r['clusterid'],r['cellid_pre'],r['cellid_post']):r for r in rows};results={}
for branch in ('author_published','both_raw_codes_finite'):
    graphs=defaultdict(list);excluded=0
    for r in rows:
        if r['connected']!='1':continue
        value=float(r['avg_psp_amplitude'])
        if not np.isfinite(value) or value<=0:continue
        a,b=r['cellid_pre'],r['cellid_post'];rev=lookup[r['clusterid'],b,a]
        ca,cb=cells[a],cells[b];assert ca['patientid']==cb['patientid']==r['patientid']
        ai,bi=int(ca['channel'])-1,int(cb['channel'])-1;m=dm[str(int(r['data_index']))]['matrix']
        assert np.isclose(value,m['avg']['psp']['amplitude'][ai,bi],rtol=1e-5,atol=1e-8)
        assert int(m['monosynaptic'][ai,bi])==1 and int(m['monosynaptic'][bi,ai])==int(rev['connected'])
        if branch=='both_raw_codes_finite' and not (np.isfinite(m['connection'][ai,bi]) and np.isfinite(m['connection'][bi,ai])):
            excluded+=1;continue
        graphs[r['clusterid']].append((a,b,int(rev['connected']),np.log(value),r['patientid']))
    records=[];patients=defaultdict(lambda:[0.,0.]);base_num=base_den=num=den=0.
    for cluster,edges in graphs.items():
        nodes=sorted({v for e in edges for v in e[:2]});x=np.zeros((len(edges),2*len(nodes)))
        for k,(a,b,_,_,_) in enumerate(edges):x[k,nodes.index(a)]=1;x[k,len(nodes)+nodes.index(b)]=1
        flag=np.array([e[2] for e in edges],float);y=np.array([e[3] for e in edges]);u,s,_=np.linalg.svd(x,full_matrices=False);q=u[:,s>1e-10]
        rf=flag-q@(q.T@flag);ry=y-q@(q.T@y)
        assert np.allclose(rf,flag-x@np.linalg.lstsq(x,flag,rcond=1e-10)[0],atol=1e-10)
        assert np.allclose(ry,y-x@np.linalg.lstsq(x,y,rcond=1e-10)[0],atol=1e-10)
        info=float(rf@rf)
        if info<=1e-10:continue
        cross=float(rf@ry);num+=cross;den+=info;patient=edges[0][4]
        patients[patient][0]+=cross;patients[patient][1]+=info
        f0=flag-flag.mean();y0=y-y.mean();base_num+=float(f0@y0);base_den+=float(f0@f0)
        records.append({'cluster':cluster,'patient':patient,'directions':len(edges),'information':info,'cross':cross,'beta':cross/info})
    leave=[(num-v[0])/(den-v[1]) for v in patients.values() if den-v[1]>1e-10]
    results[branch]={'usable_directions':sum(map(len,graphs.values())),'excluded_raw_code_directions':excluded,
        'informative_clusters':len(records),'informative_patients':len(patients),'information':den,
        'beta':num/den,'exp_beta':float(np.exp(num/den)),
        'same_records_intercept_ratio':float(np.exp(base_num/base_den)),
        'leave_one_patient_beta_range':[min(leave),max(leave)],
        'patients_positive':sum(v[0]>0 for v in patients.values()),'patients':dict(patients),'records':records}
save('peng2024_er_strength_result.json',{'contract_sha256':sha(HERE/'peng2024_er_strength_contract.json'),
    'branches':results,'verification':'PASS: source amplitude and label checks; independent projections'})
print(json.dumps({k:{a:b for a,b in v.items() if a not in ('patients','records')} for k,v in results.items()},indent=2))
