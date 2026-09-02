# -*- coding: utf-8 -*-
"""Q-NPF-02 / F-01 카드 문턱 사전등록용 합성 보정 (v6). 실제 자료 없음. 씨앗 20260902.

가설: ĝ_post(u) = e^{2γ} g_pre(u-δ(u)),  δ(u) = k_x (a u_pk + b u),  예측 (a,b) = (0,1).
  k_x = ε̂/(1+ε̂)는 평균반응 anchored warp에서만 재고 계량에는 자유 진폭이 없다.
1차: E0(u) = -½δ(u) S0(u) + O(δ²),  tr E(u) = dγ - δ(u) ∂_u log V_g + O(δ²).  E0는 γ에 무관.

동결 추정기:
  pre trial을 시간순 홀/짝 두 반쪽으로 나눈다(LHS와 템플릿의 측정오차 상관 제거).
  - 공통 whitening frame  P_k = g̃_full(u_k)^{-1/2},  g̃ = Savitzky-Golay(창 7 bin, 3차) 평활.
  - LHS   Y0_k = trace-free ½[log(P ĝ_post P) - log(P ĝ_pre^{(1)} P)]
  - 템플릿 A_k = -½ k_x u_pk S0_k (상수 지연), B_k = -½ k_x u_k S0_k (anchored 팽창),
           S0 = trace-free(P g̃'_2 P), g̃'_2 = 반쪽 2의 SG 미분
  - 잡음 복제 (ĝ^{(1)}-ĝ^{(2)})/2 로 만든 A^ν,B^ν → 보정 Gram  G* = G - 2 G^ν
  - 종점 E1 진폭 b1 = <Y0,B>/G*_BB (예측 1),  E2 형태 Ψ = b ū/(a u_pk + b ū) (예측 1; 강체지연 0),
           E3 방향-홀수 κ (예측 0),  E4 평균반응 분류 Λ_x = log(r_shift/r_dil) (예측 >0)
  Ψ는 (a,b)의 비율이라 감쇠(공통 스칼라)에 불변이다.
세계: D(anchored dilation, 참 Ψ=1) S(rigid shift, 참 Ψ=0) R(response-only, 참 진폭 0)
      G(gain-only, gate STOP) F(D + 방향-홀수 strain κ=0.30) P(placebo).
잡음: ĝ = (g^{1/2}+E/√n)^T(g^{1/2}+E/√n); 반쪽 n=N/2, post n=N; z̄ 잡음 1/√N.
"""
import numpy as np, sys, time, math
SEED = 20260902
H = 0.1; U = 0.05 + H*np.arange(15); D = 3
KFIT = np.arange(1, 14)
LAM_FLOOR = 0.02; S_FLOOR = 0.5; MIN_BINS = 7; VARU_FLOOR = 0.04
KX_LO, KX_HI = 0.05, 0.30; R2_FLOOR = 0.50
EGRID = np.arange(-0.35, 0.35 + 1e-9, 0.002); DGRID = np.arange(-0.30, 0.30 + 1e-9, 0.002)
T_LO, T_HI = U[1], U[13]
SG_HW, SG_DEG = 3, 3
def _sg_rows():
    Wv = np.zeros((15, 15)); Wd = np.zeros((15, 15))
    for k in range(15):
        lo = max(0, k-SG_HW); hi = min(15, k+SG_HW+1); idx = np.arange(lo, hi)
        X = np.vstack([(U[idx]-U[k])**j for j in range(SG_DEG+1)]).T
        Pi = np.linalg.pinv(X); Wv[k, idx] = Pi[0]; Wd[k, idx] = Pi[1]
    return Wv, Wd
SGV, SGD = _sg_rows()

def sym(A): return 0.5*(A + np.swapaxes(A, -1, -2))
def fsym(A, f):
    w, V = np.linalg.eigh(sym(A)); return np.einsum('...ij,...j,...kj->...ik', V, f(w), V)
def logm(A): return fsym(A, np.log)
def expm(A): return fsym(A, np.exp)
def sqrtm(A): return fsym(A, np.sqrt)
def isqrtm(A): return fsym(A, lambda w: w**-0.5)
def tf(E): return E - np.trace(E, axis1=-2, axis2=-1)[..., None, None]*np.eye(D)/D
def smooth(V):
    F = V.reshape(15, -1); return (SGV @ F).reshape(V.shape), (SGD @ F).reshape(V.shape)

