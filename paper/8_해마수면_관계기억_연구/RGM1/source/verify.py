"""Run bounded RGM-1 checks. No network, human label fitting, or hardware I/O."""
from pathlib import Path
import hashlib,json,math,platform
import numpy as np
import scipy
from scipy.integrate import quad_vec,solve_ivp
from scipy.linalg import expm
from scipy.optimize import minimize_scalar
from rgm_core import (path_operator,spectral_source,source_derivatives,response_moment,
                      regional_flow,two_region,fold_trajectory,fold_hessian)
from vendor.local_rule import Parameters,execute,tag_flow
ROOT=Path(__file__).resolve().parent
P=json.loads((ROOT/'protocol.json').read_text())


def spectral_checks(rng):
    errors=[];fd=[];local=[]
    for _ in range(P['spectral_cases']):
        n=int(rng.integers(3,8));Z=rng.normal(size=(n,n));C=Z.T@Z/n+.25*np.eye(n)
        s=float(rng.uniform(.4,1.4));K=C+s*np.eye(n);b=rng.normal(size=n);b/=np.linalg.norm(b)
        def integrand(t):
            v=float(b@expm(-K*t)@b)
            return np.array([v,t*v,t*t*v])
        val,err=quad_vec(integrand,0,np.inf,epsabs=1e-10,epsrel=1e-10)
        target=np.array([response_moment(K,b,k) for k in range(3)])
        errors.append(float(np.max(np.abs(val-target))))
        h=.008;points=np.arange(-4,5,dtype=float)
        vand=np.array([points**j for j in range(9)])
        values=np.array([spectral_source(C,s+h*x) for x in points])
        refs=source_derivatives(C,s)
        for d in (1,2,3):
            rhs=np.zeros(9);rhs[d]=math.factorial(d)
            weights=np.linalg.solve(vand,rhs)
            approx=weights@values/h**d
            fd.append(abs(float(approx)-refs[d-1]))
        v=np.zeros(n);v[0]=1;v[1]=-1
        eps=1e-4
        centered=(spectral_source(C+eps*np.outer(v,v),s)-spectral_source(C-eps*np.outer(v,v),s))/(2*eps)
        # source's denominator also depends on C: subtract its local response.
        target=.5*v@(np.linalg.solve(K,v)-np.linalg.solve(C+np.eye(n),v))
        local.append(abs(centered-target))
    assert max(errors)<1e-8 and max(fd)<1e-5 and max(local)<1e-7
    # Same unordered eigenvalues/global generating function, different local response.
    D=np.diag([1.,4.]);R=np.array([[1.,-1.],[1.,1.]])/math.sqrt(2)
    A=R@D@R.T;b=np.array([1.,0.])
    return {'cases':P['spectral_cases'],'moment_checks':3*P['spectral_cases'],
            'max_matrix_time_integral_error':max(errors),'max_source_finite_difference_error':max(fd),
            'max_local_source_derivative_error':max(local),
            'isospectral_counterexample':{'global_logdet_gap':abs(np.linalg.slogdet(A)[1]-np.linalg.slogdet(D)[1]),
                'local_integrated_response_original':response_moment(D,b),
                'local_integrated_response_rotated':response_moment(A,b)}}


def regional_checks(rng):
    errors=[];semigroup=[]
    for _ in range(P['regional_flow_cases']):
        n=6;K=path_operator(rng.uniform(.2,1.5,n),rng.uniform(.1,.5,n-1))
        E,I,T=rng.uniform(0,1,(3,n));te=rng.uniform(.3,3,n);tt=rng.uniform(3,12,n);duration=float(rng.uniform(.1,5))
        ours=np.concatenate(regional_flow(E,I,T,duration,K,te,tt))
        def rhs(t,y):return np.r_[-y[:n]/te,-K@y[n:2*n],y[:n]*y[n:2*n]-y[2*n:]/tt]
        sol=solve_ivp(rhs,(0,duration),np.r_[E,I,T],rtol=1e-11,atol=1e-13,method='DOP853')
        if not sol.success:raise RuntimeError(sol.message)
        errors.append(float(np.max(np.abs(ours-sol.y[:,-1]))))
        first=regional_flow(E,I,T,duration/2,K,te,tt)
        twice=np.concatenate(regional_flow(*first,duration/2,K,te,tt))
        semigroup.append(float(np.max(np.abs(ours-twice))))
    # Original LBT exact reduction when transport is disabled and parameters shared.
    p=Parameters();n=4;E=np.array([1.,.3,.2,0.]);I=np.ones(n);T=np.zeros(n)
    got=regional_flow(E,I,T,2.,np.eye(n)/p.tau_i_s,np.full(n,p.tau_e_s),np.full(n,p.tau_tag_s))
    ref=tag_flow(E,I,T,2.,p)
    reduction=max(float(np.max(np.abs(x-y))) for x,y in zip(got,ref))
    assert max(errors)<1e-8 and max(semigroup)<1e-9 and reduction<1e-12
    n=6;K=path_operator([.25,.25,.25,1.5,1.5,1.5],[.3]*5)
    e0=np.array([1.,1.,0.,1.,1.,0.]);i0=np.ones(n)
    vals=regional_flow(e0,i0,np.zeros(n),2.,K,np.full(n,2.5),np.full(n,30.))
    # Parameters deliberately supplied, not assigned to named human brain regions.
    weights=np.full(n,.2);after=execute(weights,vals[2],2.,p)
    return {'cases':P['regional_flow_cases'],'max_independent_ode_error':max(errors),
            'max_half_step_composition_error':max(semigroup),'original_lbt_reduction_error':reduction,
            'example':{'instruction':vals[1].tolist(),'tags':vals[2].tolist(),'weights_before':weights.tolist(),
                       'weights_after':after.tolist(),'untagged_indices_unchanged':bool(np.array_equal(after[[2,5]],weights[[2,5]])),
                       'input_note':'Different reaction rates supplied; not learned or mapped to anatomical regions.'}}


