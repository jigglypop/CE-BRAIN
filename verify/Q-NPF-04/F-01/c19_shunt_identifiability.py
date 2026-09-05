"""Test C18 against shunting and nuisance uncertainty without changing originals."""
from pathlib import Path
import hashlib
import itertools
import json
import platform
import sys

import numpy as np
import scipy
from scipy.optimize import least_squares

import c18_intervention_identifiability as P

HERE = Path(__file__).resolve().parent
CONTRACT = HERE / "c19_shunt_contract.json"
C = json.loads(CONTRACT.read_text(encoding="utf-8"))
F = C["fit_constants"]


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def pack(values):
    return np.r_[np.log(values[:4]), values[4]]


def unpack(theta):
    return np.r_[np.exp(theta[:4]), theta[4]]


def ratio(theta):
    g, k, tau, tm, h = unpack(theta)
    e = np.exp(-1j*P.W*tau)
    a = 1+1j*P.W*tm
    return (a+g*k*e)/(a+h+g*(k+P.DOSE)*e)


def sensitivity(theta):
    steps = np.eye(5)*1e-5
    J = np.column_stack([P.real_vector(ratio(theta+d)-ratio(theta-d))/2e-5 for d in steps])
    sv = np.linalg.svd(J,compute_uv=False)
    return dict(rank=int(np.sum(sv>1e-7*sv[0])),singular_values=sv.tolist(),condition=float(sv[0]/sv[-1]))


def fit(y, mode, truth):
    best = None
    count = 5 if mode == "joint" else 3
    lo = np.r_[np.log([.3,.05,.03,.005]),-.2][:count]
    hi = np.r_[np.log([2.,.5,.8,.1]),.8][:count]

    def expand(v):
        if mode == "joint":
            return v
        tm, h = (truth[3],truth[4]) if mode == "calibrated" else (.02,0.)
        return np.r_[v,np.log(tm),h]

    for tau in F["initial_tau"]:
        x0 = pack([1.,.3,tau,.02,.1])[:count]
        res = least_squares(lambda v:P.real_vector(ratio(expand(v))-y),x0,
            bounds=(lo,hi),max_nfev=F["max_nfev"],ftol=F["ftol"],xtol=F["xtol"],gtol=F["gtol"])
        est = unpack(expand(res.x))
        g,k,_,_,h = est
        stable = g*k<1 and g*(k+P.DOSE)<1+h
        if res.success and stable and (best is None or res.cost<best[0]):
            best = (res.cost,est)
    if best is None:
        return dict(success=False)
    return dict(success=True,estimate=best[1].tolist(),
        mechanism_relative_error=(best[1][:3]/truth[:3]-1).tolist(),
        tm_relative_error=float(best[1][3]/truth[3]-1),h_absolute_error=float(best[1][4]-truth[4]),
        complex_rmse=float(np.sqrt(2*best[0]/48)))


def summary(rows, key):
    records=[r[key] for r in rows]
    ok=[r for r in records if r["success"]]
    errors=np.abs(np.array([r["mechanism_relative_error"] for r in ok]))
    return dict(total=len(records),failed=len(records)-len(ok),columns=["gain","coupling","delay"],
        median_absolute_relative_error=None if not ok else np.median(errors,axis=0).tolist(),
        p95_absolute_relative_error=None if not ok else np.quantile(errors,.95,axis=0).tolist())


