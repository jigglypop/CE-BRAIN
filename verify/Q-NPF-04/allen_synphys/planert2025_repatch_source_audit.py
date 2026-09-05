"""공개 재기록 결합·수동교정 코드의 확인 범위를 기록한다."""
import hashlib
import zipfile
from pathlib import Path
from population_reciprocity import ROOT,sha
from superficial_ee_eligibility import save

HERE=Path(__file__).resolve().parent;archive=ROOT/'data/external/planert2025_human/humandata.zip'
assert sha(archive)=='6b0d7244dec5c665a88d0d1828ae842d084bb737a6df9f86561d53d8564c4bfd'
with zipfile.ZipFile(archive) as z:
    names=['humandata/data_processing/pipeline_repatch.m','humandata/data_processing/extract/extract_connection_repatch.m']
    names += [n for n in z.namelist() if n.endswith('/tconnection_curate.m')]
    raw={n:z.read(n) for n in names}
    text={n:b.decode('utf-8').replace('\r','') for n,b in raw.items()}
pipeline=text[names[0]]
assert 'tconnection_repatch = [tconnection_repatch;repatch(r).tconnection]' in pipeline
assert 'unique_repatched = ~ismember(tconnection_repatch.synapseid,tconnection.synapseid)' in pipeline
assert 'tconnection_all = [tconnection;tconnection_repatch]' in pipeline
curation=text[names[-1]]
assert 'tconnection.avg_psp_amplitude(i) = tcuration.manual_peak1(row)' in curation
save('planert2025_repatch_source_audit_result.json',{
    'archive_sha256':sha(archive),'code_sha256':sha(Path(__file__)),
    'member_sha256':{n:hashlib.sha256(b).hexdigest() for n,b in raw.items()},
    'observed_code_path':'append each repatch table, exclude IDs occurring in original table, then append to original; no within-repatch uniqueness step in this path',
    'curation_path':'manual_peak1 can replace matrix-derived amplitude; required external curation spreadsheet not present in downloaded archive',
    'status':'POSSIBLE_DUPLICATE_PATH_IDENTIFIED; exact historical row/session identity unresolved',
    'limits':'does not identify which conflicting row to keep; does not prove historical pipeline execution or resolve Peng TR42 amplitudes'})
print('PASS: public repatch and curation source assertions')