def contrast_checks():
    t=np.linspace(0,10,401);a1,a2,g=.2,1.4,.3
    A=two_region(0,1,a1,a2,g,t);B=two_region(0,-1,a1,a2,g,t)
    avg=(a1+a2)/2;delta=(a1-a2)/2;decay=avg+2*g
    # Independent hidden memory realization of the eliminated-contrast equation.
    def rhs(time,y):
        mean,q=y
        return [-avg*mean-delta*math.exp(-decay*time)+delta*delta*q,mean-decay*q]
    sol=solve_ivp(rhs,(0,10),[0.,0.],t_eval=t,method='DOP853',rtol=1e-12,atol=1e-14)
    er=float(np.max(np.abs(sol.y[0]-A[:,0])))
    assert er<1e-10
    return {'mean_initial':0,'hidden_contrasts':[1,-1],'mean_at_t1':[float(A[40,0]),float(B[40,0])],
            'mean_only_prediction_at_t1':0.,'memory_kernel_vs_full_max_error':er,
            'max_mean_separation':float(np.max(np.abs(A[:,0]-B[:,0])))}


def rotating_checks(rng):
    J=np.array([[0.,-1.],[1.,0.]])
    errors=[];omitted=[]
    for _ in range(P['rotating_basis_cases']):
        d=rng.uniform(.2,1.6,2);omega=float(rng.uniform(.3,2));T=float(rng.uniform(.5,3));x0=rng.normal(size=2)
        def R(t):return np.array([[math.cos(omega*t),-math.sin(omega*t)],[math.sin(omega*t),math.cos(omega*t)]])
        def rhs(t,x):return -R(t)@np.diag(d)@R(t).T@x
        sol=solve_ivp(rhs,(0,T),x0,method='DOP853',rtol=1e-12,atol=1e-14)
        exact=R(T)@expm(-(np.diag(d)+omega*J)*T)@x0
        naive=R(T)@expm(-np.diag(d)*T)@x0
        errors.append(float(np.linalg.norm(exact-sol.y[:,-1])))
        omitted.append(float(np.linalg.norm(naive-exact)))
    assert max(errors)<1e-9
    return {'cases':P['rotating_basis_cases'],'correct_connection_max_error':max(errors),
            'omitted_connection_mean_error':float(np.mean(omitted)),'omitted_connection_max_error':max(omitted)}


