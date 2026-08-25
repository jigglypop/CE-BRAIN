"""Independent H6 witness validator; does not call producer endpoint/aggregate."""
from __future__ import annotations
import importlib.util,json
from pathlib import Path
import argparse
import numpy as np
from scipy.signal import butter,filtfilt,sosfiltfilt
from scipy.stats import kurtosis
P=Path('examples/brain/ba_obs_hpc6_full_endpoint.py');s=importlib.util.spec_from_file_location('h6producer',P);m=importlib.util.module_from_spec(s);assert s.loader;s.loader.exec_module(m)
def _endpoint(x,keep):
 if not keep.any():raise ValueError('zero clean')
 y=x[keep];y=y-y[:,m.IX['baseline']].mean(1,keepdims=True);avg=y.mean(0)
 return {'mean_waveform_microvolts':avg.tolist(),'trialwise_p2p_microvolts':{w:np.ptp(y[:,m.IX[w]],axis=1).tolist() for w in ('early','late','prestim')},'mean_waveform_p2p_microvolts':{w:float(np.ptp(avg[m.IX[w]])) for w in ('early','late','prestim')}}
def _metric(ts,pb):
 r=np.random.Generator(np.random.PCG64(20260825));z=r.exponential(size=(65536,7));d=z[:,:4]@ts/z[:,:4].sum(1)-z[:,[1,3,4,5,6]]@pb/z[:,[1,3,4,5,6]].sum(1);ta=('p16','p17','p18','p19');pa=('p17','p19','p20','UC004','UC005');names=('p16','p17','p18','p19','p20','UC004','UC005')
 return {'ts_deltas':ts.tolist(),'pb_deltas':pb.tolist(),'D':float(ts.mean()-pb.mean()),'bootstrap':[float(np.quantile(d,.025)),float(np.quantile(d,.975)),float((d>0).mean())],'loo':{n:float(np.mean([x for x,s in zip(ts,ta) if s!=n])-np.mean([x for x,s in zip(pb,pa) if s!=n])) for n in names},'paired_p17_p19':float((ts[1]+ts[3]-pb[0]-pb[1])/2)}
def _aggregate(files,bipolar):
 d={(x['protocol'],x['subject'],x['phase']):x for x in files};o={}
 for ref in ('clinical','bipolar') if bipolar else ('clinical',):
  o[ref]={}
  for e in ('trial_mean','mean_waveform'):
   o[ref][e]={}
   for w in ('early','late','prestim'):
    def v(x):return float(np.mean(x['trialwise_p2p_microvolts'][w])) if e=='trial_mean' else float(x['mean_waveform_p2p_microvolts'][w])
    ts=np.array([v(d[('TS',s,'post')][ref])-v(d[('TS',s,'pre')][ref]) for s in ('p16','p17','p18','p19')]);pb=np.array([v(d[('PB',s,'post')][ref])-v(d[('PB',s,'pre')][ref]) for s in ('p17','p19','p20','UC004','UC005')]);o[ref][e][w]=_metric(ts,pb)
 return o
def same(a,b):
 if isinstance(a,dict):return set(a)==set(b) and all(same(a[k],b[k]) for k in a)
 if isinstance(a,list):return len(a)==len(b) and all(same(x,y) for x,y in zip(a,b))
 if type(a) not in (int,float) or type(b) not in (int,float) or type(a) is bool or type(b) is bool:return type(a) is type(b) and a==b
 if type(a) is not type(b):return False
 if isinstance(a,(float,int)):return bool(np.isclose(a,b,rtol=1e-10,atol=1e-8))
 return a==b
def _dft(x,kind):
 z=np.asarray(x,float)[...,:999];n=np.arange(999);t=n/499.5-.5
 if kind=='A':
  A=np.stack([np.ones(999),*[v for f in (60,120,180) for v in (np.sin(2*np.pi*f*t),np.cos(2*np.pi*f*t))]],1);c=np.linalg.lstsq(A,z.reshape(-1,999).T,rcond=None)[0];return z-(A@c).T.reshape(z.shape)+c[0].reshape(z.shape[:-1])[...,None]
 out=z.copy()
 for f in (60,120,180):
  e=np.exp(-2j*np.pi*f*n/499.5);coef=np.tensordot(z,e,axes=(-1,0))/999;out-=2*np.real(coef[...,None]*np.exp(2j*np.pi*f*n/499.5))
 return out