B0 = np.diag(np.log([0.5, 0.2, 0.08]))
BA = np.array([[1.0, 0.3, 0.1], [0.3, 0.4, 0.2], [0.1, 0.2, 0.2]])
BB_ = np.array([[0.2, -0.1, 0.0], [-0.1, 0.6, 0.15], [0.0, 0.15, 0.9]])
def g_true(u):
    u = np.atleast_1d(u)
    f1 = 1.2*np.exp(-0.5*((u-0.55)/0.22)**2); f2 = 0.8*(1-np.exp(-np.maximum(u, 0)/0.35))
    return expm(B0 + f1[:, None, None]*BA + f2[:, None, None]*BB_)
VA = np.array([0.8, 0.5, 0.33]); VA /= np.linalg.norm(VA)
VB = np.array([-0.3, 0.7, 0.65]); VB /= np.linalg.norm(VB)
def zbar_true(u):
    u = np.atleast_1d(u)
    return 1.5*np.exp(-0.5*((u-0.6)/0.25)**2)[:, None]*VA + 0.8*(1-np.exp(-np.maximum(u, 0)/0.3))[:, None]*VB
def noisy_g(g, n, rng):
    if n is None: return g.copy()
    Jh = sqrtm(g) + rng.normal(size=g.shape)/math.sqrt(n)
    return np.einsum('...ji,...jk->...ik', Jh, Jh)

def lagrange4(nodes, t):
    t = np.atleast_1d(np.asarray(t, float)); j = np.clip(np.floor((t - U[0])/H).astype(int), 1, 12)
    out = np.zeros((len(t),) + nodes.shape[1:])
    for m in range(-1, 3):
        xm = U[j+m]; w = np.ones(len(t))
        for n in range(-1, 3):
            if n != m: w *= (t - U[j+n])/(xm - U[j+n])
        out += w.reshape((-1,) + (1,)*(nodes.ndim-1))*nodes[j+m]
    return out
def warp_fit(zpre, zpost, grid, kind):
    TT = (U[None, :]/(1+grid[:, None])) if kind == 'dil' else (U[None, :] - grid[:, None])
    M = (TT >= T_LO) & (TT <= T_HI)
    Z = lagrange4(zpre, TT.ravel()).reshape(len(grid), 15, D)*M[:, :, None]
    Zo = zpost[None, :, :]*M[:, :, None]
    al = np.einsum('gkd,gkd->g', Z, Zo)/np.maximum(np.einsum('gkd,gkd->g', Z, Z), 1e-12)
    Rr = Zo - al[:, None, None]*Z
    res = np.einsum('gkd,gkd->g', Rr, Rr)/np.maximum(M.sum(1), 1); res[M.sum(1) < 8] = np.inf
    i = int(np.argmin(res)); return res[i], grid[i]

def endpoints(G, Gn, y, u_pk, ub, corr=2.0):
    Gs = G - corr*Gn; o = {'Gs11': Gs[1, 1]}
    o['b1'] = y[1]/Gs[1, 1] if Gs[1, 1] > 0 else np.nan
    o['a1'] = y[0]/Gs[0, 0] if Gs[0, 0] > 0 else np.nan
    if Gs[0, 0] > 0 and Gs[1, 1] > 0:
        rho = Gs[0, 1]/math.sqrt(Gs[0, 0]*Gs[1, 1]); rho = max(min(rho, 0.999999), -0.999999)
        D0 = (1 - rho*rho)/(1 + rho*rho)
        qa = y[0]**2/Gs[0, 0]; qb = y[1]**2/Gs[1, 1]
        o['rho'] = rho; o['D0'] = D0
        o['Psi2'] = -((qa - qb)/(qa + qb))/D0 if (qa + qb) > 0 and D0 > 1e-9 else np.nan
    else:
        o['rho'] = np.nan; o['D0'] = np.nan; o['Psi2'] = np.nan
    det = Gs[0, 0]*Gs[1, 1] - Gs[0, 1]**2; o['det'] = det
    if det > 0 and Gs[0, 0] > 0 and Gs[1, 1] > 0:
        a = (Gs[1, 1]*y[0] - Gs[0, 1]*y[1])/det; b = (Gs[0, 0]*y[1] - Gs[0, 1]*y[0])/det
        den = a*u_pk + b*ub
        o.update(a=a, b=b, lag=den/ub, Psi=(b*ub/den if abs(den) > 1e-12 else np.nan))
        M3 = np.array([[Gs[0, 0], Gs[0, 1], G[0, 2]], [Gs[0, 1], Gs[1, 1], G[1, 2]], [G[0, 2], G[1, 2], G[2, 2]]])
        try:
            o['kap'] = np.linalg.solve(M3, y)[2] if np.linalg.eigvalsh(M3).min() > 1e-12 else np.nan
        except Exception:
            o['kap'] = np.nan
    else:
        o.update(a=np.nan, b=np.nan, lag=np.nan, Psi=np.nan, kap=np.nan)
    return o

