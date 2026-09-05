# C15.  P3 channel identification certificate for candidate C2 (pairwise lag
# decomposition, no coordinates) of verify/Q-NPF-04/spec.md, on the LONG-AXIS loop
# forward model of fwd_loop.py.
#
# C1 failed C-B because gain and efficacy are EXACTLY degenerate in the single-limb
# ring: S_gain(w)/S_eff(w) is a frequency-independent constant (ratio spread 1e-15
# over every loop length and node).  C2 is tested here because it uses a DIFFERENT
# observable -- the cross-spectral phase between two cells straddling the long limb --
# which carries the transport time itself rather than a closed-loop power spectrum.
#
# To test C2 at all, observable cells must sit on BOTH sides of the long limb, so this
# script uses a PRE (upstream) and POST (downstream) readout per loop:
#     pre  cell:  x(t)
#     post cell:  x(t - tau_q)  filtered by one local membrane stage
# The antisymmetric lag matrix L = (delta - delta^T)/2 then measures tau directly.
#
# Statistic vector (declared before running):
#   U1 = mean over loops of the measured pre->post lag        (delay channel)
#   U2 = mean over loops of normalised coupling |S_xy|/sqrt(SxxSyy) (efficacy channel)
#   U3 = mean over cells of log broadband power               (gain channel)
# Same pre-registered criteria: C-A max|z| >= 2 per channel, C-B pairwise angle >= 15 deg.
#
# NO DATA PAYLOAD IS OPENED ANYWHERE IN THIS FILE.

import sys, os, json, time, itertools
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fwd_loop as F
import c14_loop_cert as C14

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "result_c15_c2_lag_cert.json")

SEED = 20260902
N_REP = 200
N_FRAME = C14.N_FRAME
WELCH_SEG = C14.WELCH_SEG
COH_BAND = (0.30, 3.00)     # Hz, band over which the phase slope is fitted
MIN_COH = 0.20              # minimum magnitude-squared coherence to admit a pair
BB_BAND = C14.BB_BAND
EPS = 1e-300

WORLDS = C14.WORLDS
WORLD_ORDER = C14.WORLD_ORDER
STAT_NAMES = ("U1_lag", "U2_coupling", "U3_baseline_power")


def make_animal_pairs(n_cell, rng):
    """Same loops as fwd_loop.make_animal, but each cell is tagged pre or post."""
    a = F.make_animal(n_cell, rng)
    a["side"] = rng.integers(0, 2, size=n_cell)      # 0 = pre, 1 = post
    return a


def simulate_pair_traces(animal, th, rng, n_frame):
    """Latent loop signal per loop; pre cells see x, post cells see x delayed by tau_q
    and passed through one membrane stage.  Returns y[cell, frame]."""
    n = animal["n"]
    nf = F._W_RAD.size
    w = F._W_RAD
    y = np.empty((n, n_frame))
    step = int(round(F.FRAME_DT / F.SIM_DT))
    idx = (np.arange(n_frame) * step) % F.NFFT_LOOP
    t = np.arange(F.NFFT_LOOP) * F.SIM_DT
    kern = np.maximum(np.exp(-t / F.CA_DECAY) - np.exp(-t / F.CA_RISE), 0.0)
    kern = kern / kern.sum()
    Khat = np.fft.rfft(kern)
    gs = np.exp(th[0])
    for q in range(F.N_LOOP):
        cells = np.where(animal["loop_of"] == q)[0]
        if cells.size == 0:
            continue
        L = animal["L"][q]
        k = animal["k"][q]
        H1, _ = F.loop_transfer(L, k, th)
        tau = (L / F.V_AXON_LOOP) * np.exp(th[2]) + F.TAU_SYN_LOOP
        # one shared latent realisation per loop
        amp = np.sqrt(np.maximum(np.abs(H1) ** 2, 0.0) * F.NFFT_LOOP) * F.CELL_NOISE_SD
        ph = rng.random(nf) * 2 * np.pi
        Xw = amp * np.exp(1j * ph)
        Xw[0] = 0.0
        post_op = np.exp(-1j * w * tau) / (1.0 + 1j * w * F.TAU_M_LOOP)
        for i in cells:
            gi = animal["g"][i] * gs
            Zw = Xw * (post_op if animal["side"][i] == 1 else 1.0)
            x = np.fft.irfft(Zw, n=F.NFFT_LOOP) * gi
            r = F.R_BASE * np.exp(x - 0.5 * x.var())
            c = np.fft.irfft(np.fft.rfft(r) * Khat, n=F.NFFT_LOOP)
            y[i] = c[idx]
    y = y + (F.IMG_SD_FRAC * F.R_BASE) * rng.standard_normal(y.shape)
    return y


