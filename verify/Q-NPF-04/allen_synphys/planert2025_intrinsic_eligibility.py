"""연결 방향과 별도 세포 생리 측정의 직접 ID 대응·가용성 조사."""
import csv
import io
import json
import math
import zipfile
from collections import Counter
from pathlib import Path
from population_reciprocity import ROOT,sha
from superficial_ee_eligibility import save

HERE=Path(__file__).resolve().parent;archive=ROOT/'data/external/planert2025_human/humandata.zip'
assert sha(archive)=='6b0d7244dec5c665a88d0d1828ae842d084bb737a6df9f86561d53d8564c4bfd'
fields=['piadistance','R_in','rheo','V_m','sag']
save('planert2025_intrinsic_eligibility_contract.json',{
    'question':'Can independently recorded intrinsic physiology be joined to directed connections within the same public release?',
    'scope':'exact public cell IDs within Planert release; no Peng pseudonym matching; no effect fit',
    'fields':fields,'exclusions':'no QC flag interpretation yet; count finite cases only; no etype, UMAP or connectivity-derived predictors',
    'gate':'unique cells and pair IDs, both endpoints found, patient/cluster consistent, reverse directions available',
    'limits':'same research lineage not independent replication; QC, units, inclusion and cohort provenance required before model fit',
    'archive_sha256':sha(archive),'code_sha256':sha(Path(__file__))})
def finite(v):
    try:return math.isfinite(float(v))
    except (ValueError,TypeError):return False
with zipfile.ZipFile(archive) as z:
    def read(n):return list(csv.DictReader(io.StringIO(z.read('humandata/data_tables/'+n).decode('utf-8-sig'))))
    cells_rows=read('tcell_all_psdn.csv');rows=read('tconnection_all_psdn.csv')
cells={r['cellid']:r for r in cells_rows};assert len(cells)==len(cells_rows)
lookup={(r['cellid_pre'],r['cellid_post']):r for r in rows};assert len(lookup)==len(rows)
counts=Counter();availability=Counter();candidate_patients=set();flags={k:Counter() for k in ('removal_boolean','resting_bool','access_bool','is_pc')}
for c in cells_rows:
    for k in flags:flags[k][c[k]]+=1
for r in rows:
    a,b=r['cellid_pre'],r['cellid_post']
    if a not in cells or b not in cells:counts['missing_endpoint_rows']+=1;continue
    ca,cb=cells[a],cells[b]
    assert ca['clusterid']==cb['clusterid']==r['clusterid']
    assert ca['patientid']==cb['patientid']==r['patientid']
    counts['joined_rows']+=1
    rev=lookup.get((b,a))
    if rev is None:counts['missing_reverse_rows']+=1;continue
    if a>=b:continue
    counts['paired_dyads']+=1
    assert r['connected'] in ('0','1') and rev['connected'] in ('0','1')
    total=int(r['connected'])+int(rev['connected']);counts['positive_directions']+=total
    if total!=1:continue
    counts['oneway_dyads']+=1
    for field in fields:
        if finite(ca[field]) and finite(cb[field]):availability[field]+=1
    if all(finite(c[field]) for c in (ca,cb) for field in ('piadistance','R_in','rheo')):
        counts['finite_pia_Rin_rheo_dyads']+=1;candidate_patients.add(r['patientid'])
out={'contract_sha256':sha(HERE/'planert2025_intrinsic_eligibility_contract.json'),
     'cells':len(cells),'connection_rows':len(rows),'counts':dict(counts),
     'oneway_both_finite_by_field':dict(availability),'candidate_patient_labels':len(candidate_patients),
     'qc_flag_values_uninterpreted':{k:dict(v) for k,v in flags.items()},
     'status':'DIRECT_JOIN_CHECKED; QC_UNITS_COHORT_GATE_PENDING; NO_EFFECT_ESTIMATED'}
save('planert2025_intrinsic_eligibility_result.json',out)
print(json.dumps(out,indent=2))
