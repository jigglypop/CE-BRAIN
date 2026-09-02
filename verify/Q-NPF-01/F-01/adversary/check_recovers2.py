# -*- coding: utf-8 -*-
"""L3 refinement: u-dependent chart with NON-affine log|det J|; and best-fit-shift residual for
   the delay channel (ladder step 3 'exactly yields E^delay')."""
import numpy as np
SEED = 20260902
def spd(sd):
    r = np.random.default_rng(sd); A = r.normal(size=(3,3)); return A@A.T + 0.5*np.eye(3)
base = spd(1); Dtau = 0.05; ug = np.array([0.45,0.75,1.05]); h = 0.3
def gfield(uu):
    M = np.array([[1+0.6*np.sin(2*uu), 0.2*uu, 0.0],
                  [0.1, 1+0.4*uu, 0.3*np.cos(uu)],
                  [0.0, 0.15*uu, 1+0.5*np.exp(-uu)]])
    return M.T@base@M
def logV(uu, phi):
    g = gfield(uu)
    if phi is not None:
        Ji = np.linalg.inv(phi(uu)); g = Ji.T@g@Ji
    return 0.5*np.log(np.linalg.det(g))
def trE(uu, phi):
    gp, gq = gfield(uu), gfield(uu-Dtau)
    if phi is not None:
        Ji = np.linalg.inv(phi(uu)); gp = Ji.T@gp@Ji; gq = Ji.T@gq@Ji
    return 0.5*np.sum(np.log(np.linalg.eigvals(np.linalg.solve(gp,gq)).real))
def beta1(phi):
    y = np.array([trE(x,phi) for x in ug])
    T = np.array([-Dtau*(logV(x+h,phi)-logV(x-h,phi))/(2*h) for x in ug])
    return np.linalg.lstsq(np.vstack([T,np.ones(3)]).T, y, rcond=None)[0][0]
Jc = np.array([[1.3,0.2,0.0],[0.0,0.8,0.1],[0.4,0.0,1.1]])
print(f"{'identity chart':44s} beta1={beta1(None):.6f}")
print(f"{'u-indep chart':44s} beta1={beta1(lambda x: Jc):.6f}")
for k in (0.5, 2.0, 5.0):
    Ju = (lambda kk: (lambda x: Jc@np.diag([np.exp(kk*x*x),1.0,1.0])))(k)
    print(f"u-DEP chart det J=exp({k}u^2) [logdetJ NON-affine] beta1={beta1(Ju):.6f}"
          f"  trE shift={trE(0.75,None)-trE(0.75,Ju):.2e}")
for k in (1.0, 4.0):
    Ju = (lambda kk: (lambda x: Jc@np.diag([np.exp(kk*np.sin(3*x)),1.0,1.0])))(k)
    print(f"u-DEP chart det J=exp({k}sin3u)               beta1={beta1(Ju):.6f}")

print("\n-- delay channel: is the response change a rigid time shift? --")
def run(tau, w, drive_shift=0.0, T=2.0, dt=2e-5, tau_m=0.05):
    n=int(T/dt); nd=int(round(tau/dt)); x=np.zeros(n+1); t=np.arange(n+1)*dt
    I=1.5*np.exp(-0.5*((t-0.30-drive_shift)/0.12)**2)
    for k in range(n):
        xd = x[k-nd] if k-nd>=0 else 0.0
        x[k+1]=x[k]+dt*(-x[k]+w*np.tanh(xd)+I[k])/tau_m
    return t,x
def best_shift_residual(xA,xB,t,mask,maxs=0.05):
    dt=t[1]-t[0]; best=(1e9,None)
    for k in range(0,int(maxs/dt)+1):
        sh=np.concatenate([np.zeros(k),xA[:-k]]) if k>0 else xA
        r=np.linalg.norm((xB-sh)[mask]); best=min(best,(r,k*dt))
    tot=np.linalg.norm((xB-xA)[mask]); return best[0]/tot, best[1]
for w,label in [(0.0,"feedforward w=0"),(0.5,"recurrent w=0.5"),(0.9,"recurrent w=0.9")]:
    t,xA=run(0.020,w); _,xB=run(0.024,w)
    m=(t>0.15)&(t<1.5)
    r,s=best_shift_residual(xA,xB,t,m)
    print(f"{label:20s} internal delay +4ms, cue-locked drive: "
          f"best-shift residual/total={r:.3f} at shift={s*1e3:.1f} ms")
# control: shift the drive too (uniform lag of everything) -> exact shift
t,xA=run(0.020,0.9); _,xB=run(0.020,0.9,drive_shift=0.004)
m=(t>0.15)&(t<1.5); r,s=best_shift_residual(xA,xB,t,m)
print(f"{'drive ALSO shifted':20s} (uniform lag)               : "
      f"best-shift residual/total={r:.3f} at shift={s*1e3:.1f} ms")