def folding_checks(rng):
    errors=[];ratios=[]
    for _ in range(P['buckling_scaling_cases']):
        B=float(rng.uniform(.001,.2));S=float(rng.uniform(.3,3))
        k=(S/(2*B))**(1/3);critical=3*B*k*k
        opt=minimize_scalar(lambda q:B*q*q+S/q,bounds=(k/10,k*10),method='bounded',options={'xatol':1e-12})
        errors.append(abs(opt.x-k)/k)
        B2=8*B;k2=(S/(2*B2))**(1/3)
        ratios.append(k/k2)
        assert abs((B*k**4+S*k-critical*k*k))<1e-10
    cfg=P['folding'];n=cfg['nodes']
    below,t,U0,E0=fold_trajectory(n,cfg['B'],cfg['substrate_S'],cfg['N_below'],quartic=cfg['quartic'],duration=cfg['duration'])
    above,t,U1,E1=fold_trajectory(n,cfg['B'],cfg['substrate_S'],cfg['N_above'],quartic=cfg['quartic'],duration=cfg['duration'])
    alt,_,Ualt,_=fold_trajectory(n,cfg['B'],cfg['substrate_S'],cfg['N_above'],quartic=cfg['quartic'],duration=cfg['duration'],method='Radau')
    finer,_,Ufine,_=fold_trajectory(2*n,cfg['B'],cfg['substrate_S'],cfg['N_above'],quartic=cfg['quartic'],duration=cfg['duration'])
    ode_err=float(np.max(np.abs(U1-Ualt)));grid_err=float(np.max(np.abs(U1-Ufine[:,::2])))
    signed_k=np.fft.fftfreq(n,d=1/n)
    slopes=np.fft.ifft(1j*signed_k[None,:]*np.fft.fft(U1,axis=1),axis=1).real
    max_slope=float(np.max(np.abs(slopes)))
    assert max_slope<.2
    # Passive neural smoothing cannot create a buckling instability.
    H,k,spectrum=fold_hessian(n,cfg['B'],cfg['substrate_S'],cfg['N_above'])
    nu=.3+.2*k*k
    passive=np.fft.ifft(np.exp(-nu*cfg['duration'])*np.fft.fft(U1[0])).real
    assert below['final_rms']<below['initial_rms'] and above['final_rms']>10*above['initial_rms']
    assert above['dominant_mode']==above['dominant_linear_growth_mode']
    assert max(below['max_energy_step_increase'],above['max_energy_step_increase'])<1e-8
    assert ode_err<1e-6 and grid_err<1e-4 and max(errors)<1e-6
    np.savez_compressed(ROOT/'folding_trajectories.npz',time=t,below=U0,above=U1,energy_below=E0,energy_above=E1)
    return {'linear_threshold_cases':P['buckling_scaling_cases'],'max_numeric_wavenumber_relative_error':max(errors),
            'double_thickness_wavelength_ratio_range':[min(ratios),max(ratios)],
            'below':below,'above':above,'independent_solver_max_field_error':ode_err,
            'grid64_vs128_max_field_error':grid_err,'max_abs_slope':max_slope,
            'passive_smoothing_final_rms':float(np.sqrt(np.mean(passive*passive))),
            'scope':'Finite periodic 1-D small-slope buckling plus quartic saturation; not fetal-brain FEM or observed folds.'}


def isometry_checks():
    u=np.linspace(-1,1,101);R=2.
    # Plane X=(u,v,0), cylindrical bending X=(R sin(u/R),v,R(1-cos(u/R))).
    Xu=np.stack([np.cos(u/R),np.zeros_like(u),np.sin(u/R)],axis=1)
    Xv=np.tile([0.,1.,0.],(len(u),1))
    g=np.einsum('nia,nja->nij',np.stack([Xu,Xv],axis=1),np.stack([Xu,Xv],axis=1))
    err=float(np.max(np.abs(g-np.eye(2))))
    assert err<1e-14
    return {'intrinsic_metric_max_difference':err,'plane_mean_curvature':0.,'cylinder_mean_curvature':1/(2*R),
            'same_intrinsic_laplacian_under_isometry':True,
            'interpretation':'Extrinsic bending alone does not necessarily alter intrinsic neural transport. Real growth can stretch, alter boundaries or long-range distances.'}


def actual_spectrum():
    path=ROOT/'data/fsLR_32k_midthickness-lh_eval_50.txt';b=path.read_bytes()
    sha=hashlib.sha1(f'blob {len(b)}\0'.encode()+b).hexdigest();expected='d53ffd0a5244211fdea238266e2714a221c6a2a5'
    assert sha==expected
    eig=np.loadtxt(path);assert eig.shape==(50,) and np.all(np.diff(eig)>=0)
    # Normalize by first nonconstant eigenvalue; coefficients are illustrative.
    normalized=eig/eig[1];K=np.diag(.7+.2*normalized)
    probes=np.ones(50)/np.sqrt(50)
    susceptibility=response_moment(K,probes,0)
    delay=response_moment(K,probes,1)/susceptibility
    return {'source':'NSBLab/BrainEigenmodes/data/examples/fsLR_32k_midthickness-lh_eval_50.txt',
            'source_git_blob':sha,'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b),'eigenvalues':eig.tolist(),
            'illustrative_equal_mode_readout_susceptibility':susceptibility,'illustrative_mean_delay':delay,
            'biological_scope':'Published population-template geometry spectrum only. No new individual brain, no time-series fitting, no local eigenvectors, no anatomical predictions.',
            'coefficients':{'leak':.7,'diffusion_in_normalized_spectrum':.2,'time_unit':'arbitrary'}}


def main():
    rng=np.random.default_rng(P['seed'])
    out={'name':'RGM-1','scope':'Conditional mathematical checks + source-verified published human template eigenvalues; no new biology fit.',
         'versions':{'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__},
         'source_hashes':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in ['protocol.json','rgm_core.py','verify.py','vendor/local_rule.py']}}
    for name,fn in [('spectral',lambda:spectral_checks(rng)),('regional',lambda:regional_checks(rng)),
                    ('contrast',contrast_checks),('moving_basis',lambda:rotating_checks(rng)),
                    ('folding',lambda:folding_checks(rng)),('isometric_bending',isometry_checks),('published_geometry',actual_spectrum)]:
        out[name]=fn();print(name,json.dumps(out[name],ensure_ascii=False)[:2500],flush=True)
    (ROOT/'results.json').write_text(json.dumps(out,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    print('RGM-1_CHECKS_PASS',flush=True)
if __name__=='__main__':main()
