"""Necessary cross-transfer constraints of a passive four-port star.

Passing these constraints does not identify direct anatomy or access resistance.
Array order: center, leaf A, leaf B, leaf C. Units may be any consistent resistance.
"""
import numpy as np


def passive_star(leak, edges):
    leak, edges = np.asarray(leak, float), np.asarray(edges, float)
    if leak.shape != (4,) or edges.shape != (3,) or not np.isfinite(leak).all() or not np.isfinite(edges).all():
        raise ValueError('Expected four finite leaks and three finite edges')
    if np.any(leak<=0) or np.any(edges<=0):
        raise ValueError('Positive leaks and edges required')
    y = np.diag(leak)
    for leaf,g in enumerate(edges,1):
        incidence = np.eye(4)[:,0]-np.eye(4)[:,leaf]
        y += g*np.outer(incidence,incidence)
    return y, np.linalg.solve(y,np.eye(4))


def predict_unseen_leaf_pairs(transfer):
    """Fit three center-leaf pairs and A-B only, predict A-C and B-C.

    Input diagonals and leaf pairs involving C are NEVER used in this fit.
    Reciprocal training estimates are averaged; that assumption requires evaluation.
    The center parameter is conditional on the exact star plus diagonal artifact model.
    """
    z = np.asarray(transfer,float)
    if z.shape != (4,4):
        raise ValueError('Expected 4-by-4 transfer in center/A/B/C order')
    center = (z[0,1:]+z[1:,0])/2
    leaf_ab = (z[1,2]+z[2,1])/2
    if not np.isfinite(center).all() or not np.isfinite(leaf_ab) or np.any(center<=0) or leaf_ab<=0:
        raise ValueError('Positive finite training cross-transfer required; no clipping or ridge')
    parameter = center[0]*center[1]/leaf_ab
    predicted = np.outer(center,center)/parameter
    return dict(center_leaf_training=center, leaf_ab_training=float(leaf_ab),
                effective_star_center_parameter=float(parameter),
                predicted_leaf_ac=float(predicted[0,2]), predicted_leaf_bc=float(predicted[1,2]))


def tetrad_products(transfer):
    """Three division-free products; zero transfer also satisfies equality."""
    z = np.asarray(transfer,float)
    if z.shape != (4,4) or not np.isfinite(z).all():
        raise ValueError('Expected a finite 4-by-4 transfer')
    s = (z+z.T)/2
    return np.array([s[0,1]*s[2,3],s[0,2]*s[1,3],s[0,3]*s[1,2]])
