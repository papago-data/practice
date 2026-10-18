"""
问题1：预热平衡阶段药材温度与水分浓度的变化规律。

模型：圆柱（一维径向）非稳态导热 + 非稳态扩散双场耦合
     ρ c_p ∂T/∂t = k ∇²T          （忽略汽化潜热，量级占比 < 1%，见论文）
     ∂C/∂t      = (1/r) ∂/∂r ( r D(C) ∂C/∂r )
边界：r = 0 对称；r = R 第三类（对流换热 / 对流传质）
物性：附录2 常物性，D = 7e-9 exp(-0.89/C)
格式：全隐式 + 追赶法，无条件稳定
"""

import os
import numpy as np

from dry_model import (
    T0_C, C0, BASE_DIR,
    PARAMS_Q1, Grid, tdma, iface_mean,
    make_env, sample_indices, interp_to_distances,
    save_result, TARGET_DISTS,
)

# ============================================================
# 配置
# ============================================================
N = 160            # 径向网格数
DT = 0.1           # 时间步长 (s)
T_END = 1800.0     # 模拟时长 (s)
SAMPLE_DT = 1.0    # 输出采样间隔 (s)

P = PARAMS_Q1
grid = Grid(N)
Ta, Ca, _ = make_env()


# ============================================================
# 时间推进：水分场与温度场均用全隐式格式推进
# ============================================================
def solve():
    """返回 (时间数组, 温度矩阵, 水分浓度矩阵)。"""
    n = N + 1
    dr = grid.dr
    r_int, r_half, r = grid.r_int, grid.r_half, grid.r

    T = np.full(n, T0_C)
    C = np.full(n, C0)

    times, steps = sample_indices(T_END, DT, SAMPLE_DT)
    T_out = np.zeros((len(steps), n))
    C_out = np.zeros((len(steps), n))
    T_out[0], C_out[0] = T, C
    out_idx = 1

    nsteps = int(round(T_END / DT))
    for step in range(1, nsteps + 1):
        t_new = step * DT

        # ---------------- 水分扩散（隐式） ----------------
        a = np.zeros(n); b = np.zeros(n); c = np.zeros(n); d = np.zeros(n)
        D_node = P.D(C)
        for i in range(1, N):
            ri = r_int[i - 1]
            rhp = r_half[i - 1]
            rhm = r_half[i - 2] if i - 2 >= 0 else r_half[0]
            D_ip = iface_mean(D_node[i], D_node[i + 1])
            D_im = iface_mean(D_node[i - 1], D_node[i])
            cp_ = DT * rhp * D_ip / (ri * dr ** 2)
            cm_ = DT * rhm * D_im / (ri * dr ** 2)
            a[i] = -cm_
            b[i] = 1.0 + cp_ + cm_
            c[i] = -cp_
            d[i] = C[i]

        # 轴心：对称条件，等价于虚拟节点法
        b[0] = 1.0 + 4.0 * D_node[0] * DT / dr ** 2
        c[0] = -4.0 * D_node[0] * DT / dr ** 2
        d[0] = C[0]

        # 表面：第三类边界，半格控制体，隐式处理
        A_R, A_in, V_h = grid.A_R, grid.A_inner, grid.V_half
        D_s = D_node[N]
        a[N] = -D_s * A_in / dr
        b[N] = V_h / DT + P.hm * A_R + D_s * A_in / dr
        d[N] = V_h / DT * C[N] + P.hm * A_R * Ca(t_new)
        C = tdma(a, b, c, d)

        # ---------------- 温度场（隐式） ----------------
        a = np.zeros(n); b = np.zeros(n); c = np.zeros(n); d = np.zeros(n)
        alpha = P.k(C)[0] / (P.rho(C)[0] * P.cp(C)[0])
        for i in range(1, N):
            ri = r_int[i - 1]
            cp_ = alpha * DT * (1.0 / dr ** 2 + 1.0 / (2.0 * ri * dr))
            cm_ = alpha * DT * (1.0 / dr ** 2 - 1.0 / (2.0 * ri * dr))
            a[i] = -cm_
            b[i] = 1.0 + cp_ + cm_
            c[i] = -cp_
            d[i] = T[i]

        b[0] = 1.0 + 4.0 * alpha * DT / dr ** 2
        c[0] = -4.0 * alpha * DT / dr ** 2
        d[0] = T[0]

        rho_cp = P.rho(C)[N] * P.cp(C)[N]
        a[N] = -P.k(C)[N] * A_in / dr
        b[N] = rho_cp * V_h / DT + P.h * A_R + P.k(C)[N] * A_in / dr
        d[N] = rho_cp * V_h / DT * T[N] + P.h * A_R * Ta(t_new)
        T = tdma(a, b, c, d)

        # ---------------- 采样 ----------------
        if out_idx < len(steps) and step == steps[out_idx]:
            T_out[out_idx], C_out[out_idx] = T, C
            out_idx += 1

    return times, T_out, C_out


# ============================================================
# 主流程
# ============================================================
times, T_out, C_out = solve()

# 插值到题面要求的到中心距离
T_grid = np.array([interp_to_distances(grid.r, T_out[i], TARGET_DISTS)
                   for i in range(len(times))])
C_grid = np.array([interp_to_distances(grid.r, C_out[i], TARGET_DISTS)
                   for i in range(len(times))])

save_result(
    os.path.join(BASE_DIR, "result1.xlsx"),
    [("温度", times, T_grid, "时间"), ("水分浓度", times, C_grid, "时间")],
)

# ============================================================
# 表1、表2
# ============================================================
TABLE_TIMES = [100, 300, 600, 900, 1200, 1500, 1800]
TABLE_DISTS = [0.0, 0.5, 1.0, 1.5, 2.0]


def col(d):
    return int(np.argmin(np.abs(TARGET_DISTS - d)))


def row(t_val):
    return int(np.argmin(np.abs(times - t_val)))


for label, data in [("表1  30分钟内药材的温度 (°C)", T_grid),
                    ("表2  30分钟内药材的水分浓度 (kg/kg)", C_grid)]:
    print(f"\n{label}")
    print(f"{'时间/s':<12}" + "".join(f"{d}cm".rjust(12) for d in TABLE_DISTS))
    print("-" * 72)
    for tv in TABLE_TIMES:
        print(f"{tv:<12}" + "".join(f"{data[row(tv), col(d)]:>12.4f}" for d in TABLE_DISTS))

print(f"\n[输出] result1.xlsx: {len(times)} 行 x {len(TARGET_DISTS)} 列")
