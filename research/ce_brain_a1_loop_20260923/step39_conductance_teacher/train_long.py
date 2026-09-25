"""Long training from the authors' random initialisation with the compiled kernel (pre-freeze screen, no contract).
The OU heading trajectory (authors' generator: sigma 225 deg/s, tau 0.5 s, start 180 deg) is produced in 100 chunks
so that 8e4 s fits in memory. Screen measures only: learning error, dark bump shape, persistence, integration gain.
Selection tests (narrow-input jump, suppression) are not computed here.

python train_long.py <label> <current|conductance> <soma euler|exp> <g0> <EE> <sigma> <M> <T_s> <seed> <out_prefix>
"""
import json
import sys
import time

import numba
import numpy as np

import us_fast as uf
import us_network as us


@numba.njit(cache=True)
def ou_chunk(theta_last, v_last, noise, dt, sigma, tau):
    """Authors' gen_theta0_OU continued: v[i+1] = (1 - dt/tau) v[i] + sigma sqrt(2/tau) sqrt(dt) n[i]; theta -= v dt."""
    K = noise.size
    th = np.empty(K + 1)
    th[0] = theta_last
    alpha = dt / tau
    sb = sigma * np.sqrt(2.0 / tau) * np.sqrt(dt)
    v = v_last
    for k in range(K):
        v = (1.0 - alpha) * v + sb * noise[k]
        th[k + 1] = th[k] - v * dt
    return th, v


def authors_init_state(n, m, theta0_first):
    st = {"f": np.zeros(n), "f_rot": np.zeros(m), "u": np.zeros(n), "Iden": np.zeros(n), "V": np.zeros(n),
          "Delta": np.zeros((n, n + m)), "PSP": np.zeros(n + m), "I_PSP": np.zeros(n + m), "x": np.zeros(n)}
    bump, peak = n // 12, n - int(theta0_first / (360 / n))
    start, end = (peak - bump) % n, peak + bump % n
    idx = np.r_[start:n, 0:end] if start > peak else np.arange(start, end)
    idx = idx[idx < n]
    st["u"][idx] = 100; st["V"][idx] = 100; st["f"][idx] = .15; st["f_rot"][idx] = .15
    return st


def screen(w, T):
    f, _ = us.run(w, [(2.0, T.light(0.0), 0.0), (3.0, us.DARK, 0.0)])
    f10, _ = us.run(w, [(2.0, T.light(100.0), 0.0), (10.0, us.DARK, 0.0)])
    s, s10 = us.shape(f), us.shape(f10)
    out = {"dark3_fwhm": s[0], "dark3_peaks": s[1], "dark3_peak_over_fmax": float(f.max() / us.P["fmax"]),
           "dark3_n_ge_0p9": int(np.sum(f >= 0.9 * us.P["fmax"])), "dark10_amp_hz": 1e3 * s10[3], "dark10_peaks": s10[1],
           "dark10_err_deg": float((us.com(f10) - 100.0 + 180) % 360 - 180)}
    every = int(0.05 / us.P["dt"])
    for om in (90.0, 360.0):
        fr, tr = us.run(w, [(2.0, T.light(0.0), 0.0), (12.0, us.DARK, om)], every)
        ph = np.degrees(np.unwrap(np.radians(tr[int(2.0 / 0.05):])))
        tt = np.arange(ph.size) * 0.05
        m = tt >= 2.0
        coef = np.polyfit(tt[m], ph[m], 1)
        r2 = 1 - np.sum((ph[m] - np.polyval(coef, tt[m])) ** 2) / max(np.sum((ph[m] - ph[m].mean()) ** 2), 1e-12)
        out[f"gain{int(om)}"] = float(coef[0] / om)
        out[f"r2_{int(om)}"] = float(r2)
    return out


def main():
    label, kind, soma = sys.argv[1], sys.argv[2], sys.argv[3]
    g0, EE, sig, M, T_s, seed, prefix = float(sys.argv[4]), float(sys.argv[5]), float(sys.argv[6]), float(sys.argv[7]), float(sys.argv[8]), int(sys.argv[9]), sys.argv[10]
    us.SOMA["mode"] = soma
    T = us.Teacher(kind, M=M, sigma=sig, g0=g0, EE=EE, EI=-1.0)
    rng = np.random.default_rng(seed)
    n, m = us.N, us.N
    w = rng.normal(0, np.sqrt(1 / (n + m)), (n, n + m))          # authors' initialisation N(0, 1/N)
    dt = us.P["dt"]
    steps = int(round(T_s / dt))
    chunks = 100
    K = steps // chunks
    th_last, v_last = 180.0, 0.0
    st = authors_init_state(n, m, th_last)
    snaps, errs, t0 = [], [], time.time()
    for c in range(chunks):
        th, v_last = ou_chunk(th_last, v_last, rng.standard_normal(K), dt, 225.0, 0.5)
        th_last = th[-1]
        w, sn, er = uf.train_fast(w, th, T, us.P, us.DIR, us.W_ROT, us.SIGN, soma=soma, n_snap=1, state=st)
        snaps.append(w.copy())
        errs.append(float(er[0]))
    np.savez(prefix + ".npz", w=w, snaps=np.array(snaps), err_hz=np.array(errs), label=label, kind=kind, soma=soma, g0=g0, EE=EE,
             sigma=sig, M=M, T_s=T_s, seed=seed)
    res = {"label": label, "kind": kind, "soma": soma, "g0": g0, "EE": EE, "sigma": sig, "M": M, "T_s": T_s, "seed": seed,
           "train_time_s": round(time.time() - t0), "err_hz_at_percent": {str(p): round(errs[p - 1], 3) for p in (1, 5, 10, 25, 50, 75, 100)},
           "screen_end": screen(w, T), "screen_mid": screen(snaps[49], T)}
    print(json.dumps(res), flush=True)


if __name__ == "__main__":
    main()
