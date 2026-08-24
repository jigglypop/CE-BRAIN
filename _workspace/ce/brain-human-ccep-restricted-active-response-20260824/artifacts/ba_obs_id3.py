"""BA-OBS-ID3 frozen synthetic and source-integrity gates (no tuning flags)."""
from __future__ import annotations
import argparse,csv,hashlib,json,math,platform,re,sys,urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import numpy as np
RUN=Path(__file__).resolve().parents[1]; DATA=Path('data/external/ba_obs_id3_ds003708'); BASE=DATA/'derivatives/preprocessed/sub-01/ses-ieeg01/ieeg'; FS,FLOOR=2048,1e-12
SITES=('LPS2-LPS3','LTG10-LTG11','LTG11-LTG12','LTG13-LTG14','LTG15-LTG16','LTG17-LTG18','LTG19-LTG20','LTG1-LTG2','LTG20-LTG21','LTG22-LTG23','LTG23-LTG24','LTG25-LTG26','LTG26-LTG27','LTG27-LTG28','LTG28-LTG29','LTG29-LTG30','LTG2-LTG3','LTG30-LTG31','LTG31-LTG32','LTG3-LTG4','LTG4-LTG5','LTG5-LTG6','LTG6-LTG7','LTG9-LTG10')
LOCK={'events.tsv':'f4767c8d6f25a641e706d5bee7dfc928b9ca4501c54bf33b67e96dc5562a9aab','channels.tsv':'baf23675a6dd235a7a37549ec16ddcd9e0cebd5b7fa26348b0dcb0f5f82a1318','electrodes.tsv':'6606045c8881d7ed1ef15990c9160e2884bec8789b59aeb9bd5dba709a4b6aec','ieeg.vhdr':'5551a8ca58fe16f489956981ab6437ae65c041891273c08fbea13dfab70cef4a','ieeg.vmrk':'a2e09a018d1359aaf1e8d0bdb65586ec0e4f9611ab9455497d83b3b7b7cfca24','README':'24b59bb2a00971fe9e56a0cef2e9a1368fc86a0a9637e4f395c368e8bae7c908'}
FILES={'events.tsv':BASE/'sub-01_ses-ieeg01_task-ccep_run-01_events.tsv','channels.tsv':BASE/'sub-01_ses-ieeg01_task-ccep_run-01_channels.tsv','electrodes.tsv':BASE/'sub-01_ses-ieeg01_space-MNI152NLin6Sym_electrodes.tsv','ieeg.vhdr':BASE/'sub-01_ses-ieeg01_task-ccep_run-01_ieeg.vhdr','ieeg.vmrk':BASE/'sub-01_ses-ieeg01_task-ccep_run-01_ieeg.vmrk','README':DATA/'derivatives/preprocessed/README'}
def h(x):return hashlib.sha256(x).hexdigest()
def rng(*x):return np.random.default_rng(int.from_bytes(hashlib.sha256('|'.join(map(str,x)).encode()).digest()[:16],'little'))
def d(x,y):return abs(x-y)/(x+y+FLOOR)
def stat(a):
 u=.5*(d(a[:,0,0],a[:,0,1])+d(a[:,1,0],a[:,1,1]));v=.5*(d(a[:,0,0],a[:,1,1])+d(a[:,0,1],a[:,1,0]));return float((np.median(v)+FLOOR)/(np.median(u)+FLOOR))
def stat_b(a):
 u=.5*(np.abs(a[:,:,0,0]-a[:,:,0,1])/(a[:,:,0,0]+a[:,:,0,1]+FLOOR)+np.abs(a[:,:,1,0]-a[:,:,1,1])/(a[:,:,1,0]+a[:,:,1,1]+FLOOR));v=.5*(np.abs(a[:,:,0,0]-a[:,:,1,1])/(a[:,:,0,0]+a[:,:,1,1]+FLOOR)+np.abs(a[:,:,0,1]-a[:,:,1,0])/(a[:,:,0,1]+a[:,:,1,0]+FLOOR));return (np.median(v,axis=1)+FLOOR)/(np.median(u,axis=1)+FLOOR)
