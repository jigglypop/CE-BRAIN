# -*- coding: utf-8 -*-
"""Q-NPF-02 / F-01: 사전등록 판정규칙의 검출률·오기각률 (합성). 실제 자료 없음. 씨앗 20260902.

규칙 (카드 kill과 동일):
  GATE  : |k_x| in [0.05,0.30] and R2_dil >= 0.50 in >= 7/8 mice; per-mouse nadm >= 7, Var(u_adm) >= 0.04 s^2,
          lambda_min >= 0.02; POWER: pooled b1의 마리수준 부트스트랩 95% CI 폭 <= 1.5 (아니면 STOP).
  K1 진폭: pooled b1의 95% CI가 1.00을 포함하지 않으면 기각        (예측 b1 = 1.00)
  K2 리만: |pooled kappa| > 0.15 또는 95% CI가 0을 배제하면 기각    (예측 kappa = 0.00)
  K3 운동학: median Lambda_x <= -0.10 이면 기각                     (예측 median Lambda_x >= +0.10)
  K4 placebo: 같은 phase 분할·primary k_x 재사용에서 pooled b1의 95% CI가 0을 배제하면 기각.
"""
import numpy as np, math, sys, time
import calib_synthetic as C

rng = np.random.default_rng(C.SEED)
NB = 400          # mouse-level bootstrap resamples
NG = 300          # 8-mouse cohorts per world


def cohort_stats(gated, plac=False):
    grp = [gated[i] for i in rng.integers(0, len(gated), 8)]
    e = C.pool_rows(grp)
    b1 = []; kp = []
    for _ in range(NB):
        rs = [grp[i] for i in rng.integers(0, 8, 8)]
        e2 = C.pool_rows(rs); b1.append(e2['b1']); kp.append(e2['kap'])
    b1 = np.array(b1, float); kp = np.array(kp, float)
    lo, hi = np.nanpercentile(b1, [2.5, 97.5]); klo, khi = np.nanpercentile(kp, [2.5, 97.5])
    lam = np.median([r['Lam_x'] for r in grp])
    out = dict(b1=e['b1'], kap=e['kap'], lo=lo, hi=hi, w=hi-lo, klo=klo, khi=khi, lam=lam)
    if plac:
        pg = [dict(G=r['G']*(r['sc']**2), Gn=r['Gn']*(r['sc']**2), yv=r['yv']*r['sc'],
                   u_pk=r['u_pk'], ub=r['ub']) for r in grp]
        pb = []
        for _ in range(NB):
            rs = [pg[i] for i in rng.integers(0, 8, 8)]
            pb.append(C.pool_rows(rs)['b1'])
        pb = np.array(pb, float); plo, phi = np.nanpercentile(pb, [2.5, 97.5])
        out.update(pb=C.pool_rows(pg)['b1'], plo=plo, phi=phi)
    return out


def verdict(s):
    if not np.isfinite(s['w']) or s['w'] > 1.5: return 'STOP_power'
    if not (s['lo'] <= 1.0 <= s['hi']): return 'K1_refute'
    if abs(s['kap']) > 0.15 or not (s['klo'] <= 0.0 <= s['khi']): return 'K2_refute'
    if s['lam'] <= -0.10: return 'K3_refute'
    return 'support'


if __name__ == '__main__':
    NM = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    NS = [int(x) for x in (sys.argv[2].split(',') if len(sys.argv) > 2 else ['300', '1000'])]
    t0 = time.time()
    print("world  N     gate   verdicts over %d cohorts (8 mice each), bootstrap %d" % (NG, NB))
    for N in NS:
        for kind, par in [('D', 0.10), ('D', 0.20), ('S', 0.10), ('R', 0.10), ('F', 0.10), ('P', 0.0)]:
            rows = C.run(kind, par, N, NM, rng)
            ok = [r for r in rows if r.get('stop') is False]
            gated = ok if kind == 'P' else [r for r in ok if C.KX_LO <= abs(r['k_x']) <= C.KX_HI and r['R2'] >= C.R2_FLOOR]
            gf = len(gated)/len(rows)
            if kind == 'P':
                for r in gated: r['sc'] = (0.10/1.10)/r['k_x'] if abs(r['k_x']) > 1e-9 else np.nan
                gated = [r for r in gated if np.isfinite(r['sc'])]
            if len(gated) < 8:
                print(f"  {kind} {par:.2f} {N:5d}  {gf:.2f}   GATE BLOCKS (n={len(gated)})"); continue
            V = {}; W = []; LAM = []; KAP = []; B1 = []; PB = []
            for _ in range(NG):
                s = cohort_stats(gated, plac=(kind == 'P'))
                v = verdict(s); V[v] = V.get(v, 0) + 1
                W.append(s['w']); LAM.append(s['lam']); KAP.append(s['kap']); B1.append(s['b1'])
                if kind == 'P': PB.append((s['plo'] > 0) or (s['phi'] < 0))
            tot = sum(V.values())
            frac = {k: v/tot for k, v in sorted(V.items(), key=lambda kv: -kv[1])}
            print(f"  {kind} {par:.2f} {N:5d}  {gf:.2f}   " + "  ".join(f"{k}={v:.3f}" for k, v in frac.items())
                  + f" | b1 med={np.nanmedian(B1):+.2f} CIw med={np.nanmedian(W):.2f}"
                  + f" kap med={np.nanmedian(KAP):+.3f} Lam med={np.nanmedian(LAM):+.3f}"
                  + (f" | K4 placebo-CI-excludes-0 rate={np.mean(PB):.3f}" if kind == 'P' else ""))
    print(f"  elapsed {time.time()-t0:.1f}s (seed {C.SEED})")
