"""동일 NWB에서 표적 세 전극의 전체 자극 설명을 조사한다."""
import json
from collections import Counter
from pathlib import Path
import h5py
import raw_metadata as raw
from population_reciprocity import sha
from superficial_ee_eligibility import save

HERE=Path(__file__).resolve().parent
save('same_cell_intrinsic_inventory_contract.json',{
    'question':'Are independent intrinsic protocols present on the same electrode records as the previously analyzed pair?',
    'scope':'All acquisition metadata for electrodes2,4,5 in NWB1574292898.139; no voltage or command payload arrays.',
    'classification':'Preserve exact stimulus descriptions and units; names alone do not establish dose, QC or unchanged cell identity over time.',
    'cache':'Reuse verified range blocks; total limit80MiB, metadata only; preserve source ETag binding.',
    'code_sha256':sha(Path(__file__)),'reader_sha256':sha(Path(raw.__file__))})
raw.LIMIT=80*1024*1024
def txt(x):
    if isinstance(x,bytes):return x.decode('utf-8')
    return str(x)
rows=[]
with raw.CachedRanges() as reader:
    with h5py.File(reader,'r') as f:
        acq=f['acquisition/timeseries']
        for name in sorted(acq):
            node=acq[name]
            electrode=txt(node['electrode_name'][()][0])
            if electrode not in ('electrode_2','electrode_4','electrode_5'):continue
            rows.append({'path':node.name,'sweep':int(name.split('_')[1]),'electrode':electrode,
                         'stimulus':txt(node['stimulus_description'][()][0]),'unit':txt(node['data'].attrs['unit']),
                         'samples':int(node['data'].shape[0]),'rate':float(node['starting_time'].attrs['rate']),
                         'start_s':float(node['starting_time'][()][0])})
    new_bytes=reader.downloaded_this_session
    remote=reader.remote
counts=Counter((r['electrode'],r['unit'],r['stimulus']) for r in rows)
out={'contract_sha256':sha(HERE/'same_cell_intrinsic_inventory_contract.json'),'remote':remote,'new_bytes':new_bytes,
     'records':rows,'summary':[{'electrode':e,'unit':u,'stimulus':s,'records':n} for (e,u,s),n in sorted(counts.items())],
     'status':'METADATA_ONLY_PROTOCOL_IDENTITY_NOT_CELL_STABILITY_OR_QC'}
save('same_cell_intrinsic_inventory_result.json',out)
print(json.dumps({k:v for k,v in out.items() if k not in ('records','remote')},indent=2))
