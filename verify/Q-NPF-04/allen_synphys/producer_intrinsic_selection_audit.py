"""공식 선택 함수를 메타데이터 대리 객체에 적용해 프로토콜 범위를 대조한다."""
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
from population_reciprocity import sha
from superficial_ee_eligibility import save

HERE=Path(__file__).resolve().parent
source=HERE/'source_snapshots/aisynphys__nwb_recordings.py'
inventory=HERE/'same_cell_intrinsic_inventory_result.json'
save('producer_intrinsic_selection_audit_contract.json',{
    'question':'Which stored protocol records does the actual pinned intrinsic selection function accept?',
    'method':'Run get_intrinsic_recording_dict on metadata proxies with known electrode and clamp unit; do not simulate waveforms or qc_recordings.',
    'scope':'Three electrodes in existing full metadata inventory; preserve earlier FastRheo diagnostics as separate non-producer-selection analysis.',
    'source_sha256':sha(source),'inventory_sha256':sha(inventory),'code_sha256':sha(Path(__file__))})
spec=importlib.util.spec_from_file_location('pinned_nwb_recordings',source)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
class Sweep(dict):
    @property
    def devices(self):return list(self)
sweeps={}
for r in json.loads(inventory.read_text(encoding='utf-8'))['records']:
    hs=int(r['electrode'].split('_')[-1])
    sweeps.setdefault(r['sweep'],Sweep())[hs]=SimpleNamespace(clamp_mode='ic' if r['unit']=='V' else 'vc',
        stimulus=SimpleNamespace(description=r['stimulus']),record=r)
nwb=SimpleNamespace(contents=[sweeps[k] for k in sorted(sweeps)])
selected=[]
for hs in (2,4,5):
    result=module.get_intrinsic_recording_dict(nwb,hs)
    for kind,recs in result.items():
        for rec in recs:selected.append({'kind':kind,**rec.record})
assert not any(82<=r['sweep']<=89 for r in selected)
out={'contract_sha256':sha(HERE/'producer_intrinsic_selection_audit_contract.json'),'selected':selected,
     'per_electrode':{str(hs):[r['sweep'] for r in selected if r['electrode']==f'electrode_{hs}'] for hs in (2,4,5)},
     'fast_rheo_82_89_selected':0,'status':'PRODUCER_PROTOCOL_SELECTION_ONLY_QC_AND_PULSE_PARSING_PENDING'}
save('producer_intrinsic_selection_audit_result.json',out)
print(json.dumps({k:v for k,v in out.items() if k!='selected'},indent=2))
