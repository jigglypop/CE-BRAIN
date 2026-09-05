"""Post-plot current/derivative observation bases with fixed earlier/later split.

Derivative improvement can reflect channel delay or filtering; not conductance.
"""
import json
from pathlib import Path

import numpy as np

from allen_joint_inventory import sha
from electrical_star_periodic_channel_association import center_windows,PRIMARY,DEVICES,score

HERE=Path(__file__).resolve().parent


def design(actual):
    current=actual[:,-1]
    derivative=np.gradient(current,.02,axis=-1,edge_order=1)
    # Central differences in the interior, never across events or window ends.
    return np.stack([current[:,PRIMARY],derivative[:,PRIMARY]],axis=-1)


def fit(x,y,columns):
    xx=x[...,columns].reshape(-1,len(columns));yy=y.reshape(-1)
    scale=np.linalg.norm(xx,axis=0)
    if np.any(scale<=0):raise ValueError("Zero training basis")
    normalized=xx/scale
    coeff,_,rank,singular=np.linalg.lstsq(normalized,yy,rcond=None)
    return dict(coefficients=(coeff/scale).tolist(),rank=int(rank),
        normalized_singular_values=singular.tolist(),normalized_condition=float(singular[0]/singular[-1]),
        column_training_norms=scale.tolist())


def main():
    output=HERE/"electrical_star_periodic_derivative_result.json"
    if output.exists():raise FileExistsError(output)
    parent_path=HERE/"electrical_star_periodic_channel_association_result.json"
    parent=json.loads(parent_path.read_text())
    assert sha(HERE/"electrical_star_periodic_channel_association.py")==parent["code_sha256"]
    waves_path=HERE/"electrical_star_periodic_channel_windows.npz"
    assert sha(waves_path)==parent["raw_windows_sha256"]
    with np.load(waves_path,allow_pickle=False) as waves:raw_values=waves["raw_current"]
    by_sweep={r["sweep"]:r for r in parent["metadata"]}
    events=parent["events"]
    conv=np.array([[d["conversion"] for d in by_sweep[e["sweep"]]["acquisition"]] for e in events])[...,None]
    offset=np.array([[d["offset"] for d in by_sweep[e["sweep"]]["acquisition"]] for e in events])[...,None]
    actual,control=center_windows(raw_values,conv,offset)
    x=design(actual);sweeps=np.array([e["sweep"] for e in events]);quiet=np.array([e["both_windows_command_clear"] for e in events])
    models={"current_only":[0],"derivative_only":[1],"current_and_derivative":[0,1]}
    blocks=[]
    for parent_block in parent["analysis"]:
        train=np.isin(sweeps,parent_block["train"])&quiet
        fits=[];rows=[]
        for model,columns in models.items():
            for c,device in enumerate(DEVICES[:-1]):
                fitted=fit(x[train],actual[train,c][:,PRIMARY],columns)
                if model=="current_only":
                    assert np.isclose(fitted["coefficients"][0],parent_block["coefficients_by_device"][str(device)],rtol=1e-10,atol=1e-15)
                fits.append(dict(model=model,device=device,columns=columns,**fitted))
                for sweep in parent_block["evaluate"]:
                    for subset in ["both_windows_clear","all_catalogue_background"]:
                        chosen=(sweeps==sweep)&(quiet if subset=="both_windows_clear" else True)
                        predicted=x[chosen][...,columns]@np.array(fitted["coefficients"])
                        real_score=score(actual[chosen,c][:,PRIMARY],predicted)
                        shifted_score=score(control[chosen,c][:,PRIMARY],predicted)
                        rows.append(dict(sweep=sweep,subset=subset,model=model,device=device,n_events=int(sum(chosen)),
                            actual=real_score,shifted_other_channel=shifted_score,
                            actual_gain_minus_shifted_gain_pA2=real_score["gain_over_zero_pA2"]-shifted_score["gain_over_zero_pA2"]))
        blocks.append(dict(holding_mV=parent_block["holding_mV"],train=parent_block["train"],evaluate=parent_block["evaluate"],
            training_events=int(sum(train)),fits=fits,evaluation=rows))
    pooled=[]
    for block in blocks:
        for model in models:
            for subset in ["both_windows_clear","all_catalogue_background"]:
                for sweep in block["evaluate"]:
                    rr=[r for r in block["evaluation"] if r["model"]==model and r["subset"]==subset and r["sweep"]==sweep]
                    zero=np.mean([r["actual"]["zero_RMSE_pA"]**2 for r in rr]);mse=np.mean([r["actual"]["RMSE_pA"]**2 for r in rr])
                    pooled.append(dict(holding_mV=block["holding_mV"],model=model,subset=subset,sweep=sweep,
                        RMSE_over_zero=float(np.sqrt(mse/zero)),gain_over_zero_pA2=float(zero-mse),
                        actual_gain_minus_shifted_gain_pA2=float(np.mean([r["actual_gain_minus_shifted_gain_pA2"] for r in rr]))))
    result=dict(version="electrical-star-periodic-derivative-v1",code_sha256=sha(Path(__file__)),
        parent_result_sha256=sha(parent_path),parent_code_sha256=parent["code_sha256"],raw_windows_sha256=sha(waves_path),
        models=models,coefficient_units={"current":"dimensionless","derivative":"ms"},analysis=blocks,pooled=pooled,
        timing="Derivative from full 20 ms actual window at 0.02 ms spacing; interior central difference then same primary mask",
        development_status="Added after viewing scalar-analysis plots; same previously exposed data, not independent confirmation",
        claim_ceiling="L1 current association and L0 observation-model development; no measured conductance or origin identification")
    with output.open("x",encoding="utf-8") as stream:
        json.dump(result,stream,indent=2,allow_nan=False);stream.write("\n")
    print(json.dumps([r for r in pooled if r["subset"]=="both_windows_clear"]))


if __name__=="__main__":main()
