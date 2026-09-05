"""공개 생리 QC 규칙과 단위를 확인하고 제한 모집단을 고정한다."""
import csv
import hashlib
import io
import json
import math
import zipfile
from collections import Counter,defaultdict
from pathlib import Path
from population_reciprocity import ROOT,sha
from superficial_ee_eligibility import save

HERE=Path(__file__).resolve().parent;archive=ROOT/'data/external/planert2025_human/humandata.zip'
assert sha(archive)=='6b0d7244dec5c665a88d0d1828ae842d084bb737a6df9f86561d53d8564c4bfd'
flags=['resting_bool','access_bool','false_high_access_bool','false_low_access_bool']
save('planert2025_qc_inventory_contract.json',{
    'question':'Which unambiguous directional dyads have paired source-defined intrinsic QC and finite pia/Rin/rheobase?',
    'scope':'exclude whole clusters with duplicate directed keys; s11 and type1 both cells; exact internal public ID join',
    'qc':'all four exported flags true at each endpoint; finite piadistance<1200 and R_in>0 and rheo>0; no etype or UMAP selection',
    'units':{'R_in':'MOhm','rheo':'pA','piadistance':'um'},
    'checks':'removal_boolean vs conjunction reported, not assumed; metadata join and reverse row; source hashes',
    'limits':'author QC may use pooled AP/access distribution; not fully independent validation preprocessing; raw traces and curation sheet unavailable',
    'archive_sha256':sha(archive),'code_sha256':sha(Path(__file__))})
with zipfile.ZipFile(archive) as z:
    def read(n):return list(csv.DictReader(io.StringIO(z.read('humandata/data_tables/'+n).decode('utf-8-sig'))))
    cells_rows=read('tcell_all_psdn.csv');rows=read('tconnection_all_psdn.csv')
    names=['humandata/data_processing/extract/extract_removal_boolean.m','humandata/data_processing/extract/extract_rheobase.m',
           'humandata/data_processing/compute/input_resistance_cc_param.m',
           'humandata/data_visualization/R_scripts/clust_intrinsic/clust_intrinsic_.Rmd']
    sources={n:z.read(n) for n in names}
text={n:b.decode('utf-8').replace('\r','') for n,b in sources.items()}
assert 'tcell.removal_boolean(c) = all' in text[names[0]] and 'The unit is pA' in text[names[1]]
assert 'Mega-Ohm' in text[names[2]] and 'tcell$piadistance < 1200' in text[names[3]]
cells={r['cellid']:r for r in cells_rows};assert len(cells)==len(cells_rows)
def good(c):return all(c[f]=='1' for f in flags)
mismatches=[c['cellid'] for c in cells_rows if (c['removal_boolean']=='1')!=good(c)]
group=defaultdict(list)
for r in rows:group[r['cellid_pre'],r['cellid_post']].append(r)
bad={r['clusterid'] for rr in group.values() if len(rr)>1 for r in rr}
rows=[r for r in rows if r['clusterid'] not in bad];lookup={(r['cellid_pre'],r['cellid_post']):r for r in rows};assert len(lookup)==len(rows)
counts=Counter();selected=[]
def num(s):
    try:return float(s)
    except ValueError:return float('nan')
for r in rows:
    a,b=r['cellid_pre'],r['cellid_post']
    if a>=b:continue
    rev=lookup[b,a];ca,cb=cells[a],cells[b]
    assert ca['patientid']==cb['patientid']==r['patientid'] and ca['clusterid']==cb['clusterid']==r['clusterid']
    if r['synapse_type']!='s11' or ca['type']!='1' or cb['type']!='1':continue
    if int(r['connected'])+int(rev['connected'])!=1:continue
    counts['oneway_type1']+=1
    if not(good(ca) and good(cb)):continue
    counts['both_four_flags']+=1
    values=[[num(c[f]) for f in ('piadistance','R_in','rheo')] for c in (ca,cb)]
    if not all(math.isfinite(v) for vv in values for v in vv):continue
    counts['also_finite_three']+=1
    if not all(d<1200 and ri>0 and rh>0 for d,ri,rh in values):continue
    counts['eligible']+=1
    selected.append({'a':a,'b':b,'patient':r['patientid'],'cluster':r['clusterid'],'y':int(r['connected']),
                     'pia':[v[0] for v in values],'R_in':[v[1] for v in values],'rheo':[v[2] for v in values]})
out={'contract_sha256':sha(HERE/'planert2025_qc_inventory_contract.json'),
     'source_member_sha256':{n:hashlib.sha256(b).hexdigest() for n,b in sources.items()},
     'removal_conjunction_mismatches':len(mismatches),'mismatch_cell_ids':mismatches,
     'all_cells_four_flags_pass':sum(good(c) for c in cells_rows),'counts':dict(counts),
     'patients':len({r['patient'] for r in selected}),'clusters':len({r['cluster'] for r in selected}),
     'selected':selected,'status':'QC_SCOPE_FROZEN; no effect estimated; author QC retained as conditioned selection'}
save('planert2025_qc_inventory_result.json',out)
print(json.dumps({k:v for k,v in out.items() if k not in ('selected','source_member_sha256','mismatch_cell_ids')},indent=2))
