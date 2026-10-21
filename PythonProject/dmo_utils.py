"""
dmo_utils.py —— 工具函数库
包含：
  1. 动态测试问题 DynamicZDT1
  2. NSGA-II 基础算子：非支配排序、拥挤距离、环境选择、锦标赛、SBX、多项式变异
  3. 评价指标：IGD
本模块只提供"零件"，不含算法主流程，也不负责画图。
"""

import numpy as np


# ============================================================
# 一、动态测试问题：动态 ZDT1
# ============================================================
class DynamicZDT1:
    """
        f1 = x1
        f2 = g * (1 - sqrt(f1/g)) + H(t)
        g  = 1 + 9/(n-1) * sum_{i>=2} (xi - G(t))^2

        G(t) = sin(0.5*pi*t)  -> POS（决策空间）随时间漂移
        H(t) = t              -> PF（目标空间）随时间平移
    """
    def __init__(self, n_var=20, tau_t=10, n_t=4):
        self.n_var = n_var
        self.tau_t = tau_t     # 每 tau_t 代环境变化一次
        self.n_t = n_t         # 整个变化周期的长度
        self.t = 0.0
        self.lb = np.zeros(n_var)
        self.ub = np.ones(n_var)

    def update_time(self, gen):
        self.t = (1.0 / self.n_t) * np.floor(gen / self.tau_t)

    def G(self):
        return np.sin(0.5 * np.pi * self.t)

    def evaluate(self, X):
        X = np.atleast_2d(X)
        x1 = X[:, 0]
        G, H = self.G(), self.t
        g = 1.0 + 9.0 / (self.n_var - 1) * np.sum((X[:, 1:] - G) ** 2, axis=1)
        f1 = x1
        f2 = g * (1.0 - np.sqrt(f1 / g)) + H
        return np.column_stack([f1, f2])

    def true_pf(self, n=200):
        f1 = np.linspace(0, 1, n)
        return np.column_stack([f1, 1.0 - np.sqrt(f1) + self.t])


# ============================================================
# 二、NSGA-II 基础算子
# ============================================================
def fast_non_dominated_sort(F):
    """向量化快速非支配排序，返回各前沿的下标列表"""
    n = F.shape[0]
    le = np.all(F[:, None, :] <= F[None, :, :], axis=2)
    lt = np.any(F[:, None, :] < F[None, :, :], axis=2)
    dom = le & lt                       # dom[i,j] = i 支配 j
    n_dom = dom.sum(axis=0)
    remaining = np.ones(n, dtype=bool)
    fronts = []
    while remaining.any():
        cur = np.where(remaining & (n_dom == 0))[0]
        if len(cur) == 0:
            break
        fronts.append(list(cur))
        remaining[cur] = False
        n_dom = n_dom - dom[cur].sum(axis=0)
    return fronts


def crowding_distance(F):
    n, m = F.shape
    if n == 0:
        return np.array([])
    cd = np.zeros(n)
    for j in range(m):
        order = np.argsort(F[:, j])
        cd[order[0]] = cd[order[-1]] = np.inf
        fmin, fmax = F[order[0], j], F[order[-1], j]
        if fmax - fmin > 1e-12:
            for k in range(1, n - 1):
                cd[order[k]] += (F[order[k + 1], j] - F[order[k - 1], j]) / (fmax - fmin)
    return cd


def assign_rank_crowding(F):
    fronts = fast_non_dominated_sort(F)
    rank = np.zeros(len(F), dtype=int)
    cd = np.zeros(len(F))
    for r, fr in enumerate(fronts):
        rank[fr] = r
        cd[fr] = crowding_distance(F[fr])
    return rank, cd


def environmental_selection(F, N):
    fronts = fast_non_dominated_sort(F)
    chosen = []
    for fr in fronts:
        if len(chosen) + len(fr) <= N:
            chosen.extend(fr)
        else:
            cd = crowding_distance(F[fr])
            order = np.argsort(-cd)
            chosen.extend([fr[i] for i in order[:N - len(chosen)]])
            break
    return chosen


def tournament(X, rank, cd, rng):
    i, j = rng.integers(0, len(X), 2)
    if rank[i] < rank[j]:
        return X[i]
    if rank[j] < rank[i]:
        return X[j]
    return X[i] if cd[i] > cd[j] else X[j]


def sbx(p1, p2, lb, ub, rng, eta=20, pc=0.9):
    c1, c2 = p1.copy(), p2.copy()
    if rng.random() > pc:
        return c1, c2
    for i in range(len(p1)):
        if rng.random() <= 0.5 and abs(p1[i] - p2[i]) > 1e-14:
            y1, y2 = min(p1[i], p2[i]), max(p1[i], p2[i])
            r = rng.random()

            beta = 1.0 + 2.0 * (y1 - lb[i]) / (y2 - y1)
            alpha = 2.0 - beta ** -(eta + 1.0)
            betaq = ((r * alpha) ** (1.0 / (eta + 1.0)) if r <= 1.0 / alpha
                     else (1.0 / (2.0 - r * alpha)) ** (1.0 / (eta + 1.0)))
            ch1 = 0.5 * ((y1 + y2) - betaq * (y2 - y1))

            beta = 1.0 + 2.0 * (ub[i] - y2) / (y2 - y1)
            alpha = 2.0 - beta ** -(eta + 1.0)
            betaq = ((r * alpha) ** (1.0 / (eta + 1.0)) if r <= 1.0 / alpha
                     else (1.0 / (2.0 - r * alpha)) ** (1.0 / (eta + 1.0)))
            ch2 = 0.5 * ((y1 + y2) + betaq * (y2 - y1))

            ch1 = np.clip(ch1, lb[i], ub[i])
            ch2 = np.clip(ch2, lb[i], ub[i])
            if rng.random() <= 0.5:
                c1[i], c2[i] = ch2, ch1
            else:
                c1[i], c2[i] = ch1, ch2
    return c1, c2


def polynomial_mutation(x, lb, ub, rng, eta=20):
    x = x.copy()
    pm = 1.0 / len(x)
    for i in range(len(x)):
        if rng.random() < pm:
            y, yl, yu = x[i], lb[i], ub[i]
            d1, d2 = (y - yl) / (yu - yl), (yu - y) / (yu - yl)
            r = rng.random()
            mp = 1.0 / (eta + 1.0)
            if r <= 0.5:
                val = 2.0 * r + (1.0 - 2.0 * r) * (1.0 - d1) ** (eta + 1.0)
                dq = val ** mp - 1.0
            else:
                val = 2.0 * (1.0 - r) + 2.0 * (r - 0.5) * (1.0 - d2) ** (eta + 1.0)
                dq = 1.0 - val ** mp
            x[i] = np.clip(y + dq * (yu - yl), yl, yu)
    return x


# ============================================================
# 三、评价指标
# ============================================================
def igd(F, pf):
    """Inverted Generational Distance：真实 PF 到近似 PF 的平均最近距离"""
    d = np.sqrt(((pf[:, None, :] - F[None, :, :]) ** 2).sum(axis=2))
    return float(np.mean(np.min(d, axis=1)))


__all__ = [
    'DynamicZDT1',
    'fast_non_dominated_sort', 'crowding_distance', 'assign_rank_crowding',
    'environmental_selection', 'tournament', 'sbx', 'polynomial_mutation',
    'igd',
]