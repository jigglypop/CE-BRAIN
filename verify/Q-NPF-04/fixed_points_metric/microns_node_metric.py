"""Internal node-heldout spatial prediction of MICrONS export annotations.

Both endpoints are excluded from training. One reconstructed volume, selected
proofread cells, retrospective metadata: not independent animals or true zeros.
"""
import csv
import hashlib
import itertools
import json
from pathlib import Path
import sys

import numpy as np
from scipy.optimize import minimize
from scipy.special import expit

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
DATA=ROOT/"data/external/microns_v1718_cosyne"
OUTPUT=HERE/"microns_node_metric_result.json"
ARRAYS=HERE/"microns_node_metric_arrays.npz"
CHECKPOINT=HERE/"microns_node_metric_blocks.jsonl"
SCALE_UM=np.array([.004,.004,.04])
MODELS=["strategy_context","strategy_isotropic_quadratic","strategy_diagonal_quadratic","strategy_isotropic_radial",
        "typed_context","typed_isotropic_quadratic","typed_diagonal_quadratic","typed_isotropic_radial","typed_signed_quadratic"]
BLOCKS=list(itertools.combinations_with_replacement(range(5),2))


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def node_fold(root):return int(hashlib.sha256(("fixed-neuron-microns-node-v1:"+str(root)).encode()).hexdigest()[:16],16)%5


def pair_blocks(node_groups,pre,post):
    lookup=np.full((5,5),-1,dtype=np.int8)
    for k,(a,b) in enumerate(BLOCKS):lookup[a,b]=lookup[b,a]=k
    return lookup[node_groups[pre],node_groups[post]]


def split_masks(node_groups,pre,post,block):
    a,b=BLOCKS[block];held=np.isin(node_groups,[a,b])
    train=~held[pre]&~held[post];test=pair_blocks(node_groups,pre,post)==block
    return train,test


def context_codes(nodes,pre,post,typed):
    def key(n,side):
        value=n["strategy_axon"] if side=="pre" else n["strategy_dendrite"]
        return (n["cell_type"] or "unknown")+"|"+value if typed else value
    left=sorted({key(n,"pre") for n in nodes});right=sorted({key(n,"post") for n in nodes})
    lmap={v:i for i,v in enumerate(left)};rmap={v:i for i,v in enumerate(right)}
    l=np.array([lmap[key(n,"pre")] for n in nodes]);r=np.array([rmap[key(n,"post")] for n in nodes])
    labels=[a+" -> "+b for a in left for b in right]
    return (l[pre]*len(right)+r[post]).astype(np.int16),labels


class Problem:
    def __init__(self,context,y):
        self.categories,self.group=np.unique(context,return_inverse=True)
        self.y=np.asarray(y,float);self.n=len(y);self.k=len(self.categories)

    def objective(self,p,features):
        offsets=p[1:1+self.k];beta=p[1+self.k:]
        z=p[0]+offsets[self.group]-features@beta;r=expit(z)-self.y
        loss=(np.sum(np.logaddexp(0,z)-self.y*z)+.5*(offsets@offsets))/self.n
        grad=np.r_[r.sum(),np.bincount(self.group,weights=r,minlength=self.k)+offsets,-features.T@r]/self.n
        return loss,grad

    def fit(self,features,signed=False,initial=None):
        if initial is None:
            initial=np.zeros(1+self.k+features.shape[1]);m=np.clip(self.y.mean(),1e-8,1-1e-8);initial[0]=np.log(m/(1-m))
        solved=minimize(self.objective,initial,args=(features,),jac=True,method="L-BFGS-B",
            bounds=[(None,None)]*(1+self.k)+[(None,None) if signed else (0,None)]*features.shape[1],
            options=dict(maxiter=2000,ftol=1e-12,gtol=1e-8,maxls=40))
        if not solved.success:raise RuntimeError(str(solved.message))
        p=solved.x
        return dict(intercept=float(p[0]),context_offsets={str(c):float(v) for c,v in zip(self.categories,p[1:1+self.k])},
            coefficients=p[1+self.k:].tolist(),objective=float(solved.fun),iterations=int(solved.nit),
            gradient_max=float(np.max(abs(solved.jac))),optimizer_message=str(solved.message)),p


def predict(fitted,context,features):
    keys=np.array([int(c) for c in fitted["context_offsets"]]);lookup=np.zeros(int(max(context.max(initial=0),keys.max(initial=0)))+1)
    for c,value in fitted["context_offsets"].items():lookup[int(c)]=value
    return fitted["intercept"]+lookup[context]-features@np.array(fitted["coefficients"])


def features_for(model,squared):
    if model.endswith("context"):return np.empty((len(squared),0))
    if model.endswith("isotropic_quadratic"):return squared.sum(axis=1)[:,None]
    if model.endswith("isotropic_radial"):return np.sqrt(squared.sum(axis=1))[:,None]
    return squared


