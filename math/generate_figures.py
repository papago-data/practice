"""
问题 1 图表生成：预热平衡阶段的温度与水分浓度分布。

输入：result1.xlsx（由 solve_problem1.py 生成）+ 附件1.xlsx（烘房环境）
输出：fig1.pdf  径向分布         fig2.pdf  中心/表面时程曲线
      fig3.pdf  扩散系数曲线     fig4.pdf  解析解校核
      fig5.pdf  预热阶段环境判定  table1.pdf 收敛性对比表
"""

import os

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.interpolate import PchipInterpolator
from scipy.optimize import brentq
from scipy.special import j0, j1

import dry_model as dm

# ---------- 绘图风格 ----------
plt.rcParams.update({
    "font.sans-serif": ["Microsoft YaHei", "SimHei", "DejaVu Sans"],
    "axes.unicode_minus": False,
    "mathtext.fontset": "stix",
    "font.size": 11,
    "axes.linewidth": 0.8,
    "figure.dpi": 100,
})

OUT_DIR = dm.BASE_DIR

# 问题1 物性（附录2）
RHO, CP, K = dm.RHO1, dm.CP1, dm.K1
H, HM, D0 = dm.PARAMS_Q1.h, dm.PARAMS_Q1.hm, dm.D0_1
ALPHA = K / (RHO * CP)


def D1_arr(C):
    """附录2 扩散系数 D = 7e-9 * exp(-0.89/C)（向量化，带数值保护）。"""
    return dm.D1(np.asarray(C, dtype=float))


# ============================================================
# 环境条件（预热平衡阶段：直接使用附件1 实测曲线）
# ============================================================
Ta_env, Ca_env, _ = dm.make_env(use_extrapolation=False)
t_air, T_air, C_air = dm.load_attachment1()


# ============================================================
# 读取求解结果
# ============================================================
def load_result1():
    """读取 result1.xlsx，返回 (时间, 距离cm, 温度矩阵, 水分矩阵)。"""
    path = dm.locate("result1.xlsx")
    sheets = pd.read_excel(path, sheet_name=None, index_col=0)
    out = []
    for key in ("温度", "水分浓度"):
        for name, df in sheets.items():
            if key in name:
                df.index = df.index.astype(float)
                df.columns = df.columns.astype(float)
                out.append((df.index.values, df.columns.values.astype(float), df.values))
                break
    return out[0][0], out[0][1], out[0][2], out[1][2]


times, dist_cm, T_data, C_data = load_result1()
r_nodes = dist_cm / 100.0
print(f"读取 result1.xlsx：{T_data.shape[0]} 时间点 × {T_data.shape[1]} 空间点")


# ============================================================
# 图1：三个时刻的径向分布
# ============================================================
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
colors = ["#2b6cb0", "#dd6b20", "#c53030"]
markers = ["o", "s", "^"]

for i, t_val in enumerate([300, 900, 1800]):
    idx = int(np.argmin(np.abs(times - t_val)))
    ax1.plot(dist_cm, T_data[idx], color=colors[i], marker=markers[i],
             markersize=5, linewidth=2, label=f"{int(times[idx])} s")
    ax2.plot(dist_cm, C_data[idx], color=colors[i], marker=markers[i],
             markersize=5, linewidth=2, label=f"{int(times[idx])} s")

ax1.set_xlabel("到药材中心距离 r (cm)")
ax1.set_ylabel("温度 T (°C)")
ax1.set_title("(a) 温度径向分布", fontweight="bold")
ax1.legend(loc="upper left")
ax1.grid(True, alpha=0.3)
ax1.set_xlim(0, 2)

ax2.set_xlabel("到药材中心距离 r (cm)")
ax2.set_ylabel("水分浓度 C (kg/kg)")
ax2.set_title("(b) 水分浓度径向分布", fontweight="bold")
ax2.legend(loc="upper right")
ax2.grid(True, alpha=0.3)
ax2.set_xlim(0, 2)

fig.suptitle("图1  预热平衡阶段温度与水分浓度径向分布",
             fontsize=14, fontweight="bold", y=1.02)
plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, "fig1.pdf"), 
            bbox_inches="tight", 
            facecolor="white")
plt.close()
print("  fig1.pdf 已保存")


