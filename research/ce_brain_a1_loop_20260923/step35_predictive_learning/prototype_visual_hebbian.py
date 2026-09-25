import numpy as np, time
DT = 0.1
sig = lambda z: 1 / (1 + np.exp(-z))
rng = np.random.default_rng(0)
N, rep = 16, 3
ang = np.repeat(np.arange(N) * 2 * np.pi / N, rep)
m = N * rep
E, L, R, G = np.arange(m), np.arange(m, 2*m), np.arange(2*m, 3*m), np.array([3*m])
n = 3 * m + 1
Kf = lambda s, k: np.exp(k * (np.cos(ang[:, None] - ang[None, :] - s) - 1))
def build(noise):
    w = np.zeros((n, n))
    w[np.ix_(E, E)] = Kf(0, 6)
    w[np.ix_(L, E)] = Kf(0, 6); w[np.ix_(R, E)] = Kf(0, 6)
    w[np.ix_(E, L)] = 0.6 * Kf(np.radians(45), 6); w[np.ix_(E, R)] = 0.6 * Kf(-np.radians(45), 6)
    w[np.ix_(G, E)] = 1.0; w[np.ix_(E, G)] = -0.35 * Kf(0, 6).sum(1)[:, None] * 1.0
    return w * np.exp(noise * np.random.default_rng(7).normal(size=w.shape)) * (w != 0)
beta = np.full(n, -1.0); beta[L] = -3.0; beta[R] = -3.0
gam = np.zeros(n); gam[L] = 1; gam[R] = -1

class Net:
    def __init__(s, W, w0, eta=0.0, k=6.0, amp=4.0):
        s.W = W.copy(); s.mask = W != 0; s.sgn = np.sign(W); s.w0 = w0; s.k = k; s.amp = amp
        s.bias = beta - w0 * (W @ sig(beta)); s.x = sig(beta).copy()
        s.rowscale = np.array([np.abs(W[i][s.mask[i]]).mean() if s.mask[i].any() else 0 for i in range(n)])
    def vis(s, th):
        v = np.zeros(n); v[E] = s.amp * np.exp(3 * (np.cos(ang - th) - 1)) - 1.0; return v
    def step(s, th=None, v=0.0, eta=0.0):
        rec = s.w0 * (s.W @ s.x) + s.bias + v * s.k * gam
        drive = rec + (s.vis(th) if th is not None else 0.0)
        new = s.x + DT * (-s.x + sig(drive))
        if eta > 0 and th is not None:
            e = sig(drive[E]) - sig(rec[E])
            rows = s.W[E] + eta * s.rowscale[E, None] * np.outer(e, s.x) * s.mask[E]
            s.W[E] = s.sgn[E] * np.maximum(s.sgn[E] * rows, 0)
        s.x = new
    def centre(s):
        e = s.x[E] - s.x[E].min(); return np.angle(np.sum(e * np.exp(1j * ang)))
    def reset(s): s.x = sig(beta).copy()

def retention(net):
    fin = []
    for h in np.arange(16) * 22.5:
        net.reset()
        for _ in range(200): net.step(np.radians(h))
        for _ in range(1000): net.step(None)
        fin.append(np.degrees(net.centre()))
    err = np.abs((np.array(fin) - np.arange(16) * 22.5 + 180) % 360 - 180)
    c = net.x[E].max() - net.x[E].min()
    return round(float(np.mean(err <= 22.5)), 3), round(float(np.median(err)), 1), round(float(c), 3)

def integ(net, vels=(-0.1, -0.05, -0.02, 0.02, 0.05, 0.1)):
    out = []
    for v in vels:
        net.reset()
        for _ in range(200): net.step(0.0)
        ph = []
        for s_ in range(600):
            net.step(None, v)
            if s_ % 10 == 0: ph.append(net.centre())
        ph = np.unwrap(ph); t = np.arange(len(ph)); half = t >= len(t) // 3
        out.append(float(np.polyfit(t[half], ph[half], 1)[0]) / (10 * DT))
    vs, bv = np.array(vels), np.array(out)
    gain = vs @ bv / (vs @ vs); r2 = 1 - np.sum((bv - gain * vs) ** 2) / np.sum((bv - bv.mean()) ** 2) if np.ptp(bv) > 0 else 0
    return round(float(gain), 3), round(float(r2), 3), np.round(bv, 4)

def train(net, steps, eta):
    th, v = 0.0, 0.0
    for _ in range(steps):
        v += DT * (-v / 20.0) + np.sqrt(2 * DT / 20.0) * 0.05 * rng.standard_normal(); th += v * DT
        net.step(th, v, eta)


def contrast(net):
    net.reset()
    for _ in range(200): net.step(0.0)
    for _ in range(1000): net.step(None)
    x = net.x[E]; return round(float((x.max() - x.min()) / max(x.max(), 1e-9)), 3)
W = build(0.3)
net = Net(W, 0.5)
t0 = time.time()
for block in range(160):
    train(net, 10000, 0.001)
    if block % 16 == 15:
        g, r2, bv = integ(net)
        print("block", block + 1, "t %.0fs" % (time.time() - t0), "retention", retention(net), "contrast", contrast(net), "gain", g, "R2", r2, np.round(bv, 4),
              "Wcorr", round(float(np.corrcoef(net.W[E][net.mask[E]], W[E][net.mask[E]])[0, 1]), 3), flush=True)
