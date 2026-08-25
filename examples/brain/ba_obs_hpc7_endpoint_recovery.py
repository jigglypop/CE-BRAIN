"""Read-only recovery authority for the terminal H6 endpoint transaction."""
from __future__ import annotations
import argparse,hashlib,importlib.util,json
from pathlib import Path
RUN=Path('_workspace/ce/brain-human-hippocampal-theta-endpoint-recovery-20260825');PRE=Path('_workspace/ce/brain-human-hippocampal-theta-full-endpoint-20260825');A=RUN/'artifacts';LOCK=A/'analysis_lock.json';EXEC=A/'execution_lock.json'
PP=PRE/'artifacts/endpoint_progress.json';W=PRE/'artifacts/source_witness.npz';R=PRE/'artifacts/raw_result.json';PA=PRE/'artifacts/analysis_lock.json';PE=PRE/'artifacts/execution_lock.json';V=Path('examples/brain/ba_obs_hpc6_full_endpoint_validator.py');P=Path('examples/brain/ba_obs_hpc6_full_endpoint.py');T=Path('tests/test_ba_obs_hpc6_full_endpoint.py')
RP=A/'recovery_progress.json';VPRE=A/'validator_precomplete.json';VCOMP=A/'validator_complete.json';RC=A/'recovery_receipt.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def write(p,x):p.parent.mkdir(parents=True,exist_ok=True);q=p.with_suffix(p.suffix+'.tmp');q.write_text(json.dumps(x,indent=2,allow_nan=False));q.replace(p)
def frozen():return {'progress':PP,'witness':W,'result':R,'analysis':PA,'execution':PE,'producer':P,'validator':V,'tests':T,'contract':RUN/'00-contract.md','sources':RUN/'10-sources.md','math':RUN/'11-math.md','routes':RUN/'12-routes.md'}
def check_analysis():
 x=read(LOCK)
 if set(x)!={'schema','hashes','attempt'} or x['schema']!='HPC7_ANALYSIS_LOCK_V1' or x['attempt']!='ENDPOINT_RECOVERY1' or set(x['hashes'])!=set(frozen()) or any(x['hashes'][k]!=sha(v) for k,v in frozen().items()):raise ValueError('RECOVERY_STOP: frozen input drift')
 return sha(LOCK)
def check_execution():
 path=EXEC
 x=read(path);want={'schema','analysis_lock_sha256','hashes','attempt'}
 if set(x)!=want or x['schema']!='HPC7_EXECUTION_LOCK_V1' or x['analysis_lock_sha256']!=sha(LOCK) or x['attempt']!='ENDPOINT_RECOVERY1' or x['hashes']!={'executor':sha(Path(__file__)),'tests':sha(Path('tests/test_ba_obs_hpc7_endpoint_recovery.py')),'validator':sha(V)}:raise ValueError('RECOVERY_STOP: execution lock')
 return sha(path)
def terminal():
 p=read(PP);r=read(R)
 if set(p)!={'status','attempt_id','analysis_lock_sha256','execution_lock_sha256','completed_files','error'} or p['status']!='IMPLEMENTATION_STOP' or p['attempt_id']!='ENDPOINT_FULL1' or p['analysis_lock_sha256']!=sha(PA) or p['execution_lock_sha256']!=sha(PE) or p['error']!="ModuleNotFoundError: No module named 'examples'" or len(p['completed_files'])!=18 or p['completed_files']!=r.get('records'):raise ValueError('RECOVERY_STOP: predecessor terminal')
 if r.get('status')!='RAW_COMPLETE' or r.get('analysis_lock_sha256')!=sha(PA) or r.get('execution_lock_sha256')!=sha(PE) or r.get('witness',{}).get('file_sha256')!=sha(W) or len(r.get('records',[]))!=18 or len(r.get('files',[]))!=18 or sum(z['integrity']['observed_size'] for z in r['records'])!=723560000:raise ValueError('RECOVERY_STOP: predecessor result')
 return r
def validator():
 s=importlib.util.spec_from_file_location('hpc7_frozen_validator',V);m=importlib.util.module_from_spec(s);assert s.loader;s.loader.exec_module(m);return m.validate
def exact(a,b):
 if type(a) is not type(b):return False
 if isinstance(a,dict):return set(a)==set(b) and all(exact(a[k],b[k]) for k in a)
 if isinstance(a,list):return len(a)==len(b) and all(exact(x,y) for x,y in zip(a,b))
 return a==b
def prior(*paths):
 if any(p.exists() for p in paths) or any(A.glob('*.tmp')):raise ValueError('RECOVERY_STOP: prior recovery artifact')
