"""배정 가능 이력 안에서 공유 표적 경로별 기술적 대비를 계산한다."""
import json
from pathlib import Path
import numpy as np
from randi_target_response import HERE, save, sha


def main():
    parents=['rowland_native_clock_comparison_result.json','rowland_assignment_support_result.json','rowland_pattern_inventory_result.json']
    save('rowland_pattern_contrast_contract.json',{
        'question':'이력 제한 후 표적 경로 구성에 따른 대비 차이를 분리할 수 있는가',
        'code_sha256':sha(Path(__file__)), 'parents':{p:sha(HERE/p) for p in parents},
        'selection':'기존 배정 가능 이력 집합 안에서 test/catch가 각각 1회 이상 남은 경로',
        'comparisons':['이력 제한 전체 무보정','공유 경로 집합 무보정','같은 집합의 경로 고정효과'],
        'weights':'경로별 n_test*n_catch/(n_test+n_catch), 합계로 정규화',
        'checks':['전체 제한 대비 재현','경로별 가중 대비와 경로 더미 OLS 일치'],
        'limits':['독립 이력층 안의 짝짓기 아님; 허용 이력들을 합침','사후 기술적 대비; 인과효과 아님',
                  '작은 경로 표본·시간 차이·누락·실제 출력 미확인'],
        'claim_ceiling':'BIO_EVIDENCE_L1'})
    loaded=[json.loads((HERE/p).read_text(encoding='utf-8'))['rows'] for p in parents]
    maps=[{(r['mouse'],r['run']):r for r in rows} for rows in loaded[1:]]
    results=[]
    for r in loaded[0]:
        key=(r['mouse'],r['run']);support=maps[0][key];inventory=maps[1][key]
        allowed=set(support['selected_indices']);idx=np.array(r['original_indices'])
        y=np.array(r['s2_delta']);t=np.array(r['test']);position={int(v):i for i,v in enumerate(idx)}
        mask=np.isin(idx,list(allowed))
        raw=float(y[mask&(t==1)].mean()-y[mask&(t==0)].mean())
        assert abs(raw-support['models']['raw']['selected']['coefficient'])<1e-12
        groups=[]; selected=[]; labels=[]
        for path,g in sorted(inventory['patterns'].items()):
            ti=[position[i] for i in g['exported_test_indices'] if i in allowed]
            ci=[position[i] for i in g['exported_catch_indices'] if i in allowed]
            if not ti or not ci:continue
            assert np.all(t[ti]==1) and np.all(t[ci]==0)
            group_id=len(groups)
            selected.extend(ti+ci);labels.extend([group_id]*(len(ti)+len(ci)))
            groups.append({'path':path,'test_n':len(ti),'catch_n':len(ci),
                           'contrast':float(y[ti].mean()-y[ci].mean()),
                           'weight':len(ti)*len(ci)/(len(ti)+len(ci)),
                           'test_indices':idx[ti].tolist(),'catch_indices':idx[ci].tolist()})
        selected=np.array(selected);labels=np.array(labels)
        assert len(set(selected.tolist()))==len(selected) and groups
        yy=y[selected];tt=t[selected]
        pooled=float(yy[tt==1].mean()-yy[tt==0].mean())
        fixed=sum(g['weight']*g['contrast'] for g in groups)/sum(g['weight'] for g in groups)
        design=np.column_stack([np.eye(len(groups))[labels],tt])
        beta,_,rank,_=np.linalg.lstsq(design,yy,rcond=None)
        assert rank==design.shape[1] and np.linalg.cond(design)<1e8
        assert abs(beta[-1]-fixed)<1e-12
        results.append({'mouse':r['mouse'],'run':r['run'],'history_raw':raw,
                        'shared_raw':pooled,'pattern_fixed_effect':fixed,
                        'test_n':int(sum(tt==1)),'catch_n':int(sum(tt==0)),
                        'groups':groups,'condition_number':float(np.linalg.cond(design))})
    assert len(results)==11
    save('rowland_pattern_contrast_result.json',{'contract_sha256':sha(HERE/'rowland_pattern_contrast_contract.json'),'rows':results})
    for r in results:print(r['mouse'],r['run'],len(r['groups']),r['test_n'],r['catch_n'],*[round(r[k],7) for k in ['history_raw','shared_raw','pattern_fixed_effect']])


if __name__=='__main__':main()
