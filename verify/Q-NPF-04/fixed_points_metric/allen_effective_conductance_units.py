"""Audit producer V/V ratios; never reinterpret them as measured siemens."""
import json
from pathlib import Path
import sqlite3

import numpy as np

from allen_joint_inventory import BASE,sha

HERE=Path(__file__).resolve().parent
REVISION="545a990ee171e6c0d23dd4bba413e1ccbf2f0853"
PRODUCER=BASE/"producer_conductance"/REVISION
HASHES={"pipeline_conductance.py":"13e746dc4ab022bd15e6e58dc9d077afe19723b20cfc5adf06e244c9a856f712",
        "schema_synapse.py":"28506002e7dbad0f5b06bdfdc8e5f7804f38351286ff26d01bb60da7ab617fb3",
        "schema_conductance.py":"9266b45b7cb6b68f7b0f62df9e9cd2c6d0262fae7e3a6875e60581963139b4bb"}


def producer_ratio(psp_V,reversal_V,baseline_V):
    if reversal_V==baseline_V: raise ValueError("Zero driving-voltage denominator")
    return (0-psp_V)/(reversal_V-baseline_V)


def conditional_steady_conductance(ratio,leak_S):
    """One passive compartment, one static synapse, fixed reversal, known leak.

    Not a conversion certified for averaged transient PSPs or this database.
    C*dV/dt = -gL*(V-V0) - gs*(V-Es), at steady state only.
    """
    if not -1<ratio<=0 or leak_S<=0:
        raise ValueError("Passive steady-state domain requires -1 < ratio <= 0 and positive leak")
    return -ratio*leak_S/(1+ratio)


def main():
    output=HERE/"allen_effective_conductance_units_result.json"
    if output.exists(): raise FileExistsError(output)
    for name,expected in HASHES.items():
        assert sha(PRODUCER/name)==expected
    db=BASE/"synphys_r2.1_small.sqlite"
    assert sha(db)=="7372499fdd874f057565080d5769baaf2659ef39d9f3bc3c7147dd1e1c280a53"
    with sqlite3.connect(db.resolve().as_uri()+"?mode=ro",uri=True) as con:
        con.row_factory=sqlite3.Row
        rows=[dict(r) for r in con.execute("SELECT c.id,c.synapse_id,p.id pair_id,p.experiment_id,p.pre_cell_id,p.post_cell_id,"
            "s.synapse_type,s.psp_amplitude,c.effective_conductance,c.adj_psp_amplitude,c.reversal_potential,"
            "c.ideal_holding_potential,c.avg_baseline_potential FROM conductance c JOIN synapse s ON s.id=c.synapse_id "
            "JOIN pair p ON p.id=s.pair_id ORDER BY c.id")]
    evaluated=[]; missing=[]
    for row in rows:
        names=["psp_amplitude","effective_conductance","reversal_potential","avg_baseline_potential"]
        if any(row[name] is None or not np.isfinite(row[name]) for name in names):
            missing.append(dict(id=row["id"],reason="missing or nonfinite field"));continue
        if row["reversal_potential"]==row["avg_baseline_potential"]:
            missing.append(dict(id=row["id"],reason="zero denominator"));continue
        eta=producer_ratio(row["psp_amplitude"],row["reversal_potential"],row["avg_baseline_potential"])
        adjusted=(eta*row["ideal_holding_potential"]-eta*row["reversal_potential"]
                  if row["ideal_holding_potential"] is not None else None)
        adjusted_match=(bool(np.isclose(adjusted,row["adj_psp_amplitude"],rtol=1e-10,atol=1e-12))
                        if adjusted is not None and row["adj_psp_amplitude"] is not None else None)
        evaluated.append(dict(**row,reconstructed_ratio=eta,
            absolute_ratio_error=abs(eta-row["effective_conductance"]),
            ratio_matches=bool(np.isclose(eta,row["effective_conductance"],rtol=1e-10,atol=1e-12)),
            adjusted_psp_reconstructed_V=adjusted,adjusted_psp_matches=adjusted_match))
    values=np.array([r["effective_conductance"] for r in evaluated])
    selected=[r for r in evaluated if r["experiment_id"]==2771 and r["post_cell_id"]==15837]
    examples=[]
    for row in selected:
        eta=row["effective_conductance"]
        examples.append(dict(pair_id=row["pair_id"],ratio=eta,
            assumed_leak_S=[1e-8,2e-8],
            conditional_synaptic_S=[conditional_steady_conductance(eta,g) for g in [1e-8,2e-8]],
            actual_leak_measured=False,steady_state_verified=False))
    result=dict(version="allen-effective-conductance-units-v1",source_sha256=sha(Path(__file__)),
        database_sha256=sha(db),producer_revision=REVISION,producer_sha256=HASHES,
        source_revision_is_proven_DB_build_revision=False,
        unit_result="V/V: dimensionless signed ratio; not calibrated siemens",
        summary=dict(total_rows=len(rows),evaluable_rows=len(evaluated),missing_rows=len(missing),
            matching_ratio_rows=sum(r["ratio_matches"] for r in evaluated),
            matching_adjusted_psp_rows=sum(r["adjusted_psp_matches"] is True for r in evaluated),
            negative_rows=int(np.sum(values<0)),zero_rows=int(np.sum(values==0)),positive_rows=int(np.sum(values>0)),
            ratio_min=float(values.min()),ratio_max=float(values.max()),
            maximum_absolute_ratio_error=max(r["absolute_ratio_error"] for r in evaluated)),
        rows=evaluated,missing=missing,selected_target7_rows=selected,
        conditional_scale_examples=examples,
        claim_ceiling="L0 measurement-definition audit and conditional passive example; no physical conductance identification")
    with output.open("x",encoding="utf-8") as stream:
        json.dump(result,stream,indent=2,allow_nan=False);stream.write("\n")
    print(json.dumps(result["summary"]))


if __name__=="__main__": main()
