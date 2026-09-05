"""Scientific figure for completed noise-conditioned geometry predictions."""
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE=Path(__file__).resolve().parent
NAMES={"depth_count_context":"Depth + count / no distance","depth_count_radial":"Depth + count / isotropic",
       "noise_context":"+ Noise / no distance","noise_radial":"+ Noise / isotropic","noise_z_radial":"+ Noise / Z anisotropy",
       "noise_z_plane_radial":"+ Noise / XY boundary","noise_z_axis_radial":"+ Noise / Z-only boundary",
       "noise_x_radial":"+ Noise / X anisotropy","noise_y_radial":"+ Noise / Y anisotropy"}


def main():
    result=json.loads((HERE/"allen_noise_axis_observation_result.json").read_text())
    previous_path=HERE/"allen_hidden_axis_metric_result.json"
    assert hashlib.sha256(previous_path.read_bytes()).hexdigest()=="91e0cb2c31c37bd2201cef454ef02483a45c8e12a359c7ac31768c3283572520"
    previous=json.loads(previous_path.read_text())
    plt.rcParams.update({"font.family":"DejaVu Sans","font.size":9,"axes.spines.top":False,"axes.spines.right":False,"svg.fonttype":"none"})
    fig,axes=plt.subplots(2,2,figsize=(13.2,8.8));a,b,c,d=axes.flat
    blue="#157f86";orange="#c77822";gray="#8d969d"
    scores=result["summary"]["scores"]
    for i,row in enumerate(scores):
        name=row["model"];color=gray if name.startswith("depth") else orange if name=="noise_z_radial" else blue
        a.scatter(row["log_loss"],i,color=color,s=35)
        a.text(row["log_loss"]+.0004,i,f"{row['log_loss']:.6f}",va="center",fontsize=8,color=color)
    a.set(yticks=range(len(scores)),yticklabels=[NAMES[r["model"]] for r in scores],xlabel="Out-of-fold log loss (lower is better)")
    a.set_xlim(min(r["log_loss"] for r in scores)-.0015,max(r["log_loss"] for r in scores)+.004)
    a.invert_yaxis();a.set_title("A. Same pairs and donor folds",loc="left",fontweight="bold")
    comparisons=[("noise_z_radial","noise_radial","Z - isotropic"),("noise_x_radial","noise_radial","X - isotropic"),
                 ("noise_y_radial","noise_radial","Y - isotropic"),("noise_z_plane_radial","noise_radial","XY boundary - isotropic"),
                 ("noise_z_radial","noise_z_plane_radial","Z - XY boundary")]
    for i,(candidate,reference,label) in enumerate(comparisons):
        row=next(r for r in result["comparisons"] if r["candidate"]==candidate and r["reference"]==reference)["log_loss_difference"]
        mean=row["pair_weighted_mean"];lo,hi=row["pair_weighted_cluster_percentile95"]
        color=orange if candidate=="noise_z_radial" else blue
        b.errorbar(mean,i,xerr=[[mean-lo],[hi-mean]],fmt="o",color=color,capsize=3,ms=5)
    b.set(yticks=range(len(comparisons)),yticklabels=[r[2] for r in comparisons],xlabel="Log-loss difference (negative favors candidate)")
    b.invert_yaxis();b.axvline(0,color=gray,ls=":");b.ticklabel_format(axis="x",style="sci",scilimits=(-3,3))
    b.set_title("B. Direction-cost comparisons with noise",loc="left",fontweight="bold")
    old=sorted([r for r in previous["radial_profiles"] if r["model"]=="z_radial"],key=lambda r:r["fold"])
    new=sorted([r for r in result["radial_profiles"] if r["model"]=="noise_z_radial"],key=lambda r:r["fold"])
    c.plot(range(5),[r["w"] for r in old],"o--",color=gray,label="Earlier: context only")
    c.plot(range(5),[r["w"] for r in new],"o-",color=orange,label="Depth + count + noise")
    c.axhline(.5,color=gray,ls=":");c.text(4.1,.51,"isotropic",fontsize=8,color=gray)
    c.set(xlabel="Held-out donor fold",ylabel="Training-selected Z weight w",xticks=range(5),ylim=(-.04,1.04),xlim=(-.3,5.1))
    c.set_title("C. w=0: XY boundary; w=1: Z-only boundary",loc="left",fontweight="bold");c.legend(frameon=False,fontsize=8)
    noise=np.array([r["mean_qc_pass_IC_noise_V"]*1e6 for r in result["cell_noise_summary"] if r["mean_qc_pass_IC_noise_V"] is not None])
    if len(noise):
        lo,hi=noise.min(),noise.max()
        if lo==hi:lo/=2;hi*=2
        d.hist(noise,bins=np.geomspace(lo,hi,26),color=blue,alpha=.8);d.set_xscale("log")
    d.set(xlabel="Mean QC-pass IC recording noise (microvolts)",ylabel="Postsynaptic cells")
    d.set_title("D. Recorded noise is not synaptic standard error",loc="left",fontweight="bold")
    d.text(.98,.94,f"{len(noise):,} valid / {result['summary']['missing_noise_cells']:,} missing\nAll target cells collected",ha="right",va="top",transform=d.transAxes,fontsize=8)
    for ax in [a,b,c]:ax.grid(axis="x",alpha=.15)
    fig.suptitle("Fixed neuron positions: noise summaries and three-dimensional connection costs",x=.04,ha="left",fontsize=14,fontweight="bold")
    fig.text(.04,.028,"Internal development comparison; raw axes are not independently registered cortical axes.\nIntervals resample donors with predictions fixed. Acquisition noise, QC and final counts may reflect selection; no detection calibration is claimed.",fontsize=8.5,color="#46515b")
    fig.tight_layout(rect=(.01,.075,1,.95),h_pad=2.4,w_pad=2.4)
    for suffix in ["png","svg"]:
        path=HERE/("allen_noise_axis_observation."+suffix)
        if path.exists():raise FileExistsError(path)
        fig.savefig(path,dpi=180,facecolor="white")
        print(path.name,path.stat().st_size,hashlib.sha256(path.read_bytes()).hexdigest())
    plt.close(fig)


if __name__=="__main__":main()
