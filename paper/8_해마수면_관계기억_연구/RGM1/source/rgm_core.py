"""RGM-1: exact finite-dimensional bridges, not a calibrated brain model.

The shared object is a spatial/response operator, not a shared physical unit or
an assertion that neural diffusion and elastic buckling are the same process.
"""
from __future__ import annotations
import math
import numpy as np
from scipy.linalg import eigh, expm
from scipy.integrate import solve_ivp


def positive(x,name,zero=False):
    if isinstance(x,(bool,np.bool_)) or not isinstance(x,(int,float,np.integer,np.floating)):
        raise TypeError(f'{name}: nonboolean real required')
    x=float(x)
    if not math.isfinite(x) or x < 0 or (x==0 and not zero):
        raise ValueError(f'{name}: finite {"nonnegative" if zero else "positive"} required')
    return x


def symmetric(matrix,name,spd=False):
    a=np.array(matrix,dtype=float,copy=True)
    if a.ndim!=2 or a.shape[0]!=a.shape[1] or not np.isfinite(a).all():
        raise ValueError(f'{name}: finite square matrix required')
    if not np.allclose(a,a.T,atol=1e-12,rtol=1e-12):
        raise ValueError(f'{name}: symmetry required')
    a=(a+a.T)*.5
    if spd and np.linalg.eigvalsh(a)[0]<=0:
        raise ValueError(f'{name}: positive definiteness required')
    return a


def path_operator(leaks,couplings):
    leaks=np.array(leaks,float,copy=True);c=np.array(couplings,float,copy=True)
    if leaks.ndim!=1 or c.shape!=(len(leaks)-1,) or not np.isfinite(leaks).all() or not np.isfinite(c).all() or np.any(leaks<=0) or np.any(c<0):
        raise ValueError('positive leak and nonnegative path coupling required')
    K=np.diag(leaks)
    for i,w in enumerate(c):
        K[i,i]+=w;K[i+1,i+1]+=w;K[i,i+1]-=w;K[i+1,i]-=w
    return K


def spectral_source(C,s,sref=1.0):
    """Dimensionless log determinant ratio; finite matrix only, NOT a bio energy."""
    C=symmetric(C,'C');s=positive(s,'s');sref=positive(sref,'sref')
    eig=np.linalg.eigvalsh(C)
    if min(eig+s)<=0 or min(eig+sref)<=0:raise ValueError('spectrum not positive')
    return .5*float(np.log((eig+s)/(eig+sref)).sum())


def source_derivatives(C,s,orders=3):
    C=symmetric(C,'C');s=positive(s,'s');e=np.linalg.eigvalsh(C)+s
    if min(e)<=0:raise ValueError('nonpositive shifted spectrum')
    return [(-1)**(n-1)*math.factorial(n-1)/2*float(np.sum(e**(-n))) for n in range(1,orders+1)]


def response_moment(K,b,order=0):
    K=symmetric(K,'K',spd=True);b=np.asarray(b,float)
    if b.shape!=(len(K),) or not np.isfinite(b).all() or type(order) is not int or order<0:raise ValueError('bad moment arguments')
    x=b.copy()
    for _ in range(order+1):x=np.linalg.solve(K,x)
    return math.factorial(order)*float(b@x)


def regional_flow(E,I,T,dt,K,tau_e,tau_tag,gain=1.):
    """Exact flow E'=-dE, I'=-KI, T'=gain E*I-cT.

    K must also be an M-matrix generator (nonpositive off-diagonals), ensuring
    nonnegative chemical proxy traces for nonnegative initial conditions.
    """
    K=symmetric(K,'K',spd=True);dt=positive(dt,'dt',True);gain=positive(gain,'gain',True)
    n=len(K);arrays=[np.array(x,float,copy=True) for x in (E,I,T,tau_e,tau_tag)]
    if any(x.shape!=(n,) or not np.isfinite(x).all() for x in arrays):raise ValueError('aligned finite vectors required')
    E,I,T,te,tt=arrays
    if any(np.any(x<0) for x in (E,I,T)) or min(te)<=0 or min(tt)<=0:raise ValueError('bad trace/rate')
    off=K-np.diag(np.diag(K))
    if off.max()>1e-12:raise ValueError('positive off-diagonal not a positive chemical semigroup')
    if dt==0:return E.copy(),I.copy(),T.copy()
    lam,U=eigh(K);coef=U*(U.T@I)[None,:]
    r=1/te[:,None]+lam[None,:];c=1/tt[:,None];gap=np.abs(r-c)
    bridge=np.full_like(r,dt)
    np.divide(-np.expm1(-gap*dt),gap,out=bridge,where=gap>1e-10)
    bridge*=np.exp(-np.minimum(r,c)*dt)
    Tnew=T*np.exp(-dt/tt)+gain*E*np.sum(coef*bridge,axis=1)
    Inew=U@(np.exp(-lam*dt)*(U.T@I))
    # Only roundoff at the level of the stated tolerance may be removed.
    if min(Tnew)<-1e-11 or min(Inew)<-1e-11:raise ArithmeticError('positivity violation')
    return E*np.exp(-dt/te),np.maximum(Inew,0),np.maximum(Tnew,0)


