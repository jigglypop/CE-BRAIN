"""Stoichiometry and conditional fixed-point hormone models, all formal L0.

No kinetic parameter below is fitted to a brain experiment. Formula identity,
reaction balance, receptor kinetics and a spatial cost metric are distinct claims.
"""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import re
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
BASE = Path(__file__).resolve().parent
FORMULAS = ROOT / "data/external/hippocampal_hormone_chemistry_20260906/pubchem_six_hormones.json"
FORMULAS_SHA256 = "33a13598a571c455cd0e3f8bfebedddebb2eb460c35eae67b59919eafa708571"

# Rhea participants denote explicit protonation states; NADP+ is a biochemical
# oxidation-state name, whereas its whole-molecule net charge here is -3.
SPECIES = {
    "glutamate": ("C5H8NO4", -1, "CHEBI:29985"),
    "proton": ("H", 1, "CHEBI:15378"),
    "GABA": ("C4H9NO2", 0, "CHEBI:59888"),
    "carbon_dioxide": ("CO2", 0, "CHEBI:16526"),
    "ATP": ("C10H12N5O13P3", -4, "CHEBI:30616"),
    "cAMP": ("C10H11N5O6P", -1, "CHEBI:58165"),
    "diphosphate": ("HO7P2", -3, "CHEBI:33019"),
    "estradiol": ("C18H24O2", 0, "CHEBI:16469"),
    "estrone": ("C18H22O2", 0, "CHEBI:17263"),
    "NADP": ("C21H25N7O17P3", -3, "CHEBI:58349"),
    "NADPH": ("C21H26N7O17P3", -4, "CHEBI:57783"),
    "cortisone": ("C21H28O5", 0, "RHEA:68616 participant"),
    "cortisol": ("C21H30O5", 0, "PUBCHEM:5754"),
    "testosterone": ("C19H28O2", 0, "RHEA:38191 participant"),
    "oxygen": ("O2", 0, "CHEBI:15379"),
    "water": ("H2O", 0, "CHEBI:15377"),
    "formate": ("CHO2", -1, "RHEA:38191 participant"),
    # Only the reacting FMN moiety; the unchanged reductase protein cancels.
    "reductase_FMN_reduced": ("C17H21N4O9P", -2, "RHEA:38191 reactive moiety"),
    "reductase_FMN_oxidized": ("C17H18N4O9P", -3, "RHEA:38191 reactive moiety"),
}

# Signed stoichiometric coefficients: products minus reactants. The signed
# orientation is bookkeeping, not a claim about in-vivo flux or irreversibility.
REACTIONS = {
    "glutamate_decarboxylase": {
        "source": "https://www.rhea-db.org/rhea/17785",
        "stoichiometry": {"glutamate": -1, "proton": -1, "GABA": 1, "carbon_dioxide": 1},
    },
    "adenylyl_cyclase": {
        "source": "https://www.rhea-db.org/rhea/15389",
        "stoichiometry": {"ATP": -1, "cAMP": 1, "diphosphate": 1},
    },
    "estradiol_dehydrogenation": {
        "source": "https://www.rhea-db.org/rhea/24616",
        "stoichiometry": {"estradiol": -1, "NADP": -1, "estrone": 1, "NADPH": 1, "proton": 1},
    },
    "cortisone_reduction": {
        "source": "https://www.rhea-db.org/rhea/68616",
        "stoichiometry": {"cortisone": -1, "NADPH": -1, "proton": -1, "cortisol": 1, "NADP": 1},
    },
    "aromatase_reductase_donor": {
        "source": "https://www.rhea-db.org/rhea/38191",
        "stoichiometry": {"testosterone": -1, "reductase_FMN_reduced": -3, "oxygen": -3,
                          "estradiol": 1, "formate": 1, "reductase_FMN_oxidized": 3,
                          "water": 4, "proton": 4},
    },
    "aromatase_NADPH_coupled_net": {
        "source": "https://www.rhea-db.org/rhea/38191",
        "derivation": "Rhea reaction plus 3*(NADPH + oxidized reductase + 2H+ -> NADP + reduced reductase); coupled net bookkeeping, not directly quoted Rhea equation",
        "stoichiometry": {"testosterone": -1, "NADPH": -3, "oxygen": -3, "proton": -2,
                          "estradiol": 1, "formate": 1, "NADP": 3, "water": 4},
    },
}


def atoms(formula: str) -> dict[str, int]:
    tokens = list(re.finditer(r"([A-Z][a-z]?)([0-9]*)", formula))
    if not tokens or "".join(m.group() for m in tokens) != formula:
        raise ValueError("Only explicit flat molecular formulas are supported")
    out = Counter()
    for match in tokens:
        number = int(match[2] or 1)
        if number < 1:
            raise ValueError("Atom counts must be positive")
        out[match[1]] += number
    return dict(out)


def balance(stoichiometry: dict[str, int]) -> dict:
    residual = Counter()
    charge = 0
    for name, coefficient in stoichiometry.items():
        formula, net_charge, _ = SPECIES[name]
        for atom, count in atoms(formula).items():
            residual[atom] += coefficient * count
        charge += coefficient * net_charge
    nonzero = {key: value for key, value in sorted(residual.items()) if value}
    return {"atom_residual": nonzero, "charge_residual": charge,
            "balanced": not nonzero and charge == 0}


def occupancy(t, hormone: float, kon: float, koff: float, initial=0.):
    """Fraction occupied for one receptor pool, constant free ligand (nM, min)."""
    if hormone < 0 or kon <= 0 or koff <= 0 or not 0 <= initial <= 1:
        raise ValueError("Invalid binding model parameter")
    t = np.asarray(t, dtype=float)
    if np.any(t < 0):
        raise ValueError("Time must be nonnegative")
    rate = kon * hormone + koff
    steady = kon * hormone / rate
    return steady + (initial - steady) * np.exp(-rate * t)


