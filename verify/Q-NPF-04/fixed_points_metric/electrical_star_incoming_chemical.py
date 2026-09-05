"""Direction-specific target-7 current repeatability in known incoming pairs.

Development analysis: annotations and full numerical notebook were exposed.
An applied VC command is not a measured presynaptic AP or membrane voltage.
No hormone concentration, synaptic conductance or spatial cost is inferred.
"""
import argparse
import json
from pathlib import Path
import sqlite3

import h5py
import numpy as np

from allen_joint_inventory import BASE, OfflineRanges, raw, sha

HERE = Path(__file__).resolve().parent
OUTPUT = HERE / "electrical_star_incoming_chemical_result.json"
WAVES = HERE / "electrical_star_incoming_chemical_waveforms.npz"
SOURCE_FILES = {
    "electrical_star_vc_inputs_result.json": "52cebb1cfbd4ce2b7d4dacb2e589194034298314fdcad852bcb35e8989ae876b",
    "electrical_star_protocol_result.json": "a889d98c7bbce920f78366a15c67e40464a3b4926ecec412bdd17e7f44dbb4d0",
}
DB_SHA = "7372499fdd874f057565080d5769baaf2659ef39d9f3bc3c7147dd1e1c280a53"
SOURCES = [0, 1, 2, 4, 5, 6]
TARGET = 7
ANNOTATED = [0, 1, 2, 5, 6]
VC_QC = [2, 5]
RATE = 50000
TIME_MS = (np.arange(400) * 5 + 2 - 600) / 50.
PRIMARY = (TIME_MS >= .5) & (TIME_MS < 15.)
BLOCKS = [dict(holding_mV=-70, train=[0, 1], evaluate=[2, 3, 4]),
          dict(holding_mV=-55, train=[5, 6], evaluate=[7, 8, 9])]


def center_epoch(values, duration_samples):
    """2000 raw samples at command offset [-12,+28) ms; onset baseline [-10,-2)."""
    values = np.asarray(values, float)
    if values.shape[-1] != 2000 or duration_samples not in [75, 76]:
        raise ValueError("Unexpected sampling or command duration")
    baseline_slice = slice(600-duration_samples-500, 600-duration_samples-100)
    baseline = values[..., baseline_slice].mean(axis=-1)
    centered = values - baseline[..., None]
    binned = centered.reshape(*centered.shape[:-1], 400, 5).mean(axis=-1)
    return binned, baseline


def score(observed, predicted):
    observed, predicted = np.broadcast_arrays(np.asarray(observed, float), np.asarray(predicted, float))
    if observed.size == 0 or not np.isfinite(observed).all() or not np.isfinite(predicted).all():
        raise ValueError("Scores require finite nonempty arrays")
    mse = float(np.mean((observed-predicted)**2))
    zero = float(np.mean(observed**2))
    return dict(rmse_pA=float(np.sqrt(mse)), zero_rmse_pA=float(np.sqrt(zero)),
                rmse_over_zero=float(np.sqrt(mse/zero)) if zero > 0 else None,
                mse_gain_over_zero_pA2=zero-mse)


def model_templates(train, shifted_train):
    repeat = np.asarray(train).mean(axis=0)  # source, pulse identity, time
    negative = repeat[SOURCES.index(4)]
    return {
        "pulse_specific": repeat,
        "pulse_pooled": np.broadcast_to(repeat.mean(axis=1, keepdims=True), repeat.shape),
        "negative_source": np.broadcast_to(negative, repeat.shape),
        "shifted_time": np.asarray(shifted_train).mean(axis=0),
    }


