# -*- coding: utf-8 -*-
"""dimension table audit + content/dof: is coefficient 1 a prediction or Jacobi's formula?
   + does a TIME-DILATION alternative (not a rigid lag) also pass kill 1 and the kappa test?"""
import numpy as np, sympy as sp
rng = np.random.default_rng(20260902)

print("== A. dimension table vs frozen_pipeline definitions ==")
O,T = sp.symbols('O T', positive=True)   # O = lick-count unit, T = time
units = {'o':O, 'mu':O, 'z':1, 'u':T, 'Delta':T, 'sigma_out':O}
J_mean = units['mu']/units['z']                      # J(u) = d mu / d z  (frozen_pipeline.metric)
Sigma   = units['sigma_out']**2
g_pipe  = J_mean*Sigma**-1*J_mean
print(f"  frozen_pipeline g = J^T Sigma^-1 J  with [mu]=O,[z]=1  ->  [J]={J_mean}, [g]={sp.simplify(g_pipe)}")
print(f"  card table says   J: 1 , sigma: O , g: 1   ->  [J^T Sigma^-1 J] = {sp.simplify(1*Sigma**-1*1)}  MISMATCH with g:1")
q = sp.Function('q'); u,s_ = sp.symbols('u sigma', positive=True)
g_toy = (units['mu']/units['u']/units['sigma_out'])**2
print(f"  recovers-2 toy g=(dq/du)^2/sigma^2 with [q]=O -> [g]={sp.simplify(g_toy)}  (NOT 1; table says g:1)")
print(f"  => 'g: 1' cannot hold in both uses. log V_g = (1/2)log det g is a log of a dimensioned"
      f" quantity in the toy; only its u-derivative is well formed.")
print(f"  d_u log V_g : [1/T] = T^-1  OK ;  Delta*dlogV : {sp.simplify(T*T**-1)}  OK (headline eq is consistent)")

print("\n== B. content/dof: is coefficient 1 derived or definitional? ==")
n=2; U=sp.Symbol('u'); D=sp.Symbol('Delta')
M=sp.Matrix(n,n, lambda i,j: sp.Function(f'm{i}{j}')(U))
G=(M.T*M)                                   # generic SPD family g(u)
jac_ok = sp.simplify(sp.diff(sp.log(G.det()),U) - sp.trace(G.inv()*sp.diff(G,U)))==0
# numeric confirmation at d=5
_r=np.random.default_rng(1); _h=1e-6
def _g(t):
    A=np.array([[np.sin(1+i+2*j*t)+0.1*i*t+ (2.0 if i==j else 0.0) for j in range(5)] for i in range(5)])
    return A.T@A+0.5*np.eye(5)
_num=(np.log(np.linalg.det(_g(0.3+_h)))-np.log(np.linalg.det(_g(0.3-_h))))/(2*_h)
_tr=np.trace(np.linalg.solve(_g(0.3),(_g(0.3+_h)-_g(0.3-_h))/(2*_h)))
print(f"  Jacobi  d_u log det g == tr(g^-1 d_u g) ?  symbolic d=2: {jac_ok} ; numeric d=5 rel.diff {abs(_num-_tr)/abs(_tr):.2e}")
print("  (21.57) tr E_fold == Delta log V_g is a DEFINITION in ch.21, not a result.")
print("  Given the shift hypothesis g_post(u)=g_pre(u-Dt):  tr E_fold = L(u-Dt)-L(u), L=log V_g,")
print("  Taylor => -Dt L'(u) + O(Dt^2).  The coefficient 1 has NO freedom once the shift is assumed.")
print("  => empirical content = (i) the metric field rigidly translates, (ii) that translation equals")
print("     the population cross-correlation lag.  NOT a new dimensionless constant.")
print("  free parameters declared: 1 (d=3).  Frozen but uncounted choices: u-subset {0.45,0.75,1.05}")
print("  out of 5, h=0.30, 3-PC subspace, kill windows, gate 0.02s/6-of-8, 0.01 nat, 0.30 placebo.")

print("\n== C. does a TIME-DILATION alternative pass kill 1 and the kappa >= 0.50 test? ==")
UG=np.array([0.45,0.75,1.05]); H=0.3
def L(u,A=1.0,u0=0.75,s=0.30): return A*np.exp(-0.5*((u-u0)/s)**2)
def ols(T,y): return np.linalg.lstsq(np.vstack([T,np.ones(len(T))]).T,y,rcond=None)[0][0]
BIN=0.1; NB=15
def lag_hat_dil(eps, width=0.30, u0=0.75):
    t=(np.arange(NB)+0.5)*BIN
    a=np.exp(-0.5*((t-u0)/width)**2); b=np.exp(-0.5*((t-u0*(1+eps))/(width*(1+eps)))**2)
    a=(a-a.mean())/a.std(); b=(b-b.mean())/b.std()
    lags=np.arange(-5,6)
    cc=np.array([np.corrcoef(a[max(0,-l):NB-max(0,l)],b[max(0,l):NB-max(0,-l)])[0,1] if NB-abs(l)>2 else -1 for l in lags])
    k=int(np.argmax(cc))
    if 0<k<len(cc)-1:
        y0,y1,y2=cc[k-1],cc[k],cc[k+1]; den=y0-2*y1+y2
        d=np.clip(0.5*(y0-y2)/den,-1,1) if abs(den)>1e-12 else 0.0
    else: d=0.0
    return (lags[k]+d)*BIN
print(f"{'dilation eps':>13s} {'Dtau_hat(s)':>12s} {'beta1':>8s} {'kappa':>7s}  kill1[0.70,1.30] / kappa>=0.50")
for eps in (0.05,0.10,0.15,0.20,0.30):
    dth=lag_hat_dil(eps)
    y=np.array([L(u*(1-eps/(1+eps)))-L(u) for u in UG])       # g_post(u)=g_pre(u/(1+eps))
    Tp=np.array([-dth*(L(u+H)-L(u-H))/(2*H) for u in UG])
    b=ols(Tp,y)
    # kappa: at each u both E_fold and E^delay are proportional to g^-1 d_u g  => cosine = +-1
    kap=np.mean([np.sign((u*eps/(1+eps))*dth) for u in UG])
    ok1="PASS" if 0.70<=b<=1.30 else "fail"
    print(f"{eps:13.2f} {dth:12.4f} {b:8.3f} {kap:7.2f}  {ok1} / {'PASS' if kap>=0.5 else 'fail'}")
print("  kappa is a per-u COSINE: any hypothesis g_post(u)=g_pre(u-delta(u)) with delta of one sign")
print("  gives kappa = +1 exactly, whatever delta(u) is. kappa>=0.50 cannot separate a rigid lag")
print("  from a time-warp, a speed change, or any local time-translation. It is nearly redundant.")
