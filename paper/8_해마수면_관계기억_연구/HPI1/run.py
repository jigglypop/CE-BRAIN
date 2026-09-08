from pathlib import Path
import hashlib,json,math,platform
import numpy as np
import scipy
from scipy.stats import ttest_rel,binomtest
from predictive_core import *
R=Path(__file__).resolve().parent

def biology():
    d=json.loads((R/'data/author_thresholds.json').read_text());A=np.asarray(d['Animal_data']);diff=A[1]-A[0]
    rng=np.random.default_rng(20260909);ix=rng.integers(0,A.shape[1],(20000,A.shape[1]))
    stat=ttest_rel(A[1],A[0]);b=binomtest(int(sum(diff>0)),len(diff))
    out={'n_mice':A.shape[1],'paired_endpoints_per_mouse':3,'mean_times':A.mean(1).tolist(),'median_times':np.median(A,axis=1).tolist(),
         'preR1_minus_preR2':diff.tolist(),'mean_difference':float(diff.mean()),'bootstrap_mouse_mean_difference_95':np.quantile(diff[ix].mean(1),[.025,.975]).tolist(),
         'paired_t':{'statistic':float(stat.statistic),'p':float(stat.pvalue)},'positive_mice':int(sum(diff>0)),
         'reversed_mice':int(sum(diff<0)),'sign_test_two_sided_p':float(b.pvalue),'off_diagonal_zero_count':int(sum(A[2]==0)),
         'scope':'Secondary descriptive reanalysis of rounded author summary, not new cohort confirmation.'}
    out['author_simulations']={}
    for key in ('CSCG_data','Hebbian_RNN_data'):
        x=np.asarray(d[key]);out['author_simulations'][key]={'n_simulations':x.shape[1],'mean_times':x.mean(1).tolist(),
        'preR2_earlier_than_preR1':int(sum(x[0]<x[1])),'reverse_order':int(sum(x[0]>x[1])),
        'mse_animal_times_vs_fixed_model_mean':float(np.mean((A-x.mean(1)[:,None])**2))}
    return out

def toy(seed,iters):
    model,slots=template(seed);Bbefore=model.emission.copy();before=model.transition.copy()
    sequences=toy_sequences();ll=model.fit(sequences,iters)
    bA=model.posterior(sequences[0][:5]);bB=model.posterior(sequences[1][:5]);bM=model.posterior([0,None,3,3,3])
    horizon=model.future_likelihoods(1)
    rewardA=bA@horizon;rewardB=bB@horizon;rewardM=bM@horizon
    last=[rewardA[4]/sum(rewardA[4:6]),rewardB[5]/sum(rewardB[4:6])]
    metrics=[]
    # Immediately after the first common G: present observation cannot separate;
    # future joint outcomes eventually distinguish the two inferred contexts.
    cA=model.posterior([0,1,3]);cB=model.posterior([0,2,3])
    for h in range(5):
        L=model.future_likelihoods(h);p=cA@L;q=cB@L
        metrics.append({'horizon':h,'squared_hellinger_chord':hellinger_chord_squared(p,q),'mixture_fisher':mixture_fisher(p,q)})
    return {'seed':seed,'training_loglik_initial':float(ll[0]),'training_loglik_final':float(ll[-1]),
            'minimum_training_loglik_increment':float(np.min(np.diff(ll))),
            'prob_correct_next_reward_with_context':last,'prob_R1_masked_context':float(rewardM[4]/sum(rewardM[4:6])),
            'likelihood_trajectory':ll.tolist(),'predictive_geometry':metrics,
            'fixed_emission_ids_unchanged':bool(np.array_equal(model.emission,Bbefore)),'learned_transition':model.transition.tolist(),
            'state_emission_symbol_ids':slots.tolist()}

def main():
    cfg=json.loads((R/'protocol.json').read_text());out={'name':'HPI-1','versions':{'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__},
    'source_hashes':{p:hashlib.sha256((R/p).read_bytes()).hexdigest() for p in ['protocol.json','predictive_core.py','data/author_thresholds.json']},
    'biology':biology(),'toy':[toy(seed,cfg['toy']['iterations']) for seed in cfg['toy']['seeds']]}
    # Distinct joint laws with identical instantaneous/marginal statistics.
    p=np.array([.5,0,0,.5]);q=np.array([0,.5,.5,0]);out['joint_not_marginal_counterexample']={
        'p':p.tolist(),'q':q.tolist(),'all_single_time_marginals_equal':True,
        'joint_squared_hellinger_chord':hellinger_chord_squared(p,q),'joint_mixture_fisher':mixture_fisher(p,q)}
    (R/'results.json').write_text(json.dumps(out,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    print(json.dumps(out['biology'],indent=2));print('toy summary',[(r['seed'],r['prob_correct_next_reward_with_context'],r['prob_R1_masked_context'],r['minimum_training_loglik_increment']) for r in out['toy']])
if __name__=='__main__':main()