def estimate(g1, g2, gpost, zpre, zpost, k_prim=None):
    r_d, eps = warp_fit(zpre, zpost, EGRID, 'dil'); r_s, dlt = warp_fit(zpre, zpost, DGRID, 'shift')
    k_x = eps/(1+eps); Lam_x = math.log(r_s/r_d) if r_d > 0 and np.isfinite(r_s) else np.nan
    R2 = 1 - r_d/max(np.mean(np.sum((zpost - zpost.mean(0))**2, 1)), 1e-12)
    tfine = np.arange(T_LO, T_HI+1e-9, 0.001)
    u_pk = tfine[int(np.argmax(np.linalg.norm(lagrange4(zpre, tfine), axis=1)))]
    out = dict(k_x=k_x, dlt_x=dlt, Lam_x=Lam_x, R2=R2, u_pk=u_pk)
    gsm, _ = smooth(0.5*(g1 + g2))
    lam = np.linalg.eigvalsh(sym(gsm)).min(-1)
    if (lam <= 0).any(): out.update(stop='npd'); return out
    P = isqrtm(gsm); wv, Vv = np.linalg.eigh(sym(gsm))
    WT = 1.0/(1.0/wv[:, :, None] + 1.0/wv[:, None, :])
    _, dg2 = smooth(g2); _, dgn = smooth(0.5*(g1 - g2))
    S0 = tf(np.einsum('kij,kjl,klm->kim', P, dg2, P)); Sn0 = tf(np.einsum('kij,kjl,klm->kim', P, dgn, P))
    Y = 0.5*(logm(np.einsum('kij,kjl,klm->kim', P, gpost, P)) - logm(np.einsum('kij,kjl,klm->kim', P, g1, P)))
    Y0 = tf(Y); trY = np.trace(Y, axis1=-2, axis2=-1)
    dlogV = 0.5*np.trace(np.einsum('kij,kjl,klm->kim', P, dg2, P), axis1=-2, axis2=-1)
    zdot = SGD @ zpre
    npk = P[int(np.argmin(np.abs(U-u_pk)))] @ lagrange4(zpre, [u_pk])[0]; npk = npk/max(np.linalg.norm(npk), 1e-12)
    keep = [k for k in KFIT if lam[k] >= LAM_FLOOR and math.sqrt(np.sum(S0[k]*S0[k])) >= S_FLOOR]
    out['nadm'] = len(keep)
    if len(keep) < MIN_BINS or np.var(U[keep]) < VARU_FLOOR: out.update(stop='degenerate'); return out
    if abs(k_x) < 1e-9: out.update(stop='kx0'); return out
    A = np.stack([-0.5*k_x*u_pk*S0[k] for k in keep]); Bm = np.stack([-0.5*k_x*U[k]*S0[k] for k in keep])
    An = np.stack([-0.5*k_x*u_pk*Sn0[k] for k in keep]); Bn = np.stack([-0.5*k_x*U[k]*Sn0[k] for k in keep])
    Ok = []
    for k in keep:
        yv = P[k] @ zdot[k]; yv = yv/max(np.linalg.norm(yv), 1e-12)
        O = tf(sym(np.outer(yv, npk)[None])[0]); Ok.append(O/max(math.sqrt(np.sum(O*O)), 1e-12))
    Ok = np.stack(Ok); Yk = np.stack([Y0[k] for k in keep])
    WK = np.stack([np.einsum('ji,jl,lm->im', Vv[k], np.ones((3, 3)), Vv[k])*0 + WT[k] for k in keep])
    rot = lambda X: np.stack([np.einsum('ji,jl,lm->im', Vv[k], X[i], Vv[k]) for i, k in enumerate(keep)])
    A = rot(A); Bm = rot(Bm); An = rot(An); Bn = rot(Bn); Ok = rot(Ok); Yk = rot(Yk)
    ip = lambda X, Z: float(np.sum(WK*X*Z))
    G = np.array([[ip(A, A), ip(A, Bm), ip(A, Ok)], [ip(A, Bm), ip(Bm, Bm), ip(Bm, Ok)], [ip(A, Ok), ip(Bm, Ok), ip(Ok, Ok)]])
    Gn = np.zeros((3, 3)); Gn[0, 0] = ip(An, An); Gn[0, 1] = Gn[1, 0] = ip(An, Bn); Gn[1, 1] = ip(Bn, Bn)
    yv = np.array([ip(Yk, A), ip(Yk, Bm), ip(Yk, Ok)])
    w = np.array([float(np.sum(WT[k]*S0[k]*S0[k])) for k in keep])
    ub = float(np.sum(w*U[keep])/np.sum(w))
    out.update(stop=False, G=G, Gn=Gn, yv=yv, ub=ub, trY=trY[keep], dlogV=dlogV[keep], u_keep=U[keep])
    out.update(endpoints(G, Gn, yv, u_pk, ub))
    if k_prim is not None:
        sc = k_prim/k_x
        out.update({'plac_'+k2: v2 for k2, v2 in endpoints(G*sc*sc, Gn*sc*sc, yv*sc, u_pk, ub).items()})
    return out