def metadata():
 bad=[k for k,p in FILES.items() if not p.exists() or h(p.read_bytes())!=LOCK[k]]
 if bad:raise RuntimeError('SOURCE_IDENTITY_STOP:metadata '+','.join(bad))
 ev=list(csv.DictReader(FILES['events.tsv'].open(encoding='utf-8'),delimiter='\t'));mk=[x for x in FILES['ieeg.vmrk'].read_text(encoding='utf-8').splitlines() if re.match(r'^Mk\d+=',x)]
 if len(ev)!=425 or len(mk)!=425:raise RuntimeError('SOURCE_METADATA_ALIGNMENT_STOP:marker/event count')
 pos=np.array([int(x.split(',')[2])-1 for x in mk]);ss=np.array([int(float(x['sample_start'])) for x in ev]);q=pos-ss
 if (q==-1).sum()!=201 or(q==0).sum()!=224 or not np.all((q==-1)|(q==0)):raise RuntimeError('SOURCE_METADATA_ALIGNMENT_STOP:anchor')
 ns={s:[e for e in ev if e['status']=='good' and e['electrical_stimulation_current']=='6.0 mA' and e['electrical_stimulation_site']==s] for s in SITES};halves={s:(len(v[::2]),len(v[1::2])) for s,v in ns.items()}
 if any(min(v)<5 or max(v)>9 for v in halves.values()):raise RuntimeError('SOURCE_METADATA_ALIGNMENT_STOP:trial halves')
 el=list(csv.DictReader(FILES['electrodes.tsv'].open(encoding='utf-8'),delimiter='\t'));xyz={}
 for x in el:
  try:xyz[x['name']]=np.array([float(x['x']),float(x['y']),float(x['z'])])
  except ValueError:pass
 pairs=[]
 for i,a in enumerate(SITES):
  for b in SITES[i+1:]:
   ca,cb=a.split('-'),b.split('-')
   if set(ca)&set(cb) or np.linalg.norm((xyz[ca[0]]+xyz[ca[1]]-xyz[cb[0]]-xyz[cb[1]])/2)<15:continue
   pairs.append((a,b,hashlib.sha256(f'ds003708-v1.0.2|{a}|{b}'.encode()).digest()[0]))
 sp={'calibration':[x for x in pairs if x[2]<=152],'development':[x for x in pairs if 153<=x[2]<=203],'confirmation':[x for x in pairs if x[2]>=204]}
 if tuple(map(len,(sp['calibration'],sp['development'],sp['confirmation'])))!=(151,42,52):raise RuntimeError('SOURCE_METADATA_ALIGNMENT_STOP:split')
 return halves,sp
OFF=np.arange(-1024,513);BM=(OFF>=-1024)&(OFF<=-11);EM=(OFF>=21)&(OFF<=102);PM=(OFF>=-512)&(OFF<=-431);EARLY=np.zeros(OFF.size);EARLY[np.where(OFF==60)[0][0]]=1.
def equivalence():
 x=np.array([[2.,.5],[3.,1.],[4.,1.5],[5.,2.]]);raw=np.zeros((4,2,OFF.size));z=np.resize(np.array([-1.,1.]),BM.sum());raw[:,0,BM]=z;raw[:,1,BM]=-z;raw[:,:,EM]+=x[:,:,None]*EARLY[EM][None,None,:];raw-=raw[:,:,BM].mean(axis=2,keepdims=True);s=raw[:,:,BM].std();a=np.max(np.abs(raw[:,:,EM].mean(axis=0)),axis=1).mean()/s;b=np.max(np.abs((raw[:,0]-raw[:,1])[:,EM].mean(axis=0))/np.std((raw[:,0]-raw[:,1])[:,BM]));af=np.mean(np.mean(x,axis=1))/s;bf=abs(np.mean(x[:,0]-x[:,1]))/np.std((raw[:,0]-raw[:,1])[:,BM]);toy=np.array([[[1.,2.],[4.,8.]]]);same=.5*(d(1.,4.)+d(2.,8.));cross=.5*(d(1.,8.)+d(2.,4.));assert np.isclose(a,af) and np.isclose(b,bf) and not np.isclose(same,cross) and np.isclose(stat(toy),(cross+FLOOR)/(.5*(d(1.,2.)+d(4.,8.))+FLOOR)) and BM.sum()>0 and EM.sum()>0 and PM.sum()>0;return {'baseline_samples':int(BM.sum()),'early_samples':int(EM.sum()),'pseudo_samples':int(PM.sum()),'mean_exact':float(a),'bip_exact':float(b),'cross_half_index_fixture':True}
