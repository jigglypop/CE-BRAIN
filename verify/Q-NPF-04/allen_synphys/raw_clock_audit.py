"""NWB 시작시각과 원 제작자가 쓰는 notebook 시각의 차이를 확인한다."""
import json
from datetime import datetime,timedelta
from pathlib import Path
import h5py
import numpy as np
from raw_metadata import CachedRanges

HERE=Path(__file__).resolve().parent


def main():
    output=HERE/'raw_clock_audit_result.json'
    if output.exists():raise RuntimeError('시각 감사 결과 보존')
    with CachedRanges() as r:
        with h5py.File(r,'r') as f:
            nb=f['general/labnotebook/ITC1600_Dev_0']
            keys=[v.decode() if isinstance(v,bytes) else str(v) for v in nb['numericalKeys'][0]]
            wanted=[k for k in keys if k in ('SweepNum','Sweep','TimeStamp','EntrySourceType','Clamp Mode','V-Clamp Holding Level')]
            indices=sorted(set([0]+[keys.index(k) for k in wanted]))
            values=nb['numericalValues'][:,indices,:]
            columns=[keys[i] for i in indices]
            ts=columns.index('TimeStamp');typ=columns.index('EntrySourceType')
            entries=[]
            for row in values:
                sw=row[0,0]
                if not np.isfinite(sw) or int(sw) not in range(10) or row[typ,0]!=0:continue
                entry={'sweep':int(sw),'source_type':float(row[typ,0]),'values':{}}
                for c,k in enumerate(columns):
                    entry['values'][k]=[None if not np.isfinite(v) else float(v) for v in row[c]]
                stamp=row[ts,0]
                entry['notebook_time_naive']=(datetime(1904,1,1)+timedelta(seconds=float(stamp))).isoformat() if np.isfinite(stamp) else None
                entries.append(entry)
            result={'shape':list(nb['numericalValues'].shape),'columns':columns,'entries':entries,
                    'note':'Notebook epoch conversion follows neuroanalysis MIES reader; naive time is not assigned a timezone here.'}
        result['new_bytes']=r.downloaded_this_session
        result['total_cached_bytes']=sum(b['bytes'] for b in r.manifest['blocks'].values())
    output.write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
    print(json.dumps({'shape':result['shape'],'columns':columns,'entries':[{k:v for k,v in e.items() if k!='values'} for e in entries],'new_bytes':result['new_bytes']},indent=2))


if __name__=='__main__':main()
