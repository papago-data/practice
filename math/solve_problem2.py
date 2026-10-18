"""
问题2：整个烘干过程药材温度与水分浓度的变化规律（前 3 小时）。

模型：圆柱（一维径向）非稳态导热 + 非稳态扩散双场耦合
     ρ(C) c_p(C) ∂T/∂t = (1/r) ∂/∂r ( r k(C) ∂T/∂r )
     ∂C/∂t             = (1/r) ∂/∂r ( r D(C,T) ∂C/∂r )
物性：附录3 变物性
阶段：预热平衡（t < t_c）→ 恒温干燥（t ≥ t_c），切换时刻由附件1 标定为 2 h。
     环境温湿度在 t_c 后趋于恒定，边界条件由强时变退化为准稳态
     Robin 条件，参数组随阶段切换。
格式：内部节点显式，表面半格节点隐式（解除表面刚性引起的稳定性限制）
"""

import os
import numpy as np

from dry_model import (
    C0, T0_C, C_CLIP_LO, BASE_DIR, T_SWITCH, T_INF_C, C_INF,
    Grid, harm_mean, iface_mean, make_env, sample_indices,
    interp_to_distances, save_result, TARGET_DISTS, params_at,
)

# ============================================================
# 配置
# ============================================================
N = 20             # 径向网格数
DT = 0.5           # 时间步长 (s)
T_END = 10800.0    # 模拟时长，3 h (s)
SAMPLE_DT = 1.0    # 输出采样间隔 (s)

grid = Grid(N)
Ta, Ca, _ = make_env()

# ---------------- 显式格式稳定性预检（轴心 4× 格式最严） ----------------
_Cg = np.linspace(max(C_CLIP_LO, 1e-3), C0, 64)
P_chk = params_at(0.0)
alpha_max = float(np.max(P_chk.k(_Cg) / (P_chk.rho(_Cg) * P_chk.cp(_Cg))))
stab_T = 4.0 * alpha_max * DT / grid.dr ** 2
if stab_T > 1.0:
    raise ValueError(
        f"显式格式不稳定：4·αmax·Δt/Δr² = {stab_T:.3f} > 1（N={N}, Δt={DT}）。"
        f"请将 Δt 减小到 {DT / stab_T:.3f} s 以下（Δt 需 ∝ Δr²）。")
print(f"[稳定性] 4·αmax·Δt/Δr² = {stab_T:.4f} ≤ 1  (αmax = {alpha_max:.3e} m²/s)")