def snapshot(execution_lock):return {**{k:sha(v) for k,v in frozen().items()},'successor_execution_lock':sha(execution_lock)}
def verify_authority(progress=RP,precomplete=VPRE,complete=VCOMP,receipt=RC):
 try:
  al=check_analysis();el=check_execution();snap=snapshot(EXEC);result=terminal();rp=read(progress);vpre=read(precomplete);vcomp=read(complete);rc=read(receipt);base={'attempt_id':'ENDPOINT_FULL1','analysis_lock_sha256':result['analysis_lock_sha256'],'execution_lock_sha256':result['execution_lock_sha256'],'completed_files':result['records']}
  if not exact(vpre,{'status':'IN_PROGRESS',**base}) or not exact(vcomp,{'status':'COMPLETE',**base,'witness_sha256':sha(W),'result_sha256':sha(R)}):return False
  want={'schema':'HPC7_RECOVERY_RECEIPT_V3','status':'CONTENT_VALIDATED_NOT_STANDALONE_AUTHORITY','attempt_id':'ENDPOINT_RECOVERY1','predecessor_terminal_status':'IMPLEMENTATION_STOP','predecessor_terminal_error':"ModuleNotFoundError: No module named 'examples'",'predecessor_attempt_id':'ENDPOINT_FULL1','predecessor_row_count':18,'frozen_hashes':snap,'witness_sha256':sha(W),'result_sha256':sha(R),'validator_precomplete_sha256':sha(precomplete),'validator_complete_sha256':sha(complete),'analysis_lock_sha256':al,'execution_lock_sha256':el,'authority':'RECOVERY_PAIR_REQUIRED'}
  if not exact(rc,want) or not exact(rp,{'status':'COMPLETE','attempt_id':'ENDPOINT_RECOVERY1','analysis_lock_sha256':al,'execution_lock_sha256':el,'snapshot':snap,'receipt_sha256':sha(receipt)}):return False
  fn=validator();return bool(fn(R,W,precomplete,check_predecessor=True,execution_lock=PE,require_complete=False)) and bool(fn(R,W,complete,check_predecessor=True,execution_lock=PE,require_complete=True)) and exact(snap,snapshot(EXEC))
 except Exception:return False
def recovery(progress=RP,precomplete=VPRE,complete=VCOMP,receipt=RC):
 prior(progress,precomplete,complete,receipt); al=check_analysis();el=check_execution();before=snapshot(EXEC);result=terminal();write(progress,{'status':'IN_PROGRESS','attempt_id':'ENDPOINT_RECOVERY1','analysis_lock_sha256':al,'execution_lock_sha256':el,'snapshot':before})
 try:
  base={'attempt_id':'ENDPOINT_FULL1','analysis_lock_sha256':result['analysis_lock_sha256'],'execution_lock_sha256':result['execution_lock_sha256'],'completed_files':result['records']}
  write(precomplete,{'status':'IN_PROGRESS',**base});fn=validator()
  if not fn(R,W,precomplete,check_predecessor=True,execution_lock=PE,require_complete=False):raise ValueError('validator precomplete false')
  if not exact(before,snapshot(EXEC)):raise ValueError('RECOVERY_STOP: drift between validator phases')
  write(complete,{'status':'COMPLETE',**base,'witness_sha256':sha(W),'result_sha256':sha(R)})
  if not fn(R,W,complete,check_predecessor=True,execution_lock=PE,require_complete=True):raise ValueError('validator complete false')
  if not exact(before,snapshot(EXEC)):raise ValueError('RECOVERY_STOP: predecessor drift')
  out={'schema':'HPC7_RECOVERY_RECEIPT_V3','status':'CONTENT_VALIDATED_NOT_STANDALONE_AUTHORITY','attempt_id':'ENDPOINT_RECOVERY1','predecessor_terminal_status':'IMPLEMENTATION_STOP','predecessor_terminal_error':"ModuleNotFoundError: No module named 'examples'",'predecessor_attempt_id':'ENDPOINT_FULL1','predecessor_row_count':18,'frozen_hashes':before,'witness_sha256':sha(W),'result_sha256':sha(R),'validator_precomplete_sha256':sha(precomplete),'validator_complete_sha256':sha(complete),'analysis_lock_sha256':al,'execution_lock_sha256':el,'authority':'RECOVERY_PAIR_REQUIRED'};write(receipt,out)
  if read(receipt)!=out:raise ValueError('receipt readback')
  if not exact(before,snapshot(EXEC)):raise ValueError('RECOVERY_STOP: postcommit drift')
  write(progress,{'status':'COMPLETE','attempt_id':'ENDPOINT_RECOVERY1','analysis_lock_sha256':al,'execution_lock_sha256':el,'snapshot':before,'receipt_sha256':sha(receipt)})
  if not verify_authority(progress,precomplete,complete,receipt):raise ValueError('RECOVERY_STOP: authority postcheck')
  return out
 except Exception as e:
  write(progress,{'status':'RECOVERY_STOP','attempt_id':'ENDPOINT_RECOVERY1','analysis_lock_sha256':al,'execution_lock_sha256':el,'snapshot':before,'error':f'{type(e).__name__}: {e}'});raise
def main(argv=None):
 p=argparse.ArgumentParser();p.add_argument('stage',choices=('recover','status'));a=p.parse_args(argv)
 try:
  status=recovery()['status'] if a.stage=='recover' else ('PENDING' if not RP.exists() else ('COMPLETE' if verify_authority() else 'INVALID'))
  print(status);return 0 if status=='COMPLETE' else 1
 except Exception as e: print(f'FAIL: {e}');return 1
if __name__=='__main__':raise SystemExit(main())
