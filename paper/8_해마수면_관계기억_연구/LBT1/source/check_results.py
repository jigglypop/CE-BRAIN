"""Independent scalar recomputation from saved simulated observations."""
import hashlib,json,math
from pathlib import Path
import numpy as np
from scipy.stats import poisson
from scipy.special import logsumexp

R=Path(__file__).resolve().parent
cfg=json.loads((R/'protocol.json').read_text());result=json.loads((R/'results.json').read_text())
pack=np.load(R/'simulated_trials.npz');error=[];mean_gap=[]
for row in result['rows']:
    seed=row['seed'];Y=pack[f'{seed}_observed'];w=pack[f'{seed}_weights'];tags=pack[f'{seed}_tags'];g=pack[f'{seed}_groups'];gs=pack[f'{seed}_shuffled']
    p=cfg['core'];nu=cfg['poisson_mean'];dose=cfg['pulse_dose'];sig=cfg['measurement_noise_sd']
    pars=[]
    for wi,ti in zip(w,tags):
        u=float(ti)/(p['tag_half']+float(ti));a=p['pot_rate']*u*u;b=p['dep_rate']*u;k=dose*(a+b);m=p['maximum']*a/(a+b)
        mu=m+(float(wi)-m)*math.exp(nu*math.expm1(-k));pars.append((mu,m,float(wi)-m,k))
    mse=math.fsum((float(y)-pa[0])**2 for ys in Y for y,pa in zip(ys,pars))/Y.size
    for name in row['results']:error.append(abs(mse-row['results'][name]['marginal_mean_mse']))
    # One observation for every partition, compared with vectorized full-observation routine:
    # independently compute every group's Poisson mixture using scalar math.
    kmax=int(poisson.ppf(1-1e-13,nu));probs=[float(poisson.pmf(i,nu)) for i in range(kmax+1)];mass=sum(probs)
    partitions={'true_branch':g,'degree_matched_shuffled':gs,'whole_cell_global':np.zeros(len(g),int),'independent_synapses':np.arange(len(g))}
    from verify import partition_logpdf
    for name,groups in partitions.items():
        scalar=0.
        for group in np.unique(groups):
            ix=np.where(groups==group)[0];terms=[]
            for count,pr in enumerate(probs):
                logp=math.log(pr/mass)
                for j in ix:
                    _,m,delta,k=pars[j];pred=m+delta*math.exp(-count*k)
                    logp+=-.5*((float(Y[0,j])-pred)/sig)**2-math.log(sig)-.5*math.log(2*math.pi)
                terms.append(logp)
            scalar+=float(logsumexp(terms))
        vector=partition_logpdf(Y[:1],w,tags,groups,nu,dose,sig)[0][0]
        error.append(abs(scalar-vector))
check={'scalar_metric_checks':len(error),'maximum_absolute_difference':max(error),
       'full_final_rerun_json_identical':(R/'results.json').read_bytes()==(R/'results_final_before_rerun.json').read_bytes(),
       'new_biological_samples':0,'notes':['Scalar recomputation and likelihood product checks are not biological evidence.',
       'Numerical bridge was stabilized and integer branch validation added after first successful run; protocol and biological assumptions unchanged.'],
       'main_branch_changed':False}
assert max(error)<1e-9
assert check['full_final_rerun_json_identical']
(R/'validation.json').write_text(json.dumps(check,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(check,ensure_ascii=False,indent=2))
