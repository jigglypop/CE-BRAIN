"""경로별 전후반 반복 비교의 표본 적격성을 결과값 없이 점검한다."""
import json
from pathlib import Path
from randi_target_response import HERE, save, sha


def main():
    parents=['rowland_pattern_contrast_result.json','rowland_native_clock_comparison_result.json']
    save('rowland_pattern_time_support_contract.json',{
        'question':'공유 표적 경로에 전후반 각각 test/catch 반복이 있는가',
        'code_sha256':sha(Path(__file__)), 'parents':{p:sha(HERE/p) for p in parents},
        'split':'세션 전체 보존 catch/test의 최초·최후 원래 획득 시각 중점; 전반<중점, 후반>=중점',
        'counts':'기존 이력 제한 및 공유 경로 집합에서 네 칸의 시행 수',
        'thresholds':'각 칸 1회 이상과 2회 이상을 모두 보고; 검정력 보장 아님',
        'rule':'결과값을 읽어 분할·경로·기준을 바꾸지 않음',
        'limits':['표본 적격성 점검; 신경 효과 검증 아님','시간적 간격 및 신호 독립성을 보장하지 않음']})
    patterns=json.loads((HERE/parents[0]).read_text(encoding='utf-8'))['rows']
    responses={(r['mouse'],r['run']):r for r in json.loads((HERE/parents[1]).read_text(encoding='utf-8'))['rows']}
    rows=[]
    for p in patterns:
        r=responses[(p['mouse'],p['run'])]
        times=dict(zip(r['original_indices'],r['native_samples']))
        cut=(min(times.values())+max(times.values()))/2
        groups=[]
        for g in p['groups']:
            counts={}
            for kind in ['test','catch']:
                indices=g[kind+'_indices']
                counts['early_'+kind]=sum(times[i]<cut for i in indices)
                counts['late_'+kind]=sum(times[i]>=cut for i in indices)
                assert counts['early_'+kind]+counts['late_'+kind]==g[kind+'_n']
            groups.append({'path':g['path'],'counts':counts,'minimum_cell_n':min(counts.values())})
        rows.append({'mouse':p['mouse'],'run':p['run'],'cut_native_samples':cut,
                     'shared_paths':len(groups),'all_four_at_least_one':sum(g['minimum_cell_n']>=1 for g in groups),
                     'all_four_at_least_two':sum(g['minimum_cell_n']>=2 for g in groups),'groups':groups})
    assert len(rows)==11
    save('rowland_pattern_time_support_result.json',{'contract_sha256':sha(HERE/'rowland_pattern_time_support_contract.json'),'rows':rows})
    for r in rows:print(r['mouse'],r['run'],r['shared_paths'],r['all_four_at_least_one'],r['all_four_at_least_two'])


if __name__=='__main__':main()
