"""Run RGM-3 equations against independent ODE, stationary and scalar checks."""
from pathlib import Path
import hashlib,json,math,platform
import numpy as np
import scipy
from scipy.integrate import solve_ivp
from scipy.linalg import null_space
from resource_core import *
ROOT=Path(__file__).resolve().parent
CFG=json.loads((ROOT/'protocol.json').read_text())


def microscopic_generator(states,cap,total,ratios):
    ix={tuple(s):i for i,s in enumerate(states)};Q=np.zeros((len(states),len(states)))
    for row,s in enumerate(states):
        free=total-int(sum(s))
        for j in range(len(cap)):
            if free and s[j]<cap[j]:
                nxt=s.copy();nxt[j]+=1;Q[row,ix[tuple(nxt)]]=ratios[j]*free*(cap[j]-s[j])
            if s[j]:
                nxt=s.copy();nxt[j]-=1;Q[row,ix[tuple(nxt)]]=s[j]
        Q[row,row]=-Q[row].sum()
    return Q


def run():
    rng=np.random.default_rng(CFG['seed']);out={
        'scope':CFG['candidate_scope'],'new_biological_samples':0,
        'versions':{'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__},
        'source_sha256':{n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in ('protocol.json','resource_core.py','verify.py')}
    }
    errors=[];mass=[];semigroup=[]
    for k in range(CFG['exact_pair_cases']):
        C=float(rng.uniform(.1,3));p=float(rng.uniform(0,3));b=float(rng.uniform(0,C))
        a=float(rng.uniform(0,5));d=float(rng.uniform(0,2));dt=float(rng.uniform(.001,4))
        p2,b2=binding_pair(p,b,C,a,d,dt)
        def fun(t,v):
            R=a*v[0]*(C-v[1])-d*v[1]
            return [-R,R]
        sol=solve_ivp(fun,(0,dt),[p,b],method='DOP853',rtol=2e-12,atol=2e-14)
        assert sol.success
        errors.append(float(np.max(np.abs(sol.y[:,-1]-[p2,b2]))))
        mass.append(abs(p+b-p2-b2))
        ph,bh=binding_pair(p,b,C,a,d,dt/2)
        semigroup.append(max(abs(x-y) for x,y in zip((p2,b2),binding_pair(ph,bh,C,a,d,dt/2))))
        assert p2>=0 and 0<=b2<=C
    out['exact_binding']={'cases':len(errors),'max_ode_error':max(errors),'max_total_error':max(mass),'max_semigroup_error':max(semigroup)}
    assert max(errors)<2e-9 and max(semigroup)<2e-11

    network=[];curves=[]
    for case in range(CFG['network_cases']):
        n=3;cap=rng.uniform(.3,1.5,6);sites=np.repeat(np.arange(3),2)
        G=np.array([[0,.45,.12],[.45,0,.35],[.12,.35,0]])
        model=Model(cap,sites,G,rng.uniform(.3,1.4,6),rng.uniform(.1,.5,6))
        m0=rng.uniform(.8,1.3,3);growth=rng.uniform(0,.3,3)
        area=lambda t:m0*np.exp(growth*t)
        tag=lambda t:.7+.2*np.cos(.8*t+np.arange(6))
        p=rng.uniform(.2,.8,3);b=rng.uniform(.01,.10,6)*cap;y0=np.r_[p,b]
        sol=solve_ivp(lambda t,y:model.rhs(t,y,area,tag),(0,CFG['duration']),y0,method='DOP853',rtol=2e-12,atol=2e-14)
        ref=solve_ivp(lambda t,y:model.rhs(t,y,area,tag),(0,CFG['duration']),y0,method='Radau',rtol=2e-11,atol=2e-13)
        assert sol.success and ref.success
        row={'case':case,'initial_total':float(y0.sum()),'ode_agreement':float(np.max(np.abs(sol.y[:,-1]-ref.y[:,-1]))),'errors':[],'conservation':[]}
        for steps in CFG['network_steps']:
            times=np.linspace(0,CFG['duration'],steps+1)
            traj=integrate(model,p,b,times,area,tag)
            row['errors'].append(float(np.max(np.abs(traj[-1]-sol.y[:,-1]))))
            row['conservation'].append(float(np.max(np.abs(traj.sum(axis=1)-y0.sum()))))
            assert traj[:,:3].min()>=0 and traj[:,3:].min()>=0 and np.max(traj[:,3:]-cap)<=1e-12
        row['convergence_ratio']=[row['errors'][j]/row['errors'][j+1] for j in range(3)]
        network.append(row)
        if case==0:curves.append(traj)
    out['coupled_network']={'cases':len(network),'rows':network,
        'max_conservation_error':max(max(r['conservation']) for r in network),
        'max_independent_ode_error':max(r['ode_agreement'] for r in network),
        'last_step_ratio_range':[min(r['convergence_ratio'][-1] for r in network),max(r['convergence_ratio'][-1] for r in network)]}
    assert out['coupled_network']['max_conservation_error']<5e-12
    assert min(r['convergence_ratio'][-1] for r in network)>3.5

    # Closed-pool dissipation. Fixed tags/geometry for the thermodynamic statement.
    model=Model(np.array([1.,.8,1.2,1.]),np.array([0,0,1,1]),np.array([[0.,.4],[.4,0.]]),np.array([.8,1.,.6,.9]),np.array([.15,.2,.12,.18]))
    area=lambda t:np.array([1.,1.4]);p=np.array([.9,.1]);b=np.array([.05,.12,.09,.01])
    ps,bs,c=equilibrium(p.sum()+b.sum(),area(0),model.capacities,model.off_rates/model.on_rates)
    times=np.linspace(0,80,1601);traj=integrate(model,p,b,times,area)
    H=np.array([entropy(y[:2],y[2:],ps,bs,model.capacities) for y in traj])
    out['dissipation']={'initial_entropy':float(H[0]),'final_entropy':float(H[-1]),
        'max_step_increase':float(np.max(np.diff(H))),
        'max_equilibrium_error_at_final_time':float(np.max(np.abs(traj[-1]-np.r_[ps,bs]))),
        'total':float(p.sum()+b.sum()),'equilibrium_concentration':c}
    assert np.max(np.diff(H))<2e-12

    response=[]
    for _ in range(CFG['equilibrium_response_cases']):
        m=rng.uniform(.4,2,3);C=rng.uniform(.4,2,5);Kd=rng.uniform(.04,.8,5);total=float(rng.uniform(.4,3))
        ps,bs,c=equilibrium(total,m,C,Kd)
        exact=capacity_response(m,C,Kd,c);approx=np.empty_like(exact)
        for j in range(len(C)):
            d=1e-5;cp=C.copy();cm=C.copy();cp[j]+=d;cm[j]-=d
            approx[:,j]=(equilibrium(total,m,cp,Kd)[1]-equilibrium(total,m,cm,Kd)[1])/(2*d)
        response.append(float(np.max(np.abs(exact-approx))))
    out['equilibrium_sensitivity']={'cases':len(response),'max_finite_difference_error':max(response)}
    assert max(response)<1e-7

    total=.8;Kd=.15
    no_comp=equilibrium(total,[1.],[1.],[Kd])
    competitor=equilibrium(total,[1.],[1.,1.],[Kd,Kd])
    rescue=equilibrium(2*total,[1.],[1.,1.],[Kd,Kd])
    chemostat=total/(Kd+total)
    out['competition_example']={'available_total':total,'one_target_bound':float(no_comp[1][0]),
        'with_competitor_each_bound':competitor[1].tolist(),
        'double_supply_each_bound':rescue[1].tolist(),
        'clamped_concentration_reservoir_each_bound':chemostat,
        'clamped_model_two_sites_bound_total':2*chemostat,
        'clamped_interpretation':'Valid open reservoir, invalid as a closed .8-unit pool without recording supply.'}

    # Pure finite pool need not be winner-take-all.
    symmetric=equilibrium(1.,[1.],[1.,1.],[.2,.2])
    out['not_winner_take_all']={'equal_sites_bound':symmetric[1].tolist(),'asymmetry':float(abs(np.diff(symmetric[1])[0])),
       'interpretation':'No spontaneous winner-take-all is generated by this fixed-affinity equilibrium. Feedback or changing tags would be an additional hypothesis.'}

    cap=CFG['microscopic_capacities'];N=CFG['microscopic_total'];ratio=CFG['microscopic_ratios']
    states,prob,mean,cov=microscopic_stationary(cap,N,ratio);Q=microscopic_generator(states,cap,N,ratio)
    ref=null_space(Q.T)[:,0];ref/=ref.sum()
    detailed=float(np.max(np.abs(prob[:,None]*Q-prob[None,:]*Q.T)))
    # Uniform supply shared between trials: law of total covariance.
    means=[];covs=[];probs=[]
    for n in CFG['mixture_totals']:
        _,_,mm,cc=microscopic_stationary(cap,n,ratio);means.append(mm);covs.append(cc)
    means=np.asarray(means);avg=means.mean(axis=0)
    within=np.mean(covs,axis=0);between=(means-avg).T@(means-avg)/len(means)
    out['finite_resource_noise']={'states':len(states),'fixed_total':N,
        'mean_bound':mean.tolist(),'fixed_pool_covariance':cov.tolist(),
        'stationarity_residual':float(np.max(np.abs(prob@Q))),
        'detailed_balance_error':detailed,'stationary_probability_max_difference':float(np.max(np.abs(prob-ref))),
        'supply_mixture':CFG['mixture_totals'],'conditional_covariance':within.tolist(),
        'between_supply_covariance':between.tolist(),'marginal_covariance':(within+between).tolist()}
    assert cov[0,1]<0 and (within+between)[0,1]>0
    assert detailed<1e-10 and np.max(np.abs(prob-ref))<1e-10

    # Memory readout is ordinary occupancy-based edge gain, not an extra decoder.
    inputs=np.array([1.,.4]);sgn=np.array([1.,-1.])
    out['same_readout_example']={'two_sites_closed_output':float(np.tanh((competitor[1]*inputs*sgn).sum())),
                               'two_sites_reservoir_output':float(np.tanh((np.full(2,chemostat)*inputs*sgn).sum())),
                               'scope':'Illustrative fixed input, no trained task or claimed accuracy improvement.'}
    (ROOT/'results.json').write_text(json.dumps(out,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
    np.savez_compressed(ROOT/'trajectories.npz',dissipation_time=times,dissipation_state=traj,entropy=H,coupled_example=curves[0])
    print(json.dumps({k:v for k,v in out.items() if k not in ('coupled_network','source_sha256')},indent=2))
    print('NETWORK',json.dumps({k:v for k,v in out['coupled_network'].items() if k!='rows'},indent=2))

if __name__=='__main__':run()