def metric_for(model,coefficients):
    if model.endswith("context"):return None
    beta=np.array(coefficients)
    if model.endswith("isotropic_radial"):diag=np.repeat(beta[0]**2/100**2,3)
    elif model.endswith("isotropic_quadratic"):diag=np.repeat(beta[0]/100**2,3)
    else:diag=beta/100**2
    return dict(diagonal_per_um2=diag.tolist(),SPD=bool(np.all(diag>0)),PSD=bool(np.all(diag>=0)),
        exact_zero_components=int(np.sum(diag==0)),negative_components=int(np.sum(diag<0)),
        smallest_eigenvalue_per_um2=float(diag.min()),
        largest_to_smallest_ratio=float(diag.max()/diag.min()) if diag.min()>0 else None,
        scope="Constant cost aligned to raw EM axes; geometry and link are assumed, not an identified individual-brain metric")


def score(y,logits):
    ll=np.logaddexp(0,logits)-y*logits;br=(expit(logits)-y)**2
    return float(ll.mean()),float(br.mean())


def main():
    if OUTPUT.exists() or ARRAYS.exists() or CHECKPOINT.exists():raise FileExistsError("Existing node-metric outputs are preserved; do not silently rerun")
    inputs={DATA/"v1718_cell_info.csv":"1959b7b7eaad7501c6331551c3ed1e229b40ed3c339ff6273b6365009e33fb09",
        DATA/"v1718_v1_column_synapses.feather":"fee7afc8c37528e3e1c1a4365f016f74c8ff42b6dad0f06100ef32d38adb0434",
        DATA/"preprocessing_celltypes_v1718.ipynb":"918d5c439a4fd637adadd77529022eb98333426c660ad277ea99588efb44e063",
        ROOT/"verify/Q-NPF-04/allen_synphys/microns_structural_inventory_result.json":"ea1da5f217a80c99fd85d3f9168200de78d5c81846995a52f237d30ad156341f",
        ROOT/"verify/Q-NPF-04/allen_synphys/microns_export_overlap_result.json":"98f33932d405552a236cea72e9cd76c6d96cfd6048547c27edb7bcce49944bab"}
    for p,h in inputs.items():assert sha(p)==h,p
    source_hash=sha(Path(__file__))
    with (DATA/"v1718_cell_info.csv").open(encoding="utf-8",newline="") as stream:all_nodes=list(csv.DictReader(stream))
    nodes=sorted([r for r in all_nodes if all(r[k]=="True" for k in ["is_column","status_axon","status_dendrite"]) and int(r["pt_root_id"])!=0],key=lambda r:int(r["pt_root_id"]))
    roots=np.array([int(r["pt_root_id"]) for r in nodes],dtype=np.int64);assert len(roots)==len(set(roots))==1348
    previous=json.loads((ROOT/"verify/Q-NPF-04/allen_synphys/microns_structural_inventory_result.json").read_text())
    assert roots.tolist()==previous["selected_roots"]
    xyz=np.array([[float(r["pt_position_"+axis]) for axis in "xyz"] for r in nodes])*SCALE_UM
    transformed=np.array([[float(r["pt_position_"+axis+"_tform"]) for axis in "xyz"] for r in nodes])
    assert np.isfinite(xyz).all() and np.isfinite(transformed).all()
    affine=np.linalg.lstsq(np.column_stack([np.ones(len(xyz)),xyz]),transformed,rcond=None)[0]
    affine_error=float(np.max(abs(np.column_stack([np.ones(len(xyz)),xyz])@affine-transformed)))
    linear=affine[1:];orthogonal_error=float(np.max(abs(linear.T@linear-np.eye(3))))
    sys.path.insert(0,str(ROOT/"data/external/analysis_tools/arrow_reader"))
    import pyarrow
    import pyarrow.feather as feather
    table=feather.read_table(DATA/"v1718_v1_column_synapses.feather",columns=["syn_id","pre_pt_root_id","post_pt_root_id"])
    ids=table["syn_id"].to_pylist();assert len(ids)==len(set(ids))
    index={int(r):i for i,r in enumerate(roots)};counts=np.zeros((len(nodes),len(nodes)),dtype=np.int32);excluded=0;self_rows=0
    for pre,post in zip(table["pre_pt_root_id"].to_pylist(),table["post_pt_root_id"].to_pylist()):
        if pre not in index or post not in index:excluded+=1;continue
        if pre==post:self_rows+=1;continue
        counts[index[pre],index[post]]+=1
    assert int(counts.sum())==145598 and int((counts>0).sum())==78301
    pre,post=np.where(~np.eye(len(nodes),dtype=bool));pre=pre.astype(np.int16);post=post.astype(np.int16)
    y=(counts[pre,post]>0).astype(np.int8);delta=xyz[post]-xyz[pre];squared=(delta/100.)**2
    assert len(y)==1815756 and np.linalg.matrix_rank(xyz-xyz.mean(axis=0))==3
    node_groups=np.array([node_fold(int(r)) for r in roots],dtype=np.int8);blocks=pair_blocks(node_groups,pre,post)
    context={};context_labels={}
    for key,typed in [("strategy",False),("typed",True)]:context[key],context_labels[key]=context_codes(nodes,pre,post,typed)
    logits=np.full((len(y),len(MODELS)),np.nan);fits=[];block_scores=[];block_info=[]
    for block,(a,b) in enumerate(BLOCKS):
        train,test=split_masks(node_groups,pre,post,block)
        train_nodes=set(pre[train])|set(post[train]);test_nodes=set(pre[test])|set(post[test]);assert train_nodes.isdisjoint(test_nodes)
        entry=dict(block=block,node_groups=[a,b],train_nodes=len(train_nodes),test_nodes=len(test_nodes),train_pairs=int(train.sum()),test_pairs=int(test.sum()),train_positive=int(y[train].sum()),test_positive=int(y[test].sum()))
        block_info.append(entry);assert train.any() and test.any()
        for key in ["strategy","typed"]:
            ctx=context[key];problem=Problem(ctx[train],y[train]);base=None;diagonal=None
            subset=[m for m in MODELS if m.startswith(key+"_")]
            for model in subset:
                ftrain=features_for(model,squared[train]);ftest=features_for(model,squared[test])
                initial=None if base is None else np.r_[base,np.zeros(ftrain.shape[1])]
                if model.endswith("signed_quadratic"):initial=diagonal
                fitted,params=problem.fit(ftrain,signed=model.endswith("signed_quadratic"),initial=initial)
                if model.endswith("context"):base=params.copy()
                if model.endswith("diagonal_quadratic"):diagonal=params.copy()
                logits[test,MODELS.index(model)]=predict(fitted,ctx[test],ftest)
                metric=metric_for(model,fitted["coefficients"])
                if metric is not None:
                    g=np.diag(metric["diagonal_per_um2"]);inv=np.linalg.inv(linear);gq=inv@g@inv.T
                    d=delta[test];dq=d@linear
                    raw_cost=np.einsum("ni,ij,nj->n",d,g,d);new_cost=np.einsum("ni,ij,nj->n",dq,gq,dq)
                    metric["transformed_full_matrix_per_um2"]=gq.tolist()
                    metric["coordinate_covariance_max_cost_error"]=float(np.max(abs(raw_cost-new_cost)))
                fitted=dict(block=block,model=model,metric=metric,**fitted);fits.append(fitted)
                loss,brier=score(y[test],logits[test,MODELS.index(model)])
                block_scores.append(dict(block=block,model=model,log_loss=loss,brier=brier,
                    unseen_context_pairs=int(np.sum(~np.isin(ctx[test],problem.categories)))))
                print("MICRONS_NODE",block,model,"iterations",fitted["iterations"],flush=True)
        with CHECKPOINT.open("a",encoding="utf-8",newline="\n") as stream:stream.write(json.dumps(dict(code_sha256=source_hash,block=entry,fits=[r for r in fits if r["block"]==block],scores=[r for r in block_scores if r["block"]==block]),allow_nan=False)+"\n")
    assert np.isfinite(logits).all()
    scores=[]
    for i,model in enumerate(MODELS):
        ll,br=score(y,logits[:,i]);scores.append(dict(model=model,log_loss=ll,brier=br))
    comparisons=[]
    pairs=[("strategy_isotropic_quadratic","strategy_context"),("strategy_diagonal_quadratic","strategy_isotropic_quadratic"),
        ("strategy_isotropic_radial","strategy_isotropic_quadratic"),("strategy_diagonal_quadratic","strategy_isotropic_radial"),
        ("typed_isotropic_quadratic","typed_context"),("typed_diagonal_quadratic","typed_isotropic_quadratic"),
        ("typed_isotropic_radial","typed_isotropic_quadratic"),("typed_diagonal_quadratic","typed_isotropic_radial"),
        ("typed_signed_quadratic","typed_diagonal_quadratic"),("typed_diagonal_quadratic","strategy_diagonal_quadratic")]
    by_score={r["model"]:r for r in scores}
    for candidate,reference in pairs:
        differences=[]
        for block in range(len(BLOCKS)):
            ca=next(r for r in block_scores if r["model"]==candidate and r["block"]==block);re=next(r for r in block_scores if r["model"]==reference and r["block"]==block)
            differences.append(dict(block=block,log_loss_difference=ca["log_loss"]-re["log_loss"],brier_difference=ca["brier"]-re["brier"]))
        comparisons.append(dict(candidate=candidate,reference=reference,log_loss_difference=by_score[candidate]["log_loss"]-by_score[reference]["log_loss"],
            brier_difference=by_score[candidate]["brier"]-by_score[reference]["brier"],blocks_with_lower_log_loss=sum(r["log_loss_difference"]<0 for r in differences),block_differences=differences))
    strata=[]
    for cid,label in enumerate(context_labels["strategy"]):
        mask=context["strategy"]==cid
        if not mask.any():continue
        for i,model in enumerate(MODELS):
            ll,br=score(y[mask],logits[mask,i]);strata.append(dict(strategy_context=label,model=model,pairs=int(mask.sum()),positive=int(y[mask].sum()),positive_fraction=float(y[mask].mean()),log_loss=ll,brier=br))
    with ARRAYS.open("xb") as stream:np.savez_compressed(stream,root_id=roots,position_um=xyz,node_group=node_groups,pre_index=pre,post_index=post,
        block=blocks,label=y,annotation_count=counts[pre,post],context_strategy=context["strategy"],context_typed=context["typed"],models=np.array(MODELS),out_of_fold_logits=logits)
    result=dict(version="microns-node-metric-v1",code_sha256=source_hash,input_sha256={p.relative_to(ROOT).as_posix():h for p,h in inputs.items()},arrays_sha256=sha(ARRAYS),checkpoint_sha256=sha(CHECKPOINT),pyarrow_version=pyarrow.__version__,
        settings=dict(selection="Prior 1348 column AND axon/dendrite proofread roots, unchanged",label="At least one annotation between distinct roots in selected export; zero means unlisted, not biological absence",
            voxel_size_nm=[4,4,40],position_unit="micrometers in raw EM image axes",length_unit_um=100.,context_ridge=1.,distance_penalty=0.,
            split="sha256 fixed-neuron-microns-node-v1:root first16hex mod5; 15 unordered group blocks; exclude both endpoint groups from training",
            training_fraction="About 80% nodes for same-group blocks, 60% for different-group blocks; identical within model comparisons",
            context="Primary: pre axon strategy and post dendrite strategy; secondary: add ordered published cell_type, unknown retained; no mtype or meso_type",
            context_scope="Retrospective fixed export metadata; cell_type corrections lack row-level provenance; metadata classifiers were not retrained within graph holdout",
            categories="Training block only; unseen context offset=0; no degree or heldout edge features",
            uncertainty="Per-block and pooled finite-volume prediction scores only; no independent-animal confidence interval or spatial-dependence correction",
            analysis="Previously exposed dataset, new node-heldout development comparison; no preregistered external confirmation"),
        summary=dict(nodes=len(nodes),pairs=len(y),positive=int(y.sum()),positive_fraction=float(y.mean()),node_group_counts=np.bincount(node_groups,minlength=5).tolist(),
            observed_annotations=int(counts.sum()),export_rows=table.num_rows,excluded_outside_selected_annotations=excluded,excluded_self_annotations=self_rows,
            strategy_axon={v:sum(r["strategy_axon"]==v for r in nodes) for v in sorted({r["strategy_axon"] for r in nodes})},
            strategy_dendrite={v:sum(r["strategy_dendrite"]==v for r in nodes) for v in sorted({r["strategy_dendrite"] for r in nodes})},
            raw_coordinate_min_max_um=[xyz.min(axis=0).tolist(),xyz.max(axis=0).tolist()],position_centered_singular_values_um=np.linalg.svd(xyz-xyz.mean(axis=0),compute_uv=False).tolist(),
            distance_quantiles_um=np.quantile(np.linalg.norm(delta,axis=1),[0,.5,.95,1]).tolist(),scores=scores),
        coordinate_bridge=dict(raw_to_exported_transform_linear_row_convention=linear.tolist(),translation_um=affine[0].tolist(),max_affine_error_um=affine_error,orthogonality_max_error=orthogonal_error,
            scope="Stored coordinates related by near-rigid affine transformation; no independent specimen calibration or local pia-normal measurement"),
        nodes=[dict(root_id=int(r["pt_root_id"]),cell_type=r["cell_type"] or "unknown",broad_type=r["broad_type"],strategy_axon=r["strategy_axon"],strategy_dendrite=r["strategy_dendrite"],node_group=int(node_groups[i])) for i,r in enumerate(nodes)],
        context_labels=context_labels,block_info=block_info,fits=fits,block_scores=block_scores,comparisons=comparisons,strategy_strata_scores=strata,
        claim_ceiling="L1 finite-volume EM annotations; L0 conditional metric development; no proof of true negatives, physical conductance, hormone effects, unique brain metric, or independent animals")
    with OUTPUT.open("x",encoding="utf-8") as stream:json.dump(result,stream,indent=2,allow_nan=False);stream.write("\n")
    print(json.dumps(result["summary"]))


if __name__=="__main__":main()