def _qc(x,subject,kind):
 x=np.asarray(x,float);non=~np.isfinite(x).all((1,2));z=np.nan_to_num(x,nan=0.,posinf=0.,neginf=0.);y=_dft(z,kind)
 if subject=='p17':y=filtfilt(*butter(10,80,fs=499.5),y,axis=-1) if kind=='A' else sosfiltfilt(butter(10,80,fs=499.5,output='sos'),y,axis=-1)
 lat=y[...,m.IX['latency']];amp=np.max(np.abs(y[...,m.IX['amp']]),axis=-1)>=500;kur=kurtosis(y[...,m.IX['kurt']],axis=-1,fisher=False,bias=False)>=5;valid=~non;zz=np.zeros(x.shape[:2],bool)
 if valid.any():
  q=lat[valid];sd=q.std(0,ddof=1);v=np.divide(q-q.mean(0),sd,out=np.zeros_like(q),where=sd!=0);zz[valid]=np.any(abs(v)>5,axis=-1)
 ch={'amplitude':amp,'kurtosis':kur,'zscore':zz,'nonfinite':np.repeat(non[:,None],x.shape[1],axis=1)};rs={k:v.any(1) for k,v in ch.items()};bad=np.logical_or.reduce(list(rs.values()))
 diag={'keep_mask_sha256':m.h5._mask_hash(~bad),'reason_mask_sha256':{k:m.h5._mask_hash(v) for k,v in rs.items()},'reason_channel_mask_sha256':{k:m.h5._mask_hash(v) for k,v in ch.items()},'reason_counts':{k:int(v.sum()) for k,v in rs.items()},'reason_channel_counts':{k:int(v.sum()) for k,v in ch.items()},'trial_union_mask_sha256':m.h5._mask_hash(bad),'trial_union_count':int(bad.sum()),'trial_max_abs_amplitude_microvolts':np.max(np.abs(y[...,m.IX['amp']]),axis=(1,2)).tolist(),'trial_amplitude_margin_microvolts':(500-np.max(np.abs(y[...,m.IX['amp']]),axis=(1,2))).tolist()};diag['amplitude_margin_microvolts']=float(min(diag['trial_amplitude_margin_microvolts']));diag['max_abs_path_difference_microvolts']=0.0
 return y,bad,diag
def dual_qc(x,subject):
 a,ab,ad=_qc(x,subject,'A');b,bb,bd=_qc(x,subject,'B')
 parity=('reason_mask_sha256','reason_channel_mask_sha256','reason_counts','reason_channel_counts','trial_union_mask_sha256','trial_union_count')
 if np.max(np.abs(a-b))>1e-6 or not np.array_equal(ab,bb) or any(ad[k]!=bd[k] for k in parity):raise ValueError('independent QC disagreement')
 ad['max_abs_path_difference_microvolts']=float(np.max(np.abs(a-b)));return a,ab,ad
