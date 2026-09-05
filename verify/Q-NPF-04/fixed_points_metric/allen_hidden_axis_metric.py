"""Internal donor-grouped test of the third raw-coordinate cost component.

Reuses the frozen 28,616-pair cohort and its folds, covariates and reference
predictions. Raw axes are not registered cortical normals. Radial shape is
optimized from training likelihood only, including exact PSD boundaries.
"""
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.optimize import minimize, minimize_scalar
from scipy.special import expit

import allen_structural_metric_baseline as baseline

HERE = Path(__file__).resolve().parent
OUTPUT = HERE / "allen_hidden_axis_metric_result.json"
ARRAYS = HERE / "allen_hidden_axis_metric_arrays.npz"
GRID = [0., .02, .05, .1, .2, .35, .5, .65, .8, .9, .95, .98, 1.]
PROFILE_XTOL = .0001
MODELS = ["no_distance", "quadratic_metric", "radial_link", "shape_control",
          "z_quadratic", "x_quadratic", "y_quadratic", "z_signed_quadratic",
          "z_plane_quadratic", "z_axis_quadratic", "z_radial", "x_radial", "y_radial",
          "z_plane_radial", "z_axis_radial"]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def squared_components(delta_um, axis):
    s = np.asarray(delta_um, float) / 100.
    return np.column_stack([np.sum(np.delete(s, axis, axis=1)**2, axis=1), s[:, axis]**2])


def radial_feature(components, w):
    if not 0 <= w <= 1:
        raise ValueError(w)
    return np.sqrt((1-w)*components[:, 0] + w*components[:, 1])[:, None]


def radial_metric(rho, w, axis):
    diagonal = np.full(3, rho**2*(1-w)/100**2)
    diagonal[axis] = rho**2*w/100**2
    return dict(diagonal_per_um2=diagonal.tolist(), rho=float(rho), w=float(w),
                axis_to_plane_ratio=float(w/(1-w)) if w < 1 else None,
                SPD=bool(rho > 1e-8 and 0 < w < 1),
                rank=int(np.count_nonzero(diagonal > 0)),
                scope="Raw-coordinate conditional probability cost, not a physical conductance or cortical-axis measurement")


class TrainingProblem:
    def __init__(self, context, y):
        self.categories = sorted(set(context)); mapping = {c:i for i,c in enumerate(self.categories)}
        self.group = np.array([mapping[c] for c in context]); self.y = np.asarray(y, float)
        self.k = len(self.categories); self.n = len(y)

    def objective(self, params, features):
        offsets = params[1:1+self.k]; beta = params[1+self.k:]
        logits = params[0] + offsets[self.group] - features@beta
        residual = expit(logits) - self.y
        loss = (np.sum(np.logaddexp(0, logits)-self.y*logits) + .5*np.sum(offsets**2))/self.n
        grad = np.r_[residual.sum(), np.bincount(self.group,weights=residual,minlength=self.k)+offsets,
                     -features.T@residual]/self.n
        return loss, grad

    def fit(self, features, signed=False, initial=None):
        if initial is None:
            initial = np.zeros(1+self.k+features.shape[1])
            mean = np.clip(self.y.mean(), 1e-6, 1-1e-6)
            initial[0] = np.log(mean/(1-mean))
        solved = minimize(self.objective, np.asarray(initial,float), args=(features,), jac=True, method="L-BFGS-B",
            bounds=[(None,None)]*(1+self.k)+[(None,None) if signed else (0,None)]*features.shape[1],
            options={"maxiter":2000,"ftol":1e-12,"gtol":1e-8,"maxls":40})
        if not solved.success:
            raise RuntimeError(f"Convex inner fit failed: {solved.message}; objective={solved.fun}; iterations={solved.nit}")
        return dict(params=solved.x, objective=float(solved.fun), iterations=int(solved.nit),
                    gradient_max=float(np.max(abs(solved.jac))))

    def pack(self, fit):
        p = fit["params"]
        return dict(intercept=float(p[0]), context_offsets=dict(zip(self.categories,p[1:1+self.k].tolist())),
                    coefficients=p[1+self.k:].tolist(), objective=fit["objective"],
                    iterations=fit["iterations"], gradient_max=fit["gradient_max"])