def pool_rows(rows):
    G = sum(r['G'] for r in rows); Gn = sum(r['Gn'] for r in rows); y = sum(r['yv'] for r in rows)
    return endpoints(G, Gn, y, float(np.mean([r['u_pk'] for r in rows])), float(np.mean([r['ub'] for r in rows])))

def world(kind, par, gamma=0.15, alpha=1.3, kap_true=0.30):
    gpre = g_true(U); zpre = zbar_true(U)
    if kind == 'D': gpost = math.exp(2*gamma)*g_true(U/(1+par)); zpost = alpha*zbar_true(U/(1+par))
    elif kind == 'S': gpost = g_true(U - par); zpost = zbar_true(U - par)
    elif kind == 'R': gpost = math.exp(2*gamma)*gpre; zpost = alpha*zbar_true(U/(1+par))
    elif kind == 'G': gpost = math.exp(2*gamma)*gpre; zpost = alpha*zpre
    elif kind == 'F':
        gpost = math.exp(2*gamma)*g_true(U/(1+par)); zpost = alpha*zbar_true(U/(1+par))
        P = isqrtm(gpre); Pi = sqrtm(gpre); E = 0.5*logm(np.einsum('kij,kjl,klm->kim', P, gpost, P))
        zd = SGD @ zpre; npk = P[6] @ zpre[6]; npk = npk/np.linalg.norm(npk)
        for k in range(15):
            yv = P[k] @ zd[k]; yv = yv/max(np.linalg.norm(yv), 1e-12)
            O = tf(sym(np.outer(yv, npk)[None])[0]); O = O/math.sqrt(np.sum(O*O)); E[k] = E[k] + kap_true*O
        gpost = np.einsum('kij,kjl,klm->kim', Pi, expm(2*E), Pi)
    else: gpost = gpre.copy(); zpost = zpre.copy()
    return gpre, gpost, zpre, zpost

def run(kind, par, N, nmice, rng):
    out = []
    for _ in range(nmice):
        gpre, gpost, zpre, zpost = world(kind, par)
        g1 = noisy_g(gpre, N/2, rng); g2 = noisy_g(gpre, N/2, rng); gp = noisy_g(gpost, N, rng)
        z1 = zpre + rng.normal(size=zpre.shape)/math.sqrt(N); z2 = zpost + rng.normal(size=zpost.shape)/math.sqrt(N)
        out.append(estimate(g1, g2, gp, z1, z2, k_prim=(0.10/1.10 if kind == 'P' else None)))
    return out

def q(x, p): return float(np.nanpercentile(x, p))