def main():
    protected=[HERE/p for p in ("c18_intervention_contract.json","c18_intervention_identifiability.py",
        "result_c18_intervention_identifiability.json","c18_measurement_requirements.json")]
    hashes={p.name:sha(p) for p in protected}
    noiseless, noisy=[],[]
    for idx,(g,k,tau,h) in enumerate(itertools.product((.8,1.2),(.25,.4),(.08,.3,.6),(0.,.1,.3))):
        truth=np.array([g,k,tau,.02,h])
        assert g*k<1 and g*(k+P.DOSE)<1+h
        theta=pack(truth)
        y=ratio(theta)
        if h==0:
            assert np.max(np.abs(y-P.ratio(theta[:3])))<1e-12
        row=dict(truth=truth.tolist(),sensitivity=sensitivity(theta))
        for mode in ("omitted","joint","calibrated"):
            row[mode]=fit(y,mode,truth)
        noiseless.append(row)
        rng=np.random.default_rng(np.random.SeedSequence([20260907,idx]))
        for rep in range(2):
            yn=y+.01*(rng.normal(size=48)+1j*rng.normal(size=48))
            nr=dict(truth=truth.tolist(),replicate=rep)
            for mode in ("omitted","joint","calibrated"):
                nr[mode]=fit(yn,mode,truth)
            noisy.append(nr)
    # Mechanism differences can be absorbed by an unrestricted condition-dependent
    # transfer filter; an exact constructive witness, not a local rank heuristic.
    a=pack([1.,.3,.3,.02,.1]); b=pack([1.2,.25,.4,.03,.2])
    filter_ratio=ratio(a)/ratio(b)
    residual=float(np.max(np.abs(filter_ratio*ratio(b)-ratio(a))))
    assert residual<1e-12
    joint_ok=all(r["joint"]["success"] and max(abs(x) for x in r["joint"]["mechanism_relative_error"])<=.001
        and abs(r["joint"]["tm_relative_error"])<=.001 and abs(r["joint"]["h_absolute_error"])<=.001 for r in noiseless)
    rank_ok=all(r["sensitivity"]["rank"]==5 for r in noiseless)
    assert hashes=={p.name:sha(p) for p in protected}
    out=dict(id="Q-NPF-04-C19",status="JOINT_NUISANCE_STRUCTURALLY_SUPPORTED" if joint_ok and rank_ok else "JOINT_NUISANCE_NOT_ESTABLISHED",
        claim_ceiling="BIO_EVIDENCE_L0",biological_endpoint_evaluated=False,
        runtime=dict(python=platform.python_version(),executable=sys.executable,numpy=np.__version__,scipy=scipy.__version__),
        hashes=dict(parent=hashes,contract=sha(CONTRACT),source=sha(Path(__file__))),
        checks=dict(noiseless_joint_recovery=joint_ok,full_local_rank=rank_ok,exact_recording_filter_counterexample=True),
        sensitivity_condition_range=[min(r["sensitivity"]["condition"] for r in noiseless),max(r["sensitivity"]["condition"] for r in noiseless)],
        noiseless_summary={mode:summary(noiseless,mode) for mode in ("omitted","joint","calibrated")},
        noisy_summary={mode:summary(noisy,mode) for mode in ("omitted","joint","calibrated")},
        noiseless=noiseless,noisy=noisy,
        filter_counterexample=dict(truth=unpack(a).tolist(),alternative=unpack(b).tolist(),
            output_residual=residual,filter_magnitude_range=[float(np.abs(filter_ratio).min()),float(np.abs(filter_ratio).max())],
            interpretation="An unconstrained changing recording transfer can exactly mimic different mechanisms. Fixed or independently calibrated readout is necessary for this inference; a restricted filter family could behave differently."),
        answers=dict(original_question_answered=False,
            refuted="Pure coupling inference can ignore conductance shunting without testing bias; unrestricted recording drift permits unique mechanism recovery.",
            survives="Conditional scalar-mechanism inference with explicitly modeled nuisance and independent calibration; no anatomical topology recovered.",
            next_allowed="Quantify real calibration/input availability; do not replace missing biological measurements with oracle values or synthetic power."))
    (HERE/"result_c19_shunt_identifiability.json").write_text(json.dumps(out,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps({k:out[k] for k in ("status","checks","sensitivity_condition_range","noiseless_summary","noisy_summary","filter_counterexample")},indent=2))


if __name__=="__main__":
    main()
