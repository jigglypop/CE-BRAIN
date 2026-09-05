"""전체 soma ID 중복 실패를 보존하고 시냅스 끝점의 고유 대응을 별도로 감사한다."""
import csv,json
from collections import Counter,defaultdict
from pathlib import Path
from reference_spike_audit import sha

HERE=Path(__file__).resolve().parent
DATA=HERE.parents[2]/'data/external/microns_pinky_v185'
contract=dict(reason='original inventory failed global soma root uniqueness; preserve failure, check whether duplicated roots affect synapse endpoints',
    policy='retain all soma rows; require exactly one row for every synapse endpoint; no coordinate analysis or population denominator',thresholds=[1,3],
    original_contract_sha256=sha(HERE/'pinky_inventory_contract.json'),code_sha256=sha(Path(__file__)))
cp=HERE/'pinky_identity_followup_contract.json'
if cp.exists():assert json.loads(cp.read_text())==contract
else:cp.write_text(json.dumps(contract,indent=2),encoding='utf-8')
for r in json.loads((HERE/'pinky_acquisition_receipt.json').read_text())['files']:
    assert sha(HERE.parents[2]/r['path'])==r['sha256']
cells=list(csv.DictReader((DATA/'soma_valence_v185.csv').open(newline='')))
syn=list(csv.DictReader((DATA/'soma_subgraph_synapses_spines_v185.csv').open(newline='')))
mapping=defaultdict(list)
for r in cells:mapping[int(r['pt_root_id'])].append(r)
duplicates={str(k):v for k,v in mapping.items() if len(v)>1}
assert len({int(r['id']) for r in syn})==len(syn)
edges=Counter((int(r['pre_root_id']),int(r['post_root_id'])) for r in syn)
roots={i for p in edges for i in p}
assert all(len(mapping[r])==1 for r in roots)
assert all(u!=v for u,v in edges)
summary=[]
for t in contract['thresholds']:
    chosen={p for p,n in edges.items() if n>=t}
    mutual=sum((v,u) in chosen for u,v in chosen)//2
    summary.append(dict(threshold=t,directed_edges=len(chosen),mutual_pairs=mutual,one_way_pairs=len(chosen)-2*mutual))
output=dict(contract_sha256=sha(cp),original_inventory_status='FAILED_GLOBAL_SOMA_ROOT_UNIQUENESS',
    all_soma_rows=len(cells),distinct_soma_roots=len(mapping),duplicate_roots=duplicates,
    duplicate_roots_in_endpoints=sorted(set(map(int,duplicates))&roots),synapses=len(syn),endpoint_cells=len(roots),
    endpoint_labels=dict(Counter(mapping[i][0]['cell_type'] for i in roots)),thresholds=summary,
    anomalous_nm_rows=sum(int(r['soma_x_nm'])==int(r['soma_y_nm']) and int(r['soma_z_nm'])==10*int(r['soma_x_nm']) for r in cells),
    status='ENDPOINT_IDENTITIES_UNIQUE_POSITIVE_GRAPH_ONLY_COORDINATES_AND_POPULATION_PENDING')
out=HERE/'pinky_identity_followup_result.json'
if out.exists():assert json.loads(out.read_text())==output
else:out.write_text(json.dumps(output,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in output.items() if k!='duplicate_roots'},indent=2))