def validate(result=m.RESULT,witness=m.WITNESS,progress=m.PROGRESS,check_predecessor=True,execution_lock=m.EXECUTION_LOCK,require_complete=True):
 x=m.load(result);p=m.load(progress);meta=x.get('witness',{})
 top={'schema','status','attempt_id','analysis_lock_sha256','execution_lock_sha256','model_lane','posthoc_status','primary_status','bipolar_status','records','files','witness','analysis'}
 if set(x)!=top or x['schema']!='HPC6_ENDPOINT_FULL1_V1' or x['status']!='RAW_COMPLETE' or x['attempt_id']!='ENDPOINT_FULL1' or x['analysis_lock_sha256']!=m.sha(m.LOCK) or x['model_lane']!='PUBLISHED_MODEL_ENGINE_UNAVAILABLE' or x['posthoc_status']!='SAME_PUBLIC_DATA_POSTHOC_AUTHOR_INTENDED_EMULATION' or x['primary_status']!='CLINICAL_AVAILABLE_CLEAN_PRIMARY' or x['bipolar_status'] not in ('BIPOLAR_SENSITIVITY_AVAILABLE','BIPOLAR_SENSITIVITY_UNAVAILABLE'):return False
 try: execution_sha=m.check_execution_lock(execution_lock,True)
 except Exception:return False
 if x['execution_lock_sha256']!=execution_sha or not m.witness_ok(witness,meta):return False
 needed={'status','attempt_id','analysis_lock_sha256','execution_lock_sha256','completed_files'}|({'witness_sha256','result_sha256'} if require_complete else set())
 if set(p)!=needed or p['attempt_id']!='ENDPOINT_FULL1' or p['analysis_lock_sha256']!=m.sha(m.LOCK) or p['execution_lock_sha256']!=execution_sha or p['completed_files']!=x.get('records') or (p['status']!='COMPLETE' if require_complete else p['status']!='IN_PROGRESS'):return False
 if require_complete and (p['witness_sha256']!=m.sha(witness) or p['result_sha256']!=m.sha(result)):return False
 if len(x['records'])!=18 or len(x['files'])!=18:return False
 with np.load(witness,allow_pickle=False) as z:
  files=[]; bip=True
  frozen=m.h5._records();oldgrid=m.h5._check_lock()['hpc4_old_grid']
  for i,sp in enumerate(m.SPECS):
   c=np.asarray(z[f'{i:02d}_clinical']);b=np.asarray(z[f'{i:02d}_bipolar']);cy,ck,cq=dual_qc(c,sp.subject);by,bk,bq=dual_qc(b[:,None,:],sp.subject)
   row=x['records'][i]; ident=(sp.protocol,sp.subject,sp.phase);rec=frozen[ident]
   expected_c={'clean_count':int((~ck).sum()),**cq};expected_b={'clean_count':int((~bk).sum()),**bq}
   integrity={'expected_sha256':rec['annex_sha256'],'observed_sha256':rec['annex_sha256'],'expected_size':rec['annex_size'],'observed_size':rec['annex_size'],'version_id':rec['eeg']['x-amz-version-id'],'etag':rec['eeg']['etag']}
   expected={'protocol':sp.protocol,'subject':sp.subject,'phase':sp.phase,'task':sp.task,'integrity':integrity,'clinical':expected_c,'bipolar':expected_b};old=oldgrid.get(f'{sp.protocol}/{sp.subject}/{sp.phase}')
   if old:expected['hpc4_old_grid']=old
   if not same(row,expected):return False
   if check_predecessor and (sp.protocol,sp.subject,sp.phase) in {(r['protocol'],r['subject'],r['phase']) for r in m.load(m.Q)['records']}:
    old=next(r for r in m.load(m.Q)['records'] if (r['protocol'],r['subject'],r['phase'])==(sp.protocol,sp.subject,sp.phase))
    if json.dumps(row,sort_keys=True)!=json.dumps(old,sort_keys=True):return False
   if not (~ck).any():return False
   bip &= bool((~bk).any());f={'protocol':sp.protocol,'subject':sp.subject,'phase':sp.phase,'clinical':_endpoint(cy[:,0],~ck)}
   if (~bk).any():f['bipolar']=_endpoint(by[:,0],~bk)
   files.append(f)
  if not bip:
   for f in files:f.pop('bipolar',None)
 return x.get('bipolar_status')==('BIPOLAR_SENSITIVITY_AVAILABLE' if bip else 'BIPOLAR_SENSITIVITY_UNAVAILABLE') and same(x.get('files'),files) and same(x.get('analysis'),_aggregate(files,bip))
def main(argv=None):
 p=argparse.ArgumentParser();p.add_argument('--result',type=Path,default=m.RESULT);p.add_argument('--witness',type=Path,default=m.WITNESS);p.add_argument('--progress',type=Path,default=m.PROGRESS);p.add_argument('--execution-lock',type=Path,default=m.EXECUTION_LOCK);a=p.parse_args(argv)
 ok=validate(a.result,a.witness,a.progress,execution_lock=a.execution_lock);print('PASS' if ok else 'FAIL');return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
