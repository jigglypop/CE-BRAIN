"""Donor-grouped comparison of fixed 3D distance and curated chemical labels.

The interior quadratic model has g=beta*I/(100 um)^2. Beta=0 is a
non-metric boundary, not an SPD discovery. Anatomical 2D distances are audited
but never mixed with raw 3D positions. This is internal development validation.
"""
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import sqlite3

import numpy as np
from scipy.optimize import minimize
from scipy.special import expit

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
BASE=ROOT/"data/external/allen_synphys_r21"
OUTPUT=HERE/"allen_structural_metric_baseline_result.json"
WAVES=HERE/"allen_structural_metric_baseline_arrays.npz"
L0_UM=100.
MAX_DISTANCE_UM=1000.  # Local candidate domain, fixed after geometry audit and before held-out scoring.
MODELS=["no_distance","quadratic_metric","radial_link","signed_quadratic","shape_control"]
DONOR_PATTERN=r'(?P<pedigree1>.*)-(?P<donor_id>\d{6,7})(?P<pedigree2>-[^\.]+)?\.(?P<section_num>\d{2})(\.(?P<orientation_num>\d{2}))?$'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def donor_id(name):
    match=re.match(DONOR_PATTERN,name or "")
    return match.group("donor_id") if match else None


def fold_for_donor(donor):
    return int(hashlib.sha256(("fixed-neuron-structural-v1:"+str(donor)).encode()).hexdigest()[:16],16)%5


def probed(pre_class,n_ex,n_in):
    ex=n_ex is not None and n_ex>10
    inh=n_in is not None and n_in>10
    return ex if pre_class=="ex" else inh if pre_class=="in" else ex and inh


def point(value,dimension):
    try:
        result=np.asarray(json.loads(value),float)
        return result if result.shape==(dimension,) and np.isfinite(result).all() else None
    except (TypeError,ValueError):return None


def features(distance_um,model):
    s=np.asarray(distance_um,float)/L0_UM
    if model=="no_distance":return np.empty((len(s),0))
    if model in ["quadratic_metric","signed_quadratic"]:return (s*s)[:,None]
    if model=="radial_link":return s[:,None]
    if model=="shape_control":return np.column_stack([s]+[np.maximum(0,s-k) for k in [.5,1.,1.5,2.,3.]])
    raise ValueError(model)


def fit_model(distance_um,context,y,model):
    categories=sorted(set(context));mapping={c:i for i,c in enumerate(categories)}
    group=np.array([mapping[c] for c in context]);f=features(distance_um,model)
    k=len(categories);n=len(y);y=np.asarray(y,float)
    initial=np.zeros(1+k+f.shape[1]);mean=np.clip(y.mean(),1e-6,1-1e-6)
    initial[0]=np.log(mean/(1-mean))
    def objective(params):
        offsets=params[1:1+k];beta=params[1+k:]
        logits=params[0]+offsets[group]-f@beta
        residual=expit(logits)-y
        penalty=.5*np.sum(offsets**2)
        beta_penalty=beta if model=="shape_control" else np.zeros_like(beta)
        if model=="shape_control":penalty+=.5*np.sum(beta**2)
        loss=(np.sum(np.logaddexp(0,logits)-y*logits)+penalty)/n
        grad=np.r_[residual.sum(),np.bincount(group,weights=residual,minlength=k)+offsets,-f.T@residual+beta_penalty]/n
        return loss,grad
    constrained=model in ["quadratic_metric","radial_link"]
    bounds=[(None,None)]*(1+k)+([(0,None)] if constrained else [(None,None)])*f.shape[1]
    solved=minimize(objective,initial,jac=True,method="L-BFGS-B",bounds=bounds,
                    options={"maxiter":2000,"ftol":1e-12,"gtol":1e-8,"maxls":40})
    if not solved.success:
        raise RuntimeError(f"{model}: {solved.message}; iterations={solved.nit}; objective={solved.fun}; gradient={np.max(abs(solved.jac))}; beta={solved.x[1+k:]}")
    beta=solved.x[1+k:]
    metric=(dict(beta=float(beta[0]),g_diagonal_per_um2=[float(beta[0]/L0_UM**2)]*3,
                 interior_SPD=bool(beta[0]>1e-8),length_scale_um=float(L0_UM/np.sqrt(beta[0])) if beta[0]>0 else None)
            if model=="quadratic_metric" else None)
    return dict(model=model,intercept=float(solved.x[0]),context_offsets=dict(zip(categories,solved.x[1:1+k].tolist())),
        distance_coefficients=beta.tolist(),context_penalty=1.,shape_penalty=1. if model=="shape_control" else 0.,
        iterations=int(solved.nit),optimizer_message=str(solved.message),gradient_max=float(np.max(abs(solved.jac))),
        metric=metric)


