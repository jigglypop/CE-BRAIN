"""Development: sanity checks of the model classes and the curvature code."""
import numpy as np
import metric_models as M
from kc_data import load_table, panel_tasks

t = load_table()
tasks = panel_tasks(t, "leave1")
ys = np.concatenate([task["test_y"] for task in tasks])


def panel_rmse(model):
    p = np.concatenate([model.predict(model.fit(task["train"]), task["test_x"]) for task in tasks])
    return float(np.sqrt(np.mean((p - ys) ** 2)))


print("published", panel_rmse(M.PublishedSPD()))
print("curved beta=0", panel_rmse(M.CurvedAPL(0.0, 0.0)))
print("input beta=0", panel_rmse(M.InputMetric(0.0, 0.0)))
print("exponent 0.625", panel_rmse(M.ExponentForce(0.625, 0.625)))
print("curved -0.6,+0.1", panel_rmse(M.CurvedAPL(-0.6, 0.1)))
print("input -0.6,+0.1", panel_rmse(M.InputMetric(-0.6, 0.1)))
print("exponent 2.0,0.625", panel_rmse(M.ExponentForce(2.0, 0.625)))
print("affine x", panel_rmse(M.Affine("x")), "affine phi", panel_rmse(M.Affine("phi")))
rng = np.random.default_rng(0)
y = rng.uniform(0.1, 0.5, 6)
u = np.ones(6) / np.sqrt(6)
eq = M.curvature_summary(np.eye(6), np.full(6, 0.4), u, 0.5, y)
print("conformal n=6 (expect scalar 0, Ricci != 0)", eq)
a = rng.normal(size=(6, 6))
g0 = a @ a.T + 6 * np.eye(6)
betas = M.compartment_betas(-0.6, 0.1)
an = M.curvature_summary(g0, betas, u, 0.5, y)
fd = M.curvature_finite_difference(g0, betas, u, 0.5, y)
print("compartment metric analytic", an, "finite-difference scalar", fd)
print("flat check beta=0", M.curvature_summary(g0, np.zeros(6), u, 0.5, y))