def two_receptor_effect(h, k_m=1., k_g=100.):
    """Illustrative independent MR/GR pools with opposing equal downstream gain."""
    h = np.asarray(h, dtype=float)
    if np.any(h < 0) or not 0 < k_m < k_g:
        raise ValueError("Require nonnegative dose and 0 < K_M < K_G")
    return h / (k_m + h) - h / (k_g + h)


def cost_metric(edges, conductances):
    """Reciprocal dissipative candidate only: K=sum c*d*d.T; g=K^-1.

    Cartesian edge vectors have units m, nonnegative effective conductances S.
    The inputs must already be independently calibrated as a reciprocal linear
    component; PSC amplitudes, signed synaptic weights and hormone levels are
    not such calibration. No regularizing background is inserted.
    """
    edges = np.asarray(edges, dtype=float)
    c = np.asarray(conductances, dtype=float)
    if (edges.ndim != 2 or edges.shape[1] != 3 or c.shape != (len(edges),)
            or not np.isfinite(edges).all() or not np.isfinite(c).all() or np.any(c < 0)):
        raise ValueError("Require finite 3D vectors and nonnegative conductances")
    K = np.einsum("e,ei,ej->ij", c, edges, edges)
    eigenvalues = np.linalg.eigvalsh(K)
    if eigenvalues[-1] <= 0 or eigenvalues[0] <= 1e-12 * eigenvalues[-1]:
        raise ValueError("Positive edges do not numerically span three dimensions")
    return K, np.linalg.inv(K)


def calculate():
    formula_bytes = FORMULAS.read_bytes()
    if sha256(formula_bytes).hexdigest() != FORMULAS_SHA256:
        raise ValueError("PubChem snapshot does not match the recorded source")
    molecular = json.loads(formula_bytes)["PropertyTable"]["Properties"]
    t = np.linspace(0, 10, 201)
    slow = occupancy(t, 10., .01, .1)
    fast = occupancy(t, 10., .1, 1.)
    dose = np.logspace(-3, 5, 401)
    effect = two_receptor_effect(dose)
    edges = np.eye(3) * 1e-4
    c0 = np.ones(3) * 1e-9
    c1 = np.array([2., .5, 1.]) * 1e-9
    K0, g0 = cost_metric(edges, c0)
    K1, g1 = cost_metric(edges, c1)
    scalar_gradient = np.array([1., 2., -1.])
    scalar_pullback = np.outer(scalar_gradient, scalar_gradient) * 3.
    return {
        "version": "hippocampal-hormone-chemistry-v1",
        "claim_ceiling": "BIO_EVIDENCE_L0; no fitted brain metric or in-vivo reaction flux",
        "source_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        "pubchem_sha256": sha256(FORMULAS.read_bytes()).hexdigest(),
        "molecules": molecular,
        "species": {k: {"formula": v[0], "charge": v[1], "identifier_or_participant_source": v[2]} for k, v in SPECIES.items()},
        "reactions": {k: {**v, **balance(v["stoichiometry"])} for k, v in REACTIONS.items()},
        "kinetics_synthetic": {
            "free_ligand_nM": 10., "Kd_nM_both": 10.,
            "kon_nM_inverse_min_inverse": [.01, .1], "koff_min_inverse": [.1, 1.],
            "steady_occupancy_both": .5, "time_min": t.tolist(),
            "slow_fraction": slow.tolist(), "fast_fraction": fast.tolist(),
            "tau_min": [5., .5],
            "at_one_min": [float(occupancy(1., 10., .01, .1)), float(occupancy(1., 10., .1, 1.))],
        },
        "opposing_receptor_synthetic": {
            "K_M_nM": 1., "K_G_nM": 100., "dose_nM": dose.tolist(),
            "effect_arbitrary_units": effect.tolist(), "analytic_peak_nM": 10.,
            "peak_effect": float(two_receptor_effect(10.)),
            "interpretation": "two distinct receptor pools; equal opposing gains are an assumption",
        },
        "fixed_points_synthetic": {
            "edge_vectors_m": edges.tolist(), "conductances_before_S": c0.tolist(),
            "conductances_after_S": c1.tolist(),
            "K_before_S_m2": K0.tolist(), "K_after_S_m2": K1.tolist(),
            "g_before_ohm_per_m2": g0.tolist(), "g_after_ohm_per_m2": g1.tolist(),
            "axis_cost_ratios_after_before": (np.diag(g1)/np.diag(g0)).tolist(),
            "scalar_hormone_fisher_pullback_rank": int(np.linalg.matrix_rank(scalar_pullback)),
            "spatial_interpolation_identified": False,
            "independent_directional_cost_measured": False,
        },
    }


if __name__ == "__main__":
    result = calculate()
    output = Path(sys.argv[1]) if len(sys.argv) > 1 else BASE / "hippocampal_hormone_chemistry_result.json"
    payload = (json.dumps(result, indent=2, allow_nan=False) + "\n").encode("utf-8")
    if output.exists():
        if output.read_bytes() != payload:
            raise FileExistsError("Existing result differs; specify a new output path")
    else:
        with output.open("xb") as stream:
            stream.write(payload)
    print(json.dumps({"output": str(output), "balanced": {k: v["balanced"] for k, v in result["reactions"].items()},
                      "one_min_occupancy": result["kinetics_synthetic"]["at_one_min"],
                      "directional_cost_ratios": result["fixed_points_synthetic"]["axis_cost_ratios_after_before"]}))
