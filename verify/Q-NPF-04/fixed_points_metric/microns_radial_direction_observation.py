"""Fixed radial link: direction costs versus reconstruction-stratum attenuation.

Same frozen nodes, annotations and endpoint-disjoint blocks. Shape selection uses
training loss only. Log-ratio bounds define a restricted positive diagonal family;
neither a global optimum over all SPD matrices nor a biological metric is claimed.
"""
import hashlib
import itertools
import json
from pathlib import Path

import numpy as np
from scipy.optimize import minimize
from scipy.special import expit

import microns_node_metric as base
from microns_schur_solver import fit_newton

HERE=Path(__file__).resolve().parent
RESULT=HERE/"microns_radial_direction_observation_result.json"
ARRAYS=HERE/"microns_radial_direction_observation_arrays.npz"
BLOCK_LOG=HERE/"microns_radial_direction_observation_blocks.jsonl"
LOG_BOUND=float(np.log(64.))
COARSE_POINTS=list(itertools.product([-float(np.log(4.)),0.,float(np.log(4.))],repeat=2))
SUFFIXES=["common_isotropic","common_directional","stratum_isotropic","stratum_directional","stratum_signed_isotropic"]
MODELS=[prefix+"_"+suffix for prefix in ["strategy","typed"] for suffix in SUFFIXES]


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def radial(theta,squared):
    weights=np.array([np.exp(theta[0]),1.,np.exp(theta[1])])
    weighted=squared*weights;distance=np.sqrt(weighted.sum(axis=1))
    derivative=np.zeros((len(distance),2));positive=distance>0
    derivative[positive]=weighted[positive][:,[0,2]]/(2*distance[positive,None])
    return distance,derivative,weights


def features(distance,strata,split_gain):
    if not split_gain:return distance[:,None]
    if set(np.unique(strata))!={0,1,2,3}:raise ValueError("All four fixed strata are required in training")
    return distance[:,None]*(strata[:,None]==np.arange(4)[None,:])


def parameters(problem,fitted):
    return np.r_[fitted["intercept"],[fitted["context_offsets"][str(c)] for c in problem.categories],fitted["coefficients"]]


def projected_shape_gradient(theta,gradient):
    projected=np.array(gradient,copy=True)
    projected[np.asarray(theta)<=-LOG_BOUND]=np.minimum(projected[np.asarray(theta)<=-LOG_BOUND],0)
    projected[np.asarray(theta)>=LOG_BOUND]=np.maximum(projected[np.asarray(theta)>=LOG_BOUND],0)
    return projected


class Profile:
    def __init__(self,context,y,squared,strata,split_gain,initial):
        self.problem=base.Problem(context,y);self.squared=squared;self.strata=strata
        self.split_gain=split_gain;self.initial=np.array(initial,copy=True);self.cache={};self.history=[]

    def evaluate(self,theta):
        theta=np.asarray(theta,dtype=float);key=tuple(theta)
        if key in self.cache:return self.cache[key]
        if self.cache:
            nearest=min(self.cache,key=lambda value:float(np.sum((np.array(value)-theta)**2)))
            initial=self.cache[nearest][2]
        else:initial=self.initial
        distance,derivative,weights=radial(theta,self.squared)
        design=features(distance,self.strata,self.split_gain)
        fitted,p=fit_newton(self.problem,design,initial=initial)
        gamma=p[1+self.problem.k:];gain=gamma[self.strata] if self.split_gain else gamma[0]
        z=p[0]+p[1:1+self.problem.k][self.problem.group]-distance*gain
        gradient=-derivative.T@((expit(z)-self.problem.y)*gain)/self.problem.n
        value=(fitted,gradient,p)
        self.cache[key]=value
        self.history.append(dict(theta=theta.tolist(),weights=weights.tolist(),objective=fitted["objective"],gradient=gradient.tolist(),
            projected_gradient_max=float(np.max(abs(projected_shape_gradient(theta,gradient)))),coefficients=gamma.tolist(),
            inner_iterations=fitted["iterations"],inner_projected_gradient_max_unscaled=fitted["projected_gradient_max_unscaled"]))
        return value

    def objective(self,theta):
        fit,gradient,_=self.evaluate(theta)
        return fit["objective"],gradient

    def search(self,extra_points=()):
        for point in [(0.,0.)]+COARSE_POINTS+list(extra_points):self.evaluate(point)
        ordered=sorted(self.cache,key=lambda point:self.cache[point][0]["objective"])
        starts=ordered[:3];optimizers=[]
        for start in starts:
            optimum=minimize(self.objective,np.array(start),jac=True,method="L-BFGS-B",bounds=[(-LOG_BOUND,LOG_BOUND)]*2,
                options=dict(maxiter=60,maxls=30,ftol=1e-12,gtol=1e-8))
            self.evaluate(optimum.x)
            optimizers.append(dict(start=list(start),theta=optimum.x.tolist(),success=bool(optimum.success),message=str(optimum.message),iterations=int(optimum.nit)))
        if not any(row["success"] for row in optimizers):raise RuntimeError("All shape searches failed")
        best=min(self.cache,key=lambda point:self.cache[point][0]["objective"])
        fitted,gradient,p=self.cache[best]
        residual=float(np.max(abs(projected_shape_gradient(best,gradient))))
        if residual>5e-7:raise RuntimeError("Selected shape has excessive projected gradient: "+str(residual))
        return dict(theta=list(best),fit=fitted,shape_gradient=gradient.tolist(),shape_projected_gradient_max=residual,
            log_box_boundary=bool(np.any(abs(np.asarray(best))>=LOG_BOUND-1e-8)),
            shape_identified_by_nonzero_gain=bool(np.any(np.array(fitted["coefficients"])>0)),
            evaluations=self.history,optimizers=optimizers),p


