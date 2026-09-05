"""정적 수동 대응표를 nucleus ID와 좌표로 기존 구조 표본에 연결한다."""
import argparse
import csv
import gzip
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from population_reciprocity import ROOT, sha
from superficial_ee_eligibility import save

HERE=Path(__file__).resolve().parent
DATA=ROOT/'data/external/microns_coregistration_v1412'
CELLS=ROOT/'data/external/microns_v1718_cosyne/v1718_cell_info.csv'
NAME='microns_coregistration_join'


def read(n): return json.loads((HERE/n).read_text(encoding='utf-8'))


def analyze():
    receipt=read('microns_coregistration_acquisition.json')
    for r in receipt['files']: assert sha(ROOT/r['path'])==r['sha256']
    with (DATA/'coregistration_manual_v4_merged_header.csv').open(newline='') as f:
        header=[r[0] for r in csv.reader(f) if r]
    with gzip.open(DATA/'coregistration_manual_v4_merged.csv.gz','rt',newline='') as f:
        rows=list(csv.DictReader(f,fieldnames=header))
    with CELLS.open(encoding='utf-8',newline='') as f: cells=list(csv.DictReader(f))
    prior=read('microns_functional_coverage_result.json')['analysis']
    targets={r['nucleus_id']:r['root_id'] for r in prior['linked']}
    bynucleus={int(c['id']):c for c in cells}
    assert len(bynucleus)==len(cells)
    assert len(targets)==486
    unit_targets=defaultdict(set)
    for r in rows:
        key=tuple(int(r[k]) for k in ('session','scan_idx','unit_id'))
        unit_targets[key].add(int(r['target_id']))
    matches=[]; rejected=[]; scans=defaultdict(set); fields=defaultdict(set)
    for r in rows:
        n=int(r['target_id'])
        if n not in targets: continue
        c=bynucleus[n]; key=tuple(int(r[k]) for k in ('session','scan_idx','unit_id'))
        coord=all(int(r['pt_position_'+k])==int(c['pt_position_'+k]) for k in 'xyz')
        conflict=len(unit_targets[key])!=1
        if not coord or conflict:
            rejected.append(dict(row_id=int(r['id']),nucleus_id=n,coordinate_match=coord,unit_conflict=conflict));continue
        root=targets[n];scan=key[:2];field=scan+(int(r['field']),)
        scans[root].add(scan); fields[root].add(field)
        matches.append(dict(nucleus_id=n,root_v1718=root,root_v1412=int(r['pt_root_id']),
            session=key[0],scan_idx=key[1],unit_id=key[2],field=int(r['field']),
            residual=float(r['residual']),score=float(r['score']),source_row_id=int(r['id'])))
    sys.path.insert(0,str(ROOT/'data/external/analysis_tools/arrow_reader'))
    import pyarrow.feather as feather
    table=feather.read_table(ROOT/'data/external/microns_v1718_cosyne/v1718_v1_column_synapses.feather',columns=['pre_pt_root_id','post_pt_root_id'])
    roots=set(targets.values())
    edges=Counter((a,b) for a,b in zip(table['pre_pt_root_id'].to_pylist(),table['post_pt_root_id'].to_pylist()) if a in roots and b in roots and a!=b)
    summaries={}
    for threshold in (1,3):
        ee={e for e,n in edges.items() if n>=threshold}
        common={e for e in ee if scans[e[0]] & scans[e[1]]}
        summaries[str(threshold)]=dict(target_edges=len(ee),mapped_both_edges=sum(bool(scans[a]) and bool(scans[b]) for a,b in ee),
            common_scan_edges=len(common),common_field_edges=sum(bool(fields[a]&fields[b]) for a,b in ee),
            common_scan_reciprocal_dyads=sum(a<b and (b,a) in common for a,b in common))
    per_scan=defaultdict(set)
    for root,ss in scans.items():
        for s in ss: per_scan[s].add(root)
    return dict(archive_rows=len(rows),archive_unique_nuclei=len({int(r['target_id']) for r in rows}),
        archive_conflicted_units=sum(len(v)>1 for v in unit_targets.values()),
        target_cells=486,matched_cells=len({r['nucleus_id'] for r in matches}),matched_rows=len(matches),
        roots_changed_rows=sum(r['root_v1718']!=r['root_v1412'] for r in matches),
        missing_nuclei=sorted(set(targets)-{r['nucleus_id'] for r in matches}),rejected=rejected,
        multiple_units_cells=sum(v>1 for v in Counter(r['nucleus_id'] for r in matches).values()),
        summaries=summaries,per_scan=[dict(session=s[0],scan_idx=s[1],cells=len(v)) for s,v in sorted(per_scan.items())],matches=matches)


def main():
    p=argparse.ArgumentParser();p.add_argument('--verify',action='store_true');args=p.parse_args()
    inputs=[CELLS,HERE/'microns_coregistration_acquisition.json',HERE/'microns_functional_coverage_result.json',ROOT/'data/external/microns_v1718_cosyne/v1718_v1_column_synapses.feather']
    if args.verify:
        c=read(NAME+'_contract.json');assert c['code_sha256']==sha(Path(__file__))
        for p,h in c['inputs'].items():assert sha(ROOT/p)==h
    else:
        save(NAME+'_contract.json',dict(question='기존486개 coreg 표시 세포를 v1412 수동 대응표에 결박하고 공유 scan 범위를 확인할 수 있는가?',
            rule='정적 merged CSV의 target_id를 세포표 nucleus id와 연결. xyz 좌표 완전 일치와 session/scan/unit의 유일 nucleus 조건을 요구. root 판본 변화는 별도 기록. 기존486개만 대상, 결과에 따른 교체 없음.',
            limits='v1412→v1718 정적 nucleus 대응이며 최신 수동 annotation 동일성은 미확인. 같은 scan/field는 기록 분모 후보이며 유효 동시 시계열 확보 아님. 원파형·품질·자극 결박 필요. L0 입력 검사.',
            code_sha256=sha(Path(__file__)),inputs={p.relative_to(ROOT).as_posix():sha(p) for p in inputs}))
    result=dict(contract_sha256=sha(HERE/(NAME+'_contract.json')),analysis=analyze())
    if args.verify:
        assert result==read(NAME+'_result.json');print('MICRONS_COREGISTRATION_JOIN_VERIFIED')
    else:
        save(NAME+'_result.json',result)
        print(json.dumps({k:v for k,v in result['analysis'].items() if k!='matches'},indent=2))


if __name__=='__main__':main()
