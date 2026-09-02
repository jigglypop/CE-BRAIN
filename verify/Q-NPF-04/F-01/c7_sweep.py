# C7. The practical-statistic certificate swept over loop gain: does the
# delay-visibility / gain-efficacy-separability frontier of C3 also hold for a
# CONCRETE estimator (S1 power, S2 coherence, S3 rms group delay, S4 paired
# instrumental group-delay scale)?
import sys, os, json, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fwd, c6_practical as c6

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "result_c7_sweep.json")
RHO_LIST = (0.40, 0.60, 0.80)
c6.N_REP = 150

def run(rho):
    c6.RHO0 = rho
    c6.OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "result_c6_rho%02d.json" % round(rho * 100))
    c6.main()
    return json.load(open(c6.OUT, encoding="utf-8"))

def main():
    t0 = time.time(); rows = []
    for rho in RHO_LIST:
        print("\n===== rho0 = %.2f =====" % rho)
        r = run(rho)
        rows.append(dict(rho0=rho,
                         channel_norms=r["channel_norms"],
                         angles=r["channel_angles_deg"],
                         null_sd=r["null_sd"],
                         placebo_mean=r["placebo_mean"],
                         z=dict((w, r["worlds"][w]["z_vs_placebo"]) for w in r["worlds"]),
                         pass_CA=r["pass_CA_each_channel_norm_ge_2"],
                         pass_CB=r["pass_CB_all_angles_ge_15"]))
    res = dict(script="c7_sweep.py", seed=fwd.SEED, n_rep=c6.N_REP,
               elapsed_s=round(time.time() - t0, 1), rows=rows,
               n_pass_all=sum(1 for r in rows if r["pass_CA"] and r["pass_CB"]))
    json.dump(res, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\n%-6s %10s %10s %10s %10s %10s %10s" %
          ("rho0","|z|gain","|z|eff","|z|delay","ang_ge","ang_gd","ang_ed"))
    for r in rows:
        print("%-6.2f %10.2f %10.2f %10.3f %10.2f %10.2f %10.2f" %
              (r["rho0"], r["channel_norms"][0], r["channel_norms"][1],
               r["channel_norms"][2], r["angles"]["gain_eff"],
               r["angles"]["gain_delay"], r["angles"]["eff_delay"]))
    print("pass both:", res["n_pass_all"], "/", len(rows), " elapsed", res["elapsed_s"])

if __name__ == "__main__":
    main()