# ============================================================
# 时间推进
# ============================================================
def solve():
    """返回 (时间数组, 温度矩阵, 水分浓度矩阵)。"""
    n = N + 1
    dr = grid.dr
    r_int, r_half = grid.r_int, grid.r_half
    A_R, A_in, V_h = grid.A_R, grid.A_inner, grid.V_half
    vols = grid.cell_volumes()

    T = np.full(n, T0_C)
    C = np.full(n, C0)

    times, steps = sample_indices(T_END, DT, SAMPLE_DT)
    T_out = np.zeros((len(steps), n))
    C_out = np.zeros((len(steps), n))
    T_out[0], C_out[0] = T, C

    water_init = float(np.sum(C * vols))
    evap_cum = 0.0
    out_idx = 1

    nsteps = int(round(T_END / DT))
    for step in range(1, nsteps + 1):
        t_new = step * DT
        P = params_at(t_new - 0.5 * DT)      # 阶段物性取半步前时刻

        # ---------------- 物性（滞后取旧时刻值） ----------------
        rho_n = P.rho(C)
        cp_n = P.cp(C)
        k_n = P.k(C)
        D_n = P.D(C, T + 273.15)

        k_h = harm_mean(k_n[:-1], k_n[1:])
        D_h = iface_mean(D_n[:-1], D_n[1:])   # 浓度连续，界面扩散系数取线性插值

        # ---------------- 各节点散度项 ----------------
        divT = np.zeros(n)
        divC = np.zeros(n)

        # 轴心：对称条件
        divT[0] = 4.0 * k_h[0] * (T[1] - T[0]) / dr ** 2
        divC[0] = 4.0 * D_h[0] * (C[1] - C[0]) / dr ** 2

        # 内部节点：界面通量差分
        qT = r_half * k_h * (T[1:] - T[:-1]) / dr
        qC = r_half * D_h * (C[1:] - C[:-1]) / dr
        divT[1:N] = (qT[1:] - qT[:-1]) / (r_int * dr)
        divC[1:N] = (qC[1:] - qC[:-1]) / (r_int * dr)

        # ---------------- 内部节点推进（显式） ----------------
        C_prev = C.copy()
        T_new = T + DT * divT / (rho_n * cp_n)
        C_new = np.concatenate([np.maximum(C[:N] + DT * divC[:N], 0.0), [C[N]]])

        # ---------------- 表面节点：半格控制体 + 隐式 ----------------
        # 能量： ρcp V_h (T_N^new − T_N)/Δt = h A_R (Ta − T_N^new) − k A_in/Δr (T_N^new − T_{N−1})
        Ta_v = Ta(t_new)
        rho_cp_s = rho_n[N] * cp_n[N]
        T_new[N] = ((rho_cp_s * V_h / DT * T[N]
                     + P.h * A_R * Ta_v
                     + k_h[-1] * A_in / dr * T_new[N - 1])
                    / (rho_cp_s * V_h / DT + P.h * A_R + k_h[-1] * A_in / dr))

        # 水分： V_h (C_N^new − C_N)/Δt = hm A_R (Ca − C_N^new) − D A_in/Δr (C_N^new − C_{N−1})
        Ca_v = Ca(t_new)
        C_new[N] = ((V_h / DT * C[N]
                     + P.hm * A_R * Ca_v
                     + D_h[-1] * A_in / dr * C_new[N - 1])
                    / (V_h / DT + P.hm * A_R + D_h[-1] * A_in / dr))

        # 累积蒸发量：边界传质通量积分（取新时刻浓度，与Q3一致）
        evap_cum += P.hm * (C_new[N] - Ca_v) * A_R * DT

        T, C = T_new, C_new

        if out_idx < len(steps) and step == steps[out_idx]:
            T_out[out_idx], C_out[out_idx] = T, C
            out_idx += 1

    # ---------------- 质量守恒校核 ----------------
    water_final = float(np.sum(C * vols))
    loss = water_init - water_final
    rel = abs(loss - evap_cum) / water_init
    print("=" * 60)
    print("质量守恒检查")
    print("=" * 60)
    print(f"初始总水量:     {water_init:.6e}")
    print(f"最终总水量:     {water_final:.6e}")
    print(f"内部水量减少:   {loss:.6e}")
    print(f"边界累积蒸发:   {evap_cum:.6e}")
    print(f"相对误差:       {rel:.3e}")

    return times, T_out, C_out


# ============================================================
# 主流程
# ============================================================
times, T_out, C_out = solve()

T_grid = np.array([interp_to_distances(grid.r, T_out[i], TARGET_DISTS)
                   for i in range(len(times))])
C_grid = np.array([interp_to_distances(grid.r, C_out[i], TARGET_DISTS)
                   for i in range(len(times))])

save_result(
    os.path.join(BASE_DIR, "result2.xlsx"),
    [("温度", times, T_grid, "时间"), ("水分浓度", times, C_grid, "时间")],
)

# ============================================================
# 表3、表4
# ============================================================
TABLE_HOURS = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]
TABLE_DISTS = [0.0, 0.5, 1.0, 1.5, 2.0]


def col(d):
    return int(np.argmin(np.abs(TARGET_DISTS - d)))


def row(t_val):
    return int(np.argmin(np.abs(times - t_val)))


for label, data in [("表3  3小时内药材的温度 (°C)", T_grid),
                    ("表4  3小时内药材的水分浓度 (kg/kg)", C_grid)]:
    print(f"\n{label}")
    print(f"{'时间/h':<12}" + "".join(f"{d}cm".rjust(12) for d in TABLE_DISTS))
    print("-" * 72)
    for th in TABLE_HOURS:
        mark = "   ← 阶段切换" if abs(th * 3600 - T_SWITCH) < 1e-6 else ""
        print(f"{th:<12.1f}" + "".join(
            f"{data[row(int(th * 3600)), col(d)]:>12.4f}" for d in TABLE_DISTS) + mark)

print(f"\n[环境] 阶段切换 t_c = {T_SWITCH/3600:.1f} h；"
      f"恒温渐近 T∞ = {T_INF_C:.3f} °C，C∞ = {C_INF:.5f} kg/kg")
print(f"[输出] result2.xlsx: {len(times)} 行 x {len(TARGET_DISTS)} 列")