def predict(fitted,distance_um,context):
    offsets=np.array([fitted["context_offsets"].get(c,0.) for c in context])
    return fitted["intercept"]+offsets-features(distance_um,fitted["model"])@np.array(fitted["distance_coefficients"])


def losses(y,logits):
    return np.logaddexp(0,logits)-y*logits,(expit(logits)-y)**2


def cluster_comparison(donors,difference,seed=20260906):
    unique,group=np.unique(donors,return_inverse=True)
    counts=np.bincount(group);sums=np.bincount(group,weights=difference)
    draws=np.random.default_rng(seed).integers(0,len(unique),size=(2000,len(unique)))
    weighted=sums[draws].sum(axis=1)/counts[draws].sum(axis=1)
    equal=(sums/counts)[draws].mean(axis=1)
    return dict(pair_weighted_mean=float(np.mean(difference)),pair_weighted_cluster_percentile95=np.quantile(weighted,[.025,.975]).tolist(),
        equal_donor_mean=float(np.mean(sums/counts)),equal_donor_percentile95=np.quantile(equal,[.025,.975]).tolist(),
        donor_count=len(unique),bootstrap_draws=2000,
        uncertainty_scope="Donor resampling of fixed out-of-fold scores; no refitting, no full model-selection uncertainty")


def extract(db):
    query="""SELECT p.id,p.experiment_id,e.slice_id,s.lims_specimen_name,p.pre_cell_id,p.post_cell_id,
        p.has_synapse,p.n_ex_test_spikes,p.n_in_test_spikes,p.distance,p.lateral_distance,p.vertical_distance,
        a.position pre_position,b.position post_position,a.cell_class_nonsynaptic pre_class,
        b.cell_class_nonsynaptic post_class,ca.cortical_layer pre_layer,cb.cortical_layer post_layer,
        ca.position pre_cortical_position,cb.position post_cortical_position
        FROM pair p JOIN experiment e ON e.id=p.experiment_id JOIN slice s ON s.id=e.slice_id
        JOIN cell a ON a.id=p.pre_cell_id JOIN cell b ON b.id=p.post_cell_id
        LEFT JOIN cortical_cell_location ca ON ca.cell_id=a.id
        LEFT JOIN cortical_cell_location cb ON cb.cell_id=b.id
        WHERE s.species='mouse' AND e.target_region='VisP' ORDER BY p.id"""
    rejected=Counter();records=[];p3=[];q3=[];geometry=[];outside_domain=[]
    with sqlite3.connect(db.resolve().as_uri()+"?mode=ro",uri=True) as con:
        con.row_factory=sqlite3.Row
        raw_rows=[dict(r) for r in con.execute(query)]
    for row in raw_rows:
        if row["has_synapse"] not in [0,1]:rejected["label_missing"]+=1;continue
        donor=donor_id(row["lims_specimen_name"])
        if donor is None:rejected["donor_name_unparsed"]+=1;continue
        if not probed(row["pre_class"],row["n_ex_test_spikes"],row["n_in_test_spikes"]):
            rejected["insufficient_QC_pass_test_spikes"]+=1;continue
        pre=point(row["pre_position"],3);post=point(row["post_position"],3)
        if pre is None or post is None:rejected["missing_3D_position"]+=1;continue
        distance=float(np.linalg.norm(pre-post))
        if distance<=0:rejected["coincident_3D_positions"]+=1;continue
        stored=row["distance"]
        if stored is None or not np.isfinite(stored):rejected["stored_distance_missing"]+=1;continue
        if not np.isclose(distance,stored,rtol=1e-5,atol=1e-9):rejected["stored_distance_mismatch"]+=1;continue
        if distance*1e6>MAX_DISTANCE_UM:
            rejected["outside_nominal_local_1mm_domain"]+=1
            outside_domain.append(dict(pair_id=row["id"],experiment_id=row["experiment_id"],distance_um=distance*1e6,
                pre_position_m=pre.tolist(),post_position_m=post.tolist()))
            continue
        pre_class=row["pre_class"] or "unknown";post_class=row["post_class"] or "unknown"
        context="|".join([pre_class,row["pre_layer"] or "unknown",post_class,row["post_layer"] or "unknown"])
        records.append(dict(pair_id=row["id"],experiment_id=row["experiment_id"],slice_id=row["slice_id"],donor_id=donor,
            donor_source="Official mouse specimen-name parser; not an independent donor registry query",
            specimen_name=row["lims_specimen_name"],pre_cell_id=row["pre_cell_id"],post_cell_id=row["post_cell_id"],
            label=row["has_synapse"],context=context,distance_um=distance*1e6,fold=fold_for_donor(donor),
            n_ex_test_spikes=row["n_ex_test_spikes"],n_in_test_spikes=row["n_in_test_spikes"]))
        p3.append(pre);q3.append(post)
        pre2=point(row["pre_cortical_position"],2);post2=point(row["post_cortical_position"],2)
        lat=row["lateral_distance"];vert=row["vertical_distance"]
        if pre2 is not None and post2 is not None and lat is not None and vert is not None and np.isfinite([lat,vert]).all():
            d2=float(np.linalg.norm(pre2-post2))
            if d2>0:
                geometry.append(dict(pair_id=row["id"],distance_3D_um=distance*1e6,distance_2D_um=d2*1e6,
                    distance_3D_over_2D=distance/d2,projected_sum_squared_um2=(lat*lat+vert*vert)*1e12,
                    squared_2D_reconstruction_error_um2=(lat*lat+vert*vert-d2*d2)*1e12))
    assert len(records)+sum(rejected.values())==len(raw_rows)
    assert len({r["pair_id"] for r in records})==len(records)
    return records,np.array(p3),np.array(q3),dict(total_mouse_VisP_rows=len(raw_rows),rejected=dict(rejected),
        outside_domain=outside_domain,domain_revision="Unbounded first fit failed numerically on impossible-scale coordinates before held-out scores were computed; nominal <=1 mm local domain then fixed. No coordinate rescaling."),geometry