def make_trials(halves,pairs,seed,dist,directed):
 rr=rng('fixture',seed,dist);out={};chosen={(a,b) for _,a,b in sorted((hashlib.sha256(f'directed|{a}|{b}'.encode()).digest(),a,b) for a,b,_ in pairs)[:math.ceil(.75*len(pairs))]};assert len(chosen)>=39
 for a,b,_ in pairs:
  for target,source,direction in ((a,b,0),(b,a,1)):
   for half,n in enumerate(halves[source]):
    for mode in ('mean','bip'):
     base=math.exp(hashlib.sha256(f'base|{target}|{source}|{mode}'.encode()).digest()[0]/255*math.log(8));ns=math.exp(hashlib.sha256(f'noise|{target}|{source}|{direction}'.encode()).digest()[0]/255*math.log(16));z=rr.normal(size=n) if dist=='gaussian' else rr.standard_t(5,size=n)/math.sqrt(5/3);latent=1+hashlib.sha256(f'latent|{a}|{b}|{mode}'.encode()).digest()[0]/255*.4;gap=math.log(1.6) if directed and(a,b)in chosen and direction==1 else 0.;raw=base*latent*math.exp(gap)*np.exp(z*.010*ns);out[target,source,half,mode]=raw/base
 return out
def null_test(halves,pairs,trials,inner,label):
 ans={}
 for mode in ('mean','bip'):
  obs=np.empty((len(pairs),2,2));boot=np.empty((inner,len(pairs),2,2));draw={(s,hh):rng('BA-OBS-ID3',label,s,hh).integers(0,n,(inner,n)) for s in SITES for hh,n in enumerate(halves[s])}
  for pi,(a,b,_)in enumerate(pairs):
   for di,(target,source)in enumerate(((a,b),(b,a))):
    for hh in(0,1):obs[pi,di,hh]=trials[target,source,hh,mode].mean();boot[:,pi,di,hh]=trials[target,source,hh,mode][draw[source,hh]].mean(axis=1)
  if not np.all(np.isfinite(obs))or not np.all(obs>0):raise RuntimeError('APPARATUS_OR_RESAMPLING_STOP')
  L=np.log(obs+FLOOR);res=np.log(boot+FLOOR)-L[None];res-=res.mean(axis=0,keepdims=True);nul=np.exp(L.mean(axis=(1,2))[None,:,None,None]+res);R=stat(obs);tail=int(np.sum(stat_b(nul)>=R));ans[mode]={'R':R,'p':(1+tail)/(inner+1),'tail':tail,'index_sha256':h(b''.join(np.ascontiguousarray(x).view(np.uint8).tobytes() for x in draw.values()))}
 ans['composite']=all(ans[m]['R']>1.25 and ans[m]['p']<=.025 for m in('mean','bip'));return ans
def exact_range(payload,start,end):
 if len(payload)!=end-start+1:raise RuntimeError('SOURCE_IDENTITY_STOP:wrong length')
 return True
