"""시행 로그의 전체 표적 경로와 자극/catch 반복 대응을 확인한다."""
import hashlib
import json
import re
from pathlib import Path, PureWindowsPath
import numpy as np
from rowland_sessions import read_sessions
from rowland_symbolic_reader import array
from randi_target_response import HERE, save, sha


def parse(info):
    if info=='all_cells_stimulated':return None
    m=re.fullmatch(r'Subset cells experiment, (Go trial, stimulating|Nogo Trial,) (\d+) cells\. File path is (.+)',info)
    assert m,info
    path=str(PureWindowsPath(m[3])).casefold()
    assert int(PureWindowsPath(path).name.split('_')[0])==int(m[2])
    return {'type':'catch' if m[1]=='Nogo Trial,' else 'test','requested_count':int(m[2]),'path':path}


def main():
    ss,status=read_sessions(Path('data/external/cortical_propagation_2023/sessions_lite_flu_2022-08-11.pkl'))
    assert status['pickle_complete'] and len(ss)==11
    rows=[]
    for s in ss:
        records=[parse(i) for i in s['subsets'].state['trial_info']]
        nominal=array(s['subsets'].state['trial_subsets'])
        idx=array(s['nonnan_trials']);lookup={int(i):j for j,i in enumerate(idx)}
        targets=array(s['is_target'])[:,:,0]
        groups={}
        for i,record in enumerate(records):
            if record is None:
                assert nominal[i]==150;continue
            kind=record['type'];assert nominal[i]==(0 if kind=='catch' else record['requested_count'])
            group=groups.setdefault(record['path'],{'requested_count':record['requested_count'],
                'test_indices':[],'catch_indices':[],'exported_test_indices':[],
                'exported_catch_indices':[],'test_mask_hashes':[]})
            assert group['requested_count']==record['requested_count']
            group[kind+'_indices'].append(i)
            if i in lookup:
                group['exported_'+kind+'_indices'].append(i)
                mask=targets[:,lookup[i]]
                if kind=='catch':assert not mask.any()
                else:group['test_mask_hashes'].append(hashlib.sha256(np.packbits(mask).tobytes()).hexdigest())
        for g in groups.values():g['test_mask_hashes']=sorted(set(g['test_mask_hashes']))
        shared=[p for p,g in groups.items() if g['exported_test_indices'] and g['exported_catch_indices']]
        inconsistent=[p for p,g in groups.items() if len(g['test_mask_hashes'])>1]
        rows.append({'mouse':s['mouse'],'run':s['run_number'],'patterns':groups,
                     'exported_shared_paths':shared,'inconsistent_test_mask_paths':inconsistent,
                     'shared_test_n':sum(len(groups[p]['exported_test_indices']) for p in shared),
                     'shared_catch_n':sum(len(groups[p]['exported_catch_indices']) for p in shared),
                     'shared_min_two_each_paths':sum(len(groups[p]['exported_test_indices'])>=2 and len(groups[p]['exported_catch_indices'])>=2 for p in shared)})
    result={'question':'표적 경로 반복과 자극/catch 대응을 관측 로그에서 확인',
            'code_sha256':sha(Path(__file__)),
            'source_sha256':sha(Path('data/external/cortical_propagation_2023/blimp_experiments_easy_test.py')),
            'parent_sha256':sha(HERE/'rowland_assignment_source_inventory.json'),'rows':rows,
            'limits':['동일 경로는 실제 광출력·원래 파일 내용의 독립 증명이 아님',
                      'catch 저장 마스크는 0; catch 표적 좌표를 복원한 것이 아님',
                      '경로 대응은 배정 확률이나 인과 식별을 보장하지 않음']}
    save('rowland_pattern_inventory_result.json',result)
    for r in rows:print(r['mouse'],r['run'],len(r['patterns']),len(r['exported_shared_paths']),r['shared_test_n'],r['shared_catch_n'],r['shared_min_two_each_paths'],len(r['inconsistent_test_mask_paths']))


if __name__=='__main__':main()
