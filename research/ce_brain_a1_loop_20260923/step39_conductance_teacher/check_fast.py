"""Equivalence of the compiled kernel (us_fast) with the numpy port (us_network), which equals fly_rec.network.
Also: does the exact soma step change the authors' learned network (dark bump, dark gain)? (pre-freeze check)"""
import time

import numpy as np

import us_fast as uf
import us_network as us

np.random.seed(3)
theta0, v, t = us.util.gen_theta0_OU(3.0, sigma=225)
w0 = us.learned()
for label, T, soma in (("current/euler", us.Teacher("current"), "euler"),
                       ("conductance g0=0.5/euler", us.Teacher("conductance", sigma=0.53, g0=0.5, EE=1.16), "euler"),
                       ("conductance g0=6/exp", us.Teacher("conductance", sigma=0.53, g0=6.0, EE=1.16), "exp")):
    us.SOMA["mode"] = soma
    t0 = time.time()
    wn, sn, en = us.train(w0, theta0, T)
    tn = time.time() - t0
    t0 = time.time()
    wf, sf, ef = uf.train_fast(w0, theta0, T, us.P, us.DIR, us.W_ROT, us.SIGN, soma=soma)
    tf = time.time() - t0
    print("%-26s max|w_numba - w_numpy| %.2e  max|err_hist diff| %.2e  weight change %.3f  time numpy %.1fs numba %.1fs (incl. compile)"
          % (label, np.max(np.abs(wf - wn)), np.max(np.abs(ef - en)), np.max(np.abs(wn - w0)), tn, tf), flush=True)
t0 = time.time()
uf.train_fast(w0, theta0, us.Teacher("current"), us.P, us.DIR, us.W_ROT, us.SIGN, soma="euler")
print("numba steady speed: %.1f us/step" % ((time.time() - t0) / (theta0.size - 1) * 1e6))

# exact soma step on the authors' learned network: dark bump and dark gain (no learning)
for soma in ("euler", "exp"):
    us.SOMA["mode"] = soma
    T = us.Teacher("current")
    f, _ = us.run(w0, [(2.0, T.light(0.0), 0.0), (3.0, us.DARK, 0.0)])
    gains = []
    for om in (90.0, 180.0, 360.0):
        every = int(0.05 / us.P["dt"])
        fr, tr = us.run(w0, [(2.0, T.light(0.0), 0.0), (6.0, us.DARK, om)], every)
        ph = np.degrees(np.unwrap(np.radians(tr[int(2.0 / 0.05):])))
        tt = np.arange(ph.size) * 0.05
        msk = tt >= 1.0
        gains.append(round(float(np.polyfit(tt[msk], ph[msk], 1)[0] / om), 3))
    print("soma", soma, "dark bump fwhm", us.shape(f)[0], "peak/fmax %.3f" % (f.max() / us.P["fmax"]), "dark gains 90/180/360", gains)