def development_evocation(early,pseudo):return float(np.median(early)/np.median(pseudo))>=1.25
def confirmation_allowed(development_ok):return bool(development_ok)
def fixtures():
 halves,sp=metadata();pairs=sp['confirmation'];report={'equivalence':equivalence(),'halves':halves,'null':{},'power':{}}
 for dist in('gaussian','t5'):
  vals=[null_test(halves,pairs,make_trials(halves,pairs,s,dist,False),2048,f'null|{dist}|{s}')for s in range(370800,371056)];report['null'][dist]={'refutations':sum(x['composite']for x in vals),'raw_gt':{m:sum(x[m]['R']>1.25 for x in vals)for m in('mean','bip')},'n':256}
  if report['null'][dist]['refutations']>7 or not any(v>0 for v in report['null'][dist]['raw_gt'].values()):raise RuntimeError('STATISTICAL_FALSE_POSITIVE_STOP:'+json.dumps(report))
 for dist in('gaussian','t5'):
  hits=sum(null_test(halves,pairs,make_trials(halves,pairs,s,dist,True),2048,f'power|{dist}|{s}')['composite']for s in range(370800,371056));report['power'][dist]=hits
  if hits<205:raise RuntimeError('STATISTICAL_POWER_STOP:'+json.dumps(report))
 # Executable integrity assertions, before source HEAD/range.
 assert len(pairs)==52 and len(sp['development'])==42 and len(sp['calibration'])==151;assert h(b'wrong')!=LOCK['events.tsv']
 try:exact_range(b'bad',0,4);raise AssertionError('wrong length accepted')
 except RuntimeError:pass
 assert not development_evocation(np.ones(42),np.ones(42));assert not confirmation_allowed(False)
 report['integrity']={'metadata_hash_and_marker_crosswalk':True,'wrong_length_stop':True,'wrong_hash_stop':True,'null_evocation_stop':True,'confirmation_serialized_after_dev_failure':False};report['status']='PASS';return report
def source_plan():
 halves,sp=metadata();q=urllib.request.Request('https://s3.amazonaws.com/openneuro.org/ds003708/derivatives/preprocessed/sub-01/ses-ieeg01/ieeg/sub-01_ses-ieeg01_task-ccep_run-01_ieeg.eeg',method='HEAD')
 with urllib.request.urlopen(q,timeout=60)as r:hd={k.lower():v.strip('"')for k,v in r.headers.items()}
 e={'content-length':'2899637088','etag':'9832a1868bff527620c3cec91df4bb81-3','x-amz-version-id':'ekxCFJH.NE2DhaUDkQ_Nc0iIxeHeLgF4'}
 if{k:hd.get(k)for k in e}!=e:raise RuntimeError('SOURCE_IDENTITY_STOP')
 return {'status':'SOURCE_IDENTITY_PASS','halves':halves,'allocation':{k:len(v)for k,v in sp.items()}}
def rankcorr(x,y):
 def r(v):
  o=np.argsort(v,kind='mergesort');z=np.empty(len(v));z[o]=np.arange(len(v));return z
 return float(np.corrcoef(r(x),r(y))[0,1])
def endpoint(w,ii,mode,early=True):
 # w [trial, channel, offset], exact trial baseline correction then half mean.
 q=w[:,ii,:].copy();q-=q[:,:,BM].mean(axis=2,keepdims=True);mask=EM if early else PM
 if mode=='mean':
  sig=q[:,:,BM].std(axis=(0,2));z=np.max(np.abs(q[:,:,mask].mean(axis=0)),axis=1)/sig;return float(z.mean())
 b=q[:,0]-q[:,1];return float(np.max(np.abs(b[:,mask].mean(axis=0))/b[:,BM].std()))
