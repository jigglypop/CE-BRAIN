"""정확 ID 유일성 gate 실패의 중복·연결 표지 충돌을 보존한다."""
import csv
import io
import zipfile
from collections import Counter,defaultdict
from pathlib import Path
from population_reciprocity import ROOT,sha
from superficial_ee_eligibility import save

HERE=Path(__file__).resolve().parent;archive=ROOT/'data/external/planert2025_human/humandata.zip'
assert sha(archive)=='6b0d7244dec5c665a88d0d1828ae842d084bb737a6df9f86561d53d8564c4bfd'
with zipfile.ZipFile(archive) as z:
    rows=list(csv.DictReader(io.StringIO(z.read('humandata/data_tables/tconnection_all_psdn.csv').decode('utf-8-sig'))))
groups=defaultdict(list)
for r in rows:groups[r['cellid_pre'],r['cellid_post']].append(r)
duplicates=[];fields=Counter()
for (a,b),rr in groups.items():
    if len(rr)==1:continue
    diff=[k for k in rr[0] if len({r[k] for r in rr})>1]
    fields.update(diff)
    duplicates.append({'pre':a,'post':b,'multiplicity':len(rr),'different_fields':diff,
                       'rows':[{'row_label':r[''],'connected':r['connected'],'amplitude':r['avg_psp_amplitude']} for r in rr]})
out={'archive_sha256':sha(archive),'code_sha256':sha(Path(__file__)),
     'failed_contract_sha256':sha(HERE/'planert2025_intrinsic_eligibility_contract.json'),
     'rows':len(rows),'unique_pair_keys':len(groups),'duplicate_pair_keys':len(duplicates),
     'multiplicity':{str(k):v for k,v in Counter(r['multiplicity'] for r in duplicates).items()},
     'different_field_counts':dict(fields),'conflicting_connection_keys':fields['connected'],
     'duplicates':duplicates,'status':'STOP_ID_AMBIGUITY; no arbitrary deduplication or effect fit'}
save('planert2025_duplicate_audit_result.json',out)
print({k:v for k,v in out.items() if k not in ('duplicates','different_field_counts')})
