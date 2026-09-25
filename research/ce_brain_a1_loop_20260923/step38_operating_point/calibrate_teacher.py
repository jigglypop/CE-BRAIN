"""Operating-point calibration (pre-freeze, scratch): continue the authors' rule from their learned network with a
teacher of width sigma and magnitude M; report only the dark bump shape (FWHM, peak/fmax). Target: literature bump
(FWHM 80-100 deg, unsaturated). No selection / rotation test is computed here."""
import importlib.util, sys, time
import numpy as np
spec = importlib.util.spec_from_file_location("cl", r"C:/dev/ce/ce-agi-runtime/research/ce_brain_a1_loop_20260923/step38_connectome_init_learning/connectome_learning.py")
cl = importlib.util.module_from_spec(spec); spec.loader.exec_module(cl)
import utilities as util

M, sigma, T, out = float(sys.argv[1]), float(sys.argv[2]), float(sys.argv[3]), sys.argv[4]
cl.P["M"], cl.P["sigma"] = M, sigma
n = 60
perm = np.r_[np.arange(0, n, 2), np.arange(1, n, 2)]
net = cl.Net(np.repeat(np.arange(30) * 12.0, 2), np.diag(np.full(n, 2 / cl.P["fmax"]))[:, np.argsort(perm)], np.r_[np.ones(30), -np.ones(30)])
w0 = cl.s37.learned()
np.random.seed(11)
theta0, v, t = util.gen_theta0_OU(T, sigma=225)
t0 = time.time()
w, snaps, err = cl.train(net, w0, theta0)
np.savez(out, w=w, snaps=snaps, err_hz=err, M=M, sigma=sigma)


def dark_shape(wm):
    f, _ = cl.run(net, wm, [(2.0, cl.light(net, 0.0), 0.0), (3.0, (0.0, 0.0), 0.0)])
    fl, _ = cl.run(net, wm, [(2.0, cl.light(net, 0.0), 0.0)])
    s, sl = cl.shape(net, f), cl.shape(net, fl)
    return {"dark_fwhm": s[0], "dark_peak_over_fmax": float(f.max() / cl.P["fmax"]), "dark_n_above_0p9": int(np.sum(f >= 0.9 * cl.P["fmax"])),
            "light_fwhm": sl[0], "light_peak_over_fmax": float(fl.max() / cl.P["fmax"])}


print("M", M, "sigma", sigma, "T", T, "time %.0f s" % (time.time() - t0), "err first/last %.2f/%.2f Hz" % (err[0], err[-5:].mean()),
      "| start", dark_shape(w0), "| end", dark_shape(w), flush=True)
