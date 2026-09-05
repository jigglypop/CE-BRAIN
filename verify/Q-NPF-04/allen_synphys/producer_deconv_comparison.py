"""고정 소스의 순수 수치 함수를 사용해480개 후보 입력의 진폭을 DB와 비교한다."""
import ast
import json
from pathlib import Path
import numpy as np
from scipy.special import lambertw
from reference_spike_audit import reference,sha
from superficial_ee_eligibility import save

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];SNAP=HERE/'source_snapshots'

def selected_functions(path,names,namespace):
    tree=ast.parse(path.read_text(encoding='utf-8'))
    nodes=[x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name in names]
    assert {x.name for x in nodes}==set(names)
    exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),'exec'),namespace)

def main():
    inputs=HERE/'producer_input_reconstruction_result.json';dbfile=HERE/'producer_pulse_fits_result.json'
    source_names=['allen971__neuroanalysis__fitting__psp.py','allen971__neuroanalysis__event_detection.py','allen971__fit_scale_offset.py','aisynphys__pulse_response_strength.py']
    save('producer_deconv_comparison_contract.json',dict(
        question='Do source-informed candidate inputs reproduce stored deconvolved reconvolved amplitudes?',
        scope='All240 responses and240 assigned baselines; cross-version numerical reproduction audit, not independent biology.',
        method='Execute selected unchanged AST function bodies; Psp static numerical functions, deconvolution, deconv_filter and scale-offset only. No nonlinear optimizer needed.',
        alignment='Both response and baseline use response data_start_time minus DB first_spike_time, as get_tseries specifies.',
        fixed='DB synapse rise/decay/latency; rise_power2; IC lowpass2000; producer fit interval and baseline subtraction.',
        tolerance='Absolute1e-9 V plus relative1e-4 against DB reconvolved amplitude. No post-result parameter adjustment.',
        tests='Analytic template scale/offset versus independent least squares; finite arrays; all inputs hashed; deconvolved kinetic values compared to stored metadata.',
        limits='Previous reconstruction uses mixed pinned versions; missing DB blobs prevent independent array equality; source-function extraction is not full pipeline execution.',
        inputs={p.name:sha(p) for p in [inputs,dbfile]},sources={n:sha(SNAP/n) for n in source_names},code_sha256=sha(Path(__file__))))
    TSeries,_,_=reference()
    from neuroanalysis import filter
    env=dict(np=np,lambertw=lambertw,TSeries=TSeries,filter=filter)
    tree=ast.parse((SNAP/source_names[0]).read_text(encoding='utf-8'))
    cls=next(x for x in tree.body if isinstance(x,ast.ClassDef) and x.name=='Psp')
    keep={'_psp_inner','_psp_max_time','psp_func','_compute_rise_tau','_compute_rise_time'}
    cls.bases=[];cls.decorator_list=[];cls.body=[x for x in cls.body if isinstance(x,ast.FunctionDef) and x.name in keep]
    assert {x.name for x in cls.body}==keep
    exec(compile(ast.Module(body=[cls],type_ignores=[]),'<pinned Psp numerical functions>','exec'),env)
    selected_functions(SNAP/source_names[1],['exp_deconvolve','exp_deconv_psp_params'],env)
    selected_functions(SNAP/source_names[2],['fit_scale_offset'],env)
    selected_functions(SNAP/source_names[3],['deconv_filter'],env)
    template=np.linspace(-1,1,50)**2;signal=2.5*template-.3
    fit=np.array(env['fit_scale_offset'](signal,template));independent=np.linalg.lstsq(np.column_stack([template,np.ones(50)]),signal,rcond=None)[0]
    assert np.allclose(fit,independent,atol=1e-12)
    candidates=json.loads(inputs.read_text(encoding='utf-8'));source=json.loads(dbfile.read_text(encoding='utf-8'));syn=source['synapse']
    stored={(r['sweep'],r['pulse']):r for r in source['records']}
    da,dr,dp,dd=env['exp_deconv_psp_params'](amp=1,rise_time=syn['psp_rise_time'],rise_power=2,decay_tau=syn['psp_decay_tau'])
    path=ROOT/candidates['array_path'];assert sha(path)==candidates['array_sha256'];rows=[]
    with np.load(path,allow_pickle=False) as archive:
        for rec in candidates['records']:
            original=stored[rec['sweep'],rec['pulse']];fits=original['fits'][0]
            t0=original['pulse_response']['data_start_time']-original['stim_pulse']['first_spike_time']
            for label,prefix in [('response',''),('baseline','baseline_')]:
                array=archive[rec['arrays'][label]['key']];trace=TSeries(array,sample_rate=20000,t0=t0)
                filtered=env['deconv_filter'](trace,None,tau=syn['psp_decay_tau'],lowpass=2000,remove_artifacts=False,bsub=True)
                window=filtered.time_slice(syn['latency']-.001,syn['latency']+syn['psp_rise_time']+.001)
                template=env['Psp'].psp_func(window.time_values,xoffset=syn['latency'],yoffset=0,amp=1,rise_time=dr,decay_tau=dd,rise_power=dp)
                scale,offset=env['fit_scale_offset'](window.data,template);amplitude=float(scale/da)
                expected=fits[prefix+'dec_fit_reconv_amp'];assert np.isfinite(amplitude) and expected is not None
                rows.append(dict(sweep=rec['sweep'],pulse=rec['pulse'],kind=label,amplitude_V=amplitude,stored_V=expected,
                    error_uV=(amplitude-expected)*1e6,within_tolerance=bool(np.isclose(amplitude,expected,atol=1e-9,rtol=1e-4)),fit_samples=len(window)))
    summary={}
    for label in ['response','baseline']:
        rr=[r for r in rows if r['kind']==label];error=np.array([r['error_uV'] for r in rr])
        summary[label]=dict(n=len(rr),matches=sum(r['within_tolerance'] for r in rr),median_abs_error_uV=float(np.median(np.abs(error))),max_abs_error_uV=float(np.max(np.abs(error))))
    save('producer_deconv_comparison_result.json',dict(contract_sha256=sha(HERE/'producer_deconv_comparison_contract.json'),records=rows,summary=summary,
        derived_template=dict(amplitude=float(da),rise_time=float(dr),rise_power=float(dp),decay_tau=float(dd)),
        stored_template={k:source['records'][0]['fits'][0][k] for k in ['dec_fit_rise_time','dec_fit_decay_tau']},new_data_bytes=0))
    print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
