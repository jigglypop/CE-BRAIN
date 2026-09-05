"""Download one authorized official summary database and inspect schema only."""
import hashlib
import json
from pathlib import Path
import sqlite3
import time
import urllib.request

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
C=json.loads((HERE/'acquisition_contract.json').read_text(encoding='utf-8'))


def main():
    target=ROOT/C['download']['destination']
    target.parent.mkdir(parents=True,exist_ok=True)
    expected=C['source']['head_content_length']
    headers={}
    if not target.exists():
        partial=target.with_suffix('.sqlite.partial')
        if partial.exists():
            raise RuntimeError('Partial file exists; inspect before retry, do not silently restart.')
        with urllib.request.urlopen(C['source']['url'],timeout=45) as response:
            headers=dict(response.headers)
            if int(response.headers['Content-Length'])!=expected:
                raise RuntimeError('Published object size changed')
            with partial.open('xb') as f:
                total=0; last=time.monotonic()
                while True:
                    chunk=response.read(1024*1024)
                    if not chunk: break
                    total+=len(chunk)
                    if total>C['download']['maximum_bytes']: raise RuntimeError('Download budget exceeded')
                    f.write(chunk)
                    if time.monotonic()-last>15:
                        print(f'Downloaded {total}/{expected} bytes',flush=True);last=time.monotonic()
        if total!=expected: raise RuntimeError('Incomplete object')
        partial.rename(target)
    if target.stat().st_size!=expected: raise RuntimeError('Unexpected existing file size')
    digest=hashlib.file_digest(target.open('rb'),'sha256').hexdigest()
    with target.open('rb') as f:
        if f.read(16)!=b'SQLite format 3\0': raise RuntimeError('Not SQLite')
    db=sqlite3.connect(target.as_uri()+'?mode=ro',uri=True)
    names=[r[0] for r in db.execute("select name from sqlite_master where type='table' order by name")]
    schema={n:[list(r) for r in db.execute('pragma table_info("'+n.replace('"','""')+'")')] for n in names}
    relevant=['slice','experiment','cell','pair','synapse','intrinsic','avg_response_fit','resting_state_fit','metadata']
    counts={n:db.execute('select count(*) from "'+n+'"').fetchone()[0] for n in relevant if n in names}
    report=dict(status='DOWNLOADED_SCHEMA_READY',bytes=expected,sha256=digest,url=C['source']['url'],
        response_headers=headers,local_path=str(target),schema=schema,row_counts=counts,
        acquisition_script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        contract_sha256=hashlib.sha256((HERE/'acquisition_contract.json').read_bytes()).hexdigest(),
        biological_relationships_evaluated=False)
    (HERE/'acquisition_receipt.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(status=report['status'],bytes=expected,sha256=digest,row_counts=counts,
        columns={n:[r[1] for r in schema[n]] for n in relevant if n in schema}),indent=2))


if __name__=='__main__': main()
