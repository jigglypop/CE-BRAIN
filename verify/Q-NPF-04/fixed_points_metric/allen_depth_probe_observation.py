"""Same-cohort internal prediction with depth and final probe-count summaries.

These are retrospective acquisition covariates, not calibrated sensitivity or
pre-acquisition inputs. The independent medium-noise collection is not consumed.
"""
import hashlib
import json
from pathlib import Path
import sqlite3

import numpy as np
from scipy.optimize import minimize
from scipy.special import expit

import allen_structural_metric_baseline as baseline

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
OUTPUT=HERE/"allen_depth_probe_observation_result.json"
ARRAYS=HERE/"allen_depth_probe_observation_arrays.npz"
MODELS=["context","radial","depth_context","depth_radial","depth_count_context","depth_count_radial"]
FEATURES=["mean_depth_per_100um","mean_depth_per_100um_squared","log1p_capped_final_count"]


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def source_features(pre_depth_m,post_depth_m,pre_class,n_ex,n_in):
    depths=[pre_depth_m,post_depth_m]
    valid=all(v is not None and np.isfinite(v) for v in depths)
    mean=float(np.mean(depths))*1e6 if valid else None
    reason="valid" if mean is not None and 0<=mean<=300 else "missing_depth" if mean is None else "mean_outside_0_300um"
    depth=mean/100 if reason=="valid" else np.nan
    n=n_ex if pre_class=="ex" else n_in if pre_class=="in" else None
    count_valid=n is not None and np.isfinite(n) and n>=0
    count=min(float(n),800.) if count_valid else None
    return np.array([depth,depth**2,np.log1p(count) if count is not None else np.nan]),dict(
        pre_depth_m=pre_depth_m,post_depth_m=post_depth_m,raw_mean_depth_um=mean,depth_status=reason,
        pre_nonsynaptic_class=pre_class,selected_final_count=n,capped_final_count=count,
        count_status="valid" if count_valid else "unknown_class_or_missing_count")


def fit_transform(raw):
    valid=np.isfinite(raw); means=[];scales=[]
    for j in range(raw.shape[1]):
        values=raw[valid[:,j],j]
        means.append(float(np.mean(values)) if len(values) else 0.)
        sd=float(np.std(values)) if len(values) else 0.
        scales.append(sd if sd>1e-12 else 1.)
    return dict(mean=means,scale=scales,valid_training_counts=valid.sum(axis=0).tolist())


def transform(raw, fitted):
    valid=np.isfinite(raw)
    z=np.where(valid,(raw-np.array(fitted["mean"]))/np.array(fitted["scale"]),0.)
    # Depth and depth squared share one missing indicator; count has its own.
    missing=(~valid[:,[0]]).astype(float)
    if raw.shape[1]==3:missing=np.column_stack([missing,(~valid[:,2]).astype(float)])
    return np.column_stack([z,missing])


class Problem:
    def __init__(self,context,y,features,distance):
        self.categories=sorted(set(context));mapping={c:i for i,c in enumerate(self.categories)}
        self.group=np.array([mapping[c] for c in context]);self.y=np.asarray(y,float)
        self.k=len(self.categories);self.features=features;self.distance=distance
        self.p=features.shape[1];self.n=len(y)

    def objective(self,params):
        offsets=params[1:1+self.k];coef=params[1+self.k:1+self.k+self.p]
        logits=params[0]+offsets[self.group]+self.features@coef
        if self.distance is not None:logits=logits-params[-1]*self.distance/100.
        residual=expit(logits)-self.y
        value=(np.sum(np.logaddexp(0,logits)-self.y*logits)+.5*(offsets@offsets+coef@coef))/self.n
        grad=np.r_[residual.sum(),np.bincount(self.group,weights=residual,minlength=self.k)+offsets,self.features.T@residual+coef]
        if self.distance is not None:grad=np.r_[grad,-residual@self.distance/100.]
        return value,grad/self.n

    def fit(self):
        initial=np.zeros(1+self.k+self.p+(self.distance is not None));mean=np.clip(self.y.mean(),1e-6,1-1e-6)
        initial[0]=np.log(mean/(1-mean))
        bounds=[(None,None)]*(1+self.k+self.p)
        if self.distance is not None:bounds.append((0,None))
        solved=minimize(self.objective,initial,jac=True,method="L-BFGS-B",bounds=bounds,
                        options=dict(maxiter=2000,ftol=1e-12,gtol=1e-8,maxls=40))
        if not solved.success:raise RuntimeError(str(solved.message))
        params=solved.x;gamma=float(params[-1]) if self.distance is not None else None
        return dict(intercept=float(params[0]),context_offsets=dict(zip(self.categories,params[1:1+self.k].tolist())),
            observation_coefficients=params[1+self.k:1+self.k+self.p].tolist(),radial_gamma=gamma,
            metric_diagonal_per_um2=[(gamma/100.)**2]*3 if gamma is not None else None,
            metric_SPD=bool(gamma is not None and gamma>0),
            objective=float(solved.fun),iterations=int(solved.nit),gradient_max=float(np.max(abs(solved.jac))))