def describe_cost(theta,gamma,split_gain,signed=False):
    weights=np.array([np.exp(theta[0]),1.,np.exp(theta[1])]);gamma=np.asarray(gamma)
    return dict(shape_diagonal=weights.tolist(),shape_g_per_um2=(weights/10000.).tolist(),
        log_ratio_box=[-LOG_BOUND,LOG_BOUND],shape_SPD=True,
        attenuation_by_stratum=gamma.tolist() if split_gain else np.repeat(gamma[0],4).tolist(),
        zero_attenuation_components=int(np.sum(gamma==0)),negative_attenuation_components=int(np.sum(gamma<0)),
        common_effective_metric_per_um2=(gamma[0]**2*weights/10000.).tolist() if not split_gain and gamma[0]>0 else None,
        scope="Fixed raw-axis positive shape; stratum coefficients describe the observation link, not stratum-dependent physical metrics. Signed gains are an observation control.")


def main():
    if any(p.exists() for p in [RESULT,ARRAYS,BLOCK_LOG]):raise FileExistsError("Preserve existing outputs; no silent rerun")
    inputs={HERE/"microns_node_metric.py":"0cec153e09731c2cecfc84049a6413f417c6256b82719113a6a31bfac6016e2a",
        HERE/"microns_schur_solver.py":"1fd75c944a10a80965cecd269c5df713a4e1f8ee7d899206977280d0d09e606b",
        HERE/"microns_node_metric_schur_result.json":"32982196f730e48c5bfd62b2d580e779429de9af7e63668547b0316a2eba9a9e",
        HERE/"microns_node_metric_schur_arrays.npz":"0b341c225a2783a65044f8f0e3a99eb760a79f9227dc67705b7a6dc1153ff228"}
    for path,digest in inputs.items():assert sha(path)==digest,path
    source_hash=sha(Path(__file__))
    old=json.loads((HERE/"microns_node_metric_schur_result.json").read_text(encoding="utf-8"))
    arrays=np.load(HERE/"microns_node_metric_schur_arrays.npz")
    pre=arrays["pre_index"];post=arrays["post_index"];y=arrays["label"];blocks=arrays["block"];strata=arrays["context_strategy"]
    positions=arrays["position_um"];squared=((positions[post]-positions[pre])/100.)**2
    node_groups=arrays["node_group"];assert len(y)==1815756 and int(y.sum())==78301
    assert np.array_equal(blocks,base.pair_blocks(node_groups,pre,post))
    assert np.array_equal(np.bincount(node_groups),[285,268,260,273,262])
    contexts={key:arrays["context_"+key] for key in ["strategy","typed"]}
    predictions=np.full((len(y),len(MODELS)),np.nan);fits=[];searches=[];scores_by_block=[];nesting=[]
    old_fits={(r["block"],r["model"]):r for r in old["fits"]}
    old_logits=arrays["out_of_fold_logits"];old_names=arrays["models"].tolist()
    for block in range(15):
        train,test=base.split_masks(node_groups,pre,post,block)
        assert np.all(blocks[test]==block)
        for prefix in ["strategy","typed"]:
            ctx=contexts[prefix];problem=base.Problem(ctx[train],y[train]);common=old_fits[block,prefix+"_isotropic_radial"]
            pcommon=parameters(problem,common);distance,_,_=radial([0.,0.],squared[train])
            baseline_objective,_=problem.objective(pcommon,distance[:,None])
            assert abs(baseline_objective-common["objective"])<1e-13
            common_predictions=base.predict(common,ctx[test],radial([0.,0.],squared[test])[0][:,None])
            assert np.max(abs(common_predictions-old_logits[test,old_names.index(prefix+"_isotropic_radial")]))<1e-12
            selected={"common_isotropic":dict(theta=[0.,0.],fit=common)}
            profile=Profile(ctx[train],y[train],squared[train],strata[train],False,pcommon)
            found,_=profile.search();selected["common_directional"]=found
            searches.append(dict(block=block,model=prefix+"_common_directional",**{k:v for k,v in found.items() if k!="fit"}))
            print("RADIAL_DIRECTION",block,prefix,"common directional",len(found["evaluations"]),flush=True)
            initial=np.r_[pcommon[:1+problem.k],np.repeat(pcommon[-1],4)]
            split_fit,split_parameters=fit_newton(problem,features(distance,strata[train],True),initial=initial)
            selected["stratum_isotropic"]=dict(theta=[0.,0.],fit=split_fit)
            profile=Profile(ctx[train],y[train],squared[train],strata[train],True,split_parameters)
            found,_=profile.search(extra_points=[selected["common_directional"]["theta"]]);selected["stratum_directional"]=found
            searches.append(dict(block=block,model=prefix+"_stratum_directional",**{k:v for k,v in found.items() if k!="fit"}))
            print("RADIAL_DIRECTION",block,prefix,"stratum directional",len(found["evaluations"]),flush=True)
            signed_fit,_=fit_newton(problem,features(distance,strata[train],True),signed=True,initial=split_parameters)
            selected["stratum_signed_isotropic"]=dict(theta=[0.,0.],fit=signed_fit)
            for candidate,reference in [("common_directional","common_isotropic"),("stratum_isotropic","common_isotropic"),("stratum_directional","stratum_isotropic"),("stratum_directional","common_directional"),("stratum_signed_isotropic","stratum_isotropic")]:
                difference=selected[candidate]["fit"]["objective"]-selected[reference]["fit"]["objective"]
                assert difference<=5e-11,(block,prefix,candidate,reference,difference)
                nesting.append(dict(block=block,condition=prefix,candidate=candidate,reference=reference,objective_difference=difference))
            for suffix in SUFFIXES:
                record=selected[suffix];fit=record["fit"];theta=record["theta"];split_gain=suffix.startswith("stratum_")
                dtest,_,_=radial(theta,squared[test]);design=dtest[:,None] if not split_gain else dtest[:,None]*(strata[test,None]==np.arange(4)[None,:])
                name=prefix+"_"+suffix;logit=base.predict(fit,ctx[test],design);predictions[test,MODELS.index(name)]=logit
                ll,br=base.score(y[test],logit)
                scores_by_block.append(dict(block=block,model=name,pairs=int(test.sum()),positive=int(y[test].sum()),log_loss=ll,brier=br))
                fits.append(dict(block=block,model=name,theta=theta,fit=fit,cost=describe_cost(theta,fit["coefficients"],split_gain,"signed" in suffix)))
        with BLOCK_LOG.open("a",encoding="utf-8",newline="\n") as stream:
            json.dump(dict(code_sha256=source_hash,block=block,fits=[r for r in fits if r["block"]==block],searches=[r for r in searches if r["block"]==block],scores=[r for r in scores_by_block if r["block"]==block]),stream,allow_nan=False);stream.write("\n")
    assert np.isfinite(predictions).all()
    scores=[]
    for i,name in enumerate(MODELS):
        ll,br=base.score(y,predictions[:,i]);scores.append(dict(model=name,log_loss=ll,brier=br))
    score_map={r["model"]:r for r in scores};comparisons=[]
    for prefix in ["strategy","typed"]:
        for cand,ref in [("common_directional","common_isotropic"),("stratum_isotropic","common_isotropic"),("stratum_directional","stratum_isotropic"),("stratum_directional","common_directional"),("stratum_signed_isotropic","stratum_isotropic"),("common_directional","stratum_isotropic")]:
            candidate=prefix+"_"+cand;reference=prefix+"_"+ref;differences=[]
            for block in range(15):
                ca=next(r for r in scores_by_block if r["block"]==block and r["model"]==candidate);re=next(r for r in scores_by_block if r["block"]==block and r["model"]==reference)
                differences.append(dict(block=block,log_loss_difference=ca["log_loss"]-re["log_loss"],brier_difference=ca["brier"]-re["brier"]))
            comparisons.append(dict(candidate=candidate,reference=reference,log_loss_difference=score_map[candidate]["log_loss"]-score_map[reference]["log_loss"],
                brier_difference=score_map[candidate]["brier"]-score_map[reference]["brier"],blocks_with_lower_log_loss=sum(r["log_loss_difference"]<0 for r in differences),block_differences=differences))
    strata_scores=[]
    for sid,label in enumerate(old["context_labels"]["strategy"]):
        mask=strata==sid
        for i,name in enumerate(MODELS):
            ll,br=base.score(y[mask],predictions[mask,i]);strata_scores.append(dict(stratum=sid,label=label,model=name,pairs=int(mask.sum()),positive=int(y[mask].sum()),log_loss=ll,brier=br))
    with ARRAYS.open("xb") as stream:np.savez_compressed(stream,models=np.array(MODELS),out_of_fold_logits=predictions)
    result=dict(version="microns-radial-direction-observation-v1",code_sha256=source_hash,
        input_sha256={p.relative_to(base.ROOT).as_posix():h for p,h in inputs.items()},arrays_sha256=sha(ARRAYS),block_log_sha256=sha(BLOCK_LOG),
        settings=dict(cohort="Same 1348 nodes, 1815756 pairs, 78301 positives, 15 endpoint-disjoint blocks; prior labels and metadata unchanged",
            geometry="Fixed raw EM axes, displacement in micrometers, divide by 100 before squaring; wY=1, wX=exp(thetaX), wZ=exp(thetaZ)",
            shape_box=[-LOG_BOUND,LOG_BOUND],coarse_points=COARSE_POINTS,local_starts="Three lowest training-loss coarse points; stratum search also includes fitted common shape",
            optimization="Fixed shape: same context ridge 1 and exact Schur Newton; outer analytic envelope gradient L-BFGS-B, 60 iterations/start; selected projected gradient <=5e-7; no global optimum claim",
            observation="Common nonnegative gain versus four reconstruction-stratum nonnegative gains, plus signed stratum isotropic control; no gain penalty",
            estimation="Context and shape fitting use training pairs only, cached nearest-training-parameter warm starts; known fixed export metadata, not metadata-classifier holdout",
            boundaries="Finite log-ratio box is not rank-deficient boundary; zero gain means no distance effect for that link, not a positive physical metric",
            uncertainty="Pooled and per-block scores only; dependent blocks in one volume, no independent-animal interval; retrospective development"),
        summary=dict(nodes=1348,pairs=len(y),positive=int(y.sum()),scores=scores),fits=fits,searches=searches,block_scores=scores_by_block,
        comparisons=comparisons,strata_scores=strata_scores,nesting=nesting,
        claim_ceiling="L1 observed EM annotations; L0 conditional direction/observation development. No true-negative calibration, hormone response, conductance or unique brain metric.")
    with RESULT.open("x",encoding="utf-8") as stream:json.dump(result,stream,indent=2,allow_nan=False);stream.write("\n")
    print(json.dumps(result["summary"]))


if __name__=="__main__":main()