if __name__ == '__main__':
    rng = np.random.default_rng(SEED); t0 = time.time()
    print("== 0. noise-free (SG smoothing + first-order truncation bias only) ==")
    for kind, par in [('D', 0.05), ('D', 0.10), ('D', 0.20), ('S', 0.05), ('S', 0.10), ('S', 0.20),
                      ('R', 0.10), ('G', 0.0), ('F', 0.10), ('P', 0.0)]:
        gpre, gpost, zpre, zpost = world(kind, par)
        r = estimate(gpre, gpre, gpost, zpre, zpost)
        s = f"  {kind} {par:.2f}: k_x={r['k_x']:+.4f} Lam_x={r['Lam_x']:+.2f} u_pk={r['u_pk']:.3f} nadm={r.get('nadm')}"
        if r.get('stop') is False:
            s += (f" b1={r['b1']:+.4f} Psi={r['Psi']:+.4f} lag={r['lag']:+.3f} a={r['a']:+.3f} b={r['b']:+.3f}"
                  f" kap={r['kap']:+.4f} Psi2={r['Psi2']:+.4f} rho={r['rho']:.4f} D0={r['D0']:.4f}")
        else: s += f" STOP({r.get('stop')})"
        print(s)
    NM = int(sys.argv[1]) if len(sys.argv) > 1 else 300
    NS = [int(x) for x in (sys.argv[2].split(',') if len(sys.argv) > 2 else ['120', '300'])]
    WORLDS = [('D', 0.10), ('D', 0.05), ('D', 0.20), ('S', 0.10), ('R', 0.10), ('G', 0.0), ('F', 0.10), ('P', 0.0)]
    NG = 800
    print("")
    print(f"== 1. noisy: 8-mouse POOLED endpoints; {NM} mice/world, {NG} groups, mouse-level bootstrap ==")
    for N in NS:
        print(f"  -- N = {N} trials/phase (pre halves N/2) --")
        for kind, par in WORLDS:
            rows = run(kind, par, N, NM, rng)
            ok = [r for r in rows if r.get('stop') is False]
            gated = ok if kind == 'P' else [r for r in ok if KX_LO <= abs(r['k_x']) <= KX_HI and r['R2'] >= R2_FLOOR]
            gf = len(gated)/len(rows)
            if len(gated) < 8:
                print(f"    {kind} {par:.2f}: gate={gf:.3f} -> STOP"); continue
            PS = []; PZ = []; B1 = []; KP = []; ciP = []; ciB = []
            for _ in range(NG):
                grp = [gated[i] for i in rng.integers(0, len(gated), 8)]
                e = pool_rows(grp); PS.append(e['Psi']); PZ.append(e['Psi2']); B1.append(e['b1']); KP.append(e['kap'])
                bp = []; bb = []
                for _ in range(100):
                    rs = [grp[i] for i in rng.integers(0, 8, 8)]
                    e2 = pool_rows(rs); bp.append(e2['Psi2']); bb.append(e2['b1'])
                ciP.append(np.nanpercentile(bp, 97.5) - np.nanpercentile(bp, 2.5))
                ciB.append(np.nanpercentile(bb, 97.5) - np.nanpercentile(bb, 2.5))
            PS = np.array(PS, float); PZ = np.array(PZ, float); B1 = np.array(B1, float); KP = np.array(KP, float)
            ciP = np.array(ciP, float); ciB = np.array(ciB, float)
            print(f"    {kind} {par:.2f}: gate={gf:.3f} nan(Psi)={np.mean(~np.isfinite(PS)):.3f} | Psi={q(PS,50):+.3f}"
                  f" [{q(PS,2.5):+.3f},{q(PS,97.5):+.3f}] | Psi2={q(PZ,50):+.3f} [{q(PZ,2.5):+.3f},{q(PZ,97.5):+.3f}]"
                  f" P(Psi2>0)={np.mean(PZ>0):.3f} P(Psi2>0.5)={np.mean(PZ>0.5):.3f} P(Psi2<-0.5)={np.mean(PZ<-0.5):.3f}")
            print(f"        b1={q(B1,50):+.3f} [{q(B1,2.5):+.3f},{q(B1,97.5):+.3f}] P(b1>0)={np.mean(B1>0):.3f}"
                  f" P(b1 in[0.5,1.5])={np.mean((B1>=0.5)&(B1<=1.5)):.3f} | kap={q(KP,50):+.3f} [{q(KP,2.5):+.3f},{q(KP,97.5):+.3f}]"
                  f" P(|kap|<=0.10)={np.mean(np.abs(KP)<=0.10):.3f}")
            print(f"        CI width: Psi2 med={np.nanmedian(ciP):.2f} 90%={q(ciP,90):.2f}; b1 med={np.nanmedian(ciB):.2f} 90%={q(ciB,90):.2f}"
                  f" | Lam_x med={np.median([r['Lam_x'] for r in gated]):+.3f} P(L>0)={np.mean([r['Lam_x'] > 0 for r in gated]):.3f}"
                  f" | per-mouse b1 sd={np.nanstd([r['b1'] for r in gated]):.2f}")
            if kind == 'P':
                pb = np.array([r.get('plac_b1', np.nan) for r in gated], float)
                mb = [np.nanmedian(pb[rng.integers(0, len(pb), 8)]) for _ in range(2000)]
                print(f"        PLACEBO(primary k_x reused): per-mouse b1 sd={np.nanstd(pb):.3f} |med8 b1| 95/99%={q(np.abs(mb),95):.3f}/{q(np.abs(mb),99):.3f}")
    print("")
    print(f"  elapsed {time.time()-t0:.1f}s (seed {SEED})")
