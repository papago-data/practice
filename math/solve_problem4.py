"""
问题4：变尺寸（移动边界）条件下的烘干时长。

模型：与问题2/3 同一套圆柱双场耦合，改写到 Landau（固连）坐标 ξ = r/R(t)：
    ∂C/∂t|ξ      = (1/(R(t)²·ξ)) ∂/∂ξ ( ξ D(C,T) ∂C/∂ξ )
    ρc_p ∂T/∂t|ξ = (1/(R(t)²·ξ)) ∂/∂ξ ( ξ k(C) ∂T/∂ξ )
干基口径下方程不含体积收缩修正项：干基含水率的分母（干料质量）在收缩中
守恒，固相连坐标的物质导数自动吸收固相速度项，方程与固定域形式同构，
仅 r → R(t)·ξ，且方程中只出现 R(t) 不出现 Ṙ。

物性：附录4 全套（问题4 专用）：
    ρ = 760 + 90C；c_p = 1850 + 2150C/(C+1)；k = 0.12 + 0.20C/(C+1)
    D = 4.2e-4 · exp(-0.30/C) · exp(-3850/T)   （T 单位 K）
几何：R(t) 由附件2 实测给出（2.0 → 1.198 cm），PCHIP 插值，超出末端取末值。
环境：与问题2/3 完全一致（make_env：预热平衡实测 + 恒温干燥外推）。

边界：ξ = 0 对称（轴心 4× 格式）；ξ = 1 表面 Robin（半格控制体隐式）：
    传质  -D ∂C/∂r = h_m (C_a - C_s)   →  ξ 形式对流系数 h_m/R(t)
    换热  -k ∂T/∂r = h   (T_a - T_s)   →  ξ 形式对流系数 R(t)·h
    界面导热/扩散系数只依赖 ξ（Landau 红利：ξ_{N-1/2}·k/Δξ 与 R 无关）。
    R ≡ R_0 时全部系数逐项退化为问题2/3 的固定域格式。

格式：内部节点显式，表面半格节点隐式；默认 Δξ = 0.05（21 节点，恰为初始半径
    0.1 cm 间隔），Δt = 0.5 s。稳定性（R 取最小 1.198 cm）：
    4·D·Δt/(RΔξ)² ≲ 0.01（水分场）、4·α·Δt/(RΔξ)² ≲ 0.49（温度场）。

判据：中心 ξ = 0（最不利点）水分浓度首次降至 C_SAFE = 0.15 kg/kg，
    线性插值定位穿越时刻；出表末行取严格达标后再推进 1 h 的状态。

算例（run_case）：
    q4    附录4 全套物性 + 移动边界 R(t)   —— 生产算例
    regr  附录3 物性 + 固定几何 R ≡ R_0    —— 回归验证，应复现 solve_problem3.py
    fix4  附录4 物性 + 固定几何 R ≡ R_0    —— 归因分解（隔离收缩效应）
    另可用 N / DT / clip_lo 参数做网格收敛与物性下界双算例。

输出 result4.xlsx：
    「水分浓度」表 —— A 列时间(s)；B~V 列为材料坐标（初始半径）
    0.0, 0.1, …, 1.9 cm 与末列「药材表面」（= ξ=1，即当前表面）。
    每列固定追踪同一物质点（其物理半径 = 列名 × R(t)/R_0），
    与模板「0 | 0.1 | … | 药材表面」的 0.1 cm 间隔一致。
    「半径」表 —— 各采样时刻的 R(t) (cm)，供查表与作图。

命令行：
    python solve_problem4.py [q4|regr|fix4]
"""

import os
import sys

import numpy as np
import pandas as pd
from scipy.interpolate import PchipInterpolator

from dry_model import (
    C0, T0_C, C_SAFE, C_CLIP_LO, C_CLIP_HI, BASE_DIR,
    R as R0, make_env, locate, harm_mean, iface_mean,
    rho3, cp3, k3, D3,
)

# ============================================================
# 常量配置
# ============================================================
DT_DEFAULT = 0.5      # 时间步长 (s)
N_DEFAULT = 20        # ξ 方向网格数（Δξ = 0.05，21 节点）
SAMPLE_DT = 60.0      # 输出采样间隔 (s)
T_MAX = 700000.0      # 仿真时长上限 (s)，约 194 h

H_CONV = 25.0         # 对流换热系数 W/(m²·K)（附录2，与问题1–3 一致）
HM_CONV = 8e-7        # 对流传质系数 m/s（附录2，与问题1–3 一致）