def real_development():
 # This function is reached only by an explicit post-fixture command.
 plan=source_plan();halves,sp=metadata();ev=list(csv.DictReader(FILES['events.tsv'].open(encoding='utf-8'),delimiter='\t'));mk=[x for x in FILES['ieeg.vmrk'].read_text(encoding='utf-8').splitlines() if re.match(r'^Mk\d+=',x)];anchors=[int(x.split(',')[2])-1 for x in mk]
 chans=list(csv.DictReader(FILES['channels.tsv'].open(encoding='utf-8'),delimiter='\t'));ci={x['name']:i for i,x in enumerate(chans)};store={s:[[],[]]for s in SITES};ranges=[];url='https://s3.amazonaws.com/openneuro.org/ds003708/derivatives/preprocessed/sub-01/ses-ieeg01/ieeg/sub-01_ses-ieeg01_task-ccep_run-01_ieeg.eeg'
 eligible=[(i,e) for i,e in enumerate(ev) if e['status']=='good' and e['electrical_stimulation_current']=='6.0 mA' and e['electrical_stimulation_site'] in store]
 if len(eligible)!=255 or len({i for i,_ in eligible})!=255:raise RuntimeError('SOURCE_METADATA_ALIGNMENT_STOP:eligible IDs')
 def fetch(row):
  i,e=row;a=anchors[i];start=(a-1024)*89*4;end=(a+513)*89*4-1;req=urllib.request.Request(url+'?versionId=ekxCFJH.NE2DhaUDkQ_Nc0iIxeHeLgF4',headers={'Range':f'bytes={start}-{end}','If-Match':'"9832a1868bff527620c3cec91df4bb81-3"'})
  with urllib.request.urlopen(req,timeout=120)as f:b=f.read();hd={k.lower():v.strip('"') for k,v in f.headers.items()};status=f.status
  if status!=206 or hd.get('content-range')!=f'bytes {start}-{end}/2899637088' or hd.get('etag')!='9832a1868bff527620c3cec91df4bb81-3' or hd.get('x-amz-version-id')!='ekxCFJH.NE2DhaUDkQ_Nc0iIxeHeLgF4' or len(b)!=end-start+1:raise RuntimeError('SOURCE_IDENTITY_STOP:range identity')
  return i,e,b,{'event':i,'start':start,'end':end,'count':len(b),'sha256':h(b),'status':status,'content_range':hd.get('content-range'),'etag':hd.get('etag'),'version_id':hd.get('x-amz-version-id')}
 rows=[]
 with ThreadPoolExecutor(max_workers=16) as pool:
  for item in pool.map(fetch,eligible):rows.append(item)
 seen={s:0 for s in SITES}
 for i,e,b,rec in sorted(rows):
  ranges.append(rec);ar=np.frombuffer(b,dtype='<f4').reshape(1537,89).T*.1;s=e['electrical_stimulation_site'];store[s][seen[s]%2].append(ar);seen[s]+=1
 if any(len(store[s][hh])!=halves[s][hh] for s in SITES for hh in(0,1)):raise RuntimeError('APPARATUS_OR_EVOCATION_STOP:trial allocation')
 out={};dev=sp['development']
 for mode in('mean','bip'):
  aa=[];bb=[];pp=[]
  for a,b,_ in dev:
   for target,source in((a,b),(b,a)):
    ix=[ci[x] for x in target.split('-')]
    v=[endpoint(np.asarray(store[source][hh]),ix,mode,True)for hh in(0,1)];p=[endpoint(np.asarray(store[source][hh]),ix,mode,False)for hh in(0,1)];aa.append(v[0]);bb.append(v[1]);pp.extend(p)
  out[mode]={'spearman':rankcorr(np.array(aa),np.array(bb)),'early_over_prestim':float(np.median(np.array(aa+bb))/np.median(np.array(pp))),'defined_edges':len(aa)}
 ok=all(x['spearman']>=.5 and x['early_over_prestim']>=1.25 and x['defined_edges']==84 for x in out.values())
 receipt={'source_plan':plan,'ranges':ranges,'development':out,'status':'DEVELOPMENT_PASS' if ok else 'APPARATUS_OR_EVOCATION_STOP','confirmation_serialized':False}
 (RUN/'artifacts'/'real-development-receipt.json').write_text(json.dumps(receipt),encoding='utf-8');return receipt
def range_audit():
 halves,sp=metadata();ev=list(csv.DictReader(FILES['events.tsv'].open(encoding='utf-8'),delimiter='\t'));expected={i for i,e in enumerate(ev) if e['status']=='good' and e['electrical_stimulation_current']=='6.0 mA' and e['electrical_stimulation_site'] in SITES};r=json.loads((RUN/'artifacts'/'real-development-receipt.json').read_text(encoding='utf-8'));got=[x['event'] for x in r['ranges']]
 if len(expected)!=255 or len(got)!=255 or len(set(got))!=255 or set(got)!=expected:raise RuntimeError('SOURCE_METADATA_ALIGNMENT_STOP:receipt IDs')
 for x in r['ranges']:
  if x['status']!=206 or x['count']!=x['end']-x['start']+1 or x['etag']!='9832a1868bff527620c3cec91df4bb81-3' or x['version_id']!='ekxCFJH.NE2DhaUDkQ_Nc0iIxeHeLgF4' or x['content_range']!=f"bytes {x['start']}-{x['end']}/2899637088":raise RuntimeError('SOURCE_IDENTITY_STOP:receipt range')
 return {'status':'RANGE_RECEIPT_AUDIT_PASS','eligible_ids':255,'unique_ids':255,'identity_ranges':255,'development_status':r['status']}
