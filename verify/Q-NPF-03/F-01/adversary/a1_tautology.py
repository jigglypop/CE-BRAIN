# -*- coding: utf-8 -*-
"""A1. Lambda=1 의 대수적 정체 + 유한 L 편의 + Lambda!=1 세계 구성.

주장: xy() 는 p 를 early 에서만 재고 late Phi 에도 같은 p 를 쓴다. 따라서
  Phi = A + B,  A = mu^2/s2 = CV^-2,  B = p^2/2 (양 phase 공통 상수)
  Y = log(A_l + B) - log(A_e + B),   X = (R-2) L,  R = (2-p) r,  r = A_e/(A_e+B)
이고 A_l/A_e = exp(2L - D), D = log s2_l - log s2_e.  Lam = (Y-2L)/((R-2)L).
1차에서 Lam = 1  <=>  D = p L  (= 위상간 분산-평균 지수가 early 지수 p 와 같다).
기하(Phi, rho, R)는 그 한 문장의 뫼비우스 재표기다.
"""
from __future__ import annotations
import json, numpy as np
from pathlib import Path
HERE = Path(__file__).resolve().parent

def lam_of(A_e, B, L, D):
    """정확한 Lam (유한 L). D = dlog s2."""
    p = np.sqrt(2.0*B)
    r = A_e/(A_e+B)
    R = (2.0-p)*r
    A_l = A_e*np.exp(2.0*L - D)
    Y = np.log(A_l+B) - np.log(A_e+B)
    return (Y - 2.0*L)/((R-2.0)*L), R

out = {"note": "adversary A1", "checks": []}

# --- (1) Lam = 1 <=> D = p L  (1차) : p_cross 를 훑는다 -------------------
A_e, p = 3.576, 1.3678          # 참 세계 중앙 CV^-2, 지상진실 p
B = p*p/2.0
rows=[]
for p_cross in (0.0, 0.5, 1.0, 1.3678, 1.5, 2.0, 2.5, 4.1034):
    for L in (0.05, 0.2281, 0.5):
        lam, R = lam_of(A_e, B, L, p_cross*L)
        rows.append({"p_cross": p_cross, "L": round(L,4), "lam": round(float(lam),4)})
out["checks"].append({"name":"A1a_lam_is_mobius_of_p_cross",
    "R": round(float(lam_of(A_e,B,0.2281,p*0.2281)[1]),4), "rows": rows,
    "verdict":"Lam=1 은 p_cross=p 와 동치(L->0). 기하항 B=p^2/2 는 양 phase 공통이라 소거되지 않고 r 로만 들어간다."})

# --- (2) 유한 L 의 Jensen 편의: 카드는 미분식을 유한차분에 그대로 쓴다 ----
r = A_e/(A_e+B); k = 2.0-p; R = k*r
rows=[]
for L in (0.01,0.1,0.2281,0.5,1.0,2.0,3.0):
    lam,_ = lam_of(A_e,B,L,p*L)   # 카드가 참인 세계(D = pL 정확)
    approx = 1.0 + r*(1-r)*k*k*L/(2*(R-2.0))
    rows.append({"L":L,"lam_exact":round(float(lam),5),"lam_2nd_order":round(float(approx),5)})
out["checks"].append({"name":"A1b_finite_L_jensen_bias","rows":rows,
    "verdict":"카드가 정확히 참인 세계에서도 Lam<1. 편의는 -r(1-r)k^2 L/(2(2-R)). 참 세계 L=0.228 에서 -0.004 로 무해하나 카드는 이 선형화를 어디에도 선언하지 않았다."})

# --- (3) Lam != 1 세계: 위상간 지수가 early 지수와 다른 세계는 무한히 많다 -
rows=[]
for dp in (-1.0,-0.5,-0.2,0.2,0.5,1.0):
    lam,_ = lam_of(A_e,B,0.2281,(p+dp)*0.2281)
    rows.append({"p_cross - p": dp, "lam": round(float(lam),4)})
out["checks"].append({"name":"A1c_lam_ne_1_worlds","rows":rows,
    "verdict":"Lam 은 p_cross 의 매끄러운 단조함수. 항등식이 아니다(무내용 아님). 다만 '내용'은 오직 p_cross=p 하나."})

# --- (4) 기하 껍데기 제거 시험: p^2/2 항을 빼도 같은 판정을 하는가 --------
#     Phi' = CV^-2 만 쓰고 R' = 2-p 로 두면 Lam' 은?
def lam_nogeo(A_e,p,L,D):
    Y = (2.0*L - D)             # log A_l - log A_e, 정확
    return (Y-2.0*L)/(((2.0-p)-2.0)*L)
rows=[]
for p_cross in (0.0,1.0,1.3678,2.0,2.5):
    rows.append({"p_cross":p_cross,
                 "lam_card": round(float(lam_of(A_e,B,0.2281,p_cross*0.2281)[0]),4),
                 "lam_no_geometry_term": round(float(lam_nogeo(A_e,p,0.2281,p_cross*0.2281)),4)})
out["checks"].append({"name":"A1d_geometry_term_is_decorative","rows":rows,
    "verdict":"p^2/2(잡음기하 항)를 통째로 버리고 Phi=CV^-2 만 써도 Lam=1 <=> p_cross=p 로 같다. 리만항은 두 판정을 가르지 않는다."})

(HERE/"a1_tautology.json").write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps(out,ensure_ascii=False,indent=2))
