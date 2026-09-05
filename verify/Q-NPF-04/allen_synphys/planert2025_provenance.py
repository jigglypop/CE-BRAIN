"""공개 전처리 코드의 규칙과 직접 연결 가능한 식별자 범위만 확인한다."""
import csv
import io
import json
import zipfile
from pathlib import Path
import numpy as np
from population_reciprocity import ROOT,sha
from superficial_ee_eligibility import save

HERE=Path(__file__).resolve().parent
archive=ROOT/'data/external/planert2025_human/humandata.zip'
assert sha(archive)=='6b0d7244dec5c665a88d0d1828ae842d084bb737a6df9f86561d53d8564c4bfd'
save('planert2025_provenance_contract.json',{
    'question':'Public preprocessing semantics and exact identifier compatibility with Peng2024',
    'scope':'Source-only audit and table inventory; no phenotype-based matching of pseudonyms; no biological endpoint',
    'archive_sha256':sha(archive),'code_sha256':sha(Path(__file__))})
with zipfile.ZipFile(archive) as z:
    prefix='humandata/data_processing/extract/'
    names=['extract_matrix.m','extract_matrix2.m','extract_connection.m']
    source={n:z.read(prefix+n).decode('utf-8').replace('\r','') for n in names}
    rows=list(csv.DictReader(io.StringIO(z.read('humandata/data_tables/tconnection_all_psdn.csv').decode('utf-8-sig'))))
assert 'matrix.connection == 1 | data(i).matrix.connection == 1.2' in source['extract_matrix.m']
assert 'ephys_import2.avgsweep' in source['extract_matrix2.m']
with zipfile.ZipFile(ROOT/'data/external/peng2024_human/data.zip') as z:
    old={co:list(csv.DictReader(io.StringIO(z.read('data/tconnection_'+co+'.csv').decode('utf-8-sig')))) for co in ('er','tr')}
ids={r[k] for r in rows for k in ('cellid_pre','cellid_post')}
overlap={co:len(ids & {r[k] for r in rr for k in ('cellid_pre','cellid_post')}) for co,rr in old.items()}
finite=[]
for r in rows:
    try:v=float(r['avg_psp_amplitude'])
    except ValueError:continue
    if np.isfinite(v):finite.append(v)
out={'contract_sha256':sha(HERE/'planert2025_provenance_contract.json'),
     'table_rows':len(rows),'clusters':len({r['clusterid'] for r in rows}),
     'patient_labels':len({r['patientid'] for r in rows}), 'finite_amplitudes':len(finite),
     'exact_cell_id_overlap':overlap,
     'source_rules':{'monosynaptic':'raw connection == 1 OR == 1.2; NaN comparisons yield false, explaining final zero but not assessment quality',
                     'matrix2':'derived from ephys_import2 using first-import combined filter; not interchangeable with matrix',
                     'amplitude':'matrix.avg is populated from ephys_import.avgsweep; raw waveform availability not established'},
     'status':'PREPROCESSING_RULE_LOCATED; TR_42_NOT_RESOLVED; NO_EXACT_ID_BRIDGE',
     'limits':'Later release source does not establish exact historical execution; pseudonyms are not reverse-mapped; dataset not assumed independent'}
save('planert2025_provenance_result.json',out)
print(json.dumps(out,indent=2))