# ============================================================
# 图2：中心与表面的时程曲线
#   (a)(b) 温度场：中心升温、(表面温度 vs 烘房温度)
#   (c)(d)(e) 水分场：局部放大、降幅 ΔC、烘房含湿量
#   中心层在 30 min 内几乎不降（表面传质为瓶颈），与表面差近 1 个量级，
#   单张图无法兼顾，故水分场用三张子图从不同尺度刻画。
# ============================================================
fig, axes = plt.subplots(2, 3, figsize=(17.5, 9))
t_env = np.array([Ta_env(x) for x in times])
c_env = np.array([Ca_env(x) for x in times])

# 三层水分曲线（标签、数据、颜色、线型、线宽），供 (c)(d) 复用
C_show = [("中心 $C(0,t)$", C_data[:, 0], "#2b6cb0", "-", 2.5),
          ("中间层 $C(1\\,\\mathrm{cm},t)$", C_data[:, 10], "#2f855a", "-.", 2.0),
          ("表面 $C(R,t)$", C_data[:, -1], "#c53030", "--", 2.0)]

# ---- (a) 中心温度 ----
axes[0, 0].plot(times, T_data[:, 0], color="#2b6cb0", linewidth=2.2)
axes[0, 0].set_title("(a) 中心温度 T(0, t)", fontweight="bold")
axes[0, 0].set_ylabel("温度 T (°C)")

# ---- (b) 表面温度 vs 烘房温度 ----
axes[0, 1].plot(times, T_data[:, -1], color="#c53030", linewidth=2.2,
                label="表面 $T(R,t)$")
axes[0, 1].plot(times, t_env, color="#718096", linewidth=1.6, linestyle="--",
                label="烘房 $T_a(t)$")
axes[0, 1].set_title("(b) 表面温度 T(R, t)", fontweight="bold")
axes[0, 1].set_ylabel("温度 T (°C)")
axes[0, 1].legend(fontsize=9, loc="upper left")

# ---- (c) 水分浓度时程：纵轴分段，让三层的真实变化都看得见 ----
# 表面从 2.55 降到 1.51，中心层只动到 2.5500；
# 若共用一个 0~2.75 的量程，中心与中间层会被压成一条贴顶的直线。
ax_c = axes[0, 2]
for lab, y, col, ls, lw in C_show:
    ax_c.plot(times, y, color=col, linestyle=ls, linewidth=lw, label=lab)
ax_c.set_title("(c) 水分浓度时程（纵轴分段）", fontweight="bold")
ax_c.set_xlabel("时间 t (s)")
ax_c.set_ylabel("水分浓度 C (kg/kg)")
ax_c.set_xlim(0, 1800)
ax_c.set_ylim(1.40, 2.72)

# 纵轴刻度：2.55 与 2.60 之间的空白用断轴符号跳过
ax_c.set_yticks([1.4, 1.6, 1.8, 2.0, 2.2, 2.4, 2.55, 2.60])
ax_c.set_yticklabels(["1.4", "1.6", "1.8", "2.0", "2.2", "2.4",
                      "2.55\n(初始)", "2.60"])
ax_c.axhspan(2.552, 2.598, color="#F7FAFC", zorder=0)
for yb in (2.552, 2.598):
    for xa in (0.0, 1.0):
        ax_c.plot([xa - 0.014, xa + 0.014], [yb, yb],
                  transform=ax_c.get_yaxis_transform(), color="black",
                  linewidth=1.2, clip_on=False, zorder=6)
ax_c.legend(fontsize=8.5, loc="center left", bbox_to_anchor=(0.02, 0.36))

# 中心层与中间层挤在 2.5500~2.5386 的窄带里，用一张放大插图单独呈现
ax_in = ax_c.inset_axes([0.42, 0.60, 0.55, 0.28])
ax_in.plot(times, C_data[:, 0], color="#2b6cb0", linewidth=1.8)
ax_in.plot(times, C_data[:, 10], color="#2f855a", linestyle="-.", linewidth=1.5)
ax_in.set_xlim(0, 1800)
ax_in.set_ylim(2.536, 2.5525)
ax_in.set_xticks([0, 900, 1800])
ax_in.set_xticklabels([])
ax_in.set_yticks([2.54, 2.545, 2.55])
ax_in.set_yticklabels(["2.540", "2.545", "2.550"], fontsize=7)
ax_in.tick_params(axis="y", pad=1)
ax_in.grid(True, alpha=0.3)
ax_in.text(0.5, 1.06, f"窄带放大：中心 0.0000 / 中间层 {dm.C0 - C_data[-1, 10]:.4f}",
           transform=ax_in.transAxes, fontsize=7.5, ha="center", va="bottom",
           color="#2D3748")
