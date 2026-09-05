"""읽기 전용 SQLite VFS로 medium DB의 필요한 페이지만 조회한다."""
import json
import sys
from pathlib import Path
from population_reciprocity import ROOT,sha
from superficial_ee_eligibility import save
import raw_metadata as raw
sys.path.insert(0,str(ROOT/'data/external/analysis_tools/apsw_runtime'))
import apsw

class ReadFile:
    def __init__(self,reader):self.reader=reader
    def xRead(self,amount,offset):
        self.reader.seek(offset);return self.reader.read(amount)
    def xFileSize(self):return self.reader.remote['bytes']
    def xClose(self):pass
    def xLock(self,level):pass
    def xUnlock(self,level):pass
    def xCheckReservedLock(self):return False
    def xFileControl(self,op,ptr):return False
    def xSectorSize(self):return 4096
    def xDeviceCharacteristics(self):return apsw.SQLITE_IOCAP_IMMUTABLE
    def xWrite(self,*args):raise apsw.ReadOnlyError('Read-only source')
    def xTruncate(self,*args):raise apsw.ReadOnlyError('Read-only source')
    def xSync(self,*args):pass
class ReadVFS(apsw.VFS):
    def __init__(self,reader):
        self.reader=reader;super().__init__('ce_medium_readonly','')
    def xOpen(self,name,flags):
        assert flags[0]&apsw.SQLITE_OPEN_MAIN_DB
        assert not flags[0]&apsw.SQLITE_OPEN_READWRITE
        flags[1]=apsw.SQLITE_OPEN_READONLY;return ReadFile(self.reader)
    def xAccess(self,name,flags):return False

def main():
    here=Path(__file__).resolve().parent
    raw.URL='https://allen-synphys.s3-us-west-2.amazonaws.com/synphys_r2.1_medium.sqlite'
    raw.CACHE=ROOT/'data/external/allen_synphys_r21/medium_ranges'
    raw.LIMIT=128*1024*1024
    save('medium_recording_lookup_contract.json',{
        'question':'Can released medium DB supply original recording/QC links missing from small for the36 producer-selected records?',
        'query':'experiment ext_id exact; sync_rec experiment index; recording per sync ID; patch_clamp_recording per recording ID; source cell mapping crosschecked later.',
        'source':raw.URL,'transport':'ETag-bound read-only range cache; SQLite native queries; 128MiB cache cap, no full download.',
        'apsw':apsw.apswversion(),'code_sha256':sha(Path(__file__)),'reader_sha256':sha(Path(raw.__file__))})
    with raw.CachedRanges() as reader:
        vfs=ReadVFS(reader)
        db=apsw.Connection('remote.sqlite',flags=apsw.SQLITE_OPEN_READONLY,vfs='ce_medium_readonly')
        db.execute('pragma query_only=ON');db.execute('pragma temp_store=MEMORY')
        def query(sql,args=()):
            cursor=db.cursor();result=cursor.execute(sql,args)
            try:keys=[d[0] for d in cursor.get_description()]
            except apsw.ExecutionCompleteError:return []
            return [dict(zip(keys,r)) for r in result]
        metadata=query('select * from metadata')
        experiments=query('select id,ext_id from experiment where ext_id=?',('1574292898.139',));assert len(experiments)==1
        eid=experiments[0]['id']
        sync=query('select id,ext_id from sync_rec where experiment_id=?',(eid,))
        selection=json.loads((here/'producer_intrinsic_selection_audit_result.json').read_text(encoding='utf-8'))['selected']
        wanted={r['sweep'] for r in selection}
        selected_sync=[r for r in sync if int(r['ext_id']) in wanted]
        electrodes=query('select id,device_id from electrode where experiment_id=?',(eid,))
        devices={r['id']:r['device_id'] for r in electrodes}
        rows=[]
        for s in selected_sync:
            for r in query('select * from recording where sync_rec_id=?',(s['id'],)):
                if devices[r['electrode_id']] not in (2,4,5):continue
                qc=query('select * from patch_clamp_recording where recording_id=?',(r['id'],))
                rows.append({'sweep':int(s['ext_id']),'device':devices[r['electrode_id']],'recording':r,'qc':qc})
            print('queried sweep',s['ext_id'],flush=True)
        out={'contract_sha256':sha(here/'medium_recording_lookup_contract.json'),'remote':reader.remote,'metadata':metadata,
             'experiments':experiments,'sync_count':len(sync),'records':rows,'new_bytes':reader.downloaded_this_session,
             'status':'SOURCE_QUERY_COMPLETE_NOT_YET_RAW_IDENTITY_VALIDATED'}
        db.close();vfs.unregister()
    save('medium_recording_lookup_result.json',out)
    print('complete records',len(rows),'new bytes',out['new_bytes'])
if __name__=='__main__':main()
