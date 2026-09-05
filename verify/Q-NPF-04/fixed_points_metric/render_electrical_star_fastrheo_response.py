"""Render observed FastRheo eligibility; no model curves are shown."""
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

HERE=Path(__file__).resolve().parent


def main():
    output=HERE/'electrical_star_fastrheo_response'
    if output.with_suffix('.png').exists() or output.with_suffix('.svg').exists():raise FileExistsError(output)
    result=json.loads((HERE/'electrical_star_fastrheo_response_result.json').read_text())
    records=result['records'];devices=result['specification']['devices']
    excursion=np.array([[c['response_peak_abs_delta_mV'] for c in r['channels']] for r in records])
    baseline=np.array([[c['baseline_delta_from_anchor_mV'] for c in r['channels']] for r in records])
    fig,axes=plt.subplots(2,2,figsize=(12,10),layout='constrained')
    im=axes[0,0].imshow(excursion,aspect='auto',vmin=0,vmax=110,cmap='magma',origin='upper')
    axes[0,0].set(title='A  Recorded peak |delta V|, 25-100 ms',ylabel='Sweep',xlabel='Device (* primary)')
    axes[0,0].set_xticks(range(7),[str(d)+('*' if d in [4,1,2,5] else '') for d in devices])
    axes[0,0].set_yticks(range(19),[r['sweep'] for r in records])
    for i,row in enumerate(records):
        for j,c in enumerate(row['channels']):
            if c['quality_pass']:axes[0,0].plot(j,i,'o',mfc='none',mec='cyan',ms=7,mew=1.3)
    fig.colorbar(im,ax=axes[0,0],label='mV; cyan circles pass all channel checks')
    im=axes[0,1].imshow(baseline,aspect='auto',vmin=-6,vmax=6,cmap='coolwarm',origin='upper')
    axes[0,1].set(title='B  Pre-pulse baseline change from sweep 16',ylabel='Sweep',xlabel='Device')
    axes[0,1].set_xticks(range(7),devices);axes[0,1].set_yticks(range(19),[r['sweep'] for r in records])
    fig.colorbar(im,ax=axes[0,1],label='mV; accepted operating range +/-2 mV')
    for ax,device,label in [(axes[1,0],4,'C'),(axes[1,1],6,'D')]:
        for sweep in [16,17,24,30]:
            row=next(r for r in records if r['sweep']==sweep)
            c=next(c for c in row['channels'] if c['device']==device)
            values=np.asarray(c['waveform_mV_0p1ms'])-c['baseline_mV']
            ax.plot((np.arange(len(values))+.5)*.1,values,label=f'Sweep {sweep}',lw=1.3)
        ax.axvspan(25,28,color='green',alpha=.1,label='3 ms current command')
        ax.axhline(10,color='black',ls=':',lw=1);ax.axhline(-10,color='black',ls=':',lw=1)
        ax.set(xlim=(15,100),xlabel='Time within recording (ms)',ylabel='Recorded delta V (mV)',
               title=f'{label}  Device {device}: observed voltage')
        ax.legend(fontsize=8,loc='upper right');ax.grid(alpha=.15)
    fig.suptitle('Only sweep 16 passes the full seven-cell small-response gate: input rank 7 -> 1\n'
                 '0.1 ms means shown; QC used 0.02 ms samples. Prediction was not executed.',fontsize=12)
    fig.savefig(output.with_suffix('.png'),dpi=170)
    fig.savefig(output.with_suffix('.svg'))
    plt.close(fig)


if __name__=='__main__':main()