# ============================================================
# 附录4 物性（工厂：clip_lo 可调，用于"夹紧 vs 自由外推"双算例）
# ============================================================
def make_props4(clip_lo=C_CLIP_LO):
    """返回附录4 物性函数组 (rho, cp, k, D)；clip_lo 为浓度数值下界。"""
    def _c(C):
        return np.clip(C, clip_lo, C_CLIP_HI)

    def rho(C):
        return 760.0 + 90.0 * _c(C)

    def cp(C):
        Cp = _c(C)
        return 1850.0 + 2150.0 * Cp / (Cp + 1.0)

    def k(C):
        Cp = _c(C)
        return 0.12 + 0.20 * Cp / (Cp + 1.0)

    def D(C, T_K):
        return 4.2e-4 * np.exp(-0.30 / _c(C)) \
            * np.exp(-3850.0 / np.clip(T_K, 250.0, 400.0))

    return rho, cp, k, D


rho4, cp4, k4, D4 = make_props4(C_CLIP_LO)      # 默认物性（与问题3 的解耦口径一致）


# ============================================================
# 几何：附件2 的 R(t)
# ============================================================
def load_radius():
    """读取附件2（时间 s，半径 cm），返回 R_of(t)（单位 m）。

    PCHIP 保单调、无过冲；超出数据末端（259200 s = 72 h）取末值 1.198 cm。
    """
    df = pd.read_excel(locate("附件2.xlsx"))
    t_d = df["时间"].values.astype(float)
    r_d = df["半径"].values.astype(float) * 1e-2      # cm → m
    pR = PchipInterpolator(t_d, r_d, extrapolate=False)

    def R_of(t):
        return float(pR(np.clip(t, t_d[0], t_d[-1])))

    return R_of


# 环境函数（所有算例共用，与问题2/3 完全一致）
TA_FUN, CA_FUN, _ = make_env()


