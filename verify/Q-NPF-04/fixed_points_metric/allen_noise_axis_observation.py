"""Frozen-cohort geometry prediction conditional on completed noise metadata.

All QC-pass IC recording noise is a retrospective acquisition summary, not
synapse-response standard error or independently calibrated detection sensitivity.
No fitting is allowed while any target cell remains uncollected.
"""
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.optimize import minimize
from scipy.special import expit

import allen_depth_probe_observation as depth
import allen_hidden_axis_metric as axis_model
import allen_structural_metric_baseline as baseline

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
OUTPUT=HERE/"allen_noise_axis_observation_result.json"
ARRAYS=HERE/"allen_noise_axis_observation_arrays.npz"
NOISE=HERE/"allen_observation_medium_inputs_result.json"
MODELS=["depth_count_context","depth_count_radial","noise_context","noise_radial",
        "noise_z_radial","noise_z_plane_radial","noise_z_axis_radial","noise_x_radial","noise_y_radial"]
FEATURE_NAMES=depth.FEATURES+["log_mean_IC_noise_per_1V","depth_missing","count_missing","noise_missing"]


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_noise(payload,wanted):
    cells={}
    for r in payload["cells"]:
        cid=r["cell_id"]
        if cid in cells:raise ValueError("Duplicate noise cell")
        if r["identity_checked"] is not True:raise ValueError("Unverified cell identity")
        records=r["qc_pass_IC_records"]
        if len(records)!=r["qc_pass_IC_count"]:raise ValueError("QC IC record count mismatch")
        if any(v["clamp_mode"]!="ic" or v["qc_pass"]!=1 for v in records):raise ValueError("Non-QC or non-IC record in noise mean")
        values=[v["baseline_noise_stdev"] for v in records]
        finite=[v is not None and bool(np.isfinite(v)) for v in values]
        if sum(finite)!=r["qc_pass_IC_finite_noise_count"]:raise ValueError("Finite noise count mismatch")
        expected=float(np.mean(values)) if len(values)>1 and all(finite) else None
        if expected is not None and expected<=0:expected=None
        if expected!=r["mean_qc_pass_IC_noise_V"]:raise ValueError("Noise mean not reproduced")
        cells[cid]=r
    if set(cells)!=set(wanted) or payload["wanted_cells"]!=len(wanted):
        raise ValueError("Noise collection incomplete or target cohort mismatch")
    return cells


def transform(raw,prep):
    if raw.ndim!=2 or raw.shape[1]!=4:raise ValueError("Four raw observation columns required")
    valid=np.isfinite(raw)
    standardized=np.where(valid,(raw-np.array(prep["mean"]))/np.array(prep["scale"]),0.)
    return np.column_stack([standardized,(~valid[:,[0,2,3]]).astype(float)])


class ObservationProblem:
    def __init__(self,context,y,observation):
        self.categories=sorted(set(context));mapping={c:i for i,c in enumerate(self.categories)}
        self.group=np.array([mapping[c] for c in context]);self.y=np.asarray(y,float)
        self.observation=np.asarray(observation,float);self.k=len(self.categories);self.q=self.observation.shape[1];self.n=len(y)

    def objective(self,params,features):
        offsets=params[1:1+self.k];theta=params[1+self.k:1+self.k+self.q];beta=params[1+self.k+self.q:]
        logits=params[0]+offsets[self.group]+self.observation@theta-features@beta
        residual=expit(logits)-self.y
        value=(np.sum(np.logaddexp(0,logits)-self.y*logits)+.5*(offsets@offsets+theta@theta))/self.n
        grad=np.r_[residual.sum(),np.bincount(self.group,weights=residual,minlength=self.k)+offsets,
                   self.observation.T@residual+theta,-features.T@residual]/self.n
        return value,grad

    def fit(self,features,initial=None):
        if initial is None:
            initial=np.zeros(1+self.k+self.q+features.shape[1]);m=np.clip(self.y.mean(),1e-6,1-1e-6);initial[0]=np.log(m/(1-m))
        assert len(initial)==1+self.k+self.q+features.shape[1]
        solved=minimize(self.objective,np.asarray(initial,float),args=(features,),jac=True,method="L-BFGS-B",
            bounds=[(None,None)]*(1+self.k+self.q)+[(0,None)]*features.shape[1],
            options=dict(maxiter=2000,ftol=1e-12,gtol=1e-8,maxls=40))
        if not solved.success:raise RuntimeError(f"Observation fit failed: {solved.message}")
        return dict(params=solved.x,objective=float(solved.fun),iterations=int(solved.nit),gradient_max=float(np.max(abs(solved.jac))))

    def pack(self,fitted):
        p=fitted["params"]
        return dict(intercept=float(p[0]),context_offsets=dict(zip(self.categories,p[1:1+self.k].tolist())),
            observation_coefficients=p[1+self.k:1+self.k+self.q].tolist(),coefficients=p[1+self.k+self.q:].tolist(),
            objective=fitted["objective"],iterations=fitted["iterations"],gradient_max=fitted["gradient_max"])


