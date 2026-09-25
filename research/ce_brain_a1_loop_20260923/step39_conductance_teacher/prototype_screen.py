"""Pre-freeze viability screen (no contract): continue the authors' learned network under the Urbanczik-Senn
conductance teacher; report only bump shape, persistence in darkness and integration at 90 deg/s.
Selection tests (narrow-input jump, suppression) are NOT computed here.

python prototype_screen.py <g0> <EE> <sigma_t> <T_s> <seed> <out.npz>
"""
import json
import sys
import time

import numpy as np

import us_network as us

g0, EE, st_, T, seed, out = float(sys.argv[1]), float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4]), int(sys.argv[5]), sys.argv[6]
teacher = us.Teacher("conductance", sigma=st_, g0=g0, EE=EE, EI=-1.0)
np.random.seed(seed)
theta0, v, t = us.util.gen_theta0_OU(T, sigma=225)
t0 = time.time()
w, snaps, err = us.train(us.learned(), theta0, teacher)
np.savez(out, w=w, snaps=snaps, err_hz=err, g0=g0, EE=EE, sigma_t=st_, T=T, seed=seed)


def screen(wm):
    f, _ = us.run(wm, [(2.0, teacher.light(0.0), 0.0), (3.0, us.DARK, 0.0)])
    f10, _ = us.run(wm, [(2.0, teacher.light(100.0), 0.0), (10.0, us.DARK, 0.0)])
    s, s10 = us.shape(f), us.shape(f10)
    every = int(0.05 / us.P["dt"])
    fr, tr = us.run(wm, [(2.0, teacher.light(0.0), 0.0), (12.0, us.DARK, 90.0)], every)
    ph = np.degrees(np.unwrap(np.radians(tr[int(2.0 / 0.05):])))
    tt = np.arange(ph.size) * 0.05
    m = tt >= 2.0
    coef = np.polyfit(tt[m], ph[m], 1)
    r2 = 1 - np.sum((ph[m] - np.polyval(coef, tt[m])) ** 2) / max(np.sum((ph[m] - ph[m].mean()) ** 2), 1e-12)
    return {"dark3_fwhm": s[0], "dark3_peaks": s[1], "dark3_peak_over_fmax": float(f.max() / us.P["fmax"]), "dark3_n_ge_0p9": int(np.sum(f >= 0.9 * us.P["fmax"])),
            "dark10_amp_hz": 1e3 * s10[3], "dark10_peaks": s10[1], "dark10_err_deg": float((us.com(f10) - 100.0 + 180) % 360 - 180),
            "gain90": float(coef[0] / 90.0), "r2_90": float(r2), "bump_after_rot_hz": 1e3 * us.shape(fr)[3]}


print(json.dumps({"g0": g0, "EE": EE, "sigma_t": st_, "T": T, "time_s": round(time.time() - t0), "err_first_last_hz": [round(float(err[0]), 3), round(float(err[-5:].mean()), 3)],
                  "start": screen(us.learned()), "end": screen(w)}), flush=True)
