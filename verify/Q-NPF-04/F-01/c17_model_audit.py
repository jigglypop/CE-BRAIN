"""Read-only audit of C14-C16; writes only its own new result receipt."""
from pathlib import Path
import hashlib
import json
import platform
import sys

import numpy as np
import scipy
from scipy.special import lambertw

import fwd_loop as F
import c14_loop_cert as C14
import c15_c2_lag_cert as C15

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalized_acf(x):
    x = x - x.mean()
    c = np.fft.irfft(np.abs(np.fft.rfft(x)) ** 2, n=len(x))
    return c / c[0]


def main():
    inputs = [HERE / p for p in (
        "fwd.py", "fwd_loop.py", "c14_loop_cert.py", "c15_c2_lag_cert.py",
        "prover_loop_report.json", "result_c14_loop_cert.json",
        "result_c15_c2_lag_cert.json", "result_c16_structural.json",
        "c17_audit_contract.json")]
    inputs += [HERE.parent / "spec.md"]
    before = {str(p.relative_to(ROOT)): sha(p) for p in inputs}
    # tau_m*s+1+a*exp(-s*tau)=0. Let w=(s+1/tau_m)*tau:
    # w*exp(w)=-(a*tau/tau_m)*exp(tau/tau_m).
    stability = []
    for L in np.geomspace(F.L_MIN, F.L_MAX, F.N_LOOP):
        tau = L / F.V_AXON_LOOP + F.TAU_SYN_LOOP
        a, tm = F.K_LOOP, F.TAU_M_LOOP
        arg = complex(-a * tau / tm * np.exp(tau / tm))
        roots = lambertw(arg, np.arange(-8, 9)) / tau - 1 / tm
        s = roots[np.argmax(roots.real)]
        residual = abs(tm*s + 1 + a*np.exp(-s*tau)) / (1+abs(tm*s)+a*abs(np.exp(-s*tau)))
        critical = tm * np.arccos(-1 / a) / np.sqrt(a*a-1)
        assert residual < 1e-9
        stability.append(dict(L_m=float(L), tau_s=float(tau),
                              critical_delay_s=float(critical),
                              positive_root_real_per_s=float(s.real),
                              root_imag_per_s=float(s.imag), residual=float(residual)))

    # Matched product: 10% gain versus 10% efficacy (not the unequal original worlds).
    hg = F.loop_transfer(.024, F.K_LOOP, (np.log(1.1), 0., 0.))[0]
    he = F.loop_transfer(.024, F.K_LOOP, (0., np.log(1.1), 0.))[0]
    ratio = np.abs(hg / he) ** 2
    assert np.max(np.abs(ratio - 1.21)) < 1e-10
    rng = np.random.default_rng(20260905)
    phase = rng.uniform(0, 2*np.pi, he.size)
    # This uses the existing Fourier recipe and constants, not a new biological fit.
    xw = F.CELL_NOISE_SD * np.sqrt(F.NFFT_LOOP) * np.abs(he) * np.exp(1j*phase)
    xw[0] = 0
    x = np.fft.irfft(xw, n=F.NFFT_LOOP)
    t = np.arange(F.NFFT_LOOP) * F.SIM_DT
    kernel = np.maximum(np.exp(-t/F.CA_DECAY)-np.exp(-t/F.CA_RISE), 0.)
    kernel /= kernel.sum()
    khat = np.fft.rfft(kernel)
    step = int(round(F.FRAME_DT / F.SIM_DT))
    idx = (np.arange(C14.N_FRAME)*step) % F.NFFT_LOOP
    traces = []
    for scale in (1., 1.1):
        z = scale*x
        rate = F.R_BASE*np.exp(z-.5*z.var())
        calcium = np.fft.irfft(np.fft.rfft(rate)*khat, n=F.NFFT_LOOP)
        traces.append((rate, calcium, calcium[idx]))
    differences = {}
    for col, name in enumerate(("rate", "calcium", "sampled_calcium")):
        ac = [normalized_acf(v[col]) for v in traces]
        differences[name] = float(np.max(np.abs(ac[0]-ac[1])))
    # Exact Gaussian-link example: Cov(exp(aX),exp(aY)) normalized by its variance.
    rho, variance = .5, 1.
    gauss_ac = [float(np.expm1(a*a*variance*rho)/np.expm1(a*a*variance)) for a in (1.,1.1)]

    # f_max limits principal phase, not the unwrapped slope across a dense band.
    freq = np.fft.rfftfreq(C15.WELCH_SEG, F.FRAME_DT)
    freq = freq[(freq >= C15.COH_BAND[0]) & (freq <= C15.COH_BAND[1])]
    delays = []
    for tau in (0., .08, .167, .3, .6):
        phase = np.unwrap(np.angle(np.exp(2j*np.pi*freq*tau)))
        fit = np.linalg.lstsq(np.column_stack((2*np.pi*freq, np.ones_like(freq))), phase, rcond=None)[0]
        assert abs(fit[0]-tau) < 1e-10
        delays.append(dict(true_s=tau, recovered_s=float(fit[0])))

    c14 = json.loads((HERE / "result_c14_loop_cert.json").read_text())
    c15 = json.loads((HERE / "result_c15_c2_lag_cert.json").read_text())
    assert before == {str(p.relative_to(ROOT)): sha(p) for p in inputs}
    out = dict(
        id="Q-NPF-04-C17", status="PRIOR_MODEL_INTERPRETATION_STOP",
        claim_ceiling="BIO_EVIDENCE_L0", biological_endpoint_evaluated=False,
        inputs_sha256=before, source_sha256=sha(Path(__file__)),
        runtime=dict(executable=sys.executable, python=platform.python_version(),
                     numpy=np.__version__, scipy=scipy.__version__),
        stability=dict(rows=stability,
            unstable_nominal_loops=sum(r["positive_root_real_per_s"] > 0 for r in stability),
            interpretation="Positive root disproves stationary causal-linear interpretation. A finite Fourier-shaped random process still exists but is not that stable driven DDE. No nonlinear saturation dynamics are implemented."),
        observation=dict(latent_ratio_min=float(ratio.min()), latent_ratio_max=float(ratio.max()),
            latent_acf_difference=float(np.max(np.abs(normalized_acf(x)-normalized_acf(1.1*x)))) ,
            existing_recipe_acf_differences=differences,
            gaussian_example_normalized_covariance=gauss_ac,
            interpretation="Latent linear scale no-go survives. Its extension to exponential-rate/calcium observations is not proved and has counterexamples. This does not establish practical identifiability or power."),
        clock=dict(declared_dt_s=F.FRAME_DT, actual_stride_dt_s=step*F.SIM_DT,
            relative_error=step*F.SIM_DT/F.FRAME_DT-1,
            latent_period_s=F.NFFT_LOOP*F.SIM_DT,
            requested_nominal_span_s=(C14.N_FRAME-1)*F.FRAME_DT,
            latent_wraps=int(((C14.N_FRAME-1)*step)//F.NFFT_LOOP),
            independent_new_latent_noise_after_wrap=False,
            interpretation="Modulo playback of one finite periodic trajectory, not fresh latent innovations. Does not itself quantify split leakage or corrected power."),
        phase=dict(noiseless_delay_recovery=delays,
            contiguous_bin_local_unwrap_bound_s=float(1/(2*np.max(np.diff(freq)))),
            claimed_fmax_bound_s=1/(2*C15.COH_BAND[1]),
            interpretation="0.167 s is not a general unwrapped-slope ceiling. Real coherence gaps, finite samples, filtering and SNR remain unresolved."),
        source_audit=[
            {"severity":"P0", "finding":"C15 applies gs inside H1 and again in gi; latent amplitude gain is squared whereas C14 applies it once. Channel contracts differ."},
            {"severity":"P1", "finding":"C14/C15 placebo z=0 subtracts its own sample mean; this is not independent false-positive calibration."},
            {"severity":"P1", "finding":"C14 valid replicates differ by world; report survivors and missingness before interpreting power.",
             "C14_counts":{k:v["n_rep"] for k,v in c14["table"].items()},
             "C15_counts":{k:v["n_rep"] for k,v in c15["table"].items()}},
            {"severity":"P1", "finding":"C14 per-cell random phases do not implement joint loop covariance; C15 uses a different shared-drive construction."}
        ],
        answers=dict(original_question_answered=False,
            refuted="Stationary causal-linear interpretation of nominal loops; blanket observation-level scaling impossibility; universal 0.167 s unwrap ceiling.",
            survives="Latent linear scaling identity at matched gain*efficacy; three-channel biological target is open.",
            next_allowed="Register stable causal generator or independently calibrated intervention design; do not promote old P3 numbers or write a passing card."))
    (HERE / "result_c17_model_audit.json").write_text(json.dumps(out, indent=2, allow_nan=False)+"\n", encoding="utf-8")
    print(json.dumps({"status":out["status"], "unstable_loops":out["stability"]["unstable_nominal_loops"],
                      "nonlinear_acf_differences":differences, "phase_recovery":delays}, indent=2))


if __name__ == "__main__":
    main()