def summarize(real, shifted, duration_samples):
    groups = {"all_annotated": ANNOTATED, "VC_QC_pass": VC_QC,
              "inhibitory_annotated": [0, 1, 2, 5], "excitatory_annotated": [6]}
    results = []
    for block in BLOCKS:
        templates = model_templates(real[block["train"]], shifted[block["train"]])
        rows = []
        for sweep in block["evaluate"]:
            per_source = []
            for index, source in enumerate(SOURCES):
                windows = {"post_offset_primary": PRIMARY,
                           "onset_0_20ms_auxiliary": (TIME_MS[None, :]+duration_samples[sweep,index,:,None]/50. >= 0)
                              & (TIME_MS[None, :]+duration_samples[sweep,index,:,None]/50. < 20.)}
                scores = {}
                for name, mask in windows.items():
                    mask = np.broadcast_to(mask, real[sweep,index].shape)
                    scores[name] = {model: score(real[sweep,index][mask], template[index][mask])
                                    for model, template in templates.items()}
                pulses = {}
                for label, indices in {"first": [0], "after_gap": [8],
                                       "other": [1,2,3,4,5,6,7,9,10,11]}.items():
                    pulses[label] = {model: score(real[sweep,index][indices][:,PRIMARY], template[index][indices][:,PRIMARY])
                                     for model, template in templates.items()}
                per_source.append(dict(source=source, windows=scores, pulse_groups=pulses,
                    primary_mean_current_pA=real[sweep,index][:,PRIMARY].mean(axis=1).tolist(),
                    primary_signed_charge_pA_ms=(real[sweep,index][:,PRIMARY].sum(axis=1)*.1).tolist()))
            grouped = {}
            for label, sources in groups.items():
                indices = [SOURCES.index(s) for s in sources]
                grouped[label] = {model: score(real[sweep,indices][:,:,PRIMARY], template[indices][:,:,PRIMARY])
                                  for model, template in templates.items()}
            rows.append(dict(sweep=sweep, sources=per_source, groups=grouped))
        source_gates = []
        for index, source in enumerate(SOURCES):
            primary = [r["sources"][index]["windows"]["post_offset_primary"] for r in rows]
            repeatable = all(p["pulse_specific"]["rmse_over_zero"] is not None and
                             p["pulse_specific"]["rmse_over_zero"] <= .8 for p in primary)
            specific = (all(p["pulse_specific"]["rmse_pA"] < p["negative_source"]["rmse_pA"] for p in primary)
                        if source != 4 else None)
            temporal = all(p["pulse_specific"]["rmse_pA"] < p["shifted_time"]["rmse_pA"] for p in primary)
            source_gates.append(dict(source=source, repeatability_gate=repeatable,
                better_than_negative_source_all_repeats=specific,
                better_than_shifted_time_all_repeats=temporal,
                combined_development_gate=(repeatable and specific and temporal) if source != 4 else None))
        group_gates = {}
        for label in groups:
            group_gates[label] = all(r["groups"][label]["pulse_specific"]["rmse_over_zero"] is not None and
                                    r["groups"][label]["pulse_specific"]["rmse_over_zero"] <= .8 for r in rows)
        results.append(dict(**block, training_templates_pA={k:v.tolist() for k,v in templates.items()},
                            evaluation=rows, source_gates=source_gates, pooled_repeatability_gates=group_gates))
    return results


def database_inventory():
    path = BASE / "synphys_r2.1_small.sqlite"
    if sha(path) != DB_SHA:
        raise ValueError("Database hash changed")
    with sqlite3.connect(path.resolve().as_uri()+"?mode=ro", uri=True) as con:
        con.row_factory = sqlite3.Row
        pairs = [dict(row) for row in con.execute(
            "SELECT p.id pair_id,el.device_id source,p.has_synapse,p.has_electrical,s.id synapse_id,"
            "s.synapse_type,s.latency,s.psp_amplitude,s.psc_amplitude FROM pair p "
            "JOIN cell c ON c.id=p.pre_cell_id JOIN electrode el ON el.id=c.electrode_id "
            "LEFT JOIN synapse s ON s.pair_id=p.id WHERE p.experiment_id=2771 AND p.post_cell_id=15837 ORDER BY el.device_id")]
        for pair in pairs:
            pair["average_fit_QC"] = [dict(row) for row in con.execute(
                "SELECT clamp_mode,holding,manual_qc_pass,n_averaged_responses FROM avg_response_fit "
                "WHERE synapse_id=? ORDER BY clamp_mode,holding", (pair["synapse_id"],))]
        preparation = dict(con.execute("SELECT e.target_region,e.internal,e.acsf,e.target_temperature,"
            "s.species,s.age,s.sex,s.genotype FROM experiment e JOIN slice s ON e.slice_id=s.id WHERE e.id=2771").fetchone())
    assert [p["source"] for p in pairs if p["has_synapse"]] == ANNOTATED
    assert [p["source"] for p in pairs if any(q["clamp_mode"]=="vc" and q["manual_qc_pass"]==1
                                             for q in p["average_fit_QC"])] == VC_QC
    return dict(database_sha256=DB_SHA, preparation=preparation, pairs=pairs,
                QC_interpretation="QC belongs to each averaged fit's mode and holding, not to the connection as a whole")


