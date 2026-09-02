# -*- coding: utf-8 -*-
"""A6: at the real trial count the raw lambda_min >= 0.02 gate is passed BY THE NOISE. Seed 20260902."""
import sys, os, math, numpy as np
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import calib_synthetic as C
rng = np.random.default_rng(C.SEED)
U = C.U; gpre = C.g_true(U)
true_lam = np.linalg.eigvalsh(C.sym(C.smooth(gpre)[0])).min()
print(f"   noise-free lambda_min(g_sm) = {true_lam:.4f};  card floor = 0.02")
print("   n_half = N/2 trials per pre half;  E[E^T E] = d/n * I = 3/n * I is an additive noise floor")
print("   N     n_half   E[bias]=3/n   median lambda_min   frac passing 0.02   frac passing 0.02 when g_true := 0")
for N in [60, 120, 300, 1000, 4000]:
    n = N/2
    lams = []; lams0 = []
    for _ in range(200):
        g1 = C.noisy_g(gpre, n, rng); g2 = C.noisy_g(gpre, n, rng)
        lams.append(np.linalg.eigvalsh(C.sym(C.smooth(0.5*(g1+g2))[0])).min())
        z1 = C.noisy_g(np.zeros_like(gpre), n, rng); z2 = C.noisy_g(np.zeros_like(gpre), n, rng)
        lams0.append(np.linalg.eigvalsh(C.sym(C.smooth(0.5*(z1+z2))[0])).min())
    lams = np.array(lams); lams0 = np.array(lams0)
    print(f"  {N:5d}  {n:6.0f}   {3/n:10.4f}   {np.median(lams):15.4f}   {np.mean(lams>=0.02):17.3f}"
          f"   {np.mean(lams0>=0.02):.3f}")
print("   -> the last column is a metric that is IDENTICALLY ZERO; at every real N it still clears the")
print("      0.02 floor, i.e. the 'raw rank' gate certifies nothing at the trial counts of the named data.")