def predict(fit, context, features):
    return fit["intercept"] + np.array([fit["context_offsets"].get(c,0.) for c in context]) - features@np.array(fit["coefficients"])


def profile_radial(problem, components, initial=None):
    cache = {}
    def at(w):
        w = float(w)
        if w not in cache:
            start = cache[min(cache,key=lambda z:abs(z-w))]["params"] if cache else initial
            cache[w] = problem.fit(radial_feature(components,w),initial=start)
        return cache[w]
    at(.5); at(0.); at(1.)
    for w in GRID:
        at(w)
    # Refine each local minimum seen on the fixed grid, plus both endpoint intervals.
    brackets = {(GRID[0],GRID[1]), (GRID[-2],GRID[-1])}
    for i in range(1,len(GRID)-1):
        if at(GRID[i])["objective"] <= min(at(GRID[i-1])["objective"],at(GRID[i+1])["objective"]):
            brackets.add((GRID[i-1],GRID[i+1]))
    refinements = []
    for left,right in sorted(brackets):
        solved = minimize_scalar(lambda w:at(w)["objective"],bounds=(left,right),method="bounded",
                                 options={"xatol":PROFILE_XTOL,"maxiter":50})
        if not solved.success:
            raise RuntimeError("Radial profile interval refinement failed")
        refinements.append(dict(interval=[left,right],w=float(solved.x),objective=float(solved.fun)))
    w = min(cache,key=lambda z:cache[z]["objective"])
    best = at(w)
    assert best["objective"] <= min(at(v)["objective"] for v in [0.,.5,1.]) + 1e-12
    profile = [dict(w=z,objective=v["objective"],delta_penalized_sum=(v["objective"]-best["objective"])*problem.n,
                    rho=float(v["params"][-1])) for z,v in sorted(cache.items())]
    return dict(w=w,fit=problem.pack(best),profile=profile,refinements=refinements,
                boundaries={str(z):problem.pack(at(z)) for z in [0.,.5,1.]},
                optimization_scope="Fixed grid plus local interval refinement; no proof of continuous global optimality")


def schur_information(problem, features, fitted):
    """Curvature of penalized training objective after nuisance elimination, not a CI."""
    logits=predict(fitted,np.array([problem.categories[i] for i in problem.group]),features)
    weight=expit(logits)*(1-expit(logits))
    wc=np.bincount(problem.group,weights=weight,minlength=problem.k)
    wf=np.column_stack([np.bincount(problem.group,weights=weight*features[:,i],minlength=problem.k) for i in range(features.shape[1])])
    ff=features.T@(weight[:,None]*features) - wf.T@(wf/(wc+1)[:,None])
    fa=np.sum(wf/(wc+1)[:,None],axis=0); aa=np.sum(wc/(wc+1))
    info=ff-np.outer(fa,fa)/aa
    norms=np.sqrt(np.maximum(np.diag(info),1e-300)); corr=info/np.outer(norms,norms)
    return dict(eigenvalues=np.linalg.eigvalsh(info).tolist(),normalized_eigenvalues=np.linalg.eigvalsh(corr).tolist(),
                scope="Penalized conditional training curvature only; no donor uncertainty or biological identification claim")