class TrackedFetch(raw.CachedRanges):
    def __init__(self):
        super().__init__()
        self.used = {}

    def block(self, start):
        value = super().block(start)
        self.used[str(start)] = self.manifest["blocks"][str(start)]
        return value


def run(fetch=False):
    if OUTPUT.exists():
        raise FileExistsError("Existing incoming-chemical analysis must not be overwritten")
    for name, expected in SOURCE_FILES.items():
        assert sha(HERE/name) == expected
    inputs = json.loads((HERE/"electrical_star_vc_inputs_result.json").read_text())
    protocol = json.loads((HERE/"electrical_star_protocol_result.json").read_text())
    inventory = database_inventory()
    adc = {(r["sweep"],r["device"]):r for r in protocol["records"] if r["kind"]=="acquisition"}
    cache = BASE / "raw_ranges/1552517188.758"
    manifest = json.loads((cache/"manifest.json").read_text())
    initial = sum(b["bytes"] for b in manifest["blocks"].values())
    raw.URL, raw.CACHE, raw.LIMIT = manifest["remote"]["url"], cache, initial+32*1024*1024
    real = np.empty((10,6,12,400)); shifted = np.empty_like(real)
    baseline = np.empty((10,6,12)); shift_baseline = np.empty_like(baseline)
    durations = np.empty((10,6,12),int); offsets = np.empty((10,6,12),int)
    absolute_peak = np.empty((10,6,12)); centered_peak = np.empty_like(absolute_peak)
    command_rows = []; states = {}
    with (TrackedFetch() if fetch else OfflineRanges(cache)) as reader:
        assert reader.remote == manifest["remote"]
        with h5py.File(reader,"r") as f:
            for sweep in range(10):
                descriptors = {d["device"]:d for d in inputs["sweeps"][sweep]["devices"]}
                holds = {}
                for device, d in descriptors.items():
                    states.setdefault(device,{}).update(d["incremental_instrument_settings"])
                    assert states[device]["OperatingModeString"]=="V-Clamp"
                    assert states[device]["V-Clamp Holding Enable"]=="On"
                    holds[device] = float(states[device]["V-Clamp Holding Level"].split()[0])
                    assert abs(holds[device]-(-70 if sweep<5 else -55)) < .05
                target = adc[sweep,TARGET]
                assert target["unit"]=="A" and target["rate"]==RATE
                data = f[target["path"]+"/data"]
                for index, source in enumerate(SOURCES):
                    assert adc[sweep,source]["start"]==target["start"]
                    pulses = [p for p in descriptors[source]["command_segments"] if p["command_mV"]>1]
                    assert len(pulses)==12
                    for pulse_index, pulse in enumerate(pulses):
                        assert abs(pulse["command_mV"]-70)<.001
                        onset = round(pulse["start_s"]*RATE); offset = round(pulse["end_s"]*RATE)
                        duration = offset-onset
                        assert duration in [75,76]
                        for other,d in descriptors.items():
                            if other==source: continue
                            for segment in d["command_segments"]:
                                if segment["start_s"] < (offset+1400)/RATE and segment["end_s"] > (offset-1850)/RATE:
                                    assert abs(segment["command_mV"]-d["baseline_command_mV"]) < .005
                        values = (np.asarray(data[offset-1850:offset+1400],float)*target["conversion"]+target["offset"])*1e12
                        assert values.shape==(3250,) and np.isfinite(values).all()
                        current = values[1250:3250]; control = values[:2000]
                        real[sweep,index,pulse_index],baseline[sweep,index,pulse_index] = center_epoch(current,duration)
                        shifted[sweep,index,pulse_index],shift_baseline[sweep,index,pulse_index] = center_epoch(control,duration)
                        absolute_peak[sweep,index,pulse_index] = np.max(np.abs(current))
                        centered_peak[sweep,index,pulse_index] = np.max(np.abs(current-baseline[sweep,index,pulse_index]))
                        durations[sweep,index,pulse_index] = duration
                        offsets[sweep,index,pulse_index] = offset
                command_rows.append(dict(sweep=sweep, nominal_holding_mV=holds, target_path=target["path"],
                                         recording_start_s=target["start"]))
                print("EXTRACTED",sweep,"new_bytes",getattr(reader,"downloaded_this_session",0),flush=True)
        provenance = dict(remote=reader.remote, initial_cached_bytes=initial,
                          new_download_bytes=getattr(reader,"downloaded_this_session",0), used_blocks=reader.used)
    analysis = summarize(real,shifted,durations)
    arrays=dict(current_pA=real,shifted_current_pA=shifted,baseline_pA=baseline,
                shifted_baseline_pA=shift_baseline,duration_samples=durations,offset_samples=offsets,
                max_absolute_raw_pA=absolute_peak,max_absolute_centered_pA=centered_peak,time_ms=TIME_MS)
    if WAVES.exists():
        # Resume a report-write failure by checking every previously saved value.
        # Different data are never overwritten, and the completed JSON blocks reruns.
        with np.load(WAVES,allow_pickle=False) as previous:
            if set(previous.files)!=set(arrays) or any(not np.array_equal(previous[k],v) for k,v in arrays.items()):
                raise ValueError("Existing extracted waveforms differ from cached raw data")
    else:
        with WAVES.open("xb") as stream:
            np.savez_compressed(stream,**arrays)
    result = dict(version="electrical-star-incoming-chemical-v1",code_sha256=sha(Path(__file__)),
        raw_reader_sha256=sha(Path(raw.__file__)),offline_reader_sha256=sha(HERE/"allen_joint_inventory.py"),
        input_sha256=SOURCE_FILES,waveform_sha256=sha(WAVES),sources=SOURCES,target=TARGET,
        database=inventory,cells=protocol["selection"]["cells"],provenance=provenance,
        settings=dict(sample_rate_Hz=RATE,bin_ms=.1,alignment="actual recorded source command offset",
            baseline="source onset -10 to -2 ms",primary_window_offset_ms=[.5,15.],
            auxiliary_window_onset_ms=[0.,20.],shifted_control_ms=-25,
            train_evaluate=BLOCKS,pooled_primary_sources=ANNOTATED,VC_QC_subset=VC_QC,
            repeatability_threshold_RMSE_over_zero=.8,
            source_specificity="own template strictly better than source-4 template in all 3 evaluation records",
            time_specificity="own template strictly better than same-source shifted template in all 3 evaluation records",
            exclusion="none; all 720 pulse windows retained, including large current events"),
        commands=command_rows,primary_mask=PRIMARY.tolist(),time_ms=TIME_MS.tolist(),analysis=analysis,
        current_flags=dict(absolute_over_1nA=int(np.sum(absolute_peak>1000)),
                           baseline_centered_over_1nA=int(np.sum(centered_peak>1000)),
                           absolute_max_pA=float(absolute_peak.max()),
                           warning="Threshold flags only; not established clamp escape, exclusion, or origin classification"),
        claim_ceiling="BIO_EVIDENCE_L1 current observations; exposed-data development comparison; no independent biological validation",
        metric_verdict="NOT_IDENTIFIED; no calibrated conductance, hormone measurement or independent directional cost",
        limitations=["One mouse visual-cortex preparation, not hippocampal hormone data",
            "All 89 sweeps' numerical notebook summaries and pair annotations were exposed before this analysis",
            "12 pulses and time bins are nested within 3 evaluation records per holding, not independent biological samples",
            "Source-4 negative annotation is not an artifact-matched or pharmacological control",
            "Shifted control may contain preceding pulse tails; first and post-gap pulses are reported separately",
            "Command offset is not measured presynaptic spike time",
            "Both presynaptic and postsynaptic holding change; block differences do not identify reversal potential",
            "QC is mode- and holding-specific; source-0 and source-6 IC fits do not establish their VC quality"])
    with OUTPUT.open("x",encoding="utf-8") as stream:
        json.dump(result,stream,indent=2,allow_nan=False);stream.write("\n")
    print(json.dumps({"result":str(OUTPUT),"new_bytes":provenance["new_download_bytes"],
        "flags":result["current_flags"],"blocks":[{"holding":b["holding_mV"],"pooled":b["pooled_repeatability_gates"],
        "source_gates":b["source_gates"]} for b in analysis]}),flush=True)


if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--fetch-missing",action="store_true")
    args=parser.parse_args()
    run(args.fetch_missing)