# ============================================================
# 通用算例求解器
# ============================================================
def run_case(mode="q4", N=N_DEFAULT, DT=DT_DEFAULT, clip_lo=C_CLIP_LO,
             sample_dt=SAMPLE_DT, t_max=T_MAX, verbose=False):
    """求解一个算例。

    mode: "q4"   附录4 + 移动边界 R(t)
          "regr" 附录3 + 固定几何 R ≡ R0（回归验证）
          "fix4" 附录4 + 固定几何 R ≡ R0（归因分解）

    返回 dict：times, C(采样矩阵), R(采样半径数组 m), xi(节点 ξ),
               t_f, t_s, t_solved, C_tf(达标后 1 h 的节点浓度),
               T_max, report(质量守恒报告), N, DT
    """
    if mode == "regr":
        rho_f, cp_f, k_f, D_f = rho3, cp3, k3, D3
        R_of = lambda t: R0
    elif mode == "fix4":
        rho_f, cp_f, k_f, D_f = make_props4(clip_lo)
        R_of = lambda t: R0
    elif mode == "q4":
        rho_f, cp_f, k_f, D_f = make_props4(clip_lo)
        R_of = load_radius()
    else:
        raise ValueError(f"未知算例模式 {mode!r}")

    # ---------------- Landau（固连）网格 ----------------
    n = N + 1
    dxi = 1.0 / N
    xi = np.linspace(0.0, 1.0, n)                        # 节点 ξ_j = j·Δξ
    xi_half = (np.arange(N) + 0.5) * dxi                 # 界面 ξ_{j+1/2}
    bnd = np.concatenate(([0.0], xi_half, [1.0]))
    W = 0.5 * (bnd[1:] ** 2 - bnd[:-1] ** 2)             # 控制体 ξ 测度 ∫ξdξ（不随时间变）
    assert abs(W.sum() - 0.5) < 1e-12

    C = np.full(n, C0)
    T = np.full(n, T0_C)

    # ---------------- 显式格式稳定性预检 ----------------
    # 内部节点显式推进要求 4·α·Δt/(R_min·Δξ)² ≤ 1（轴心节点最严）；
    # 网格加密时 Δt 必须按 Δξ² 同步缩小，否则会发散（NaN）。
    _Cg = np.linspace(max(clip_lo, 1e-3), C0, 64)
    alpha_max = float(np.max(k_f(_Cg) / (rho_f(_Cg) * cp_f(_Cg))))
    R_min = min(R_of(0.0), R_of(1e9))
    stab_T = 4.0 * alpha_max * DT / (R_min * dxi) ** 2
    if stab_T > 1.0:
        raise ValueError(
            f"显式格式不稳定：4·α·Δt/(R·Δξ)² = {stab_T:.3f} > 1（N={N}, Δt={DT}）。"
            f"请将 Δt 减小到 {DT / stab_T:.3f} s 以下（Δt 需 ∝ Δξ²）。")
    D_max = float(np.max(D_f(_Cg, np.clip(T0_C + 273.15, 250.0, 400.0))))
    stab_C = 4.0 * D_max * DT / (R_min * dxi) ** 2
    if stab_C > 1.0:
        raise ValueError(
            f"显式格式不稳定：4·Dmax·Δt/(R·Δξ)² = {stab_C:.3f} > 1（N={N}, Δt={DT}）。"
            f"请将 Δt 减小到 {DT / stab_C:.3f} s 以下。")
    if verbose:
        print(f"[稳定性] 4·αmax·Δt/(R·Δξ)² = {stab_T:.4f} ≤ 1  "
              f"(αmax = {alpha_max:.3e} m²/s, R_min = {R_min*100:.3f} cm)")
        print(f"[稳定性] 4·Dmax·Δt/(R·Δξ)² = {stab_C:.4f} ≤ 1  "
              f"(Dmax = {D_max:.3e} m²/s)")

    water_init = float(np.sum(C * W))     # 干基口径总水量（∝ 物理水量，权重恒定）
    evap_cum = 0.0

    times = [0.0]
    C_out = [C.copy()]
    R_out = [R_of(0.0)]
    stride = max(1, int(round(sample_dt / DT)))

    t_f = None                # 中心首次达标时刻（插值）
    t_s = None                # 表面首次达标时刻（插值）
    t_solved = None           # 严格达标后再推进 1 h 的末行时刻
    C_at_tf = None
    T_max = T0_C
    step = 0

    def fields(C, T, t_new):
        """推进一个时间步：内部显式 + 表面半格隐式（问题2/3 的 ξ 形式）。"""
        R_t = R_of(t_new)
        R2 = R_t * R_t

        # ---------------- 物性（滞后取旧时刻值） ----------------
        rho_n = rho_f(C)
        cp_n = cp_f(C)
        k_n = k_f(C)
        D_n = D_f(C, T + 273.15)
        k_h = harm_mean(k_n[:-1], k_n[1:])
        D_h = iface_mean(D_n[:-1], D_n[1:])   # 浓度连续，界面扩散系数取线性插值

        # 界面通量（ξ 形式）：q = ξ·coef·Δfield/Δξ；R 的作用集中在 1/R²
        qC = xi_half * D_h * (C[1:] - C[:-1]) / dxi
        qT = xi_half * k_h * (T[1:] - T[:-1]) / dxi

        divC = np.zeros(n)
        divT = np.zeros(n)
        # 轴心：对称条件（等价于 4×(field[1]-field[0]) 格式）
        divC[0] = qC[0] / (R2 * W[0])
        divT[0] = qT[0] / (R2 * W[0])
        # 内部节点
        divC[1:N] = (qC[1:] - qC[:-1]) / (R2 * W[1:N])
        divT[1:N] = (qT[1:] - qT[:-1]) / (R2 * W[1:N])

        # ---------------- 内部节点推进（显式） ----------------
        T_new = T + DT * divT / (rho_n * cp_n)
        C_new = np.concatenate([np.maximum(C[:N] + DT * divC[:N], 0.0), [C[N]]])

        # ---------------- 表面节点：半格控制体 + 隐式 ----------------
        xi_s = xi_half[-1]                     # 1 - Δξ/2，界面系数与 R 无关
        Ta_v, Ca_v = TA_FUN(t_new), CA_FUN(t_new)

        # 能量：R²·w·ρcp·(T_N^n − T_N)/Δt = ξ_s·k/Δξ·(T_{N−1}^n − T_N^n) + R·h·(Ta − T_N^n)
        rho_cp_s = rho_n[N] * cp_n[N]
        T_new[N] = ((R2 * W[N] * rho_cp_s / DT * T[N]
                     + xi_s * k_h[-1] / dxi * T_new[N - 1]
                     + R_t * H_CONV * Ta_v)
                    / (R2 * W[N] * rho_cp_s / DT
                       + xi_s * k_h[-1] / dxi + R_t * H_CONV))

        # 水分：w·(C_N^n − C_N)/Δt = (h_m/R)·(Ca − C_N^n) + ξ_s·D/(ΔξR²)·(C_{N−1}^n − C_N^n)
        C_new[N] = ((W[N] / DT * C[N]
                     + HM_CONV / R_t * Ca_v
                     + xi_s * D_h[-1] / (dxi * R2) * C_new[N - 1])
                    / (W[N] / DT + HM_CONV / R_t
                       + xi_s * D_h[-1] / (dxi * R2)))

        # 边界蒸发量（干基口径）：d(ΣWC)/dt = −(h_m/R)·(C_N − Ca)
        evap = HM_CONV / R_t * (C_new[N] - Ca_v) * DT
        return C_new, T_new, evap

    while step * DT < t_max and t_f is None:
        step += 1
        t_new = step * DT
        C_prev = C.copy()

        C, T, evap = fields(C, T, t_new)
        evap_cum += evap
        T_max = max(T_max, float(T.max()))

        # ---------------- 表面首次达标 ----------------
        if t_s is None and C[N] <= C_SAFE:
            frac = ((C_prev[N] - C_SAFE) / (C_prev[N] - C[N])
                    if C_prev[N] != C[N] else 0.0)
            t_s = t_new - DT + DT * frac

        # ---------------- 中心首次达标：线性插值 + 延长 1 h ----------------
        if C[0] <= C_SAFE:
            frac = ((C_prev[0] - C_SAFE) / (C_prev[0] - C[0])
                    if C_prev[0] != C[0] else 0.0)
            t_f = t_new - DT + DT * frac
            extra = int(round(3600.0 / DT))
            for _ in range(extra):
                step += 1
                t_new = step * DT
                C, T, evap = fields(C, T, t_new)
                evap_cum += evap
                T_max = max(T_max, float(T.max()))
            C_at_tf = C.copy()
            t_solved = t_new
            break

        # ---------------- 采样 ----------------
        if step % stride == 0:
            times.append(t_new)
            C_out.append(C.copy())
            R_out.append(R_of(t_new))

    if t_f is None:
        print(f"[警告] 仿真达到上限 {t_max/3600:.1f} h，中心水分浓度仍为 {C[0]:.4f}")
        t_f = step * DT
        t_solved = t_f
        C_at_tf = C.copy()

    # 把「严格达标 + 1 h」时刻的真实状态追加为末行
    if times[-1] < t_solved:
        times.append(t_solved)
        C_out.append(C_at_tf.copy())
        R_out.append(R_of(t_solved))

    # ---------------- 质量守恒校核（干基口径） ----------------
    # 药材总水量（ΣWC，权重恒定）的减少应等于表面传质通量的时间积分
    water_final = float(np.sum(C * W))
    loss = water_init - water_final
    rel = (loss - evap_cum) / water_init * 100.0
    report = (f"初始水量 {water_init:.6e}  最终水量 {water_final:.6e}\n"
              f"内部失水量 {loss:.6e}  表面累计蒸发 {evap_cum:.6e}\n"
              f"守恒残差 {rel:.4f}%")

    return {
        "mode": mode, "N": N, "DT": DT, "clip_lo": clip_lo,
        "xi": xi, "W": W,
        "times": np.array(times),
        "C": np.array(C_out),
        "R": np.array(R_out),
        "t_f": t_f, "t_s": t_s, "t_solved": t_solved,
        "C_tf": C_at_tf, "T_max": T_max, "report": report,
        "rel": rel,
    }


