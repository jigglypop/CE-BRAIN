"""동일 측정식을 적용한 두 개체 결과를 유지 전압별로 병렬 보고한다."""
import json
from pathlib import Path
from population_reciprocity import sha
from superficial_ee_eligibility import save

HERE=Path(__file__).resolve().parent


def main():
    before=HERE/'different_donor_holding_groups_result.json'
    after=HERE/'next_donor_vc_response_result.json'
    old=json.loads(before.read_text(encoding='utf-8'))['vc_analysis']
    new=json.loads(after.read_text(encoding='utf-8'))['groups']
    rows=[]
    for donor,groups in [('581866',old),('593646',new)]:
        for group in groups:
            summary=group.get('summary') or group['analysis']['summary']
            condition=group['condition']
            for pulse in summary:
                rows.append(dict(donor=donor,post_holding_V=condition['post_holding_value'],
                    pre_holding_V=condition['pre_holding_value'],sweeps=group['sweeps'],**pulse))
    assert len(rows)==48 and all(r['n']==5 for r in rows)
    save('next_donor_vc_comparison_result.json',dict(
        previous_sha256=sha(before),next_sha256=sha(after),code_sha256=sha(Path(__file__)),records=rows,
        interpretation='개체별·전압별 기술 비교. 합동 평균·효과검정 없음. 알려진 양성 연결 조건부이며 표본 수는2개체2연결, 조건별5시행. 생물 상태와펄스길이가완전히같지않음.'))
    for r in rows:
        if r['pulse'] in (1,9):
            print(r['donor'],round(r['post_holding_V']*1000),r['pulse'],round(r['mean_pA'],4),r['inward_count'],r['within_control_range'])


if __name__=='__main__':main()