def main():
    if OUTPUT.exists() or WAVES.exists():raise FileExistsError("Completed structural comparison artifacts are immutable")
    db=BASE/"synphys_r2.1_small.sqlite"
    hashes={db:"7372499fdd874f057565080d5769baaf2659ef39d9f3bc3c7147dd1e1c280a53",
        ROOT/"verify/Q-NPF-04/allen_synphys/qc_sources/lims.py":"af1eff74b14ed4344f3cc0ff3e3dc7a536a0e0435005dc7841b86f264cedd2d8",
        BASE/"producer_connectivity/545a990ee171e6c0d23dd4bba413e1ccbf2f0853/connectivity.py":"9c13f009f9d1e08b5baf4ce9c176f406f99e0bfc216bc057f16f0b2d7d5a3aca"}
    for path,expected in hashes.items():assert sha(path)==expected
    records,pre,post,eligibility,geometry=extract(db)
    y=np.array([r["label"] for r in records]);distance=np.array([r["distance_um"] for r in records])
    context=np.array([r["context"] for r in records]);donors=np.array([r["donor_id"] for r in records]);folds=np.array([r["fold"] for r in records])
    assert len(set(donors))>=25 and set(folds)==set(range(5))
    fits=[];fold_scores=[];all_logits=np.full((len(records),len(MODELS)),np.nan)
    for fold in range(5):
        train=folds!=fold;evaluate=folds==fold
        assert set(donors[train]).isdisjoint(donors[evaluate])
        assert len(set(y[train]))==2 and len(set(y[evaluate]))==2
        for column,model in enumerate(MODELS):
            fitted=fit_model(distance[train],context[train],y[train],model)
            logits=predict(fitted,distance[evaluate],context[evaluate]);ll,br=losses(y[evaluate],logits)
            all_logits[evaluate,column]=logits
            fits.append(dict(fold=fold,train_pairs=int(sum(train)),train_donors=len(set(donors[train])),**fitted))
            fold_scores.append(dict(fold=fold,model=model,test_pairs=int(sum(evaluate)),test_positive=int(y[evaluate].sum()),
                test_donors=len(set(donors[evaluate])),unseen_context_pairs=int(sum(c not in fitted["context_offsets"] for c in context[evaluate])),
                log_loss=float(ll.mean()),brier=float(br.mean())))
        print("STRUCTURAL_FOLD",fold,"train",int(sum(train)),"test",int(sum(evaluate)),flush=True)
    assert np.isfinite(all_logits).all()
    all_ll,all_brier=losses(y[:,None],all_logits)
    comparisons=[]
    for candidate,reference in [("quadratic_metric","no_distance"),("radial_link","no_distance"),
            ("signed_quadratic","quadratic_metric"),("radial_link","quadratic_metric"),("shape_control","quadratic_metric")]:
        a=MODELS.index(candidate);b=MODELS.index(reference)
        comparisons.append(dict(candidate=candidate,reference=reference,
            log_loss_difference=cluster_comparison(donors,all_ll[:,a]-all_ll[:,b]),
            brier_difference=cluster_comparison(donors,all_brier[:,a]-all_brier[:,b])))
    by_pair={(r["pre_cell_id"],r["post_cell_id"]):r["label"] for r in records}
    reciprocal=[(value,by_pair[(b,a)]) for (a,b),value in by_pair.items() if a<b and (b,a) in by_pair]
    with WAVES.open("xb") as stream:
        np.savez_compressed(stream,pre_position_m=pre,post_position_m=post,label=y,donor_id=donors,fold=folds,
            pair_id=np.array([r["pair_id"] for r in records]),distance_um=distance,context=context,
            models=np.array(MODELS),out_of_fold_logits=all_logits,out_of_fold_probability=expit(all_logits))
    result=dict(version="allen-structural-metric-baseline-v1",code_sha256=sha(Path(__file__)),
        inputs_sha256={path.relative_to(ROOT).as_posix():value for path,value in hashes.items()},arrays_sha256=sha(WAVES),
        settings=dict(primary_model="quadratic_metric",reference="no_distance",length_unit_um=L0_UM,
            maximum_local_distance_um=MAX_DISTANCE_UM,
            fold_rule="sha256 fixed-neuron-structural-v1:donor first16hex mod5",folds=5,
            context="Ordered pre/post nonsynaptic class and cortical layer; unknown retained; unseen context deviation=0",
            context_ridge=1.,shape_control_ridge=1.,shape_knots_um=[50,100,150,200,300],hyperparameter_search=False,
            primary_endpoint="Out-of-fold log loss difference; Brier and fixed-prediction donor bootstrap supplementary",
            coordinate_scope="Raw 3D soma positions only for prediction; 2D histology distances audited separately",
            beta_zero_is_metric_ineligible=True,claim_scope="Curated labels among selected QC-probed mouse VisP pairs"),
        eligibility=eligibility,summary=dict(pairs=len(records),positive=int(y.sum()),donors=len(set(donors)),
            experiments=len({r["experiment_id"] for r in records}),slices=len({r["slice_id"] for r in records}),
            contexts=len(set(context)),distance_min_median_max_um=np.quantile(distance,[0,.5,1]).tolist(),
            reciprocal_pairs=len(reciprocal),discordant_reciprocal_pairs=sum(a!=b for a,b in reciprocal)),
        records=records,geometry_audit=geometry,model_fits=fits,fold_scores=fold_scores,
        overall_scores=[dict(model=model,log_loss=float(all_ll[:,i].mean()),brier=float(all_brier[:,i].mean())) for i,model in enumerate(MODELS)],
        comparisons=comparisons,
        claim_ceiling="L1 existing curated observations and L0 candidate/development inference; no unique anisotropic metric, physical power, hormone or causal circuit identification")
    with OUTPUT.open("x",encoding="utf-8") as stream:
        json.dump(result,stream,indent=2,allow_nan=False);stream.write("\n")
    print(json.dumps(dict(summary=result["summary"],scores=result["overall_scores"])))


if __name__=="__main__":main()
