"""Compare the completed first real-data block, without refitting either method."""
import csv
import hashlib
import json
from pathlib import Path

import numpy as np
import microns_node_metric as model

HERE=Path(__file__).resolve().parent


def main():
    paths=[HERE/"microns_node_metric_blocks.jsonl",HERE/"microns_node_metric_schur_blocks.jsonl"]
    records=[];line_hashes=[]
    for path in paths:
        with path.open("rb") as stream:line=stream.readline()
        records.append(json.loads(line));line_hashes.append(hashlib.sha256(line).hexdigest())
    old,new=records
    assert old["block"]==new["block"] and old["block"]["block"]==0
    with (model.DATA/"v1718_cell_info.csv").open(encoding="utf-8",newline="") as stream:
        nodes=sorted([r for r in csv.DictReader(stream) if all(r[k]=="True" for k in ["is_column","status_axon","status_dendrite"]) and int(r["pt_root_id"])!=0],key=lambda r:int(r["pt_root_id"]))
    xyz=np.array([[float(r["pt_position_"+axis]) for axis in "xyz"] for r in nodes])*model.SCALE_UM
    pre,post=np.where(~np.eye(len(nodes),dtype=bool));squared=((xyz[post]-xyz[pre])/100.)**2
    groups=np.array([model.node_fold(int(r["pt_root_id"])) for r in nodes]);train,test=model.split_masks(groups,pre,post,0)
    context={key:model.context_codes(nodes,pre,post,key=="typed")[0] for key in ["strategy","typed"]}
    rows=[]
    for name in model.MODELS:
        a=next(r for r in old["fits"] if r["model"]==name);b=next(r for r in new["fits"] if r["model"]==name)
        features=model.features_for(name,squared);ctx=context[name.split("_")[0]]
        za=model.predict(a,ctx,features);zb=model.predict(b,ctx,features)
        test_a=next(r for r in old["scores"] if r["model"]==name);test_b=next(r for r in new["scores"] if r["model"]==name)
        rows.append(dict(model=name,old_iterations=a["iterations"],new_iterations=b["iterations"],
            new_minus_old_penalized_objective=b["objective"]-a["objective"],
            train_max_absolute_logit_difference=float(np.max(abs(zb[train]-za[train]))),
            test_max_absolute_logit_difference=float(np.max(abs(zb[test]-za[test]))),
            test_rms_logit_difference=float(np.sqrt(np.mean((zb[test]-za[test])**2))),
            test_log_loss_difference=test_b["log_loss"]-test_a["log_loss"],
            old_scaled_gradient_max=a["gradient_max"],new_projected_gradient_max_unscaled=b["projected_gradient_max_unscaled"]))
    assert max(r["new_minus_old_penalized_objective"] for r in rows)<5e-11
    output=HERE/"microns_solver_comparison_result.json"
    with output.open("x",encoding="utf-8") as stream:
        json.dump(dict(code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            compared_block=old["block"],checkpoint_first_line_sha256=dict(zip([p.name for p in paths],line_hashes)),
            analysis_code_sha256=dict(original=old["code_sha256"],schur=new["code_sha256"]),
            scope="Numerical comparison on one completed real-data block, fixed statistical objective, no new biological confirmation",models=rows),stream,indent=2,allow_nan=False);stream.write("\n")
    print(json.dumps(rows))


if __name__=="__main__":main()