# ============================================================
# 主流程（命令行）
# ============================================================
def main():
    mode = sys.argv[1].strip().lower() if len(sys.argv) > 1 else "q4"
    if mode not in ("q4", "regr", "fix4"):
        raise SystemExit(f"用法: python solve_problem4.py [q4|regr|fix4]，未知模式 {mode!r}")

    if mode == "q4":
        print("[模式] Q4：附录4 全套物性 + 附件2 移动边界 R(t)")
    elif mode == "regr":
        print("[模式] REGR 回归验证：R = R0 恒定 + 附录3 物性 —— 应复现 solve_problem3.py")
    else:
        print("[模式] FIX4 归因分解：附录4 物性 + 固定几何 R = R0")

    res = run_case(mode, verbose=True)

    N, DT = res["N"], res["DT"]
    xi, times = res["xi"], res["times"]
    C_out, R_out = res["C"], res["R"]
    t_f, t_s, t_solved = res["t_f"], res["t_s"], res["t_solved"]
    C_at_tf, T_max = res["C_tf"], res["T_max"]

    # ---------------- 输出文件 ----------------
    if mode == "q4":
        out_path = os.path.join(BASE_DIR, "result4.xlsx")
    elif mode == "regr":
        out_path = os.path.join(BASE_DIR, "result4_REGR.xlsx")
    else:
        out_path = os.path.join(BASE_DIR, "result4_FIX4.xlsx")

    # 节点 j 的材料坐标 = ξ_j·R0（N=20 时即 0.1j cm）；j = N 即「药材表面」
    cols = [f"{xi[j] * R0 * 100:.1f}" for j in range(N)] + ["药材表面"]
    df_C = pd.DataFrame(np.round(C_out, 4), columns=cols)
    df_C.insert(0, "时间\\到药材中心的距离", times.astype(int))
    df_R = pd.DataFrame({
        "时间": times.astype(int),
        "半径": np.round(R_out * 100.0, 4),       # cm
    })
    with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
        df_C.to_excel(writer, sheet_name="水分浓度", index=False)
        df_R.to_excel(writer, sheet_name="半径", index=False)

    # ---------------- 物理自检 ----------------
    mono = bool(np.all(np.diff(C_out, axis=0) <= 1e-9))    # 无水源 → 单调不增
    C_avg_tf = float(np.sum(res["W"] * C_at_tf) / res["W"].sum())

    print("=" * 60)
    print("物理自检")
    print("=" * 60)
    print(f"浓度单调不增（每节点）:   {'通过' if mono else '失败'}")
    print(f"温度上界 T_max = {T_max:.3f} ℃（不应超过环境最高约 50.25 ℃）")
    print(f"t_f 时刻面积加权平均含水率 = {C_avg_tf:.4f} kg/kg")
    print()
    print("=" * 60)
    print("质量守恒（干基口径）")
    print("=" * 60)
    print(res["report"])

    # ---------------- 表6：每 6 h、材料坐标 0 / 0.5 / 1.0 / 1.5 cm 与药材表面 ----------------
    idx = [int(round(f * N)) for f in (0.0, 0.25, 0.5, 0.75, 1.0)]   # ξ = 0,0.25,0.5,0.75,1
    lbl = [f"{xi[j] * R0 * 100:.1f}" for j in idx[:-1]] + ["表面"]

    def row_of(t_val):
        return int(np.argmin(np.abs(times - t_val)))

    print()
    print("=" * 72)
    print("表6  药材烘干过程的水分浓度 (kg/kg)   [列 = 材料坐标，末列 = 药材表面]")
    print(f"烘干结束时间: {t_f/3600:.2f} h ({t_f:.0f} s)")
    print("=" * 72)
    print(f"{'时间/h':<12}" + "".join(f"{l}cm".rjust(12) for l in lbl))
    print("-" * 72)
    for th in [6, 12, 18, 24, 30, 36, 42]:
        if th * 3600 > times[-1]:
            continue
        print(f"{th:<12.1f}" + "".join(f"{C_out[row_of(th*3600), j]:>12.4f}" for j in idx))
    print(f"{t_f/3600:<12.2f}" + "".join(f"{C_at_tf[j]:>12.4f}" for j in idx))

    # ---------------- 结果摘要 ----------------
    print()
    print("=" * 60)
    print("结果摘要")
    print("=" * 60)
    print(f"烘干总时长 t_f = {t_f/3600:.4f} h = {t_f:.1f} s ≈ {t_f/86400:.2f} 天")
    if t_s is not None:
        print(f"表面首次达标 t_s = {t_s/3600:.4f} h；表面→中心时滞 "
              f"{(t_f - t_s)/3600:.2f} h")
    print(f"t_f 时刻半径 R(t_f) = {R_out[-1] * 100:.4f} cm")
    print(f"[判据] 中心 C(0, t_f) = {C_at_tf[0]:.4f} kg/kg ≤ {C_SAFE}，"
          f"各处最大 C = {C_at_tf.max():.4f} kg/kg")
    print(f"[输出] {os.path.basename(out_path)}: {len(times)} 行 x {len(cols)} 列"
          f"（+ 半径表 {len(times)} 行）")
    if mode == "regr":
        print("[核对] 请与 solve_problem3.py 的 t_f 及 result3.xlsx 末行时间比对")


if __name__ == "__main__":
    main()