def predict(fitted,context,observation,features):
    return (fitted["intercept"]+np.array([fitted["context_offsets"].get(c,0.) for c in context])
            +observation@np.array(fitted["observation_coefficients"])-features@np.array(fitted["coefficients"]))


def main():
    if OUTPUT.exists() or ARRAYS.exists():raise FileExistsError("Completed noise-axis artifacts are immutable")
    if not NOISE.exists():raise FileNotFoundError("Complete target-cell noise collection is required before fitting")
    inputs={
        HERE/"allen_depth_probe_observation.py":"96740157994fca8170afaf354935ae5eefe09d621c2abae773394ba4542679a9",
        HERE/"allen_depth_probe_observation_arrays.npz":"c062f197a27fe2b78abd846ff2549c4015b35fe8205fe047738d0b426b0f8b29",
        HERE/"allen_depth_probe_observation_result.json":"10ca64e4e32679d07decd5c7d3ef305d6228fef19c433fc14c2a062823f551b9",
        HERE/"allen_hidden_axis_metric.py":"6ad3738a0bf4b283f35be4f942a7a9b4070dbd44b1b618275ac07e6d59cf8a86",
        HERE/"allen_structural_metric_baseline.py":"eeb736602e86b29fee7839bc4c46a3cdbdb97439a8d19fe3588468d4ec7c8c23",
        HERE/"allen_structural_metric_baseline_result.json":"d13c396980d7e509d8206e2324b1be6ca8a0fcdfe666df7864435391e72e9e14",
        HERE/"allen_structural_metric_baseline_arrays.npz":"c82fd88911fa13d893f6a08816ca8b43f7a52d8f3096750d0a5127a8ba0b9d75",
        HERE/"allen_observation_medium_inputs.py":"31e3277aa69c8e83cecbfc61133742947b3e5813428ad04caf2d9adfd36b8477"}
    for p,h in inputs.items():assert sha(p)==h,p
    payload=json.loads(NOISE.read_text());assert payload["code_sha256"]==inputs[HERE/"allen_observation_medium_inputs.py"]
    for name,key in [("allen_observation_medium_inputs_state.json","source_state_sha256"),("allen_observation_medium_cells.jsonl","journal_sha256"),("allen_observation_medium_used_blocks.json","used_blocks_sha256")]:
        path=HERE/name;assert sha(path)==payload[key],path;inputs[path]=payload[key]
    state=json.loads((HERE/"allen_observation_medium_inputs_state.json").read_text());assert state["status"]=="complete"
    assert state["remote"]==payload["remote"] and state["completed_cells"]==payload["wanted_cells"]
    inputs[NOISE]=sha(NOISE)
    original=json.loads((HERE/"allen_structural_metric_baseline_result.json").read_text())
    wanted=sorted({r["post_cell_id"] for r in original["records"]});cells=validate_noise(payload,wanted)
    with np.load(HERE/"allen_depth_probe_observation_arrays.npz",allow_pickle=False) as a:
        pair_ids=a["pair_id"];y=a["label"];donor=a["donor_id"];fold=a["fold"];context=a["context"];distance=a["distance_um"]
        raw3=a["observation_raw"];all_logits=np.full((len(y),len(MODELS)),np.nan)
        for i,name in enumerate(MODELS[:2]):all_logits[:,i]=a["out_of_fold_logits"][:,a["models"].tolist().index(name)]
    assert np.array_equal(pair_ids,[r["pair_id"] for r in original["records"]])
    with np.load(HERE/"allen_structural_metric_baseline_arrays.npz",allow_pickle=False) as a:
        assert np.array_equal(a["pair_id"],pair_ids)
        delta_um=(a["post_position_m"]-a["pre_position_m"])*1e6
    assert np.allclose(np.linalg.norm(delta_um,axis=1),distance)
    post_ids=np.array([r["post_cell_id"] for r in original["records"]]);noise=np.array([cells[cid]["mean_qc_pass_IC_noise_V"] if cells[cid]["mean_qc_pass_IC_noise_V"] is not None else np.nan for cid in post_ids])
    assert np.all(noise[np.isfinite(noise)]>0)
    raw=np.column_stack([raw3,np.log(noise)])
    fits=[];profiles=[];scores=[]
    for f in range(5):
        train=fold!=f;test=fold==f;assert set(donor[train]).isdisjoint(donor[test])
        prep=depth.fit_transform(raw[train]);tr=transform(raw[train],prep);te=transform(raw[test],prep)
        problem=ObservationProblem(context[train],y[train],tr)
        for model,feature in [("noise_context",np.empty((len(y),0))),("noise_radial",distance[:,None]/100.)]:
            solved=problem.fit(feature[train]);fitted=problem.pack(solved)
            all_logits[test,MODELS.index(model)]=predict(fitted,context[test],te,feature[test])
            fits.append(dict(model=model,fold=f,preprocessing=prep,**fitted))
            if model=="noise_radial":iso_params=solved["params"].copy();iso_params[-1]*=np.sqrt(2)
        for axis,label in [(2,"z"),(0,"x"),(1,"y")]:
            components=axis_model.squared_components(delta_um,axis)
            profile=axis_model.profile_radial(problem,components[train],initial=iso_params)
            w=profile["w"];model="noise_"+label+"_radial"
            all_logits[test,MODELS.index(model)]=predict(profile["fit"],context[test],te,axis_model.radial_feature(components[test],w))
            fits.append(dict(model=model,fold=f,axis=axis,preprocessing=prep,**profile["fit"],metric=axis_model.radial_metric(profile["fit"]["coefficients"][0],w,axis)))
            iso=predict(profile["boundaries"]["0.5"],context[test],te,axis_model.radial_feature(components[test],.5))
            difference=float(np.max(abs(iso-all_logits[test,MODELS.index("noise_radial")])))
            assert difference<1e-3,difference
            profiles.append(dict(model=model,fold=f,axis=axis,**profile,isotropic_logit_max_difference=difference))
            if axis==2:
                for boundary,bmodel in [(0.,"noise_z_plane_radial"),(1.,"noise_z_axis_radial")]:
                    fitted=profile["boundaries"][str(boundary)]
                    all_logits[test,MODELS.index(bmodel)]=predict(fitted,context[test],te,axis_model.radial_feature(components[test],boundary))
                    fits.append(dict(model=bmodel,fold=f,axis=axis,preprocessing=prep,**fitted,metric=axis_model.radial_metric(fitted["coefficients"][0],boundary,axis)))
            print("NOISE_AXIS",f,label,"profile_points",len(profile["profile"]),"training_w",w,flush=True)
        for i,model in enumerate(MODELS):
            ll,br=baseline.losses(y[test],all_logits[test,i]);scores.append(dict(model=model,fold=f,log_loss=float(ll.mean()),brier=float(br.mean())))
    assert np.isfinite(all_logits).all();ll,br=baseline.losses(y[:,None],all_logits)
    comparisons=[]
    for candidate,reference in [("noise_context","depth_count_context"),("noise_radial","depth_count_radial"),("noise_radial","noise_context"),
        ("noise_z_radial","noise_radial"),("noise_z_radial","noise_z_plane_radial"),("noise_x_radial","noise_radial"),("noise_y_radial","noise_radial"),
        ("noise_z_plane_radial","noise_radial"),("noise_z_axis_radial","noise_radial")]:
        a=MODELS.index(candidate);b=MODELS.index(reference)
        comparisons.append(dict(candidate=candidate,reference=reference,log_loss_difference=baseline.cluster_comparison(donor,ll[:,a]-ll[:,b]),brier_difference=baseline.cluster_comparison(donor,br[:,a]-br[:,b])))
    before=ll[:,1]-ll[:,0];after=ll[:,3]-ll[:,2]
    valid=noise[np.isfinite(noise)];cell_values=np.array([r["mean_qc_pass_IC_noise_V"] for r in cells.values() if r["mean_qc_pass_IC_noise_V"] is not None])
    missing_rows=[r for r in cells.values() if r["mean_qc_pass_IC_noise_V"] is None]
    with ARRAYS.open("xb") as stream:np.savez_compressed(stream,pair_id=pair_ids,label=y,donor_id=donor,fold=fold,context=context,delta_um=delta_um,
        observation_raw=raw,post_cell_id=post_ids,noise_V=noise,models=np.array(MODELS),out_of_fold_logits=all_logits)
    result=dict(version="allen-noise-axis-observation-v1",code_sha256=sha(Path(__file__)),input_sha256={p.relative_to(ROOT).as_posix():h for p,h in inputs.items()},arrays_sha256=sha(ARRAYS),
        settings=dict(feature_names=FEATURE_NAMES,context_ridge=1.,observation_ridge=1.,distance_ridge=0.,length_unit_um=100.,
            noise_units="Natural log of numerical volts divided by 1 V; finite positive producer mean only",
            noise_scope="All stored QC-pass IC records of postsynaptic cell; >=2 records, arithmetic mean, no holding or chronology separation; not synaptic standard error",
            preprocessing="Observed training fold means/SD, zero standardized missing plus depth/count/noise indicators; never discard cohort rows",
            profile_grid=axis_model.GRID,profile_refinement_xatol=axis_model.PROFILE_XTOL,parameter_selection="Training penalized likelihood only; no test-based axis or shape selection",
            primary_comparison="Noise Z-axis radial versus noise isotropic radial and exact XY boundary; distance value within same noise observation model",
            evaluation="Previously exposed same cohort and internal donor folds; no external confirmation or calibrated sensitivity",raw_axes_not_pia_normals=True),
        summary=dict(pairs=len(y),positive=int(y.sum()),donors=len(set(donor)),collected_postsynaptic_cells=len(cells),
            valid_noise_cells=len(cell_values),missing_noise_cells=len(missing_rows),valid_noise_pairs=len(valid),missing_noise_pairs=int(np.isnan(noise).sum()),
            missing_noise_cell_reasons=dict(fewer_than_two_QC_IC=sum(r["qc_pass_IC_count"]<2 for r in missing_rows),
                at_least_two_but_nonfinite_or_nonpositive=sum(r["qc_pass_IC_count"]>=2 for r in missing_rows)),
            noise_cell_quantile_probs=[0,.01,.5,.99,1],noise_cell_quantiles_V=np.quantile(cell_values,[0,.01,.5,.99,1]).tolist() if len(cell_values) else [],
            scores=[dict(model=model,log_loss=float(ll[:,i].mean()),brier=float(br[:,i].mean())) for i,model in enumerate(MODELS)]),
        fits=fits,radial_profiles=profiles,fold_scores=scores,comparisons=comparisons,
        radial_log_loss_gain_change=baseline.cluster_comparison(donor,after-before),
        cell_noise_summary=[{k:v for k,v in r.items() if k!="qc_pass_IC_records"} for r in cells.values()],
        claim_ceiling="L1 selected labels and source metadata; L0 retrospective predictive models; no true detection rates, pia normal, physical power, hormone pathway, or unique biological metric")
    with OUTPUT.open("x",encoding="utf-8") as stream:json.dump(result,stream,indent=2,allow_nan=False);stream.write("\n")
    print(json.dumps(result["summary"]))


if __name__=="__main__":main()