for sp in ax_in.spines.values():
    sp.set_edgecolor("#A0AEC0")

ax_c.annotate(f"表面降幅 {dm.C0 - C_data[-1, -1]:.4f}",
              xy=(1380.0, C_data[1380, -1]), xytext=(700.0, 1.80),
              fontsize=8.5, color="#c53030", ha="left",
              arrowprops=dict(arrowstyle="->", color="#c53030", lw=1.2))

# ---- (d) 降幅 ΔC：三层「动了多少」直接可比，无需断轴 ----
ax_d = axes[1, 0]
for lab, y, col, ls, lw in C_show:
    ax_d.plot(times, dm.C0 - y, color=col, linestyle=ls, linewidth=lw, label=lab)
ax_d.set_title("(d) 相对初始浓度的降幅 $\\Delta C = C_0 - C$", fontweight="bold")
ax_d.set_xlabel("时间 t (s)")
ax_d.set_ylabel("降幅 ΔC (kg/kg)")
ax_d.legend(fontsize=8.5, loc="upper left")
ax_d.annotate(f"表面 {dm.C0 - C_data[-1, -1]:.4f}", xy=(1800.0, dm.C0 - C_data[-1, -1]),
              xytext=(1080.0, 0.80), fontsize=8.5, color="#c53030", ha="left",
              arrowprops=dict(arrowstyle="->", color="#c53030", lw=1.2))
ax_d.annotate(f"中间层 {dm.C0 - C_data[-1, 10]:.4f} ；中心 {dm.C0 - C_data[-1, 0]:.4f}",
              xy=(1450.0, 0.006), xytext=(330.0, 0.30),
              fontsize=8.5, color="#2f855a", ha="left",
              arrowprops=dict(arrowstyle="->", color="#2f855a", lw=1.2))
ax_d.set_xlim(0, 1800)

# ---- (e) 烘房含湿量：量级 0.02~0.03，比药材内部低两个数量级 ----
ax_e = axes[1, 1]
ax_e.plot(times, c_env, color="#718096", linewidth=2.2)
ax_e.set_title("(e) 烘房含湿量 $C_a(t)$", fontweight="bold")
ax_e.set_xlabel("时间 t (s)")
ax_e.set_ylabel("烘房水分浓度 $C_a$ (kg/kg)")
ax_e.annotate(f"{c_env[0]:.5f} → {c_env[-1]:.5f}\n（远低于药材表面 {C_data[-1,-1]:.2f}）",
              xy=(900.0, c_env[900]), xytext=(120.0, c_env[-1] * 0.92),
              fontsize=8.5, color="#4a5568", ha="left",
              arrowprops=dict(arrowstyle="->", color="#4a5568", lw=1.2))

# ---- (f) 径向剖面：给出水分沿半径的分布 ----
ax_f = axes[1, 2]
idx = int(np.argmin(np.abs(times - 1800.0)))
ax_f.plot(dist_cm, C_data[idx], "o-", color="#c53030", linewidth=2.2, markersize=5,
          label=f"水分 C (t={int(times[idx])} s)")
ax_f.set_xlabel("到中心距离 r (cm)")
ax_f.set_ylabel("水分浓度 C (kg/kg)")
ax_f.set_title("(f) 水分浓度径向剖面", fontweight="bold")
ax_f.legend(fontsize=8.5, loc="upper right")
ax_f.set_xlim(0, 2)
# 标出水分梯度只集中在表层
i_flat = int(np.argmax(C_data[idx] < 2.5499))
ax_f.axvspan(0.0, dist_cm[i_flat], color="#2b6cb0", alpha=0.09)
ax_f.annotate(f"r < {dist_cm[i_flat]:.1f} cm 仍为初始值\n（梯度集中在表层约 {2.0 - dist_cm[i_flat]:.1f} cm）",
              xy=(0.55, 2.535), xytext=(0.12, 2.05), fontsize=8.5,
              color="#2b6cb0", ha="left",
              arrowprops=dict(arrowstyle="->", color="#2b6cb0", lw=1.2))

