"""Conditional intervention-identifiability witnesses; no biological payload."""
from pathlib import Path
import hashlib
import itertools
import json
import platform
import sys

import numpy as np
import scipy
from scipy.optimize import least_squares

HERE = Path(__file__).resolve().parent
CONTRACT = HERE / "c18_intervention_contract.json"
C = json.loads(CONTRACT.read_text(encoding="utf-8"))
FREQ = np.linspace(.3, 3., 48)
W = 2*np.pi*FREQ
TM, DOSE = .02, .1


def ratio(theta, mode="known_additive"):
    g, k, tau = np.exp(theta[:3])
    if mode == "multiplicative":
        dose = .25*k
    elif mode == "unknown_additive":
        dose = np.exp(theta[3])
    elif mode == "none":
        dose = 0.
    else:
        dose = DOSE
    e = np.exp(-1j*W*tau)
    a = 1+1j*W*TM
    return (a+g*k*e)/(a+g*(k+dose)*e)


def real_vector(z):
    return np.concatenate((z.real, z.imag))


def sensitivity(theta, mode):
    step = 1e-5
    eye = np.eye(len(theta))*step
    J = np.column_stack([real_vector(ratio(theta+d, mode)-ratio(theta-d, mode))/(2*step) for d in eye])
    singular = np.linalg.svd(J, compute_uv=False)
    rank = int(np.sum(singular > 1e-7*singular[0])) if singular[0] > 0 else 0
    return dict(rank=rank, singular_values=singular.tolist())


def fit(y):
    options = C["optimizer"]
    best = None
    for start in options["starts"]:
        res = least_squares(lambda th: real_vector(ratio(th)-y), np.log(start),
            bounds=(np.log([.3,.05,.03]),np.log([2.,.5,.8])),
            max_nfev=options["max_nfev"], ftol=options["ftol"],
            xtol=options["xtol"], gtol=options["gtol"])
        g, k, tau = np.exp(res.x)
        if res.success and g*(k+DOSE) < 1 and (best is None or res.cost < best.cost):
            best = res
    if best is None:
        return None
    return np.exp(best.x)


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    rows, rank_controls, noisy = [], [], []
    for truth in itertools.product((.8,1.,1.2),(.25,.4),(.08,.3,.6)):
        truth = np.array(truth)
        th = np.log(truth)
        assert truth[0]*(truth[1]+DOSE) < 1
        info = sensitivity(th,"known_additive")
        recovered = fit(ratio(th))
        err = None if recovered is None else float(np.max(np.abs(recovered/truth-1)))
        rows.append(dict(truth=truth.tolist(), sensitivity=info,
            recovered=None if recovered is None else recovered.tolist(), max_relative_error=err))
        extended = np.r_[th, np.log(DOSE)]
        shift = np.log(1.1)*np.array([1.,-1.,0.,-1.])
        gauge_unknown = float(np.max(np.abs(ratio(extended,"unknown_additive")-ratio(extended+shift,"unknown_additive"))))
        gauge_fractional = float(np.max(np.abs(ratio(th,"multiplicative")-ratio(th+shift[:3],"multiplicative"))))
        rank_controls.append(dict(truth=truth.tolist(),
            fractional=sensitivity(th,"multiplicative"),
            unknown_dose=sensitivity(extended,"unknown_additive"),
            unknown_dose_gauge_error=gauge_unknown,
            fractional_gauge_error=gauge_fractional,
            known_dose_gauge_difference=float(np.max(np.abs(ratio(th)-ratio(th+shift[:3]))))))
        for seed in (20260905,20260906):
            # Different independent noise per case and replicate; reproducible seed ancestry.
            rng = np.random.default_rng(np.random.SeedSequence([seed, len(rows)]))
            for rep in range(C["noise"]["repetitions_per_grid_point_per_seed"]):
                y = ratio(th)+C["noise"]["complex_component_sd"]*(rng.normal(size=48)+1j*rng.normal(size=48))
                estimate = fit(y)
                noisy.append(dict(truth=truth.tolist(), seed=seed, replicate=rep,
                    estimate=None if estimate is None else estimate.tolist(),
                    relative_error=None if estimate is None else (estimate/truth-1).tolist()))
    checks = dict(
        known_additive_local_rank_3=all(r["sensitivity"]["rank"]==3 for r in rows),
        noiseless_recovery=all(r["max_relative_error"] is not None and r["max_relative_error"]<=1e-4 for r in rows),
        fractional_rank_at_most_2=all(r["fractional"]["rank"]<=2 for r in rank_controls),
        unknown_dose_rank_at_most_3=all(r["unknown_dose"]["rank"]<=3 for r in rank_controls),
        exact_gauge_controls=all(max(r["unknown_dose_gauge_error"],r["fractional_gauge_error"])<1e-10 for r in rank_controls))
    errors = np.array([r["relative_error"] for r in noisy if r["relative_error"] is not None])
    out = dict(id="Q-NPF-04-C18",status="CONDITIONAL_DESIGN_SUPPORTED" if all(checks.values()) else "DESIGN_TEST_FAILED",
        claim_ceiling="BIO_EVIDENCE_L0", biological_endpoint_evaluated=False,
        runtime=dict(executable=sys.executable,python=platform.python_version(),numpy=np.__version__,scipy=scipy.__version__),
        hashes={"contract":sha(CONTRACT),"source":sha(Path(__file__)),"parent_audit":sha(HERE/"result_c17_model_audit.json")},
        checks=checks, noiseless=rows, negative_controls=rank_controls,
        noise_summary=dict(total=len(noisy),failed=sum(r["estimate"] is None for r in noisy),
            columns=["gain","coupling","delay"],
            median_absolute_relative_error=np.median(np.abs(errors),axis=0).tolist(),
            p95_absolute_relative_error=np.quantile(np.abs(errors),.95,axis=0).tolist(),
            interpretation="Illustrative ratio-noise model only; not empirical mouse power or a P6 pass."),
        noisy_recovery=noisy,
        minimal_measurements=[
            "Identified same loop/cells and measured exogenous broadband probe before and after intervention.",
            "Independent calibration of additive effective coupling dose; fractional change alone is insufficient in this model.",
            "Independent gain, membrane-time and delay fidelity controls; sham, off-target and recovery arms.",
            "Repeated independent trials on native non-wrapped timestamps; stable recording transfer across arms.",
            "Independent confirmation animals plus scalar-loop versus multi-loop, nonlinear and state-change competitors.",
            "For original CE folding/mediation claim: independent neural chart and output likelihood, separate behavior, direct microvariables and identity; this test supplies none of them."],
        calibration_caveat="If assumed d is c times actual d, the recovered g is divided by c and k multiplied by c. Without independent dose calibration individual mechanism values remain unidentified.",
        answers=dict(original_question_answered=False,
            refuted="Fractional coupling intervention alone resolves gain/coupling ambiguity in this scalar ratio model.",
            survives="Known additive calibrated intervention is a conditional candidate; biological actuator feasibility and target-chain evidence are absent.",
            next_allowed="Check independently measured actuator calibration and same-unit availability; otherwise design that measurement rather than fit unidentified gains to existing calcium data."))
    (HERE/"result_c18_intervention_identifiability.json").write_text(json.dumps(out,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps({"status":out["status"],"checks":checks,"noise_summary":out["noise_summary"]},indent=2))
    if not all(checks.values()):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
