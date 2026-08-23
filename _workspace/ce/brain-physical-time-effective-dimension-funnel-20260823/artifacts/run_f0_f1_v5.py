"""v5 rerun: v4 floor apparatus with explicit constant-truth fail-closed hook."""
from __future__ import annotations
import math
from funnel_core_v2 import ROOT,sha
import run_f0_f1_v4 as prior
prior.F0=ROOT/'f0-receipt-v4.json';prior.F1=ROOT/'f1-receipt-v5.json'
_old=prior.spearman
def spearman(a,b):
 r=_old(a,b)
 return r if math.isfinite(r) else float('nan')
prior.spearman=spearman
if __name__=='__main__':prior.main()
