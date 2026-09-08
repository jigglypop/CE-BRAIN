"""Independent scalar data checks and finite-difference information checks."""
from pathlib import Path
import json,math,hashlib
import numpy as np
from scipy.integrate import quad
from predictive_core import *
R=Path(__file__).resolve().parent
D=json.loads((R/'data/author_thresholds.json').read_text());O=json.loads((R/'results.json').read_text())
a=D['Animal_data'];n=len(a[0]);diff=[y-x for x,y in zip(a[0],a[1])]
mean=math.fsum(diff)/n;var=math.fsum((v-mean)**2 for v in diff)/(n-1);t=mean/math.sqrt(var/n);df=n-1
norm=math.gamma((df+1)/2)/(math.sqrt(df*math.pi)*math.gamma(df/2))
p=2*quad(lambda x:norm*(1+x*x/df)**(-(df+1)/2),abs(t),np.inf,epsabs=1e-13)[0]
k=min(sum(v>0 for v in diff),sum(v<0 for v in diff));sign=min(1.,2*sum(math.comb(n,i) for i in range(k+1))/2**n)
errs=[abs(mean-O['biology']['mean_difference']),abs(t-O['biology']['paired_t']['statistic']),abs(p-O['biology']['paired_t']['p']),abs(sign-O['biology']['sign_test_two_sided_p'])]
for row,value in zip(a,O['biology']['mean_times']):errs.append(abs(math.fsum(row)/len(row)-value))
for key in ('CSCG_data','Hebbian_RNN_data'):
 x=D[key];means=[math.fsum(r)/len(r) for r in x];ref=O['biology']['author_simulations'][key]
 errs.extend(abs(v-w) for v,w in zip(means,ref['mean_times']))
 mse=math.fsum((val-means[r])**2 for r,row in enumerate(a) for val in row)/(3*n)
 errs.append(abs(mse-ref['mse_animal_times_vs_fixed_model_mean']))
assert max(errs)<1e-12
# No tests are interpreted as animal samples.
rng=np.random.default_rng(93401);klerrs=[];monotonic=[];exact_word_errors=[]
for _ in range(64):
 T=rng.uniform(.1,1,(3,3));T/=T.sum(1,keepdims=True);B=rng.uniform(.1,1,(3,2));B/=B.sum(1,keepdims=True)
 m=ContextModel(T,B,np.ones(3)/3);vals=[]
 for h in range(4):
  L=m.future_likelihoods(h);p0=L[0];q0=L[1];vals.append(mixture_fisher(p0,q0))
  if h:
   eps=2e-4;c=(p0+q0)/2;lo=(.5-eps)*p0+(.5+eps)*q0;hi=(.5+eps)*p0+(.5-eps)*q0
   numerical=float(np.sum(c*(np.log(c/lo)+np.log(c/hi)))/eps**2)
   klerrs.append(abs(numerical-vals[-1]))
 monotonic.append(float(min(np.diff(vals))))
 # Exact transition/emission path summation for one word independent of recursion.
 word=(0,1,0);L=m.future_likelihoods(3)
 from itertools import product
 for start in range(3):
  terms=[]
  for path in product(range(3),repeat=3):
   term=1.;i=start
   for j,y in zip(path,word):term*=float(T[i,j])*float(B[j,y]);i=j
   terms.append(term)
  exact_word_errors.append(abs(math.fsum(terms)-L[start,2]))
assert max(klerrs)<1e-6 and min(monotonic)>-1e-12 and max(exact_word_errors)<1e-12
out={'independent_biological_summary_scalars':len(errs),'maximum_summary_difference':max(errs),
     'independent_t_tail_integral_p':p,'exact_sign_test_p':sign,
     'information_cases':64,'kl_curvature_comparisons':len(klerrs),'maximum_kl_curvature_error':max(klerrs),
     'minimum_information_increment':min(monotonic),'joint_path_scalar_comparisons':len(exact_word_errors),'maximum_joint_path_error':max(exact_word_errors),
     'new_raw_neural_recordings':0,'newly_analyzed_author_mouse_summary_records':11,
     'author_literal_source_crosscheck':'Array literals checked against a second read of original notebook lines60-108; printed t-test p reproduces. Full notebook blob not locally verified.',
     'rerun_results_identical': (R/'results.json').read_bytes()==(R/'results_first_current.json').read_bytes() if (R/'results_first_current.json').exists() else None,
     'rerun_refinement_identical':(R/'refinement_results.json').read_bytes()==(R/'refinement_first.json').read_bytes() if (R/'refinement_first.json').exists() else None}
(R/'validation.json').write_text(json.dumps(out,indent=2,allow_nan=False)+'\n');print(json.dumps(out,indent=2))
