import numpy as np
from ripser import ripser

def lifetimes(Y):
    D = np.linalg.norm(Y[:, None] - Y[None], axis=2)
    dg = ripser(D, distance_matrix=True, maxdim=1)["dgms"][1]
    life = np.sort(dg[:, 1] - dg[:, 0])[::-1] if len(dg) else np.zeros(0)
    return np.r_[life, 0, 0][:2]

def test(X, rng, nnull=300):
    Xc = X - X.mean(0)
    U, s, Vt = np.linalg.svd(Xc, full_matrices=False)
    s = s[: len(X) - 1]
    Y = U[:, : len(s)] * s
    l1, l2 = lifetimes(Y)
    null = np.array([lifetimes(rng.normal(size=Y.shape) * s / np.sqrt(len(X) - 1))[0] for _ in range(nnull)])
    q = np.quantile(null, 0.95)
    return l1, l2, q, (l1 > q) and (l1 >= 2 * l2)

rng = np.random.default_rng(1)
n, extra = 23, 20
def embed(P2, noise):
    return np.c_[P2, np.zeros((n, extra))] + noise * rng.normal(size=(n, 2 + extra))
cases = {
 "ring": lambda: (lambda t: np.c_[np.cos(t), np.sin(t)])(np.sort(rng.uniform(0, 2*np.pi, n))),
 "ellipse0.6": lambda: (lambda t: np.c_[np.cos(t), 0.6*np.sin(t)])(np.sort(rng.uniform(0, 2*np.pi, n))),
 "ring_radius_cv0.3": lambda: (lambda t, r: np.c_[r*np.cos(t), r*np.sin(t)])(np.sort(rng.uniform(0, 2*np.pi, n)), 1 + 0.3*rng.normal(size=n)),
 "disk": lambda: (lambda t, r: np.c_[r*np.cos(t), r*np.sin(t)])(rng.uniform(0, 2*np.pi, n), np.sqrt(rng.uniform(0, 1, n))),
 "line": lambda: np.c_[np.linspace(-1, 1, n), np.zeros(n)],
 "two_blobs": lambda: np.r_[rng.normal(size=(12, 2))*0.2 + [1, 0], rng.normal(size=(11, 2))*0.2 - [1, 0]],
}
for noise in (0.05, 0.1, 0.15):
    for name, f in cases.items():
        res = [test(embed(f(), noise), rng, 200)[3] for _ in range(20)]
        print(f"noise {noise:.2f} {name:18s} pass {sum(res)}/20")
