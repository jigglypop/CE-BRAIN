"""연결 CSV와 분석용 행렬, 진폭 후보 필드의 대응을 추적한다."""
import csv
import io
import json
import zipfile
from collections import Counter
from pathlib import Path
import numpy as np
from scipy.io import loadmat
from population_reciprocity import ROOT,sha
from superficial_ee_eligibility import save

HERE=Path(__file__).resolve().parent
archive=ROOT/'data/external/peng2024_human/data.zip'
assert sha(archive)=='3711f8b8b911a24b0e5fd69e6e6c845f9e8601539807a9b960118c77ba5ad68d'
save('peng2024_matrix_paths_contract.json',{
    'question':'CSV 표지는 최종 monosynaptic 행렬과 일치하며 진폭은 어떤 원본 필드와 대응하는가?',
    'scope':'두코호트 전체 행; 연결코드 임의변환 없음; ID공백정리 후 data_index/channel 직접 접근',
    'amplitude_candidates':['matrix.avg.psp.amplitude','matrix.mean.psp.amplitude','matrix2.avg.psp.amplitude','matrix2.mean.psp.amplitude'],
    'endpoint':'monosynaptic 코드×CSV표지 교차표; 유한CSV에 대한 후보필드 일치/결측 수; 기존matrix.avg결측42개 별도 추적',
    'limits':'수치 일치는 생성 코드의 의미와 QC 보증이 아님; 후보검색을 생물학적 효과 선택으로 사용하지 않음',
    'archive_sha256':sha(archive),'code_sha256':sha(Path(__file__))})
results={}
with zipfile.ZipFile(archive) as z:
    for co in ('er','tr'):
        def read(prefix):return list(csv.DictReader(io.StringIO(z.read('data/'+prefix+'_'+co+'.csv').decode('utf-8-sig'))))
        cells={r['cellid'].replace(' ',''):r for r in read('tcell')};rows=read('tconnection')
        dm={str(int(r['data_index'])):r for r in loadmat(io.BytesIO(z.read('data/data_matrix_'+co+'.mat')),simplify_cells=True)['data']}
        cross=Counter();stats={};unresolved=[]
        for r in rows:
            a=int(cells[r['cellid_pre']]['channel'])-1;b=int(cells[r['cellid_post']]['channel'])-1
            d=dm[str(int(r['data_index']))];m=d['matrix']['monosynaptic'][a,b]
            cross[str(m),r['connected']]+=1
            value=float(r['avg_psp_amplitude'])
            if not np.isfinite(value):continue
            original=d['matrix']['avg']['psp']['amplitude'][a,b];missing=not np.isfinite(original);matches=[]
            for outer in ('matrix','matrix2'):
                for inner in ('avg','mean'):
                    key=outer+'.'+inner+'.psp.amplitude';stat=stats.setdefault(key,Counter())
                    candidate=d[outer][inner]['psp']['amplitude'][a,b]
                    stat['csv_finite']+=1
                    if not np.isfinite(candidate):stat['candidate_missing']+=1;continue
                    match=bool(np.isclose(candidate,value,rtol=1e-5,atol=1e-8))
                    stat['match' if match else 'mismatch']+=1
                    if missing:stat['original_missing_match' if match else 'original_missing_mismatch']+=1
                    if match:matches.append(key)
            if missing:unresolved.append({'synapseid':r['synapseid'],'cluster':r['clusterid'],'matches':matches})
        results[co]={'monosynaptic_to_csv':[{'matrix_value':k[0],'csv':k[1],'count':v} for k,v in sorted(cross.items())],
            'amplitude_fields':{k:dict(v) for k,v in stats.items()},'original_missing_rows':unresolved}
save('peng2024_matrix_paths_result.json',{'contract_sha256':sha(HERE/'peng2024_matrix_paths_contract.json'),'cohorts':results})
print(json.dumps({k:{a:b for a,b in v.items() if a!='original_missing_rows'} for k,v in results.items()},indent=2))
