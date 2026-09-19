"""Audit the deposited Rey2025 response subset without selecting on recall effect.

Spike extrema are not recording boundaries. The candidate timing guard is not
proof of coverage and does not reconstruct behavioural correctness.
"""
import hashlib
import json
import platform
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import scipy
from scipy.io import loadmat

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DATA = ROOT/'data/external/hippocampal_reinstatement/rey2025_processed_v1'
EXPECTED = {'README.txt':'2fcda5b4414368d0ccefa7266fab9c5109e12b9ee4fa4ac99e34e667722eb81e',
            'Reyetal_CR_dataset.mat':'736ad3947a0185a65a9194b0bfc8140b14d14185cab622923980dcc98cd19a08'}


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def vector(value):
    return np.asarray(value,dtype=float).ravel()


def main():
    output = HERE/'rey_input_audit_result.json'
    if output.exists():
        raise FileExistsError('Preserve existing audit output')
    for name,digest in EXPECTED.items():
        if sha(DATA/name)!=digest:
            raise ValueError('Dataset identity changed: '+name)
    records = np.atleast_1d(loadmat(DATA/'Reyetal_CR_dataset.mat',squeeze_me=True,struct_as_record=False)['resp'])
    units,trials,problems = [],[],[]
    behavioural = defaultdict(list)
    vp_shapes,vp_padding,vp_nonterminal_padding = Counter(),0,0
    encoding_trials = 0
    for index,record in enumerate(records):
        session = int(record.sessionID)
        key = f'{session}:{int(record.channel_number)}:{str(record.cluster)}'
        responsive = np.asarray(record.responsive_Storiesindex,dtype=int).ravel().tolist()
        nonresponsive = np.asarray(record.nonresponsive_Storiesindex,dtype=int).ravel().tolist()
        if len(responsive)!=2 or len(nonresponsive)!=2 or sorted(responsive+nonresponsive)!=[1,2,3,4]:
            raise ValueError('Invalid story mapping')
        vp = np.asarray(record.spike_times_VP,dtype=object).ravel()
        for matrix in vp:
            matrix = np.asarray(matrix,float)
            if matrix.ndim!=2 or not np.isfinite(matrix).all():
                raise ValueError('Unexpected VP trial/padding schema')
            vp_shapes[str(matrix.shape)] += 1
            padding = matrix==10000
            vp_padding += int(np.count_nonzero(padding))
            vp_nonterminal_padding += int(np.count_nonzero(np.maximum.accumulate(padding,axis=1)&~padding))
        enc = np.asarray(record.spike_times_Enc,dtype=object).ravel()
        enc_counts = [len(np.atleast_1d(story)) for story in enc]
        encoding_trials += sum(enc_counts)
        recall = np.asarray(record.spike_times_Rec,dtype=object).ravel()
        timing = np.asarray(record.trecall_phasic_ms,dtype=object).ravel()
        has_recall = bool(recall.size)
        if has_recall and (recall.size!=4 or timing.size!=4):
            raise ValueError('Unexpected recall story schema')
        if not has_recall and timing.size:
            raise ValueError('Recall/timing mismatch')
        unit = dict(unit=key,index=index,session=session,site=str(record.recording_site),
                    responsive_identity=str(record.responsive_stilmulus),
                    nonresponsive_identity=str(record.nonresponsive_stilmulus),
                    responsive_stories=responsive,nonresponsive_stories=nonresponsive,
                    encoding_trials=enc_counts,has_recall=has_recall)
        units.append(unit)
        if not has_recall:
            continue
        for slot in range(4):
            spike_trials = np.atleast_1d(recall[slot])
            mention_times = vector(timing[slot])
            if len(spike_trials)!=len(mention_times):
                raise ValueError('Trial alignment mismatch')
            for trial,(spikes,mention) in enumerate(zip(spike_trials,mention_times)):
                spikes = vector(spikes)
                if not np.isfinite(spikes).all() or not np.isfinite(mention):
                    raise ValueError('Nonfinite spike or mention')
                if np.any(np.diff(spikes)<0):
                    problems.append(dict(unit=key,story=slot+1,trial=trial,issue='unsorted_spikes'))
                behaviour_key = f'{session}:{slot+1}:{trial}'
                row = dict(unit=key,session=session,site=unit['site'],story=slot+1,trial=trial,
                    behavioural_key=behaviour_key,responsive=(slot+1 in responsive),mention_ms=float(mention),
                    spike_count=len(spikes),spike_min_ms=float(spikes.min()) if len(spikes) else None,
                    spike_max_ms=float(spikes.max()) if len(spikes) else None,
                    mention_before_cue=bool(mention<0),mention_before_1500ms=bool(mention<1500),
                    mention_after_13000ms=bool(mention>13000),candidate_timing_guard=bool(1500<=mention<=13000))
                trials.append(row)
                behavioural[behaviour_key].append(row)
    if len({r['unit'] for r in units})!=len(units):
        raise ValueError('Duplicate unit identity')
    unique_trials = []
    for key,rows in behavioural.items():
        times = sorted({r['mention_ms'] for r in rows})
        if len(times)!=1:
            problems.append(dict(behavioural_key=key,issue='mention_disagreement',times_ms=times))
        unique_trials.append(dict(behavioural_key=key,neuron_records=len(rows),mention_times_ms=times,
            consistent=len(times)==1,candidate_timing_guard=all(r['candidate_timing_guard'] for r in rows)))
    recall_units = [u for u in units if u['has_recall']]
    summary = dict(units=len(units),sessions=len({u['session'] for u in units}),
        sites=dict(Counter(u['site'] for u in units)),recall_units=len(recall_units),
        recall_sessions=len({u['session'] for u in recall_units}),recall_sites=dict(Counter(u['site'] for u in recall_units)),
        encoding_neuron_trials=encoding_trials,recall_neuron_trials=len(trials),
        unique_behavioural_trials=len(unique_trials),
        candidate_neuron_trials=sum(t['candidate_timing_guard'] for t in trials),
        candidate_behavioural_trials=sum(t['candidate_timing_guard'] for t in unique_trials),
        negative_mentions=sum(t['mention_before_cue'] for t in trials),
        before_1500ms=sum(t['mention_before_1500ms'] for t in trials),
        after_13000ms=sum(t['mention_after_13000ms'] for t in trials),
        mention_range_ms=[min(t['mention_ms'] for t in trials),max(t['mention_ms'] for t in trials)],
        spike_range_ms=[min(t['spike_min_ms'] for t in trials if t['spike_count']),max(t['spike_max_ms'] for t in trials if t['spike_count'])],
        vp_trial_matrix_shapes=dict(vp_shapes),vp_padding_entries=vp_padding,
        vp_nonterminal_padding_entries=vp_nonterminal_padding)
    result = dict(schema='hippocampal.rey2025.input-audit.v1',source_sha256=sha(__file__),
        inputs={name:dict(path=(DATA/name).relative_to(ROOT).as_posix(),bytes=(DATA/name).stat().st_size,sha256=digest) for name,digest in EXPECTED.items()},
        environment=dict(python=platform.python_version(),numpy=np.__version__,scipy=scipy.__version__),
        summary=summary,units=units,trials=trials,behavioural_trials=unique_trials,problems=problems,
        interpretation=dict(selection='Author-deposited encoding-responsive subset; no filtering by is_signif_recall.',
            time='Recall spikes and mention times in ms relative to context cue; MATLAB story indices converted explicitly.',
            guard='1500<=mention<=13000 is a proposed full postcue premention window inside nominal task duration; not proof of acquisition coverage.',
            missing='No per-trial correctness, participant mapping, acquisition-boundary or coverage fields. Spike extrema cannot prove coverage.',
            vp='10000 padding must be removed for future VP analyses; VP combines before and after the memory task.',
            claim='Input audit only. No recall effect, CE mechanism, synaptic plasticity or metric estimate computed.'))
    with output.open('x',encoding='utf-8') as stream:
        json.dump(result,stream,ensure_ascii=False,indent=2)
    print(json.dumps(dict(summary=summary,problems=problems,output=str(output)),ensure_ascii=True))


if __name__=='__main__':
    main()
