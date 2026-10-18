"""
问题3：确定药材烘干所需时间（各处水分浓度低于 0.15 kg/kg）。

模型：与问题2 同一套圆柱双场耦合模型，延长至烘干完成。
阶段：预热平衡（t < t_c = 2 h）→ 恒温干燥（t ≥ t_c），参数组随阶段切换。
判据：以药材中心 r = 0 的水分浓度首次降至 C_SAFE = 0.15 kg/kg 作为
     烘干完成时刻 t_f —— 中心是最后达标的部位。
      物性函数的数值保护下界取 1e-4，与判据阈值解耦，
      避免阈值处扩散系数被人为抬高而系统性提前 t_f。
格式：内部节点显式，表面半格节点隐式。
"""

import os
import numpy as np

from dry_model import (
    C0, T0_C, C_SAFE, C_CLIP_LO, BASE_DIR, T_SWITCH,
    Grid, harm_mean, iface_mean, make_env,
    interp_to_distances, save_result, TARGET_DISTS, params_at,
)

# ============================================================
# 配置
# ============================================================
N = 20                # 径向网格数
DT = 0.5              # 时间步长 (s)
SAMPLE_DT = 60.0      # 输出采样间隔 (s)
T_MAX = 700000.0      # 仿真时长上限 (s)，约 194 h

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
# 时间推进（含烘干完成事件检测）
# ============================================================
def solve():
    """返回 (时间数组, 水分浓度矩阵, t_f, C_at_tf, 守恒报告)。"""
    n = N + 1
    dr = grid.dr
    r_int, r_half = grid.r_int, grid.r_half
    A_R, A_in, V_h = grid.A_R, grid.A_inner, grid.V_half
    vols = grid.cell_volumes()

    C = np.full(n, C0)
    T = np.full(n, T0_C)

    water_init = float(np.sum(C * vols))
    evap_cum = 0.0

    times = [0.0]
    C_out = [C.copy()]
    next_sample = SAMPLE_DT
    stride = int(round(SAMPLE_DT / DT))

    t_f = None                  # 烘干完成时刻（插值到阈值穿越点）
    t_solved = None             # 严格达标的首个时间步
    C_at_tf = None              # 该时间步的水分浓度分布
    step = 0

    while step * DT < T_MAX and t_f is None:
        step += 1
        t_new = step * DT
        P = params_at(t_new - 0.5 * DT)

        # ---------------- 物性（滞后取旧时刻值） ----------------
        rho_n = P.rho(C)
        cp_n = P.cp(C)
        k_n = P.k(C)
        D_n = P.D(C, T + 273.15)

        k_h = harm_mean(k_n[:-1], k_n[1:])
        D_h = iface_mean(D_n[:-1], D_n[1:])   # 浓度连续，界面扩散系数取线性插值

        divT = np.zeros(n)
        divC = np.zeros(n)

        # 轴心：对称条件
        divT[0] = 4.0 * k_h[0] * (T[1] - T[0]) / dr ** 2
        divC[0] = 4.0 * D_h[0] * (C[1] - C[0]) / dr ** 2

        # 内部节点
        qT = r_half * k_h * (T[1:] - T[:-1]) / dr
        qC = r_half * D_h * (C[1:] - C[:-1]) / dr
        divT[1:N] = (qT[1:] - qT[:-1]) / (r_int * dr)
        divC[1:N] = (qC[1:] - qC[:-1]) / (r_int * dr)

        C_prev = C.copy()
        T_new = T + DT * divT / (rho_n * cp_n)
        C_new = np.concatenate([np.maximum(C[:N] + DT * divC[:N], 0.0), [C[N]]])

        # ---------------- 表面节点：半格控制体 + 隐式 ----------------
        Ta_v = Ta(t_new)
        rho_cp_s = rho_n[N] * cp_n[N]
        T_new[N] = ((rho_cp_s * V_h / DT * T[N]
                     + P.h * A_R * Ta_v
                     + k_h[-1] * A_in / dr * T_new[N - 1])
                    / (rho_cp_s * V_h / DT + P.h * A_R + k_h[-1] * A_in / dr))

        Ca_v = Ca(t_new)
        C_new[N] = ((V_h / DT * C[N]
                     + P.hm * A_R * Ca_v
                     + D_h[-1] * A_in / dr * C_new[N - 1])
                    / (V_h / DT + P.hm * A_R + D_h[-1] * A_in / dr))

        # 累计蒸发量 = 表面传质通量对时间积分（唯一的质量出口）
        evap_cum += P.hm * (C_new[N] - Ca_v) * A_R * DT
        T, C = T_new, C_new

        # ---------------- 烘干完成事件：中心首次跌破阈值 ----------------
        if t_f is None and C[0] <= C_SAFE:
            # 用线性插值定位穿越时刻，用于报告所需的精确时长
            c0, c1 = C_prev[0], C[0]
            frac = (c0 - C_SAFE) / (c0 - c1) if c0 != c1 else 0.0
            t_f = t_new - DT + DT * frac
            # 末行取越过阈值后 1 h 的状态，确保表中数值明显低于判据
            # （穿越瞬间 C 恰好等于阈值，四舍五入后仍显示 0.1500）
            extra = int(round(3600.0 / DT))
            for _ in range(extra):
                step += 1
                t_new = step * DT
                P = params_at(t_new - 0.5 * DT)
                rho_n, cp_n = P.rho(C), P.cp(C)
                k_n, D_n = P.k(C), P.D(C, T + 273.15)
                k_h = harm_mean(k_n[:-1], k_n[1:])
                D_h = iface_mean(D_n[:-1], D_n[1:])
                divT = np.zeros(n)
                divC = np.zeros(n)
                divT[0] = 4.0 * k_h[0] * (T[1] - T[0]) / dr ** 2
                divC[0] = 4.0 * D_h[0] * (C[1] - C[0]) / dr ** 2
                qT = r_half * k_h * (T[1:] - T[:-1]) / dr
                qC = r_half * D_h * (C[1:] - C[:-1]) / dr
                divT[1:N] = (qT[1:] - qT[:-1]) / (r_int * dr)
                divC[1:N] = (qC[1:] - qC[:-1]) / (r_int * dr)
                T_new = T + DT * divT / (rho_n * cp_n)
                C_new = np.concatenate(
                    [np.maximum(C[:N] + DT * divC[:N], 0.0), [C[N]]])
                Ta_v, Ca_v = Ta(t_new), Ca(t_new)
                rho_cp_s = rho_n[N] * cp_n[N]
                T_new[N] = ((rho_cp_s * V_h / DT * T[N] + P.h * A_R * Ta_v
                             + k_h[-1] * A_in / dr * T_new[N - 1])
                            / (rho_cp_s * V_h / DT + P.h * A_R
                               + k_h[-1] * A_in / dr))
                C_new[N] = ((V_h / DT * C[N] + P.hm * A_R * Ca_v
                             + D_h[-1] * A_in / dr * C_new[N - 1])
                            / (V_h / DT + P.hm * A_R + D_h[-1] * A_in / dr))
                evap_cum += P.hm * (C_new[N] - Ca_v) * A_R * DT
                T, C = T_new, C_new
            C_at_tf = C.copy()
            t_solved = t_new
            break

        # ---------------- 采样 ----------------
        if step % stride == 0:
            times.append(t_new)
            C_out.append(C.copy())
            next_sample += SAMPLE_DT

    if t_f is None:
        print(f"[警告] 仿真达到上限 {T_MAX/3600:.1f} h，中心水分浓度仍为 {C[0]:.4f}")
        t_f = step * DT
        t_solved = t_f
        C_at_tf = C.copy()

    # 把「严格达标」时刻的真实状态追加为末行
    if times[-1] < t_solved:
        times.append(t_solved)
        C_out.append(C_at_tf.copy())

    # ---------------- 质量守恒校核 ----------------
    # 药材总水量的减少，应等于表面传质通量的时间积分（唯一质量出口）
    water_final = float(np.sum(C * vols))
    loss = water_init - water_final
    rel = (loss - evap_cum) / water_init * 100.0
    report = (f"初始水量 {water_init:.6e}  最终水量 {water_final:.6e}\n"
              f"内部失水量 {loss:.6e}  表面累计蒸发 {evap_cum:.6e}\n"
              f"守恒残差 {rel:.4f}%")

    return np.array(times), np.array(C_out), t_f, C_at_tf, report


