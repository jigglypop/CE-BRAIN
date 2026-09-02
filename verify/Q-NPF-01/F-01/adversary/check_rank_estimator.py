# -*- coding: utf-8 -*-
"""ladder gaps: raw rank / SPD of g_hat, log det blow-up, Var(T)->0 degeneracy,
   shared-noise coupling between LHS and RHS, and the type of kill 3's Randers term."""
import numpy as np
rng=np.random.default_rng(20260902)
UG=np.array([0.45,0.75,1.05]); H=0.3
def ols(T,y): return np.linalg.lstsq(np.vstack([T,np.ones(len(T))]).T,y,rcond=None)[0][0]

print("== A. g = J^T Sigma^-1 J with o in R^3, d=3: log det sensitivity to the smallest sv of J ==")
print(f"{'sv_min(J)':>10s} {'log det g':>11s} {'sd(logdet g_hat)':>17s}  (Jhat = J + 1% noise, 400 draws)")
for sv in (1.0,0.3,0.1,0.03,0.01,0.0):
    Jt=np.diag([1.0,0.5,sv]); S=np.eye(3)
    g=Jt.T@np.linalg.inv(S)@Jt
    ld=np.log(np.linalg.det(g)) if sv>0 else -np.inf
    sds=[]
    for _ in range(400):
        Jh=Jt+0.01*rng.normal(size=(3,3)); gh=Jh.T@Jh
        sds.append(np.log(max(np.linalg.det(gh),1e-300)))
    print(f"{sv:10.3f} {ld:11.3f} {np.std(sds):17.3f}"+("   <- raw rank lost, log det = -inf" if sv==0 else ""))
print("  ch.21 (lines 1018-1026): raw full rank with a positive lower bound on lambda_min is REQUIRED;")
print("  'g + lambda*g_ref' working SPD is NOT rank evidence. Card states no rank test, no lambda_min,")
print("  no ridge policy, and no minimum trial count for Sigma_hat.")

print("\n== B. Var(T) -> 0 degeneracy: beta1 is undefined at an extremum of log V_g ==")
def L(u,u0): return np.exp(-0.5*((u-u0)/0.30)**2)
for u0 in (0.75,0.74,0.70,0.60,0.45):
    T=np.array([-0.1*(L(u+H,u0)-L(u-H,u0))/(2*H) for u in UG])
    y=np.array([L(u-0.1,u0)-L(u,u0) for u in UG])
    print(f"  logV peak at u0={u0:.2f}: Var(T)={np.var(T):.3e}  beta1={ols(T,y):8.3f}")
print("  input_gate constrains |Dtau| only; there is NO pre-registered lower bound on Var(T).")

print("\n== C. shared-noise coupling: L_hat(u) enters BOTH sides on the frozen grid ==")
print("  LHS(u_i) = L_post(u_i) - L_pre(u_i) ; RHS(u_i) = -Dt[L_pre(u_i+0.3)-L_pre(u_i-0.3)]/0.6")
print("  grid {0.15,0.45,0.75,1.05,1.35} with h=0.3 => L_pre(0.45),L_pre(0.75),L_pre(1.05) appear on BOTH sides.")
for sL in (0.0,0.05,0.10,0.20):
    bs=[]
    for _ in range(20000):
        u0=0.75; Dt=0.10
        eps={u:rng.normal(0,sL) for u in (0.15,0.45,0.75,1.05,1.35)}
        Lp=lambda u: L(u,u0)+eps[round(u,2)]
        y=np.array([L(u-Dt,u0)+rng.normal(0,sL)-Lp(u) for u in UG])       # post independent noise
        T=np.array([-Dt*(Lp(round(u+H,2))-Lp(round(u-H,2)))/(2*H) for u in UG])
        bs.append(ols(T,y))
    bs=np.array(bs)
    print(f"  sigma_L={sL:.2f}: median beta1={np.median(bs):7.3f}  P(in [0.70,1.30])={np.mean((bs>=0.7)&(bs<=1.3)):.3f}"
          f"  P(beta1>0)={np.mean(bs>0):.3f}")
print("  (errors-in-variables: noise in the SAME L_hat on both sides attenuates/biases the slope;")
print("   no pre-registered correction, and the true value is 1.403 here, not 1.00 -- see check_truncation_beta1.)")

print("\n== D. kill 3 type check: is 'mu = a + Jz + b max(v^T z,0)' a Randers/Finsler discriminator? ==")
print("  Randers: F(z,y) = sqrt(y^T g(z) y) + b(z)^T y  -- asymmetry in the TANGENT direction y.")
print("  Card M1 puts a hinge in the MEAN as a function of the STATE z, i.e. a nonlinear readout.")
z=rng.normal(size=(4000,3)); v=np.array([1.,0,0]); b=0.8
mu=lambda Z: Z@np.eye(3) + b*np.maximum(Z@v,0)[:,None]*np.array([1.,0,0])
# Fisher of the M1 family at z: J(z)=dmu/dz -> still a SYMMETRIC quadratic form -> Riemannian, just z-dependent
for zz in (np.array([-1.,0,0]), np.array([1.,0,0])):
    Jz=np.eye(3)+ (b*np.outer(np.array([1.,0,0]),v) if zz@v>0 else 0.0)
    g=Jz.T@Jz
    y1=np.array([1.,0,0]); y2=-y1
    print(f"  z={zz}: length of +y = {np.sqrt(y1@g@y1):.4f}, of -y = {np.sqrt(y2@g@y2):.4f}"
          f"  -> reversible: {np.isclose(np.sqrt(y1@g@y1), np.sqrt(y2@g@y2))}")
print("  => b != 0 makes g depend on z (state-dependent Riemannian), but F stays ABSOLUTELY HOMOGENEOUS")
print("     and REVERSIBLE: F(z,-y)=F(z,y). It can never exhibit Randers/Finsler direction asymmetry.")
print("  kill 3 therefore tests readout LINEARITY, not Riemann-vs-Finsler. Mislabeled.")
print("  Also 'v^T z' pairs the eigenVECTOR v of E_fold=g^-1 g_post with the vector z: a covector/vector")
print("     type mismatch, chart-dependent unless v is transported with g.")
