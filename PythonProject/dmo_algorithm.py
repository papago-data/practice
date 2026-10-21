"""
dmo_algorithm.py —— 动态多目标优化算法实现
包含：
  1. 环境变化响应策略 react_to_change
  2. 动态 NSGA-II 主循环 run_dmo
依赖 dmo_utils 提供的算子与问题。
"""

import numpy as np

from dmo_utils import (
    assign_rank_crowding,
    environmental_selection,
    tournament,
    sbx,
    polynomial_mutation,
    igd,
)


# ============================================================
# 一、环境变化响应策略
# ============================================================
def react_to_change(X, F, problem, N, rng, keep_ratio=0.5):
    """精英保留 + 大变异 + 随机重启"""
    rank, _ = assign_rank_crowding(F)
    order = np.argsort(rank)
    n_keep = int(keep_ratio * N)
    X_keep = X[order[:n_keep]]

    X_mut = np.clip(X_keep + 0.2 * rng.standard_normal(X_keep.shape),
                    problem.lb, problem.ub)

    n_left = N - n_keep
    n_mut = n_left // 2
    n_rand = n_left - n_mut
    X_rand = rng.uniform(problem.lb, problem.ub, size=(n_rand, problem.n_var))
    return np.vstack([X_keep, X_mut[:n_mut], X_rand])


# ============================================================
# 二、动态 NSGA-II 主循环
# ============================================================
def run_dmo(problem, N=100, max_gen=60, use_reaction=True, seed=0):
    """
    参数
    ----
    problem      : 动态测试问题对象，需实现 update_time/evaluate/true_pf/lb/ub/n_var
    N            : 种群规模
    max_gen      : 总进化代数
    use_reaction : 是否启用环境变化响应策略
    seed         : 随机种子

    返回
    ----
    dict: {'igd': [...], 'x2': [...], 'snaps': {gen: (F, t)}}
    """
    rng = np.random.default_rng(seed)

    X = rng.uniform(problem.lb, problem.ub, size=(N, problem.n_var))
    F = problem.evaluate(X)

    # 用一个固定探测解来检测环境是否变化
    probe = rng.uniform(problem.lb, problem.ub)
    last_probe_f = problem.evaluate(probe.reshape(1, -1))

    igd_hist, x2_hist, snaps = [], [], {}
    snap_gens = {9, 10, 20, 45}

    for gen in range(max_gen):
        # ---------- 环境变化 & 检测 ----------
        problem.update_time(gen)
        probe_f = problem.evaluate(probe.reshape(1, -1))
        changed = not np.allclose(probe_f, last_probe_f)
        last_probe_f = probe_f

        if changed:
            F = problem.evaluate(X)              # 目标函数变了，必须重评估
            if use_reaction:                     # 动态响应
                X = react_to_change(X, F, problem, N, rng)
                F = problem.evaluate(X)

        # ---------- 记录 ----------
        igd_hist.append(igd(F, problem.true_pf()))
        x2_hist.append(X[:, 1].copy())
        if gen in snap_gens:
            snaps[gen] = (F.copy(), problem.t)

        # ---------- 繁殖 ----------
        rank, cd = assign_rank_crowding(F)
        C = []
        while len(C) < N:
            p1 = tournament(X, rank, cd, rng)
            p2 = tournament(X, rank, cd, rng)
            c1, c2 = sbx(p1, p2, problem.lb, problem.ub, rng)
            C.append(polynomial_mutation(c1, problem.lb, problem.ub, rng))
            C.append(polynomial_mutation(c2, problem.lb, problem.ub, rng))
        C = np.array(C[:N])
        Fc = problem.evaluate(C)

        # ---------- 环境选择 ----------
        Xall, Fall = np.vstack([X, C]), np.vstack([F, Fc])
        idx = environmental_selection(Fall, N)
        X, F = Xall[idx], Fall[idx]

    return dict(igd=igd_hist, x2=x2_hist, snaps=snaps)


__all__ = ['react_to_change', 'run_dmo']