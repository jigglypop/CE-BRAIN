import numpy as np, time
import calib_power as C
t0=time.time()
wp = C.prepare_world("true", C.SEED)
print("prep s", round(time.time()-t0,1))
e = wp[0]
a = np.maximum(e["lam"][("early","A")][:, 3:24].mean(1) - e["lam"][("early","A")][:, :2].mean(1), 0)
a/=np.linalg.norm(a)
mu_e,s2_e = C.exact_moments(e["lam"][("early","A")], e["dlam"][("early","A")], a)
mu_l,s2_l = C.exact_moments(e["lam"][("late","A")],  e["dlam"][("late","A")],  a)
print("mu_e", np.round(mu_e[::4],3))
print("cv_e", np.round(np.sqrt(s2_e)/mu_e,3)[::4])
print("logalpha", np.round(np.log(mu_l)-np.log(mu_e),3)[::4])
de=C.bin_quantities(mu_e,s2_e)
print("m", np.round(de["m"],2)[::4]); print("p", np.round(de["p"],2)[::4]); print("rho", np.round(de["rho"],3)[::4])
K=int(round(C.T_END/C.BIN))
keep=C.select_bins(mu_e,s2_e,mu_l,K); print("keep", keep.sum(), "of", K)
print("TRUTH", C.truth_lambda(wp))
