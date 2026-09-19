"""Observed waveforms for preselected first-QC sweeps in three protocols."""
import json

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from vc20hz_source_inputs import HERE, ROOT, sha


def main():
    image_path=HERE/'figures/mixed_clamp_observed_waveforms.png'
    receipt_path=HERE/'mixed_clamp_waveform_figure.json'
    if image_path.exists() or receipt_path.exists():raise FileExistsError('Preserve figure outputs')
    raw=HERE/'mixed_clamp_raw_inputs_result.json';pulses=HERE/'mixed_clamp_pulses_result.json'
    assert sha(raw)=='311e4ecca0709b306651090ca210d12637d92a32659ed13dc9a9609d018b323b'
    assert sha(pulses)=='f023db5b41d40c4ccbb5bb91c89af926898f38d7fb607c09b8446bb341aa76c7'
    inputs=json.loads(raw.read_text(encoding='utf-8'));inventory=json.loads(pulses.read_text(encoding='utf-8'))
    assert sha(ROOT/inputs['arrays']['path'])==inputs['arrays']['sha256']
    records={(r['sweep'],r['device'],r['kind']):r for r in inputs['records']}
    selected=((69,'50 Hz'),(77,'20 Hz'),(82,'100 Hz'))
    pulse_numbers=(0,7,8,11);colors=('#2166ac','#d6604d','#4d9221','#762a83');styles=('-','--','-.',':')
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    fig,axes=plt.subplots(3,3,figsize=(13,8.8),sharex=True,sharey='col')
    evidence=[]
    with np.load(ROOT/inputs['arrays']['path'],allow_pickle=False) as arrays:
        for row,(sweep,label) in enumerate(selected):
            meta=next(s for s in inventory['sweeps'] if s['sweep']==sweep)
            source=next(r for r in meta['records'] if r['device_id']==6)
            target=next(r for r in meta['records'] if r['device_id']==1)
            assert source['qc_pass']==target['qc_pass']==1
            schedule={p['pulse_number']:p for p in meta['source_pulses'][str(source['id'])]}
            signals=[records[sweep,6,'command'],records[sweep,6,'acquisition'],records[sweep,1,'acquisition']]
            for number,color,style in zip(pulse_numbers,colors,styles):
                p=schedule[number];rate=signals[0]['rate'];onset=p['onset_time']
                a=int(np.ceil((onset-.002)*rate-1e-8));b=int(np.ceil((onset+.008)*rate-1e-8))
                pre_end=int(np.ceil((onset-.0002)*rate-1e-8))
                assert 0<=a<pre_end<b<=signals[0]['samples']
                x=(np.arange(a,b)/rate-onset)*1000
                baseline=None
                for col,(signal,scale) in enumerate(zip(signals,(1e12,1e3,1e12))):
                    values=arrays[signal['array_key']]
                    y=values[a:b].copy()
                    if col==2:
                        baseline=float(values[a:pre_end].mean());y-=baseline
                    axes[row,col].plot(x,y*scale,color=color,linestyle=style,lw=1.2,label=f'Pulse {number+1}')
                evidence.append(dict(sweep=sweep,protocol=label,pulse_number=number,pulse_id=p['id'],
                    onset_s=onset,sample_start=a,sample_stop=b,pre_stop=pre_end,target_baseline_A=baseline,
                    array_keys=[r['array_key'] for r in signals]))
            axes[row,0].set_ylabel(f'{label} | sweep {sweep}\nCommand (pA)')
            axes[row,1].set_ylabel('Source voltage (mV)')
            axes[row,2].set_ylabel('Target current change (pA)')
            for ax in axes[row]:
                ax.axvline(0,color='#555555',lw=.6,alpha=.7)
                ax.grid(axis='y',alpha=.15);ax.set_xlim(-2,8)
    for ax,title in zip(axes[0],('Injected current: device 6','Observed voltage: device 6','Observed VC current: device 1')):
        ax.set_title(title,pad=10)
    for ax in axes[-1]:ax.set_xlabel('Time from source command onset (ms)')
    handles,labels=axes[0,0].get_legend_handles_labels()
    fig.legend(handles,labels,loc='upper center',bbox_to_anchor=(.5,.925),ncol=4,frameon=False)
    fig.suptitle('Same recorded pair across three stimulation protocols',y=.98,fontsize=16)
    fig.text(.5,.942,'First jointly QC-passing sweep in each protocol; four predetermined pulses',ha='center',fontsize=10)
    fig.text(.03,.025,'Target current is centered by the mean at [-2, -0.2) ms. These are observed waveforms, not isolated PSCs.\n'
        'One pair and different sweep order/state; no independent frequency-effect or plasticity estimate.',fontsize=9)
    fig.tight_layout(rect=(.015,.075,.995,.88))
    image_path.parent.mkdir(parents=True,exist_ok=True);fig.savefig(image_path,dpi=160);plt.close(fig)
    receipt=dict(source_sha256=sha(__file__),raw_result_sha256=sha(raw),pulse_result_sha256=sha(pulses),
        arrays=inputs['arrays'],matplotlib=matplotlib.__version__,numpy=np.__version__,selected=evidence,
        image=dict(path=image_path.relative_to(ROOT).as_posix(),sha256=sha(image_path)),
        selection='First joint recording-QC pass in each50/20/100Hz block; source6 pair121566; pulses1/8/9/12 chosen before raw waveform audit.')
    with receipt_path.open('x',encoding='utf-8') as stream:json.dump(receipt,stream,indent=2,allow_nan=False)
    print(json.dumps(dict(image=str(image_path),traces=len(evidence)*3)))


if __name__=='__main__':main()
