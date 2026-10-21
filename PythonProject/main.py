"""
main.py —— 入口：跑动态/静态两组实验并可视化
"""

import numpy as np
import matplotlib.pyplot as plt

from dmo_utils import DynamicZDT1
from dmo_algorithm import run_dmo

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'PingFang SC', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


# ============================================================
# 可视化
# ============================================================
def plot_igd_compare(res_dyn, res_sta, max_gen):
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.plot(res_dyn['igd'], 'o-', ms=3, label='动态响应策略')
    ax.plot(res_sta['igd'], 's--', ms=3, label='无响应（静态 NSGA-II）')
    for g in range(10, max_gen, 10):
        ax.axvline(g, color='gray', ls=':', alpha=0.6)
    ax.set_yscale('log')
    ax.set_xlabel('代数 gen')
    ax.set_ylabel('IGD (log)')
    ax.set_title('环境变化时的 IGD（竖线 = 环境变化时刻）')
    ax.legend()
    plt.tight_layout()
    plt.show()


def plot_decision_tracking(res_dyn, problem, max_gen):
    t_axis = (1.0 / problem.n_t) * np.floor(np.arange(max_gen) / problem.tau_t)
    G_axis = np.sin(0.5 * np.pi * t_axis)

    fig, ax = plt.subplots(figsize=(9, 4))
    for gen in range(max_gen):
        y = res_dyn['x2'][gen]
        ax.scatter(np.full(len(y), gen), y, s=3, alpha=0.25, c='tab:blue')
    ax.plot(t_axis, G_axis, 'r-', lw=2, label=r'真实 POS: $x_i = G(t)$')
    ax.set_xlabel('代数 gen')
    ax.set_ylabel(r'$x_2$ 取值')
    ax.set_title(r'决策空间追踪：种群 $x_2$ 跟随 $G(t)$ 漂移')
    ax.legend()
    plt.tight_layout()
    plt.show()


def plot_snapshots(res_dyn):
    gens = sorted(res_dyn['snaps'].keys())
    fig, axes = plt.subplots(1, len(gens), figsize=(4 * len(gens), 4))
    if len(gens) == 1:
        axes = [axes]
    for ax, gen in zip(axes, gens):
        F, t = res_dyn['snaps'][gen]
        f1 = np.linspace(0, 1, 200)
        ax.plot(f1, 1 - np.sqrt(f1) + t, 'r--', lw=1.5, label='真实 PF')
        ax.scatter(F[:, 0], F[:, 1], s=8, alpha=0.6, label='种群')
        ax.set_title(f'gen={gen}, t={t:.2f}')
        ax.set_xlabel(r'$f_1$')
        ax.set_ylabel(r'$f_2$')
        ax.set_xlim(-0.05, 1.1)
    axes[0].legend()
    plt.tight_layout()
    plt.show()


# ============================================================
# 主实验
# ============================================================
if __name__ == '__main__':
    N, MAXGEN = 100, 60

    p1 = DynamicZDT1()
    res_dyn = run_dmo(p1, N=N, max_gen=MAXGEN, use_reaction=True, seed=1)

    p2 = DynamicZDT1()
    res_sta = run_dmo(p2, N=N, max_gen=MAXGEN, use_reaction=False, seed=1)

    plot_igd_compare(res_dyn, res_sta, MAXGEN)
    plot_decision_tracking(res_dyn, p1, MAXGEN)
    plot_snapshots(res_dyn)