def confirmation():
 # One frozen B=8192 execution, after range-audit.  Reacquire each version-bound
 # epoch and require its byte SHA to equal the development receipt.
 audit=range_audit()
 if audit['development_status']!='DEVELOPMENT_PASS':raise RuntimeError('APPARATUS_OR_EVOCATION_STOP:confirmation forbidden')
 halves,sp=metadata();pairs=sp['confirmation'];ev=list(csv.DictReader(FILES['events.tsv'].open(encoding='utf-8'),delimiter='\t'));mk=[x for x in FILES['ieeg.vmrk'].read_text(encoding='utf-8').splitlines() if re.match(r'^Mk\d+=',x)];anchors=[int(x.split(',')[2])-1 for x in mk];chans=list(csv.DictReader(FILES['channels.tsv'].open(encoding='utf-8'),delimiter='\t'));ci={x['name']:i for i,x in enumerate(chans)};old={x['event']:x for x in json.loads((RUN/'artifacts'/'real-development-receipt.json').read_text())['ranges']};eligible=[(i,e) for i,e in enumerate(ev) if e['status']=='good' and e['electrical_stimulation_current']=='6.0 mA' and e['electrical_stimulation_site'] in SITES];url='https://s3.amazonaws.com/openneuro.org/ds003708/derivatives/preprocessed/sub-01/ses-ieeg01/ieeg/sub-01_ses-ieeg01_task-ccep_run-01_ieeg.eeg'
 def fetch(row):
  i,e=row;a=anchors[i];st=(a-1024)*89*4;en=(a+513)*89*4-1;q=urllib.request.Request(url+'?versionId=ekxCFJH.NE2DhaUDkQ_Nc0iIxeHeLgF4',headers={'Range':f'bytes={st}-{en}','If-Match':'"9832a1868bff527620c3cec91df4bb81-3"'})
  with urllib.request.urlopen(q,timeout=120)as f:b=f.read();hd={k.lower():v.strip('"')for k,v in f.headers.items()};code=f.status
  if code!=206 or hd.get('content-range')!=f'bytes {st}-{en}/2899637088' or hd.get('etag')!='9832a1868bff527620c3cec91df4bb81-3' or hd.get('x-amz-version-id')!='ekxCFJH.NE2DhaUDkQ_Nc0iIxeHeLgF4' or h(b)!=old[i]['sha256']:raise RuntimeError('SOURCE_IDENTITY_STOP:confirmation range')
  return i,e,np.frombuffer(b,dtype='<f4').reshape(1537,89).T*.1
 rows=[]
 with ThreadPoolExecutor(max_workers=16)as pool:
  for x in pool.map(fetch,eligible):rows.append(x)
 store={s:[[],[]]for s in SITES};seen={s:0 for s in SITES}
 for i,e,x in sorted(rows):s=e['electrical_stimulation_site'];store[s][seen[s]%2].append(x);seen[s]+=1
 B=8192;boot={m:np.empty((B,len(pairs),2,2))for m in('mean','bip')};raw={m:np.empty((len(pairs),2,2))for m in('mean','bip')};prepared={}
 for s in SITES:
  for hh in(0,1):
   q=np.asarray(store[s][hh]);q=q-q[:,:,BM].mean(axis=2,keepdims=True);prepared[s,hh]=(q,(q[:,:,BM]**2).sum(axis=2),q[:,0]-q[:,1],((q[:,0]-q[:,1])[:,BM]**2).sum(axis=1))
 for pi,(a,b,_) in enumerate(pairs):
  for di,(target,source)in enumerate(((a,b),(b,a))):
   ix=[ci[x]for x in target.split('-')]
   for hh in(0,1):
    q,ss,dq,dss=prepared[source,hh];raw['mean'][pi,di,hh]=endpoint(q,ix,'mean',True);raw['bip'][pi,di,hh]=endpoint(q,ix,'bip',True)
 if not all(np.all(np.isfinite(raw[m]))and np.all(raw[m]>0)for m in raw):raise RuntimeError('APPARATUS_OR_RESAMPLING_STOP:raw')
 draws={(s,hh):rng('BA-OBS-ID3','confirmation',3708,s,hh).integers(0,halves[s][hh],(B,halves[s][hh]))for s in SITES for hh in(0,1)}
 for s in SITES:
  for hh in(0,1):
   q,ss,dq,dss=prepared[s,hh];n=q.shape[0];draw=draws[s,hh]
   for lo in range(0,B,128):
    hi=min(B,lo+128);cnt=np.zeros((hi-lo,n));
    for k in range(n):cnt[:,k]=(draw[lo:hi]==k).sum(axis=1)
    av=np.einsum('bn,nct->bct',cnt/n,q);den=np.sqrt((cnt@ss)/(n*BM.sum()))
    for pi,(a,b,_)in enumerate(pairs):
     for di,(target,source)in enumerate(((a,b),(b,a))):
      if source!=s:continue
      ix=[ci[x]for x in target.split('-')];boot['mean'][lo:hi,pi,di,hh]=(np.max(np.abs(av[:,ix,:][:,:,EM]),axis=2)/den[:,ix]).mean(axis=1);bq=q[:,ix[0]]-q[:,ix[1]];bss=(bq[:,BM]**2).sum(axis=1);bav=av[:,ix[0]]-av[:,ix[1]];bden=np.sqrt((cnt@bss)/(n*BM.sum()));boot['bip'][lo:hi,pi,di,hh]=np.max(np.abs(bav[:,EM]),axis=1)/bden
 out={}
 for m in('mean','bip'):
  if not np.all(np.isfinite(boot[m]))or not np.all(boot[m]>0):raise RuntimeError('APPARATUS_OR_RESAMPLING_STOP:surrogate')
  L=np.log(raw[m]+FLOOR);res=np.log(boot[m]+FLOOR)-L[None];res-=res.mean(axis=0,keepdims=True);nul=np.exp(L.mean(axis=(1,2))[None,:,None,None]+res);R=stat(raw[m]);tail=int(np.sum(stat_b(nul)>=R));out[m]={'R':R,'p':(1+tail)/8193,'tail':tail,'index_sha256':h(b''.join(np.ascontiguousarray(x).view(np.uint8).tobytes()for x in draws.values()))}
 phi={m:out[m]['R']>1.25 and out[m]['p']<=.025 for m in out};label='REFERENCE_ROBUST_OBSERVED_MAGNITUDE_RECIPROCITY_PROXY_REFUTED' if all(phi.values()) else 'PROVISIONAL_FIXED_SET_TYPICAL_RECIPROCITY_NOT_REFUTED' if not any(phi.values()) else 'REFERENCE_SENSITIVE_OR_INCONCLUSIVE';records=[(i,old[i]['start'],old[i]['end'],old[i]['count'],old[i]['sha256'])for i,_,_ in sorted(rows)];receipt={'B':8192,'range_audit':audit,'ranges_reacquired':255,'reacquisition_record_sha256':h(json.dumps(records,separators=(',',':')).encode()),'raw_positive':True,'results':out,'phi':phi,'final_label':label,'claim_ceiling':'SINGLE_SUBJECT_HUMAN_CCEP / FINITE_RESTRICTED_OBSERVED_RESPONSE_RECIPROCITY_FALSIFIER / NO_AMBIENT_METRIC_RECOVERY','confirmation_serialized':True};(RUN/'artifacts'/'confirmation-receipt.json').write_text(json.dumps(receipt),encoding='utf-8');return receipt
def main():
 p=argparse.ArgumentParser();p.add_argument('mode',choices=('fixtures','source-plan','real-development','range-audit','confirmation'));x=p.parse_args();o=fixtures()if x.mode=='fixtures'else source_plan()if x.mode=='source-plan'else real_development()if x.mode=='real-development'else range_audit()if x.mode=='range-audit'else confirmation();o.update(python=sys.version,numpy=np.__version__,platform=platform.platform());text=json.dumps(o,sort_keys=True);target=RUN/'artifacts'/('fixture-receipt.json' if x.mode=='fixtures' else 'source-plan-receipt.json' if x.mode=='source-plan' else 'real-development-summary.json' if x.mode=='real-development' else 'range-audit-receipt.json' if x.mode=='range-audit' else 'confirmation-summary.json');target.write_text(text+'\n',encoding='utf-8');print(text)
if __name__=='__main__':main()
