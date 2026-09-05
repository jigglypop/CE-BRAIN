"""Collect indexed medium-DB noise inputs for the frozen structural cohort.

Read-only APSW source, ETag-bound reused byte cache. A per-cell journal permits
resuming a terminal collection without downloading or querying completed cells.
No labels are fit and no sensitivity probabilities are estimated here.
"""
from collections import OrderedDict
import hashlib
import json
from pathlib import Path
import sqlite3
import sys

import numpy as np

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
SOURCE=ROOT/"verify/Q-NPF-04/allen_synphys"
sys.path.insert(0,str(SOURCE))
import medium_recording_lookup as medium

STATE=HERE/"allen_observation_medium_inputs_state.json"
JOURNAL=HERE/"allen_observation_medium_cells.jsonl"
OUTPUT=HERE/"allen_observation_medium_inputs_result.json"
READS=HERE/"allen_observation_medium_used_blocks.json"
CACHE=ROOT/"data/external/allen_synphys_r21/medium_ranges"
URL="https://allen-synphys.s3-us-west-2.amazonaws.com/synphys_r2.1_medium.sqlite"


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def atomic_json(path,data):
    temp=path.with_suffix(path.suffix+".tmp")
    temp.write_text(json.dumps(data,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    temp.replace(path)


def finite(value):return value is not None and np.isfinite(value)


def aggregate(rows):
    good=[r for r in rows if r["clamp_mode"]=="ic" and r["qc_pass"]==1]
    values=[r["baseline_noise_stdev"] for r in good]
    valid=len(values)>1 and all(finite(v) for v in values)
    mean=float(np.mean(values)) if valid else None
    if mean is not None and mean<=0:mean=None
    return dict(total_recordings=len(rows),qc_pass_IC_count=len(good),
                qc_pass_IC_finite_noise_count=sum(finite(v) for v in values),
                mean_qc_pass_IC_noise_V=mean,
                noise_scope="Producer mean requires more than one QC-pass IC record; nonfinite input or nonpositive mean stays unavailable",
                qc_pass_IC_records=good)


class ObservedRanges(medium.raw.CachedRanges):
    def __init__(self):
        super().__init__();self.used=set();self.ram=OrderedDict();self.last_progress=0
    def block(self,start):
        self.used.add(start)
        if start in self.ram:
            self.ram.move_to_end(start);return self.ram[start]
        value=super().block(start);self.ram[start]=value
        if len(self.ram)>512:self.ram.popitem(last=False)
        if self.downloaded_this_session-self.last_progress>=8*1024*1024:
            print("MEDIUM_NEW_BYTES",self.downloaded_this_session,flush=True);self.last_progress=self.downloaded_this_session
        return value


def main():
    if OUTPUT.exists():
        print("COLLECTION_ALREADY_COMPLETE",sha(OUTPUT));return
    expected={
        HERE/"allen_structural_metric_baseline_result.json":"d13c396980d7e509d8206e2324b1be6ca8a0fcdfe666df7864435391e72e9e14",
        ROOT/"data/external/allen_synphys_r21/synphys_r2.1_small.sqlite":"7372499fdd874f057565080d5769baaf2659ef39d9f3bc3c7147dd1e1c280a53",
        ROOT/"data/external/allen_synphys_r21/producer_connectivity/545a990ee171e6c0d23dd4bba413e1ccbf2f0853/connectivity.py":"9c13f009f9d1e08b5baf4ce9c176f406f99e0bfc216bc057f16f0b2d7d5a3aca"}
    for path,value in expected.items():assert sha(path)==value,path
    source_hash=sha(Path(__file__))
    structural=json.loads((HERE/"allen_structural_metric_baseline_result.json").read_text())
    wanted=sorted({r["post_cell_id"] for r in structural["records"]})
    small=ROOT/"data/external/allen_synphys_r21/synphys_r2.1_small.sqlite"
    with sqlite3.connect(small.resolve().as_uri()+"?mode=ro",uri=True) as c:
        c.row_factory=sqlite3.Row
        cells={r["id"]:dict(r) for r in c.execute("select id,experiment_id,ext_id,electrode_id,position,depth from cell")}
        experiments={r["id"]:r["ext_id"] for r in c.execute("select id,ext_id from experiment")}
    completed={}
    if JOURNAL.exists():
        for line in JOURNAL.read_text(encoding="utf-8").splitlines():
            r=json.loads(line);assert r["cell_id"] not in completed;completed[r["cell_id"]]=r
    if STATE.exists():
        old=json.loads(STATE.read_text());assert old["code_sha256"]==source_hash
        assert old["wanted_cells"]==wanted
    previous_reads=json.loads(READS.read_text()) if READS.exists() else {"blocks":{}}
    medium.raw.URL=URL;medium.raw.CACHE=CACHE;medium.raw.LIMIT=1024*1024*1024
    reader=ObservedRanges();vfs=None;db=None
    state=dict(code_sha256=source_hash,input_sha256={p.relative_to(ROOT).as_posix():v for p,v in expected.items()},
               reader_code_sha256=sha(Path(medium.raw.__file__)),vfs_code_sha256=sha(Path(medium.__file__)),
               apsw_version=medium.apsw.apswversion(),sqlite_version=medium.apsw.sqlitelibversion(),
               remote=reader.remote,wanted_cells=wanted,status="collecting")
    if STATE.exists():assert old["remote"]==reader.remote
    atomic_json(STATE,state)
    try:
        vfs=medium.ReadVFS(reader)
        db=medium.apsw.Connection('remote.sqlite',flags=medium.apsw.SQLITE_OPEN_READONLY,vfs='ce_medium_readonly')
        db.execute('pragma query_only=ON');db.execute('pragma temp_store=MEMORY')
        def query(sql,args=()):
            cur=db.cursor();rows=cur.execute(sql,args)
            try:names=[d[0] for d in cur.get_description()]
            except medium.apsw.ExecutionCompleteError:return []
            return [dict(zip(names,row)) for row in rows]
        remote_cells={r["id"]:r for r in query('select id,experiment_id,ext_id,electrode_id,position,depth from cell')}
        remote_experiments={r["id"]:r["ext_id"] for r in query('select id,ext_id from experiment')}
        for cid in wanted:
            assert cid in remote_cells,cid
            assert cells[cid]==remote_cells[cid],("Small-medium cell mismatch",cid)
            eid=cells[cid]["experiment_id"]
            assert experiments[eid]==remote_experiments[eid],eid
        print("MEDIUM_IDENTITY_MATCH",len(wanted),flush=True)
        with JOURNAL.open("a",encoding="utf-8",newline="\n") as stream:
            for cid in wanted:
                if cid in completed:continue
                rows=query('''select p.id,p.recording_id,p.clamp_mode,p.qc_pass,p.baseline_noise_stdev
                    from recording r join patch_clamp_recording p on p.recording_id=r.id
                    where r.electrode_id=? order by r.id''',(cells[cid]["electrode_id"],))
                for r in rows:
                    if r["baseline_noise_stdev"] is not None and not np.isfinite(r["baseline_noise_stdev"]):
                        r["baseline_noise_stdev"]=None
                entry=dict(cell_id=cid,experiment_id=cells[cid]["experiment_id"],electrode_id=cells[cid]["electrode_id"],
                           identity_checked=True,**aggregate(rows))
                stream.write(json.dumps(entry,allow_nan=False)+"\n");stream.flush();completed[cid]=entry
                if len(completed)%100==0:
                    print("MEDIUM_CELLS",len(completed),"of",len(wanted),"new_bytes",reader.downloaded_this_session,flush=True)
        state.update(status="complete",completed_cells=len(completed))
        assert set(completed)==set(wanted)
    except Exception as exc:
        state.update(status="terminal_error",completed_cells=len(completed),error=type(exc).__name__+": "+str(exc))
        raise
    finally:
        if db is not None:db.close()
        if vfs is not None:vfs.unregister()
        blocks=dict(previous_reads["blocks"])
        absent=[]
        for offset in reader.used:
            record=reader.manifest["blocks"].get(str(offset))
            if record is None:absent.append(offset)
            else:blocks[str(offset)]=record
        atomic_json(READS,dict(remote=reader.remote,blocks=blocks,failed_unavailable_offsets=sorted(absent),scope="Only accessed cache blocks, not full medium database"))
        state["new_bytes_this_invocation"]=reader.downloaded_this_session
        atomic_json(STATE,state);reader.close()
    output=dict(version="allen-observation-medium-inputs-v1",code_sha256=source_hash,
        source_state_sha256=sha(STATE),journal_sha256=sha(JOURNAL),used_blocks_sha256=sha(READS),
        remote=state["remote"],wanted_cells=len(wanted),cells_with_valid_mean_noise=sum(r["mean_qc_pass_IC_noise_V"] is not None for r in completed.values()),
        all_recordings=sum(r["total_recordings"] for r in completed.values()),qc_pass_IC_records=sum(r["qc_pass_IC_count"] for r in completed.values()),
        input_scope="QC/noise metadata from all stored records of selected postsynaptic cells; acquisition chronology/decision independence not established",
        cells=[completed[cid] for cid in wanted],claim_ceiling="Source input availability; not an independent detection sensitivity or biological metric")
    with OUTPUT.open("x",encoding="utf-8") as stream:json.dump(output,stream,indent=2,allow_nan=False);stream.write("\n")
    print(json.dumps({k:v for k,v in output.items() if k!="cells"}))


if __name__=="__main__":main()
