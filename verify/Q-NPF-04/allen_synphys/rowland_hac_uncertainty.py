"""원래 시행 번호 거리의 Bartlett sandwich 근사; 인과 신뢰구간 아님."""
import json
from pathlib import Path
from statistics import NormalDist
import numpy as np
from randi_target_response import HERE,save,sha

LAGS=[0,5,10,20]
Z=NormalDist().inv_cdf(.975)


def covariance(x,resid,indices,lag):
    scores=x*resid[:,None]
    distance=np.abs(indices[:,None]-indices[None,:])
    kernel=np.maximum(1-distance/(lag+1),0)
    bread=np.linalg.inv(x.T@x)
    cov=bread@(scores.T@kernel@scores)@bread*len(x)/(len(x)-x.shape[1])
    assert np.allclose(cov,cov.T,atol=1e-12)
    assert np.linalg.eigvalsh(cov).min()>-1e-10
    return cov


def validate():
    rng=np.random.default_rng(20260905)
    x=np.column_stack([np.ones(30),rng.normal(size=30)])
    y=rng.normal(size=30); beta=np.linalg.lstsq(x,y,rcond=None)[0]; u=y-x@beta
    indices=2*np.arange(30)
    bread=np.linalg.inv(x.T@x); scores=x*u[:,None]
    hc=bread@(scores.T@scores)@bread*30/28
    assert np.allclose(covariance(x,u,indices,0),hc,atol=1e-12)
    assert np.allclose(covariance(x,u,indices,1),hc,atol=1e-12)
    padded=np.zeros((indices[-1]+1,2));padded[indices]=scores
    meat=padded.T@padded
    for lag in range(1,6):
        cross=padded[lag:].T@padded[:-lag]
        meat+=(1-lag/6)*(cross+cross.T)
    assert np.allclose(covariance(x,u,indices,5),bread@meat@bread*30/28,atol=1e-12)


def main():
    validate()
    source=HERE/'rowland_prestate_adjustment_result.json'
    parent=HERE/'rowland_prestate_adjustment_contract.json'
    contract=save('rowland_hac_uncertainty_contract.json',{
        'question':'관측 대비의 근사 불확실성이 시행 상관 범위 가정에 따라 어떻게 달라지는가',
        'input_sha256':sha(source),'parent_contract_sha256':sha(parent),'code_sha256':sha(Path(__file__)),
        'helper_sha256':sha(HERE/'randi_target_response.py'),
        'inherit':'원 자료·시행 제외·세 모형·비인과 추정량은 기존 전 상태 계약 유지',
        'selection':'이미 본 11세션 전체의 사후 탐색; 독립 확인자료 없음',
        'source_method':'https://www.statsmodels.org/stable/generated/statsmodels.stats.sandwich_covariance.cov_hac.html',
        'adaptation':'시간 대신 원래 시행 번호 거리; 제외 시행은 추정식 score 0, 분석 행을 압축한 거리 사용 안 함',
        'kernel':'K_ij=max(1-abs(original_i-original_j)/(L+1),0)',
        'covariance':'n/(n-k) * inv(XtX) * scores.T K scores * inv(XtX); scores_i=X_i*residual_i',
        'lags_original_trials':LAGS,'interval':'beta +/- NormalQuantile(.975)*SE; 모형·약한 의존 가정 아래 점별 근사 95%',
        'report':'세 모형·네 범위 모두 보고; 다중비교 보정이나 유의성 선택 없음',
        'validation':'L=0 HC1 식, 비연속 인덱스의 간격 보존, 0 score 채운 원래 격자의 lag 합과 직접 kernel 식 일치',
        'limits':['실제 시간 등간격 아님','관측된 시간 변화로 정상성·안정 모형 가정 의심',
                  '이 선택·표본에서 95% 포함률 검증 안 됨','더 긴 의존·미측정 교란 제거 안 됨',
                  '동물 간 통합 없음','신뢰구간이 0을 제외해도 인과 식별 아님'],
        'claim_ceiling':'BIO_EVIDENCE_L1 exploratory model-conditional uncertainty'})
    rows=[]
    for row in json.loads(source.read_text(encoding='utf-8'))['rows']:
        t=np.array(row['test']);y=np.array(row['s2_delta']);idx=np.array(row['original_indices'])
        assert np.all(np.diff(idx)>0)
        z=np.column_stack([row['elapsed_seconds'],row['s1_pre'],row['s2_pre']])
        z=(z-z.mean(axis=0))/z.std(axis=0)
        models={}
        for name,cols in [('raw',0),('time_only',1),('time_prestate',3)]:
            x=np.column_stack([np.ones(len(t)),z[:,:cols],t])
            beta,_,rank,_=np.linalg.lstsq(x,y,rcond=None)
            assert rank==x.shape[1] and np.linalg.cond(x)<1e8
            assert abs(beta[-1]-row[name]['coefficient'])<1e-12
            intervals=[]
            for lag in LAGS:
                cov=covariance(x,y-x@beta,idx,lag)
                se=float(np.sqrt(cov[-1,-1]));lo=float(beta[-1]-Z*se);hi=float(beta[-1]+Z*se)
                intervals.append({'lag':lag,'se':se,'lower':lo,'upper':hi,'contains_zero':lo<=0<=hi})
            models[name]={'coefficient':float(beta[-1]),'intervals':intervals}
        rows.append({'mouse':row['mouse'],'run':row['run'],'n':len(t),'models':models})
    save('rowland_hac_uncertainty_result.json',{'contract_sha256':sha(contract),'synthetic_validation_passed':True,'rows':rows})
    print(json.dumps([{'mouse':r['mouse'],'run':r['run'],**r['models']['time_prestate']} for r in rows]))


if __name__=='__main__':main()