def cross_stats(y, animal):
    """Per-loop lag from the cross-spectral phase slope, and normalised coupling."""
    nseg = WELCH_SEG
    step = nseg // 2
    starts = list(range(0, y.shape[1] - nseg + 1, step))
    win = np.hanning(nseg)
    freq = np.fft.rfftfreq(nseg, F.FRAME_DT)
    band = (freq >= COH_BAND[0]) & (freq <= COH_BAND[1])
    lags, coups = [], []
    for q in range(F.N_LOOP):
        pre = np.where((animal["loop_of"] == q) & (animal["side"] == 0))[0]
        post = np.where((animal["loop_of"] == q) & (animal["side"] == 1))[0]
        if pre.size < 1 or post.size < 1:
            continue
        Sxy = np.zeros(freq.size, complex)
        Sxx = np.zeros(freq.size)
        Syy = np.zeros(freq.size)
        for s in starts:
            a = y[pre, s:s + nseg].mean(axis=0)
            b = y[post, s:s + nseg].mean(axis=0)
            a = (a - a.mean()) * win
            b = (b - b.mean()) * win
            A = np.fft.rfft(a)
            B = np.fft.rfft(b)
            Sxy += A * np.conj(B)
            Sxx += np.abs(A) ** 2
            Syy += np.abs(B) ** 2
        coh = (np.abs(Sxy) ** 2) / np.maximum(Sxx * Syy, EPS)
        use = band & (coh >= MIN_COH)
        if use.sum() < 5:
            continue
        phase = np.unwrap(np.angle(Sxy[use]))
        X = np.vstack([2 * np.pi * freq[use], np.ones(use.sum())]).T
        sl = np.linalg.lstsq(X, phase, rcond=None)[0][0]
        lags.append(sl)                          # pre->post lag (s)
        coups.append(float(np.mean(np.sqrt(coh[band]))))
    if len(lags) < 3:
        return None
    bbfreq = np.fft.rfftfreq(nseg, F.FRAME_DT)
    bb = (bbfreq >= BB_BAND[0]) & (bbfreq <= BB_BAND[1])
    P = []
    for s in starts:
        seg = (y[:, s:s + nseg] - y[:, s:s + nseg].mean(axis=1, keepdims=True)) * win[None, :]
        P.append(np.abs(np.fft.rfft(seg, axis=-1)) ** 2)
    P = np.mean(P, axis=0)
    U3 = float(np.mean(np.log(np.maximum(P[:, bb].mean(axis=1), EPS))))
    return np.array([float(np.mean(lags)), float(np.mean(coups)), U3])


