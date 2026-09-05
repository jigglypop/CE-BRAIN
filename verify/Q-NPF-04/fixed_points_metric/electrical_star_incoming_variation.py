"""Post-hoc variation diagnostic; not estimated intrinsic noise or conductance."""
import json
from pathlib import Path

import numpy as np

from allen_joint_inventory import sha

HERE=Path(__file__).resolve().parent


def expected_mse_ratio(signal_power, variation_power, train_repeats=2):
    """Ratio of EXPECTED MSEs under equal, independent, zero-mean repeat noise.

    This is not E[the observed ratio], and does not require independent time bins.
    signal_power = average squared true mean waveform; variation_power = average
    within-waveform marginal noise variance. No such noise model is assumed fitted.
    """
    if signal_power<0 or variation_power<0 or train_repeats<1 or signal_power+variation_power==0:
        raise ValueError("Require nonnegative nonzero powers and positive repeat count")
    return (1+1/train_repeats)*variation_power/(signal_power+variation_power)


def main():
    output=HERE/"electrical_star_incoming_variation_result.json"
    if output.exists(): raise FileExistsError(output)
    source=HERE/"electrical_star_incoming_chemical_result.json"
    d=json.loads(source.read_text())
    path=HERE/"electrical_star_incoming_chemical_waveforms.npz"
    assert sha(path)==d["waveform_sha256"]
    with np.load(path,allow_pickle=False) as waves:
        values=waves["current_pA"]
    mask=np.array(d["primary_mask"])
    rows=[]
    for block in d["settings"]["train_evaluate"]:
        for column,source_device in enumerate(d["sources"]):
            first,second=values[block["train"],column][:,:,mask]
            variation=float(np.mean((first-second)**2)/2)
            cross=float(np.mean(first*second))
            rows.append(dict(holding_mV=block["holding_mV"],source=source_device,
                repeat_difference_power_pA2=variation,cross_repeat_second_moment_pA2=cross,
                cross_moment_over_difference_power=cross/variation if variation>0 else None,
                interpretation="observed training-repeat moments; stationarity and independent noise not established"))
    result=dict(version="electrical-star-incoming-variation-v1",source_sha256=sha(Path(__file__)),
        observed_result_sha256=sha(HERE/"electrical_star_incoming_chemical_result.json"),
        waveform_sha256=sha(path),observed_training_moments=rows,
        conditional_noise_model=dict(train_repeats=2,target_RMSE_ratio=.8,
            required_signal_to_variation_power=(1+1/2)/(.8**2)-1,
            meaning="Only in ratio-of-expected-MSE model; not a bound on this dataset or a biological absence test"),
        claim_ceiling="L0 conditional identity; post-hoc observed variation summaries, not independent validation")
    with output.open("x",encoding="utf-8") as stream:
        json.dump(result,stream,indent=2,allow_nan=False);stream.write("\n")
    print(json.dumps({"output":str(output),"conditional_required_ratio":result["conditional_noise_model"]["required_signal_to_variation_power"],
                      "observed_ratio_range":[min(r["cross_moment_over_difference_power"] for r in rows),max(r["cross_moment_over_difference_power"] for r in rows)]}))


if __name__=="__main__": main()
