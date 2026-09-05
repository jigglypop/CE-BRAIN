"""원자료의 중복·자기연결을 있는 그대로 기록한다. 기존 실패 영수증은 보존한다."""
import csv,json
from collections import Counter,defaultdict
from pathlib import Path
from reference_spike_audit import sha
HERE=Path(__file__).resolve().parent
DATA=HERE.parents[2]/'data/external/microns_pinky_v185'
receipt=json.loads((HERE/'pinky_acquisition_receipt.json').read_text())
for r in receipt['files']:assert sha(HERE.parents[2]/r['path'])==r['sha256']
cells=list(csv.DictReader((DATA/'soma_valence_v185.csv').open(newline='')))
syn=list(csv.DictReader((DATA/'soma_subgraph_synapses_spines_v185.csv').open(newline='')))
mapping=defaultdict(list)
for r in cells:mapping[int(r['pt_root_id'])].append(r)
edges=Counter((int(r['pre_root_id']),int(r['post_root_id'])) for r in syn)
roots={i for p in edges for i in p}
assert len({r['id'] for r in syn})==len(syn) and all(len(mapping[i])==1 for i in roots)
duplicate={str(i):r for i,r in mapping.items() if len(r)>1}
summary=[]
for t in (1,3):
    selected={p for p,n in edges.items() if p[0]!=p[1] and n>=t}
    mutual=sum((v,u) in selected for u,v in selected)//2
    summary.append(dict(threshold=t,nonself_directed_edges=len(selected),mutual_pairs=mutual,one_way_pairs=len(selected)-2*mutual))
result=dict(code_sha256=sha(Path(__file__)),acquisition_sha256=sha(HERE/'pinky_acquisition_receipt.json'),
    retained_failures=['pinky_structural_inventory:global soma root uniqueness false',
                      'pinky_identity_followup:no self links false; not treated as corrupt data'],
    soma_rows=len(cells),distinct_soma_roots=len(mapping),duplicate_roots=duplicate,
    duplicated_roots_in_synapse_endpoints=sorted(set(map(int,duplicate))&roots),
    synapse_rows=len(syn),endpoint_cells=len(roots),endpoint_labels=dict(Counter(mapping[i][0]['cell_type'] for i in roots)),
    self_links=[dict(root_id=u,synapses=n) for (u,v),n in edges.items() if u==v],thresholds=summary,
    anomalous_coordinate_rows=sum(int(r['soma_x_nm'])==int(r['soma_y_nm']) and int(r['soma_z_nm'])==10*int(r['soma_x_nm']) for r in cells),
    status='OBSERVED_POSITIVE_GRAPH_INVENTORY_ONLY_POPULATION_AND_COORDINATES_UNRESOLVED')
out=HERE/'pinky_source_findings.json'
if out.exists():assert json.loads(out.read_text())==result
else:out.write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='duplicate_roots'},indent=2))