def two_region(mean,contrast,a1,a2,coupling,times):
    a1=positive(a1,'a1');a2=positive(a2,'a2');g=positive(coupling,'coupling',True)
    avg=(a1+a2)/2;diff=(a1-a2)/2
    M=np.array([[-avg,-diff],[-diff,-avg-2*g]])
    return np.array([expm(t*M)@np.array([mean,contrast]) for t in times])


def fourier_laplacian(n,length=2*math.pi):
    if type(n) is not int or n<8 or n%2:raise ValueError('even n>=8 required')
    length=positive(length,'length')
    k=2*math.pi*np.fft.fftfreq(n,d=length/n)
    ident=np.eye(n)
    L=np.fft.ifft(k[:,None]**2*np.fft.fft(ident,axis=0),axis=0).real
    return (L+L.T)*.5,np.abs(k)


def fold_hessian(n,B,S,N,length=2*math.pi):
    """Thin-plate on a linear elastic half-space proxy, periodic finite grid.
    B k^4 + S |k| - N k^2, followed by a quartic saturation in fold_trajectory.
    NOT a finite-strain fetal brain model. Constant translations are projected out.
    """
    B=positive(B,'B');S=positive(S,'S');N=positive(N,'N',True)
    L,k=fourier_laplacian(n,length)
    spectrum=B*k**4+S*k-N*k**2
    H=np.fft.ifft(spectrum[:,None]*np.fft.fft(np.eye(n),axis=0),axis=0).real
    return (H+H.T)*.5,k,spectrum


def fold_trajectory(n,B,S,N,quartic=1.,duration=50.,seed=39,method='BDF'):
    H,k,spectrum=fold_hessian(n,B,S,N)
    quartic=positive(quartic,'quartic');duration=positive(duration,'duration')
    grid=2*math.pi*np.arange(n)/n
    rng=np.random.default_rng(seed)
    # The same smooth initial field at either resolution, not regenerated noise.
    u0=sum(1e-3*rng.normal()*np.cos(j*grid+rng.uniform(0,2*math.pi)) for j in range(1,10))
    u0-=u0.mean();P=np.eye(n)-np.ones((n,n))/n
    def rhs(t,u):return -P@(H@u+quartic*u**3)
    def jac(t,u):return -P@(H+np.diag(3*quartic*u*u))
    times=np.linspace(0,duration,301)
    sol=solve_ivp(rhs,(0,duration),u0,t_eval=times,method=method,jac=jac,rtol=2e-9,atol=2e-11)
    if not sol.success:raise RuntimeError(sol.message)
    U=sol.y.T
    energy=np.einsum('ti,ij,tj->t',U,H,U)/2+quartic*np.sum(U**4,axis=1)/4
    power=np.abs(np.fft.rfft(U[-1]))**2;power[0]=0
    return {'initial_rms':float(np.sqrt(np.mean(u0*u0))),
            'final_rms':float(np.sqrt(np.mean(U[-1]**2))),
            'dominant_mode':int(np.argmax(power)),
            'initial_energy':float(energy[0]),'final_energy':float(energy[-1]),
            'max_energy_step_increase':float(np.max(np.diff(energy))),
            'dominant_linear_growth_mode':int(np.argmax(-spectrum[:n//2+1])),
            'max_linear_growth_rate':float(np.max(-spectrum)),
            'N_critical_discrete':float(np.min((B*k*k+np.divide(S,k,out=np.full_like(k,np.inf),where=k>0))[k>0])),
            'nfev':int(sol.nfev)}, times,U,energy
