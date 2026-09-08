"""Finite-horizon geometry from fixed neuron-index linear pathways.
This is a supplied-system identity, not an inferred biological connection map.
The full observation covariance is required, including cross-time dependence.
"""
import numpy as np


def path_jacobians(A, B, C, horizon, dA=None):
    A=np.array(A,float,copy=True);B=np.array(B,float,copy=True);C=np.array(C,float,copy=True)
    if type(horizon) is not int or horizon < 1:raise ValueError('positive integer horizon')
    if A.ndim!=2 or A.shape[0]!=A.shape[1] or B.ndim!=2 or C.ndim!=2 or B.shape[0]!=len(A) or C.shape[1]!=len(A):raise ValueError('incompatible pathways')
    if not all(np.isfinite(a).all() for a in (A,B,C)):raise ValueError('nonfinite pathways')
    D=np.zeros_like(A) if dA is None else np.array(dA,float,copy=True)
    if D.shape!=A.shape or not np.isfinite(D).all():raise ValueError('invalid pathway direction')
    J=B.copy();dJ=np.zeros_like(B);rows=[];drows=[]
    for _ in range(horizon):
        dJ=D@J+A@dJ;J=A@J
        rows.append(C@J);drows.append(C@dJ)
    return np.vstack(rows),np.vstack(drows)


def path_metric(A,B,C,Sigma,horizon,dA=None):
    J,dJ=path_jacobians(A,B,C,horizon,dA)
    S=np.array(Sigma,float,copy=True)
    if S.shape!=(len(J),len(J)) or not np.isfinite(S).all() or not np.allclose(S,S.T,rtol=1e-12,atol=1e-12):raise ValueError('aligned symmetric covariance required')
    np.linalg.cholesky(S)
    SJ=np.linalg.solve(S,J)
    return J.T@SJ,dJ.T@SJ+J.T@np.linalg.solve(S,dJ)