def main():
    t0 = time.time()
    rng_c = np.random.default_rng(SEED)
    animals = [make_animal_pairs(n, rng_c) for n in F.CELLS_PER_MOUSE]
    reps = []
    for r in range(N_REP):
        out = {}
        for mi, a in enumerate(animals):
            ye = simulate_pair_traces(a, (0.0, 0.0, 0.0),
                                      np.random.default_rng(SEED + 1000 * r + mi), N_FRAME)
            Se = cross_stats(ye, a)
            if Se is None:
                continue
            for w in WORLD_ORDER:
                yl = simulate_pair_traces(
                    a, WORLDS[w],
                    np.random.default_rng(SEED + 500000 + 1000 * r + 37 * mi
                                          + 7 * WORLD_ORDER.index(w)), N_FRAME)
                Sl = cross_stats(yl, a)
                if Sl is None:
                    continue
                out.setdefault(w, []).append(Sl - Se)
        reps.append({k: np.mean(np.array(v), axis=0) for k, v in out.items() if v})
        if (r + 1) % 10 == 0:
            print("rep", r + 1, "%.1fs" % (time.time() - t0), flush=True)

    pl = np.array([x["placebo"] for x in reps if "placebo" in x])
    null_sd = pl.std(axis=0, ddof=1)
    pl_mean = pl.mean(axis=0)
    table = {}
    for w in WORLD_ORDER:
        arr = np.array([x[w] for x in reps if w in x])
        table[w] = dict(n_rep=int(arr.shape[0]), mean=arr.mean(axis=0).tolist(),
                        sd=arr.std(axis=0, ddof=1).tolist(),
                        z=[float((arr.mean(axis=0)[j] - pl_mean[j]) / max(null_sd[j], 1e-30))
                           for j in range(3)])
    R = np.array([table[w]["z"] for w in ("gain_only", "efficacy_only", "delay_only")])
    norms = np.linalg.norm(R, axis=1)
    nm = ("gain", "efficacy", "delay")
    ang = {}
    for i, j in itertools.combinations(range(3), 2):
        d = norms[i] * norms[j]
        cs = float(R[i] @ R[j] / d) if d > 1e-12 else 0.0
        ang["%s-%s" % (nm[i], nm[j])] = float(np.degrees(np.arccos(np.clip(abs(cs), 0, 1))))
    # subset scan, as for C1
    subsets = {}
    for rsz in (1, 2, 3):
        for sub in itertools.combinations(range(3), rsz):
            S = R[:, list(sub)]
            n2 = np.linalg.norm(S, axis=1)
            aa = []
            for i, j in itertools.combinations(range(3), 2):
                dd = n2[i] * n2[j]
                cc = abs(float(S[i] @ S[j] / dd)) if dd > 1e-12 else 0.0
                aa.append(float(np.degrees(np.arccos(min(cc, 1.0)))))
            subsets[str(list(sub))] = dict(norms=n2.tolist(),
                                           min_angle=float(min(aa)) if rsz > 1 else None,
                                           pass_CA=bool(np.all(n2 >= 2.0)),
                                           pass_CB=bool(min(aa) >= 15.0) if rsz > 1 else None)
    out = dict(script="c15_c2_lag_cert.py", seed=SEED, elapsed_s=round(time.time() - t0, 1),
               candidate="C2 pairwise lag decomposition on long-axis loops",
               constants=dict(N_REP=N_REP, N_FRAME=N_FRAME, WELCH_SEG=WELCH_SEG,
                              COH_BAND=list(COH_BAND), MIN_COH=MIN_COH,
                              BB_BAND=list(BB_BAND), N_LOOP=F.N_LOOP,
                              L_MIN=F.L_MIN, L_MAX=F.L_MAX, V_AXON=F.V_AXON_LOOP,
                              TAU_SYN=F.TAU_SYN_LOOP, TAU_M=F.TAU_M_LOOP,
                              K_LOOP=F.K_LOOP, DG=F.DG, DW=F.DW, VFAC=F.VFAC,
                              cells_per_mouse=list(F.CELLS_PER_MOUSE)),
               stat_names=list(STAT_NAMES), null_sd=null_sd.tolist(),
               placebo_mean=pl_mean.tolist(), table=table,
               channel_response_matrix=R.tolist(), channel_norms=norms.tolist(),
               pairwise_angle_deg=ang, subset_scan=subsets,
               pass_CA=bool(np.all(norms >= 2.0)), pass_CB=bool(min(ang.values()) >= 15.0))
    with open(OUT, "w") as f:
        json.dump(out, f, indent=1)
    print(json.dumps(dict(null_sd=out["null_sd"], norms=out["channel_norms"],
                          ang=ang, pass_CA=out["pass_CA"], pass_CB=out["pass_CB"]), indent=1))
    for w in WORLD_ORDER:
        print(w, table[w]["n_rep"], [round(x, 5) for x in table[w]["mean"]],
              "z", [round(x, 3) for x in table[w]["z"]])
    print("subsets:")
    for k, v in subsets.items():
        print(" ", k, np.round(v["norms"], 2), v["min_angle"], v["pass_CA"], v["pass_CB"])


if __name__ == "__main__":
    main()