# ============================================================
# 主流程
# ============================================================
times, C_out, t_f, C_at_tf, report = solve()

C_grid = np.array([interp_to_distances(grid.r, C_out[i], TARGET_DISTS)
                   for i in range(len(times))])
C_tf_grid = C_grid[-1]          # 末行即「严格达标」时刻的分布

print("=" * 60)
print("质量守恒")
print("=" * 60)
print(report)

save_result(
    os.path.join(BASE_DIR, "result3.xlsx"),
    [("水分浓度", times, C_grid, "时间\\到药材中心的距离")],
)

# ============================================================
# 表5
# ============================================================
TABLE_HOURS = [6, 12, 18, 24, 30, 36, 42]
TABLE_DISTS = [0.0, 0.5, 1.0, 1.5, 2.0]


def col(d):
    return int(np.argmin(np.abs(TARGET_DISTS - d)))


def row(t_val):
    return int(np.argmin(np.abs(times - t_val)))


print("\n" + "=" * 72)
print("表5  药材烘干过程的水分浓度 (kg/kg)")
print(f"烘干结束时间: {t_f/3600:.2f} h ({t_f:.0f} s)")
print("=" * 72)
print(f"{'时间/h':<12}" + "".join(f"{d}cm".rjust(12) for d in TABLE_DISTS))
print("-" * 72)
for th in TABLE_HOURS:
    t_val = min(int(th * 3600), int(times[-1]))
    print(f"{th:<12.1f}" + "".join(f"{C_grid[row(t_val), col(d)]:>12.4f}" for d in TABLE_DISTS))
print(f"{t_f/3600:<12.2f}" + "".join(f"{C_tf_grid[col(d)]:>12.4f}" for d in TABLE_DISTS))
print(f"\n[环境] 阶段切换 t_c = {T_SWITCH/3600:.1f} h；物性保护下界 C_CLIP_LO = {C_CLIP_LO:.0e}")
print(f"[判据] 中心 C(0,t_f) = {C_grid[-1, col(0.0)]:.4f} kg/kg < {C_SAFE}，"
      f"各处最大 C = {C_grid[-1].max():.4f} kg/kg")
print(f"[输出] result3.xlsx: {len(times)} 行 x {len(TARGET_DISTS)} 列")
