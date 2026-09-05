"""완료한 36파형을 원장에 등록하고 설정값·실제값 차이를 요약한다."""
import importlib.util
import json
from pathlib import Path
from population_reciprocity import ROOT, sha

HERE=Path(__file__).resolve().parent

def main():
    source=HERE/'intrinsic_waveforms_result.json'
    result=json.loads(source.read_text(encoding='utf-8'))
    assert len(result['records'])==36
    spec=importlib.util.spec_from_file_location('data_registry',ROOT/'.codex/hooks/data_registry.py')
    registry=importlib.util.module_from_spec(spec);spec.loader.exec_module(registry)
    summaries=[]
    for r in result['records']:
        path=ROOT/r['array_path'];assert sha(path)==r['array_sha256']
        registry.register(registry.DEFAULT_LEDGER,'allen_synphys','nwb-1574292898.139',
            f"producer-intrinsic-{r['sweep']}-{r['device']}",path,
            'https://allen-synphys.s3-us-west-2.amazonaws.com/synphys-1574292898.139.nwb',
            'Producer-selected intrinsic command and voltage; reused existing byte-range cache')
        c=r['comparison'];start,end=c['start_index']/r['rate'],c['stop_index']/r['rate']
        segments=[x for x in r['analysis']['command_segments'] if x['start_s']<=start+1/r['rate'] and x['end_s']>=end-1/r['rate']]
        assert len(segments)==1
        summaries.append(dict(sweep=r['sweep'],device=r['device'],protocol=r['stimulus'],
            actual_pA=segments[0]['current_pA'],specified_pA=c['pulse']['amplitude']*1e12,
            max_error_pA=c['amplitude_max_error_A']*1e12,
            delta_voltage_mV=c['last_100ms_median_mV']-c['pre_50ms_median_mV']))
    output=dict(source_sha256=sha(source),code_sha256=sha(Path(__file__)),new_bytes=result['new_bytes'],
        strict_amplitude_matches=result['matched'],records=summaries,
        limits='Voltage differences are descriptive, not resistance or spike classifications. No relaxed tolerance applied.')
    target=HERE/'intrinsic_waveforms_inventory_result.json'
    if target.exists():assert json.loads(target.read_text(encoding='utf-8'))==output
    else:
        with target.open('x',encoding='utf-8') as stream:json.dump(output,stream,indent=2)
    registry.register(registry.DEFAULT_LEDGER,'allen_synphys','nwb-1574292898.139','producer-intrinsic-inventory',target,
        'https://allen-synphys.s3-us-west-2.amazonaws.com/synphys-1574292898.139.nwb',
        'Complete 36-record command comparison; preserves strict mismatches')
    print(json.dumps(output,indent=2))

if __name__=='__main__':main()
