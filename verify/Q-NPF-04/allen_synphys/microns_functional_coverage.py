"""기존 구조 표본에서 기능 대응 표시의 세포·연결 범위를 계산한다."""
import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path
from population_reciprocity import ROOT, sha
from superficial_ee_eligibility import save

HERE = Path(__file__).resolve().parent
DATA = ROOT / 'data/external/microns_v1718_cosyne'
NAME = 'microns_functional_coverage'


def calculate():
    with (DATA / 'v1718_cell_info.csv').open(encoding='utf-8', newline='') as f:
        cells = list(csv.DictReader(f))
    selected = [c for c in cells if all(c[k] == 'True' for k in ('is_column', 'status_axon', 'status_dendrite'))]
    prior = json.loads((HERE / 'microns_structural_inventory_result.json').read_text(encoding='utf-8'))
    assert sorted(int(c['pt_root_id']) for c in selected) == prior['selected_roots']
    assert all(c['coreg'] in ('True', 'False') for c in cells)
    byroot = {int(c['pt_root_id']): c for c in selected}
    assert len(byroot) == len(selected)
    linked = {r for r, c in byroot.items() if c['coreg'] == 'True'}
    sys.path.insert(0, str(ROOT / 'data/external/analysis_tools/arrow_reader'))
    import pyarrow.feather as feather
    table = feather.read_table(DATA / 'v1718_v1_column_synapses.feather', columns=['pre_pt_root_id', 'post_pt_root_id'])
    edges = Counter((a, b) for a, b in zip(table['pre_pt_root_id'].to_pylist(), table['post_pt_root_id'].to_pylist()) if a in byroot and b in byroot and a != b)
    strata = {}
    for threshold in (1, 3):
        kept = {e for e, n in edges.items() if n >= threshold}
        both = {e for e in kept if e[0] in linked and e[1] in linked}
        strata[str(threshold)] = dict(all_edges=len(kept), both_coreg_edges=len(both),
            one_coreg_edges=sum((a in linked) != (b in linked) for a, b in kept),
            neither_coreg_edges=sum(a not in linked and b not in linked for a, b in kept),
            both_coreg_reciprocal_dyads=sum(a < b and (b, a) in both for a, b in both),
            both_coreg_touched_cells=len({v for e in both for v in e}))
        assert len(kept) == prior['thresholds'][str(threshold)]['directed_edges']
    return dict(all_cells=len(cells), all_coreg_cells=sum(c['coreg'] == 'True' for c in cells),
        selected_cells=len(selected), selected_coreg_cells=len(linked),
        selected_types=dict(Counter(c['broad_type'] or 'unknown' for c in selected)),
        selected_coreg_types=dict(Counter(byroot[r]['broad_type'] or 'unknown' for r in linked)),
        strata=strata, linked=[dict(nucleus_id=int(byroot[r]['id']), root_id=r) for r in sorted(linked)],
        missing=['session/scan_idx/unit_id identity map', 'per-unit response data or explicitly model-derived properties', 'simultaneously observed pair coverage'],
        status='FUNCTIONAL_IDENTITY_LOOKUP_NEEDED_NOT_FUNCTIONAL_CONNECTIVITY_RESULT')


def main():
    p = argparse.ArgumentParser(); p.add_argument('--verify', action='store_true'); args = p.parse_args()
    paths = [DATA / n for n in ('v1718_cell_info.csv', 'v1718_v1_column_synapses.feather', 'preprocessing_celltypes_v1718.ipynb')]
    paths += [HERE / 'microns_structural_inventory_result.json']
    if args.verify:
        c = json.loads((HERE / (NAME + '_contract.json')).read_text(encoding='utf-8'))
        assert c['code_sha256'] == sha(Path(__file__))
        for path, digest in c['inputs'].items(): assert sha(ROOT / path) == digest
    else:
        save(NAME + '_contract.json', dict(
            question='기존 MICrONS V1 구조 표본에서 수동 기능 대응 표시가 있는 세포와 연결은 얼마나 되는가?',
            selection='기존 양쪽 교정 column 1348세포 유지. coreg 값으로 표본을 교체하지 않고 양 끝/한 끝/없음으로 구분. 기존 시냅스수1/3 문턱 유지.',
            meaning='coreg는 전처리 notebook에서 coregistration_manual_v4 nucleus id 포함 여부. 기능 파형·동일 스캔·자극 반응 확보를 뜻하지 않는다.',
            limits='한 표본의 조건부 범위 점검. SynPhys와 동일 세포 대응 아님. 관측되지 않은 edge는 export 미표지. 기능 연결·인과 검정 아님. L0 입력 범위.',
            code_sha256=sha(Path(__file__)), inputs={p.relative_to(ROOT).as_posix(): sha(p) for p in paths}))
    result = dict(contract_sha256=sha(HERE / (NAME + '_contract.json')), analysis=calculate())
    if args.verify:
        assert result == json.loads((HERE / (NAME + '_result.json')).read_text(encoding='utf-8'))
        print('MICRONS_FUNCTIONAL_COVERAGE_VERIFIED')
    else:
        save(NAME + '_result.json', result)
        print(json.dumps({k:v for k,v in result['analysis'].items() if k != 'linked'}, indent=2))


if __name__ == '__main__': main()