for ax in axes.ravel():
    ax.grid(True, alpha=0.3)

fig.suptitle("图2  中心与表面的温度、水分浓度时程曲线",
             fontsize=15, fontweight="bold", y=1.00)
plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, "fig2.pdf"), 
            bbox_inches="tight", 
            facecolor="white")
plt.close()
print("  fig2.pdf 已保存")

# ============================================================
# 图3：扩散系数 D(C)
# ============================================================
fig, ax = plt.subplots(figsize=(8, 5))
C_range = np.linspace(0.15, 2.55, 500)
D_vals = D1_arr(C_range)

ax.plot(C_range, D_vals, color="#2b6cb0", linewidth=2.5)
ax.fill_between(C_range, D_vals, alpha=0.1, color="#2b6cb0")

for cm in [2.55, 1.5, 0.5, 0.15]:
    dv = float(D1_arr([cm])[0])
    ax.plot(cm, dv, "o", color="#c53030", markersize=7, zorder=5)
    ax.annotate(f"C={cm:.2f}\nD={dv:.2e}", xy=(cm, dv),
                xytext=(cm + 0.15, dv + 0.25e-9), fontsize=8,
                arrowprops=dict(arrowstyle="->", color="#718096", lw=1))

ax.set_xlabel("水分浓度 C (kg/kg)")
ax.set_ylabel("扩散系数 D (m²/s)")
ax.set_title("图3  水分浓度扩散系数 D(C)\n"
             r"$D = 7 \times 10^{-9} \exp(-0.89/C)$",
             fontsize=13, fontweight="bold")
ax.grid(True, alpha=0.3)
ax.set_xlim(0.1, 2.6)
ax.text(0.3, 0.95, "越干越难干\n(D 随 C 减小而减小)",
        transform=ax.transAxes, fontsize=10, va="top", color="#c53030",
        bbox=dict(boxstyle="round,pad=0.3", facecolor="#FFF5F5",
                  alpha=0.9, edgecolor="#FC8181"))
plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, "fig3.pdf"), 
            bbox_inches="tight", 
            facecolor="white")
plt.close()
print("  fig3.pdf 已保存")


# ============================================================
# 图4：解析解校核（恒温恒湿环境，仅考察温度场）
# ============================================================
Ta_const, Ca_const = float(T_air[-1]), float(C_air[-1])
print(f"  校验环境：Ta = {Ta_const:.3f} °C, Ca = {Ca_const:.5f} kg/kg")

times_v, T_v, C_v, r_v = dm.solve_problem1_generic(
    N=20, dt=0.5, t_end=1800.0,
    Ta_func=lambda t: Ta_const, Ca_func=lambda t: Ca_const)

Bi = H * dm.R / K
mus = dm.bessel_eigenvalues(Bi, 20)
print(f"  Bi = {Bi:.4f}，特征值前 5 个: {np.round(mus[:5], 4)}")

fig, axes = plt.subplots(1, 2, figsize=(12, 5))
for ax_idx, t_val in enumerate([300, 1800]):
    ax = axes[ax_idx]
    idx = int(np.argmin(np.abs(times_v - t_val)))
    ax.plot(r_v * 100, T_v[idx], "o-", color="#2b6cb0", markersize=6,
            linewidth=2, label="数值解 (隐式差分)")
    T_exact = dm.analytical_T_cylinder(r_v, t_val, Ta_const, dm.T0_C,
                                       mus, Bi, dm.R, ALPHA)
    ax.plot(r_v * 100, T_exact, "--", color="#c53030", linewidth=2,
            label="解析解 (贝塞尔级数)")
    max_err = float(np.max(np.abs(T_v[idx] - T_exact)))
    ax.set_xlabel("到药材中心距离 r (cm)")
    ax.set_ylabel("温度 T (°C)")
    ax.set_title(f"({'ab'[ax_idx]}) t = {t_val} s  (最大误差 {max_err:.2e} °C)",
                 fontweight="bold")
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_xlim(0, 2)

fig.suptitle(f"图4  解析解与数值解对比（恒温恒湿校核, $T_a$ = {Ta_const:.2f} °C）",
             fontsize=13, fontweight="bold", y=1.02)
plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, "fig4.pdf"), 
            bbox_inches="tight", 
            facecolor="white")
plt.close()
print("  fig4.pdf 已保存")


# ============================================================
# 图5：预热平衡阶段环境判定
#     一阶惯性拟合 + 到达渐近值 0.1 K 以内的时刻
# ============================================================
fig, axes = plt.subplots(1, 2, figsize=(13, 5))

# (a) 环境温度与其渐近值
axes[0].plot(t_air / 3600, T_air, color="#2b6cb0", linewidth=2, label="烘房温度 $T_a(t)$")
axes[0].axhline(dm.T_INF_C, color="#c53030", linestyle="--", linewidth=1.8,
                label=f"渐近值 $T_\\infty$ = {dm.T_INF_C:.3f} °C")
axes[0].axhline(dm.T_INF_C - 0.1, color="#718096", linestyle=":", linewidth=1.2)
axes[0].fill_between([0, t_air[-1] / 3600],
                     dm.T_INF_C - 0.1, dm.T_INF_C + 0.1,
                     color="#c53030", alpha=0.10)
axes[0].set_xlabel("时间 t (h)")
axes[0].set_ylabel("温度 T (°C)")
axes[0].set_title("(a) 环境温度趋于恒温", fontweight="bold")
axes[0].legend(loc="lower right")
axes[0].grid(True, alpha=0.3)

# (b) 温差判据 |Ta - T_inf| 随时间衰减
resid_T = np.abs(T_air - dm.T_INF_C)
resid_C = np.abs(C_air - C_air[-1])

axes[1].semilogy(t_air / 3600, resid_T, color="#2b6cb0", linewidth=2,
                 label=r"$|T_a - T_\infty|$")
axes[1].semilogy(t_air / 3600, resid_C, color="#dd6b20", linewidth=2,
                 label=r"$|C_a - C_a^{\rm end}|$")
axes[1].axhline(0.1, color="#c53030", linestyle="--", linewidth=1.6,
                label="判定阈 0.1 K")
axes[1].axvline(dm.T_SWITCH / 3600, color="#2ca02c", linestyle="-.",
                linewidth=2, label=f"切换时刻 $t_c$ = {dm.T_SWITCH/3600:.1f} h")
axes[1].set_xlabel("时间 t (h)")
axes[1].set_ylabel("偏差（对数轴）")
axes[1].set_title("(b) 环境量趋于恒定的判据", fontweight="bold")
axes[1].legend(loc="upper right", fontsize=9)
axes[1].grid(True, alpha=0.3, which="both")

fig.suptitle("图5  预热平衡阶段与恒温干燥阶段的切换判定",
             fontsize=13, fontweight="bold", y=1.02)
plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, "fig5.pdf"), 
            bbox_inches="tight", 
            facecolor="white")
plt.close()
print("  fig5.pdf 已保存")


# ============================================================
# 表1：网格与步长收敛性对比
# ============================================================
print("生成表1（收敛性对比）...")
table_times = [100, 300, 600, 900, 1200, 1500, 1800]
table_dists = [0.0, 0.5, 1.0, 1.5, 2.0]

# 参考解取最细网格（N=640, Δt=0.0625 s），而非表中任一配置，
# 否则参考解自身的离散误差会被计入，收敛阶无法单调。
times_ref, T_ref, C_ref, r_ref = dm.solve_problem1_generic(
    N=640, dt=0.0625, t_end=1800.0, Ta_func=Ta_env, Ca_func=Ca_env)
dist_ref = r_ref * 100

configs = [
    ("基准 (Δr=0.100cm, Δt=1.00s)", 20, 1.00),
    ("加密空间 (Δr=0.050cm, Δt=1.00s)", 40, 1.00),
    ("加密时间 (Δr=0.100cm, Δt=0.50s)", 20, 0.50),
    ("双重加密 (Δr=0.050cm, Δt=0.50s)", 40, 0.50),
    ("再加密 (Δr=0.025cm, Δt=0.25s)", 80, 0.25),
    ("三度加密 (Δr=0.0125cm, Δt=0.125s)", 160, 0.125),
    ("四度加密 (Δr=0.0063cm, Δt=0.0625s)", 320, 0.0625),
]