def main():
    if OUTPUT.exists() or ARRAYS.exists():
        raise FileExistsError("Completed hidden-axis artifacts are immutable")
    inputs={
        HERE/"allen_structural_metric_baseline.py":"eeb736602e86b29fee7839bc4c46a3cdbdb97439a8d19fe3588468d4ec7c8c23",
        HERE/"allen_structural_metric_baseline_result.json":"d13c396980d7e509d8206e2324b1be6ca8a0fcdfe666df7864435391e72e9e14",
        HERE/"allen_structural_metric_baseline_arrays.npz":"c82fd88911fa13d893f6a08816ca8b43f7a52d8f3096750d0a5127a8ba0b9d75",
        HERE/"allen_cortical_registration_audit_result.json":"93c77524169d1debdc82fd986e40fac0d3fbff4164724f9856c91722c23f4239"}
    for path,expected in inputs.items():
        assert sha(path)==expected,path
    original=json.loads((HERE/"allen_structural_metric_baseline_result.json").read_text())
    registration=json.loads((HERE/"allen_cortical_registration_audit_result.json").read_text())
    with np.load(HERE/"allen_structural_metric_baseline_arrays.npz",allow_pickle=False) as a:
        y=a["label"];context=a["context"];donor=a["donor_id"];fold=a["fold"];pair_ids=a["pair_id"]
        delta=(a["post_position_m"]-a["pre_position_m"])*1e6
        all_logits=np.full((len(y),len(MODELS)),np.nan)
        for name in MODELS[:4]:
            all_logits[:,MODELS.index(name)]=a["out_of_fold_logits"][:,a["models"].tolist().index(name)]
    assert np.array_equal(pair_ids,np.array([r["pair_id"] for r in original["records"]]))
    assert np.allclose(np.linalg.norm(delta,axis=1),[r["distance_um"] for r in original["records"]])
    registered_cells={r["experiment_id"]:{c["cell_id"] for c in r["cells"]} for r in registration["experiments"]
        if all(v["all_loo_identifiable"] for v in r["models"].values()) and r["models"]["xy_similarity"]["loo_max_error_um"] <= 1}
    assert len(registered_cells)==1177
    subset=np.array([r["experiment_id"] in registered_cells and {r["pre_cell_id"],r["post_cell_id"]} <= registered_cells[r["experiment_id"]] for r in original["records"]])
    fits=[]; profiles=[]; scores=[]
    for f in range(5):
        train=fold!=f; test=fold==f
        assert set(donor[train]).isdisjoint(donor[test])
        problem=TrainingProblem(context[train],y[train])
        for axis,name in [(2,"z"),(0,"x"),(1,"y")]:
            components=squared_components(delta,axis); ft=components[train]
            fitted=problem.pack(problem.fit(ft))
            diag=np.full(3,fitted["coefficients"][0]/100**2);diag[axis]=fitted["coefficients"][1]/100**2
            model=name+"_quadratic"
            all_logits[test,MODELS.index(model)]=predict(fitted,context[test],components[test])
            fits.append(dict(fold=f,model=model,axis=axis,**fitted,metric_diagonal_per_um2=diag.tolist(),
                             SPD=bool(np.all(diag>1e-12)),information=schur_information(problem,ft,fitted)))
            if axis==2:
                for model,feature,signed in [("z_signed_quadratic",components,True),("z_plane_quadratic",components[:,:1],False),("z_axis_quadratic",components[:,1:],False)]:
                    other=problem.pack(problem.fit(feature[train],signed=signed))
                    all_logits[test,MODELS.index(model)]=predict(other,context[test],feature[test])
                    fits.append(dict(fold=f,model=model,axis=axis,**other))
            # Start the isotropic profile from the already frozen same-fold reference.
            old=next(r for r in original["model_fits"] if r["model"]=="radial_link" and r["fold"]==f)
            start=np.r_[old["intercept"],[old["context_offsets"][c] for c in problem.categories],old["distance_coefficients"][0]*np.sqrt(2)]
            profile=profile_radial(problem,ft,initial=start)
            model=name+"_radial"; w=profile["w"]
            all_logits[test,MODELS.index(model)]=predict(profile["fit"],context[test],radial_feature(components[test],w))
            profiles.append(dict(fold=f,axis=axis,model=model,**profile))
            fits.append(dict(fold=f,model=model,axis=axis,**profile["fit"],metric=radial_metric(profile["fit"]["coefficients"][0],w,axis)))
            iso=predict(profile["boundaries"]["0.5"],context[test],radial_feature(components[test],.5))
            iso_difference=float(np.max(abs(iso-all_logits[test,MODELS.index("radial_link")])))
            assert iso_difference < 1e-3,iso_difference
            profiles[-1]["isotropic_logit_max_difference_from_frozen"]=iso_difference
            if axis==2:
                for w,model in [(0.,"z_plane_radial"),(1.,"z_axis_radial")]:
                    other=profile["boundaries"][str(w)]
                    all_logits[test,MODELS.index(model)]=predict(other,context[test],radial_feature(components[test],w))
                    fits.append(dict(fold=f,model=model,axis=axis,**other,metric=radial_metric(other["coefficients"][0],w,axis)))
            print("HIDDEN_AXIS",f,name,"profile_points",len(profile["profile"]),"training_w",profile["w"],flush=True)
        for i,model in enumerate(MODELS):
            ll,br=baseline.losses(y[test],all_logits[test,i])
            scores.append(dict(fold=f,model=model,pairs=int(test.sum()),log_loss=float(ll.mean()),brier=float(br.mean())))
    assert np.isfinite(all_logits).all()
    ll,br=baseline.losses(y[:,None],all_logits)
    comparisons=[]
    pairs=[("z_quadratic","quadratic_metric"),("x_quadratic","quadratic_metric"),("y_quadratic","quadratic_metric"),
           ("z_radial","radial_link"),("x_radial","radial_link"),("y_radial","radial_link"),
           ("z_quadratic","z_plane_quadratic"),("z_radial","z_plane_radial"),
           ("z_signed_quadratic","z_quadratic"),("z_radial","x_radial"),("z_radial","y_radial"),
           ("z_radial","shape_control"),("z_plane_radial","radial_link")]
    for candidate,reference in pairs:
        a=MODELS.index(candidate);b=MODELS.index(reference)
        comparisons.append(dict(candidate=candidate,reference=reference,
            log_loss_difference=baseline.cluster_comparison(donor,ll[:,a]-ll[:,b]),
            brier_difference=baseline.cluster_comparison(donor,br[:,a]-br[:,b])))
    subset_scores=[dict(model=model,pairs=int(subset.sum()),positive=int(y[subset].sum()),donors=len(set(donor[subset])),
        log_loss=float(ll[subset,i].mean()),brier=float(br[subset,i].mean())) for i,model in enumerate(MODELS)]
    with ARRAYS.open("xb") as stream:
        np.savez_compressed(stream,pair_id=pair_ids,delta_um=delta,label=y,donor_id=donor,fold=fold,context=context,
                            registration_subset=subset,models=np.array(MODELS),out_of_fold_logits=all_logits)
    result=dict(version="allen-hidden-axis-metric-v1",code_sha256=sha(Path(__file__)),
        input_sha256={p.name:v for p,v in inputs.items()},arrays_sha256=sha(ARRAYS),
        settings=dict(raw_axes_not_cortical_normals=True,primary_comparison="z_radial versus isotropic radial_link",
            radial_profile_grid=GRID,radial_refinement_xatol=PROFILE_XTOL,context_ridge=1.,hyperparameter_search=False,
            parameter_selection="Training penalized likelihood only; axis labels and reference models fixed before this evaluation",
            evaluation="Reused internal donor folds and previously exposed dataset, not new external confirmation",
            subset_scope="Descriptive subset of frozen OOF predictions; good coordinate correspondence for both endpoints; no refit or validation promotion"),
        summary=dict(pairs=len(y),positive=int(y.sum()),donors=len(set(donor)),registration_subset_pairs=int(subset.sum()),
            registration_subset_experiments=len({r["experiment_id"] for r,s in zip(original["records"],subset) if s}),
            absolute_component_quantiles_um=np.quantile(abs(delta),[0,.5,.95,1],axis=0).tolist(),
            models=[dict(model=model,log_loss=float(ll[:,i].mean()),brier=float(br[:,i].mean())) for i,model in enumerate(MODELS)]),
        fits=fits,radial_profiles=profiles,fold_scores=scores,comparisons=comparisons,registration_subset_scores=subset_scores,
        claim_ceiling="L1 selected-label observations and L0 candidate development; no unique biological metric, causal circuit, pia axis, conductance or hormone inference")
    with OUTPUT.open("x",encoding="utf-8") as stream:
        json.dump(result,stream,indent=2,allow_nan=False);stream.write("\n")
    print(json.dumps(result["summary"]))


if __name__=="__main__":
    main()