def predict(fitted,context,features,distance):
    logits=fitted["intercept"]+np.array([fitted["context_offsets"].get(c,0.) for c in context])+features@np.array(fitted["observation_coefficients"])
    if fitted["radial_gamma"] is not None:logits-=fitted["radial_gamma"]*distance/100.
    return logits


def detection_equivalence(delta_over_L0):
    """Conditional mathematical witness, not fitted biological detection rates."""
    d=np.asarray(delta_over_L0,float)
    g1=np.eye(3);g2=np.diag([1.,.5,.25])
    pi1=expit(-np.einsum("ni,ij,nj->n",d,g1,d))
    pi2=expit(-np.einsum("ni,ij,nj->n",d,g2,d))
    s1=np.full(len(d),.8);s2=.8*pi1/pi2
    return g1,g2,pi1,pi2,s1,s2


def main():
    if OUTPUT.exists() or ARRAYS.exists():raise FileExistsError("Completed observation artifacts are immutable")
    inputs={
        HERE/"allen_structural_metric_baseline.py":"eeb736602e86b29fee7839bc4c46a3cdbdb97439a8d19fe3588468d4ec7c8c23",
        HERE/"allen_structural_metric_baseline_result.json":"d13c396980d7e509d8206e2324b1be6ca8a0fcdfe666df7864435391e72e9e14",
        HERE/"allen_structural_metric_baseline_arrays.npz":"c82fd88911fa13d893f6a08816ca8b43f7a52d8f3096750d0a5127a8ba0b9d75",
        ROOT/"data/external/allen_synphys_r21/synphys_r2.1_small.sqlite":"7372499fdd874f057565080d5769baaf2659ef39d9f3bc3c7147dd1e1c280a53",
        ROOT/"data/external/allen_synphys_r21/producer_connectivity/545a990ee171e6c0d23dd4bba413e1ccbf2f0853/connectivity.py":"9c13f009f9d1e08b5baf4ce9c176f406f99e0bfc216bc057f16f0b2d7d5a3aca"}
    for p,h in inputs.items():assert sha(p)==h,p
    original=json.loads((HERE/"allen_structural_metric_baseline_result.json").read_text())
    with np.load(HERE/"allen_structural_metric_baseline_arrays.npz",allow_pickle=False) as a:
        y=a["label"];context=a["context"];donor=a["donor_id"];fold=a["fold"];pair_ids=a["pair_id"];distance=a["distance_um"]
        delta_um=(a["post_position_m"]-a["pre_position_m"])*1e6
        logits=np.full((len(y),len(MODELS)),np.nan)
        for i,name in enumerate(["no_distance","radial_link"]):logits[:,i]=a["out_of_fold_logits"][:,a["models"].tolist().index(name)]
    assert np.array_equal(pair_ids,[r["pair_id"] for r in original["records"]])
    db=ROOT/"data/external/allen_synphys_r21/synphys_r2.1_small.sqlite"
    with sqlite3.connect(db.resolve().as_uri()+"?mode=ro",uri=True) as conn:
        cells={r[0]:dict(depth=r[1],cell_class=r[2],position=r[3],experiment_id=r[4]) for r in conn.execute("select id,depth,cell_class_nonsynaptic,position,experiment_id from cell")}
        missing_tables={table:conn.execute("select count(*) from "+table).fetchone()[0] for table in ["patch_clamp_recording","synapse_prediction","multi_patch_probe"]}
    rows=[];raw=[]
    for r in original["records"]:
        pre=cells[r["pre_cell_id"]];post=cells[r["post_cell_id"]]
        cls=pre["cell_class"] or "unknown";assert cls==r["context"].split("|")[0]
        values,detail=source_features(pre["depth"],post["depth"],cls,r["n_ex_test_spikes"],r["n_in_test_spikes"])
        raw.append(values);rows.append(dict(pair_id=r["pair_id"],**detail))
    raw=np.array(raw);fits=[];scores=[]
    for f in range(5):
        train=fold!=f;test=fold==f;assert set(donor[train]).isdisjoint(donor[test])
        for model in MODELS[2:]:
            columns=3 if "count" in model else 2
            prep=fit_transform(raw[train,:columns]);tr=transform(raw[train,:columns],prep);te=transform(raw[test,:columns],prep)
            radial=model.endswith("radial")
            fitted=Problem(context[train],y[train],tr,distance[train] if radial else None).fit()
            logits[test,MODELS.index(model)]=predict(fitted,context[test],te,distance[test])
            fits.append(dict(model=model,fold=f,preprocessing=prep,feature_names=FEATURES[:columns]+["depth_missing"]+(["count_missing"] if columns==3 else []),**fitted))
        for i,model in enumerate(MODELS):
            ll,br=baseline.losses(y[test],logits[test,i]);scores.append(dict(model=model,fold=f,log_loss=float(ll.mean()),brier=float(br.mean())))
        print("DEPTH_PROBE_FOLD",f,flush=True)
    assert np.isfinite(logits).all();ll,br=baseline.losses(y[:,None],logits)
    comparisons=[]
    for a,b in [(1,0),(3,2),(5,4),(2,0),(3,1),(4,2),(5,3),(5,1)]:
        comparisons.append(dict(candidate=MODELS[a],reference=MODELS[b],log_loss_difference=baseline.cluster_comparison(donor,ll[:,a]-ll[:,b]),
            brier_difference=baseline.cluster_comparison(donor,br[:,a]-br[:,b])))
    interactions=[]
    for a,b in [(3,2),(5,4)]:
        interactions.append(dict(adjusted_radial=MODELS[a],adjusted_context=MODELS[b],
            log_loss_gain_change=baseline.cluster_comparison(donor,(ll[:,a]-ll[:,b])-(ll[:,1]-ll[:,0])),
            brier_gain_change=baseline.cluster_comparison(donor,(br[:,a]-br[:,b])-(br[:,1]-br[:,0]))))
    cell_ids=sorted({r[k] for r in original["records"] for k in ["pre_cell_id","post_cell_id"]})
    depths=[dict(cell_id=cid,depth_um=cells[cid]["depth"]*1e6,experiment_id=cells[cid]["experiment_id"]) for cid in cell_ids if cells[cid]["depth"] is not None and np.isfinite(cells[cid]["depth"])]
    by_experiment={}
    for cid in cell_ids:
        c=cells[cid]
        if c["depth"] is None or not np.isfinite(c["depth"]):continue
        by_experiment.setdefault(c["experiment_id"],[]).append(c["depth"]+json.loads(c["position"])[2])
    identity_max=max(float(np.ptp(v)) for v in by_experiment.values())
    witness=detection_equivalence(delta_um/100.)
    with ARRAYS.open("xb") as stream:np.savez_compressed(stream,pair_id=pair_ids,label=y,donor_id=donor,fold=fold,context=context,distance_um=distance,
        observation_raw=raw,models=np.array(MODELS),out_of_fold_logits=logits)
    result=dict(version="allen-depth-probe-observation-v1",code_sha256=sha(Path(__file__)),input_sha256={p.relative_to(ROOT).as_posix():h for p,h in inputs.items()},arrays_sha256=sha(ARRAYS),
        settings=dict(context_ridge=1.,observation_ridge=1.,distance_ridge=0.,length_unit_um=100.,depth_basis="d/100um and its square; source valid mean 0..300um",count_basis="log1p(min(n,800)); unknown nonsynaptic class remains missing",
            preprocessing="Observed training-fold mean and SD; zero standardized missing value plus missing flag; no evaluation statistics",
            primary_comparison="Radial versus context within identical depth-count observation covariates; contrast of distance log-loss gains",
            evaluation="Previously exposed same cohort and donor folds; retrospective predictive development; no new external confirmation",
            input_timing="Final counts and acquisition depth can reflect selection; no chronology or pretreatment independence assumed",
            medium_noise="Not used; absent in small database, separate collection in progress at analysis creation"),
        summary=dict(pairs=len(y),positive=int(y.sum()),donors=len(set(donor)),
            pair_depth_status={key:sum(r["depth_status"]==key for r in rows) for key in sorted({r["depth_status"] for r in rows})},
            pair_count_missing=sum(r["capped_final_count"] is None for r in rows),pair_count_above_800=sum(r["selected_final_count"] is not None and r["selected_final_count"]>800 for r in rows),
            unique_cells=len(cell_ids),cells_with_depth=len(depths),negative_depth_cells=sum(r["depth_um"]<0 for r in depths),depth_above_300um_cells=sum(r["depth_um"]>300 for r in depths),
            depth_plus_z_within_experiment_max_range_m=identity_max,small_database_recording_table_rows=missing_tables,
            scores=[dict(model=model,log_loss=float(ll[:,i].mean()),brier=float(br[:,i].mean())) for i,model in enumerate(MODELS)]),
        fits=fits,fold_scores=scores,comparisons=comparisons,distance_gain_changes=interactions,records=rows,
        atypical_depth_cells=[r for r in depths if r["depth_um"]<0 or r["depth_um"]>300],
        conditional_detection_witness=dict(g1_L0_squared=witness[0].tolist(),g2_L0_squared=witness[1].tolist(),false_positive=0.,
            sensitivity1=.8,sensitivity2_min_max=[float(witness[5].min()),float(witness[5].max())],
            observed_probability_max_difference=float(np.max(abs(witness[2]*witness[4]-witness[3]*witness[5]))),
            scope="Constructed observational equivalence on fixed points; not empirical sensitivities or the fitted radial model"),
        claim_ceiling="L1 selected curated labels, L0 modeling and conditional mathematics; no calibrated latent connectivity, hormone mechanism or unique biological metric")
    with OUTPUT.open("x",encoding="utf-8") as stream:json.dump(result,stream,indent=2,allow_nan=False);stream.write("\n")
    print(json.dumps(result["summary"]))


if __name__=="__main__":main()