# 输出精度：结果按四位小数输出，故以半个末位 (5e-5) 作为「四位小数稳定」的判据
TOL = 5e-5


def at(times_arr, X, dists, tv, dv):
    ti = int(np.argmin(np.abs(times_arr - tv)))
    di = int(np.argmin(np.abs(dists - dv)))
    return X[ti, di]


cell_data = []
for name, N_cfg, dt_cfg in configs:
    print(f"  运行 {name} ...")
    tt, Tc, Cc, rc = dm.solve_problem1_generic(
        N=N_cfg, dt=dt_cfg, t_end=1800.0, Ta_func=Ta_env, Ca_func=Ca_env)
    dc = rc * 100
    errT = max(abs(at(tt, Tc, dc, tv, dv) - at(times_ref, T_ref, dist_ref, tv, dv))
               for tv in table_times for dv in table_dists)
    errC = max(abs(at(tt, Cc, dc, tv, dv) - at(times_ref, C_ref, dist_ref, tv, dv))
               for tv in table_times for dv in table_dists)
    # 以温度场（更严格）判定是否达到输出精度
    if errT < TOL:
        status = "通过"
    elif errT < 10 * TOL:
        status = "接近"
    else:
        status = "待加密"
    cell_data.append([
        name, f"{2.0/N_cfg:.4f}", f"{dt_cfg:.4f}",
        f"{errT:.2e}", f"{errC:.2e}", status,
    ])

fig, ax = plt.subplots(figsize=(16, 5.4))
ax.axis("off")
fig.suptitle("表1  网格与步长收敛性对比", fontsize=14, fontweight="bold", y=0.975)
ax.set_title(
    f"参考解：N=640, Δt=0.0625 s（比表中任一配置更细）；对比量：{len(table_times)} 时刻 × "
    f"{len(table_dists)} 距离\n"
    f"判据：与参考解的最大偏差 < {TOL:.0e}（即结果四舍五入到 4 位小数后不变）；"
    "温度场偏差比水分场更严格，故以温度判定",
    fontsize=9.5, color="#4A5568", pad=14)

col_labels = ["配置", "Δr (cm)", "Δt (s)",
              "温度最大偏差 (°C)", "水分最大偏差 (kg/kg)", "四位小数"]
table = ax.table(cellText=cell_data, colLabels=col_labels,
                 cellLoc="center", loc="center")
table.auto_set_font_size(False)
table.set_fontsize(10)
table.scale(1, 2.0)

STATUS_COLOR = {"通过": "#2F855A", "接近": "#B7791F", "待加密": "#C05621"}
n_cols = len(col_labels)
for j in range(n_cols):
    table[0, j].set_facecolor("#2b6cb0")
    table[0, j].set_text_props(color="white", fontweight="bold")
for i in range(1, len(cell_data) + 1):
    for j in range(n_cols):
        table[i, j].set_facecolor("#F7FAFC" if i % 2 == 0 else "white")
    table[i, n_cols - 1].set_text_props(
        color=STATUS_COLOR[cell_data[i - 1][-1]], fontweight="bold")

# 图下注：说明判定口径与观察到的收敛行为
fig.text(0.5, 0.035,
         "说明：① 只加密时间步（Δt: 1.0→0.5 s）几乎不改变结果，"
         "说明时间格式已充分收敛、误差由空间离散主导。\n"
         "② 随 Δr 减半，最大偏差按约 1.5 阶下降（细网格下趋近 2 阶）；"
         "空间是唯一需要加密的方向，故 Q1 取 Δr=0.0125 cm（N=160）即可让"
         "输出到 4 位小数的结果稳定。\n"
         "③ 表面浓度梯度陡、且 D(C) 在低浓度侧急剧衰减，"
         "是空间离散误差的主要来源，故需比内部问题更细的网格。",
         fontsize=8.5, color="#4A5568", ha="center", va="bottom")

plt.tight_layout(rect=[0, 0.17, 1, 0.92])
plt.savefig(os.path.join(OUT_DIR, "table1.pdf"), 
            bbox_inches="tight", 
            facecolor="white")
plt.close()
print("  table1.pdf 已保存")

print("\n" + "=" * 60)
print("问题1 全部图表生成完毕")
print("=" * 60)
