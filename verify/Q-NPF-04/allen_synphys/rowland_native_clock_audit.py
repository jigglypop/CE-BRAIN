"""행동 시계 변환 누락과 원래 획득 시각의 보존 상태를 구분한다."""
import json
from pathlib import Path
import numpy as np
from rowland_sessions import read_sessions
from rowland_symbolic_reader import array
from randi_target_response import HERE, save, sha


def main():
    base=Path('data/external/cortical_propagation_2023')
    sessions,status=read_sessions(base/'sessions_lite_flu_2022-08-11.pkl')
    assert status['pickle_complete'] and len(sessions)==11
    rows=[]
    for s in sessions:
        idx=array(s['nonnan_trials']); g=array(s['galvo_ms'])
        b=array(s['tstart_galvo']); a=array(s['trial_start'])
        assert g.shape==b.shape==a.shape
        assert np.isfinite(b).all() and np.all(np.diff(b)>0)
        assert np.isfinite(a).all() and np.all(np.diff(a)>0)
        ok=np.isfinite(g)
        # 20 kHz is the author's source default, not an independently measured rate.
        native_seconds=(b-b[0])/20000.
        x=np.column_stack([np.ones(ok.sum()),native_seconds[ok]])
        beta=np.linalg.lstsq(x,g[ok]/1000.,rcond=None)[0]
        residual=g[ok]/1000.-x@beta
        missing=[]
        for export_index,original in enumerate(idx):
            if np.isfinite(g[original]):continue
            y=array(s['behaviour_trials'])[:,export_index,:]
            missing.append({'original_index':int(original),'export_index':export_index,
                            'native_sample':float(b[original]),'trial_start_ms':float(a[original]),
                            'nominal_count':int(array(s['trial_subsets'])[export_index]),
                            'neural_all_finite':bool(np.isfinite(y).all()),
                            'native_prev_gap_samples':float(b[original]-b[original-1]) if original>0 else None,
                            'native_next_gap_samples':float(b[original+1]-b[original]) if original+1<len(b) else None})
        assert all(r['neural_all_finite'] for r in missing)
        rows.append({'mouse':s['mouse'],'run':s['run_number'],'original_n':len(b),
                     'exported_n':len(idx),'native_finite_strictly_increasing':True,
                     'assumed_rate_hz':20000,'native_to_behavior_slope':float(beta[1]),
                     'affine_residual_max_seconds':float(np.max(np.abs(residual))),
                     'affine_residual_rms_seconds':float(np.sqrt(np.mean(residual**2))),
                     'missing_behavior_clock':missing})
    assert sum(len(r['missing_behavior_clock']) for r in rows)==9
    result={'question':'행동 시계 변환 누락 시행의 원래 획득 시각 보존 여부',
            'code_sha256':sha(Path(__file__)), 'source_sha256':sha(base/'author_Session.py'),
            'parent_sha256':sha(HERE/'rowland_trial_history_result.json'),'rows':rows,
            'decision':'신경 배열 분석의 원래 시각 후보를 확보; 행동 시계 누락값을 보간하거나 덮어쓰지 않음',
            'limits':['20kHz는 소스 기본값; 원래 획득 메타데이터 미확인',
                      '원래 프레임 시계 부재로 이벤트-프레임 정렬을 독립 재검증하지 못함',
                      '선형 대응 잔차는 진단이며 복구된 행동 시각이 아님']}
    save('rowland_native_clock_audit_result.json',result)
    for r in rows:print(r['mouse'],r['run'],len(r['missing_behavior_clock']),round(r['native_to_behavior_slope'],7),round(r['affine_residual_max_seconds'],4))


if __name__=='__main__':main()
