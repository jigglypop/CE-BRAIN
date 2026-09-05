"""상호 연결의 단순 참조값에 세포 종류·거리 층화를 추가한 사후 민감도 분석."""
import argparse
import csv
import json
import sqlite3
from collections import defaultdict,Counter
from pathlib import Path
from population_reciprocity import DB,TABLE,HERE,sha

CONTRACT=HERE/'reciprocity_stratified_contract.json'
OUTPUT=HERE/'reciprocity_stratified_result.json'


def distance_bin(value):
    if value=='':return 'missing'
    value=float(value)
    if value<0:raise ValueError('negative distance')
    return next((label for hi,label in [(50e-6,'0-50um'),(100e-6,'50-100um'),(200e-6,'100-200um')] if value<hi),'200um+')


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--verify',action='store_true');args=parser.parse_args()
    spec=dict(timing='post-result sensitivity, not independent confirmation',
        purpose='Measure how reciprocity reference changes after fixing more observed heterogeneity',
        strata=['experiment','experiment+ordered nonsynaptic cell classes','experiment+ordered nonsynaptic cell classes+distance bins'],
        bins_m=[0,50e-6,100e-6,200e-6],missing_distance='separate stratum',
        expectation='same stratum k(k-1)/(n(n-1)); different strata (k1/n1)*(k2/n2), independent shuffles across strata',
        limitations='sparse strata can force labels and erase comparison power; no p-values, no causal or population-independent claim',
        table_sha256=sha(TABLE),db_sha256=sha(DB),code_sha256=sha(Path(__file__)))
    if CONTRACT.exists():assert spec==json.loads(CONTRACT.read_text(encoding='utf-8'))
    elif args.verify:raise RuntimeError('계약 없음')
    else:
        with CONTRACT.open('x',encoding='utf-8') as stream:json.dump(spec,stream,indent=2)
    with TABLE.open(encoding='utf-8',newline='') as stream:dyads=list(csv.DictReader(stream))
    with sqlite3.connect(DB.as_uri()+'?mode=ro',uri=True) as db:
        classes={r[0]:r[1] or 'unknown' for r in db.execute('SELECT id,cell_class_nonsynaptic FROM cell')}
    outputs={}
    for level in range(3):
        counts=defaultdict(Counter);assignments=[]
        for d in dyads:
            a=classes[int(d['cell_a'])];b=classes[int(d['cell_b'])];eid=int(d['experiment_id'])
            dist=distance_bin(d['distance_m']);keys=[]
            for pre,post,label in ((a,b,int(d['label_ab'])),(b,a,int(d['label_ba']))):
                key=(eid,)+( (pre,post) if level>=1 else ())+( (dist,) if level>=2 else ())
                counts[key]['n']+=1;counts[key]['k']+=label;keys.append(key)
            assignments.append(keys)
        species=defaultdict(lambda:dict(dyads=0,observed=0,expected=0.,dyads_with_any_movable_direction=0,dyads_with_both_movable_directions=0))
        for d,(a,b) in zip(dyads,assignments):
            ca=counts[a];cb=counts[b]
            expected=ca['k']*(ca['k']-1)/(ca['n']*(ca['n']-1)) if a==b else (ca['k']/ca['n'])*(cb['k']/cb['n'])
            entry=species[d['species']];entry['dyads']+=1;entry['observed']+=int(d['positive_directions'])==2;entry['expected']+=expected
            movable=[0<c['k']<c['n'] for c in (ca,cb)]
            entry['dyads_with_any_movable_direction']+=any(movable)
            entry['dyads_with_both_movable_directions']+=all(movable)
        outputs[spec['strata'][level]]=dict(strata_count=len(counts),species=dict(species))
    previous=json.loads((HERE/'population_reciprocity_result.json').read_text(encoding='utf-8'))
    for species,value in outputs[spec['strata'][0]]['species'].items():
        assert abs(value['expected']-previous['analysis']['species'][species]['exchangeable_label_expected_reciprocal'])<1e-8
    result=dict(contract_sha256=sha(CONTRACT),analysis=outputs)
    if args.verify:
        assert result==json.loads(OUTPUT.read_text(encoding='utf-8'));print('STRATIFIED_REFERENCE_REPRODUCED')
    else:
        with OUTPUT.open('x',encoding='utf-8') as stream:json.dump(result,stream,indent=2)
    print(json.dumps(outputs,indent=2))


if __name__=='__main__':main()
