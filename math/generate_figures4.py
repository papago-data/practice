"""
问题 4 图表生成：变尺寸（移动边界）烘干模型的输入、方法与结果。

输入：solve_problem4.py 的求解器（内部直接调用 run_case，无需先跑主程序）
      附件1（环境）、附件2（半径收缩）；result3.xlsx（问题3 结果，用于归因对比）
输出：fig41.pdf  图1 两阶段环境曲线 T_a(t)/C_a(t) + 2 h 分界线；R(t) 收缩曲线（双子图）
      fig42.pdf  图2 收缩域映射示意图（物理域 → ξ 固定域）
      fig43.pdf  图3 中心与表面 C(t) + 0.15 阈值 + t_f 标注（主图）
      fig44.pdf  图4 每 6 h 径向 C 分布折线族（横轴至当前表面）
      fig45.pdf  图5 归因分解：Q3 / 附录4+固定R / 附录4+收缩 三条 C(0,t)
      fig46.pdf  图6 附录3 vs 附录4 的 D(C) 物性对比
      tables_Q4.xlsx  表6（材料坐标版 + 物理距离版）、t_f 对比表、
                      网格收敛表、双算例表
"""

import os

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import dry_model as dm
from solve_problem4 import run_case, load_radius, make_props4

# ---------- 绘图风格（与问题1–3 图表一致） ----------
plt.rcParams.update({
    "font.sans-serif": ["Microsoft YaHei", "SimHei", "DejaVu Sans"],
    "axes.unicode_minus": False,
    "mathtext.fontset": "stix",
    "font.size": 13,
    "axes.titlesize": 16,
    "axes.labelsize": 14,
    "lines.linewidth": 2.5,
    "axes.grid": True,
    "grid.color": "#E0E0E0",
    "grid.linestyle": "--",
    "grid.linewidth": 0.8,
    "axes.axisbelow": True,
    "axes.spines.top": False,
    "axes.spines.right": False,
})
BASE_DIR = dm.BASE_DIR
DPI = 300
C_SAFE = dm.C_SAFE
R0_CM = dm.R * 100.0            # 2.0 cm

C_Q4 = "#1f77b4"                # 收缩（生产）
C_FIX = "#ff7f0e"               # 附录4 + 固定几何
C_Q3 = "#2ca02c"                # 问题3
C_THR = "#d62728"               # 阈值线
C_MARK = "#7f7f7f"

# ============================================================
# 数据准备
# ============================================================
print("=" * 60)
print("问题4 图表生成")
print("=" * 60)

print("[1/6] 求解算例 ……")
RES_Q4 = run_case("q4")          # 附录4 + 移动边界
RES_FIX = run_case("fix4")       # 附录4 + 固定几何
print(f"      q4   : t_f = {RES_Q4['t_f']/3600:.4f} h")
print(f"      fix4 : t_f = {RES_FIX['t_f']/3600:.4f} h")

def first_crossing(t_arr, c_arr, thr=C_SAFE):
    """线性插值定位数组首次穿越阈值（若无穿越返回 NaN）。"""
    b = np.where(c_arr <= thr)[0]
    if b.size == 0:
        return float("nan")
    i = int(b[0])
    if i == 0 or c_arr[i - 1] == c_arr[i]:
        return float(t_arr[i])
    fr = (c_arr[i - 1] - thr) / (c_arr[i - 1] - c_arr[i])
    return float(t_arr[i - 1] + (t_arr[i] - t_arr[i - 1]) * fr)


# 问题3 曲线：优先读取 result3.xlsx（问题3 的正式产物），缺失时用 regr 算例兜底
try:
    _p3 = dm.locate("result3.xlsx")
    _df3 = pd.read_excel(_p3, sheet_name=0, index_col=0)
    T3 = _df3.index.values.astype(float)
    C3 = _df3.values[:, 0]
    TF_Q3 = first_crossing(T3, C3)
    TS_Q3 = first_crossing(T3, _df3.values[:, -1])
    print(f"      Q3   : 读取 result3.xlsx，t_f = {TF_Q3/3600:.4f} h，"
          f"t_s = {TS_Q3/3600:.4f} h")
except Exception as exc:                                    # noqa: BLE001
    print(f"      [提示] 未读到 result3.xlsx（{exc}），改用 regr 算例")
    _r = run_case("regr")
    T3, C3 = _r["times"], _r["C"][:, 0]
    TF_Q3 = _r["t_f"]
    TS_Q3 = _r["t_s"]

R_of = load_radius()
TA_F, CA_F, _ = dm.make_env()          # 环境函数（只构造一次，避免重复读附件1）

# q4 的常用量
T4, C4, R4 = RES_Q4["times"], RES_Q4["C"], RES_Q4["R"]
TF_Q4, TS_Q4 = RES_Q4["t_f"], RES_Q4["t_s"]
TF_FIX, TS_FIX = RES_FIX["t_f"], RES_FIX["t_s"]
XI_NODES = RES_Q4["xi"]
MAT_CM = XI_NODES * R0_CM                    # 材料坐标（初始半径）cm
R4_CM = R4 * 100.0


# ============================================================
# 图1：两阶段环境曲线 + R(t) 收缩曲线（双子图）
# ============================================================
print("[2/6] 图1 环境与几何 ……")
_t_at, _T_at, _C_at = dm.load_attachment1()
_tt = np.linspace(0.0, TF_Q4 * 1.03, 2000)
_Ta_ext = np.array([TA_F(t) for t in _tt])
_Ca_ext = np.array([CA_F(t) for t in _tt])
_tc_h = dm.T_SWITCH / 3600.0

fig, axes = plt.subplots(1, 2, figsize=(15.5, 5.9))

ax = axes[0]
ax.plot(_tt / 3600, _Ta_ext, color=C_Q4, lw=2.6, zorder=4,
        label=r"环境温度 $T_a(t)$")
ax.plot(_t_at / 3600, _T_at, color="#0B4C8C", lw=0, marker="o", ms=2.4,
        alpha=0.55, zorder=5, label="附件1 温度实测")
ax.axvspan(0, _tc_h, color="#FFF3E0", alpha=0.70, zorder=0)
ax.axvspan(dm.T_SWITCH_BAND[0] / 3600, dm.T_SWITCH_BAND[1] / 3600,
           color="#BDBDBD", alpha=0.30, zorder=0)
ax.axvline(_tc_h, color=C_MARK, ls="--", lw=1.8, zorder=2)
ax.axvline(14400 / 3600, color="#BBBBBB", ls=":", lw=1.5, zorder=2)
ax.text(3.3, 44.5, "阶段 I\n预热平衡", fontsize=11.5, color="#B26A00",
        fontweight="bold", ha="center", va="center", zorder=6)
ax.text(13.5, 46.0, "阶段 II 恒温干燥", fontsize=12, color="#5F5F5F",
        fontweight="bold", va="top", zorder=6)
ax.text(4.75, 30.4, "附件1 实测末端 4 h", fontsize=10, color="#8A8A8A",
        rotation=90, va="bottom", ha="center", zorder=6)
ax.annotate(f"$T_a \\to T_\\infty$ = {dm.T_INF_C:.3f} ℃",
            xy=(TF_Q4 / 3600 * 0.88, TA_F(TF_Q4 * 0.88)),
            xytext=(TF_Q4 / 3600 * 0.27, 41.4), fontsize=11.5, color=C_Q4,
            zorder=6,
            arrowprops=dict(arrowstyle="->", color=C_Q4, lw=1.5,
                            connectionstyle="arc3,rad=-0.18"))
ax.annotate("2 h 分界", xy=(_tc_h, 51.5), xytext=(4.6, 52.2), fontsize=10.5,
            color="#666666", zorder=6,
            arrowprops=dict(arrowstyle="->", color="#999999", lw=1.2))
ax.set_xlabel("时间 t (h)")
ax.set_ylabel(r"环境温度 $T_a$ (℃)", color=C_Q4)
ax.tick_params(axis="y", labelcolor=C_Q4)
ax.set_xlim(0, TF_Q4 / 3600 * 1.03)
ax.set_ylim(26, 53.4)

ax2 = ax.twinx()
ax.plot(_tt / 3600, _Ca_ext, color="#8e44ad", lw=2.6, ls="-", zorder=3,
         label=r"环境含湿量 $C_a(t)$")
ax2.plot(_t_at / 3600, _C_at, color="#5B2C6F", lw=0, marker="s", ms=2.2,
         alpha=0.50, zorder=5,
         label="附件1 含湿量实测")
ax2.axhline(dm.C_A_DRY, color="#8e44ad", ls=":", lw=1.5)
ax2.annotate(f"4.5 h 起除湿：$C_a \\to$ {dm.C_A_DRY:.5f}",
             xy=(5.2, dm.C_A_DRY),
             xytext=(7.6, 0.0255), fontsize=10.5,
             color="#8e44ad", zorder=6,
             arrowprops=dict(arrowstyle="->", color="#8e44ad", lw=1.3))
ax2.set_ylabel(r"环境含湿量 $C_a$ (kg/kg)", color="#8e44ad")
ax2.tick_params(axis="y", labelcolor="#8e44ad")
ax2.set_ylim(0.015, 0.088)
ax2.grid(False)
h1, l1 = ax.get_legend_handles_labels()
h2, l2 = ax2.get_legend_handles_labels()
ax.legend(h1 + h2, l1 + l2, loc="center right", frameon=False, fontsize=10.5,
          bbox_to_anchor=(1.005, 0.42))
ax.set_title("(a) 两阶段环境曲线与 2 h 分界线", fontweight="bold")

ax = axes[1]
_t_r = np.linspace(0, 259200, 800)
ax.plot(_t_r / 3600, [R_of(t) * 100 for t in _t_r],
        color="#D85A30", lw=2.8, label=r"$R(t)$（附件2 PCHIP 插值）")
_r2t = pd.read_excel(dm.locate("附件2.xlsx"))
ax.plot(_r2t["时间"].values / 3600, _r2t["半径"].values, color="#7B2D0E",
        lw=0, marker="o", ms=3.6, alpha=0.65, label="附件2 实测点（1 800 s）")
ax.axvline(TF_Q4 / 3600, color=C_Q4, ls="-.", lw=1.8,
           label=f"$t_f$ = {TF_Q4/3600:.2f} h")
ax.axhline(1.198, color=C_MARK, ls=":", lw=1.5,
           label=r"$R_\infty$ = 1.198 cm（饱和半径）")
ax.annotate(r"$R_0$ = 2.000 cm", xy=(0.6, 1.996), xytext=(5.2, 1.925),
            fontsize=11, color="#D85A30", zorder=6,
            arrowprops=dict(arrowstyle="->", color="#D85A30", lw=1.5))
ax.annotate(r"$R_\infty$ = 1.198 cm", xy=(62.0, 1.199), xytext=(47.0, 1.305),
            fontsize=11, color="#8A8A8A", zorder=6,
            arrowprops=dict(arrowstyle="->", color="#8A8A8A", lw=1.4))
ax.scatter([TF_Q4 / 3600], [R_of(TF_Q4) * 100], color=C_Q4, s=110, zorder=6,
           edgecolors="white", linewidths=1.5)
ax.annotate(f"$t_f$ 时刻 $R$ = {R_of(TF_Q4)*100:.3f} cm\n"
            f"$(R/R_0)^2$ = {(R_of(TF_Q4)/dm.R)**2:.3f}",
            xy=(TF_Q4 / 3600, R_of(TF_Q4) * 100),
            xytext=(21.0, 1.635), fontsize=11, color=C_Q4, zorder=6,
            ha="left", va="center",
            bbox=dict(boxstyle="round,pad=0.4", fc="#EAF2FB", ec=C_Q4, alpha=0.92),
            arrowprops=dict(arrowstyle="->", color=C_Q4, lw=1.8,
                            connectionstyle="arc3,rad=-0.15"))
ax.text(56.0, 1.165, "42 h 后近似饱和", fontsize=10, color="#8A8A8A", zorder=6)
ax.set_xlabel("时间 t (h)")
ax.set_ylabel("药材半径 R (cm)")
ax.set_xlim(0, 73)
ax.set_ylim(1.14, 2.10)
ax.legend(loc="upper right", frameon=False, fontsize=10.5)
ax.set_title(r"(b) 附件2 半径收缩曲线 $R(t)$", fontweight="bold")

fig.suptitle("图1  两阶段环境曲线与半径收缩曲线（问题四 模型输入）",
             fontsize=16, fontweight="bold")
plt.tight_layout()
plt.savefig(os.path.join(BASE_DIR, "fig41.pdf"), dpi=DPI,
            bbox_inches="tight", facecolor="white")
plt.close()
print("      fig41.pdf 已保存")


# ============================================================
# 图2：收缩域映射示意图（物理域 → ξ 固定域）
# ============================================================
print("[3/6] 图2 收缩域映射示意 ……")
_T_SHOW = [0.0, 18.0, TF_Q4 / 3600]
_MAT_SHOW = np.arange(0.0, 2.0 + 1e-9, 0.5)          # 材料坐标 0/0.5/1.0/1.5/2.0 cm
CMAP_T = ["#1f77b4", "#ff7f0e", "#d62728"]

fig, axes = plt.subplots(2, 1, figsize=(13, 7.6),
                         gridspec_kw={"height_ratios": [2.1, 1.0], "hspace": 0.35})

ax = axes[0]
for k, th in enumerate(_T_SHOW):
    y = len(_T_SHOW) - 1 - k
    Rt = R_of(th * 3600) * 100
    ax.plot([0, R0_CM], [y, y], color="#EEEEEE", lw=9, solid_capstyle="butt",
            zorder=1)
    ax.plot([0, Rt], [y, y], color=CMAP_T[k], lw=9, solid_capstyle="butt",
            zorder=2, alpha=0.85)
    ax.scatter(_MAT_SHOW / R0_CM * Rt, np.full_like(_MAT_SHOW, y),
               color="#333333", s=26, zorder=3)
    ax.text(Rt + 0.045, y, f"$R$ = {Rt:.3f} cm", va="center",
            fontsize=11.5, color=CMAP_T[k], fontweight="bold")
    ax.text(-0.045, y, f"$t$ = {th:.0f} h", va="center", ha="right", fontsize=12)
    for m in _MAT_SHOW[:-1]:
        ax.annotate("", xy=(m / R0_CM * Rt, y - 0.34),
                    xytext=(m, y - 0.34),
                    arrowprops=dict(arrowstyle="->", color="#AAAAAA", lw=1.2))
ax.annotate("", xy=(1.02, -0.62), xytext=(0.62, -0.62),
            arrowprops=dict(arrowstyle="<->", color="#666666", lw=1.6))
ax.text(0.80, -0.82, "同一点向内收缩", fontsize=11, color="#666666", ha="center")
ax.set_xlim(-0.55, 2.45)
ax.set_ylim(-0.95, 2.62)
ax.set_xticks(np.arange(0, 2.01, 0.5))
ax.set_xlabel("到中心距离 r (cm)   —— 物理域，长度随时间缩短")
ax.set_yticks([])
ax.grid(False)
ax.set_title("(a) 物理域：网格点随药材一起收缩（同一点的门牌号会变）",
             fontweight="bold")
for s in ("left", "right", "bottom"):
    ax.spines[s].set_visible(False)

ax = axes[1]
ax.plot([0, 1], [0, 0], color="#2C7FB8", lw=9, solid_capstyle="butt",
        alpha=0.85, zorder=2)
ax.scatter(XI_NODES, np.zeros_like(XI_NODES), color="#333333", s=26, zorder=3)
for xv in XI_NODES[::2]:
    ax.text(xv, -0.52, f"{xv:.2f}", ha="center", fontsize=9.5, color="#555555")
ax.set_xlim(-0.02, 1.14)
ax.set_ylim(-0.75, 0.62)
ax.set_xticks([])
ax.set_yticks([])
ax.grid(False)
ax.text(1.015, 0, r"$\xi = 1$（表面）", va="center", fontsize=11.5)
ax.text(-0.012, 0, r"$\xi = 0$", va="center", ha="right", fontsize=11.5)
ax.set_xlabel(r"归一化坐标 $\xi$   —— 计算域，网格永远不动")
ax.set_title(r"(b) 计算域：$\xi = r/R(t) \in [0,1]$ 固定网格（门牌号不变）",
             fontweight="bold")
for s in ("left", "right", "bottom", "top"):
    ax.spines[s].set_visible(False)

fig.text(0.5, 0.485, r"坐标变换  $r = \xi \cdot R(t)$",
         ha="center", fontsize=14, fontweight="bold", color="#2C7FB8",
         bbox=dict(boxstyle="round,pad=0.45", fc="#EAF2FB", ec="#2C7FB8"))
fig.suptitle("图2  收缩域映射：物理域 → ξ 固定域（Landau 固连坐标）",
             fontsize=16, fontweight="bold")
plt.savefig(os.path.join(BASE_DIR, "fig42.pdf"), dpi=DPI,
            bbox_inches="tight", facecolor="white")
plt.close()
print("      fig42.pdf 已保存")


# ============================================================
# 图3：主图 —— 中心与表面 C(t) + 阈值 + t_f
# ============================================================
print("[4/6] 图3 主图 ……")
fig, ax = plt.subplots(figsize=(12.5, 7))
_th = T4 / 3600
_ylim = (1.2e-2, 3.6)
ax.plot(_th, C4[:, 0], color=C_Q4, lw=2.8, zorder=4,
        label=r"中心 $\xi=0$（最不利点，决定 $t_f$）")
ax.plot(_th, C4[:, -1], color="#D85A30", lw=2.8, zorder=4,
        label=r"药材表面 $\xi=1$")
ax.fill_between(_th, C4[:, 0], C_SAFE, where=(C4[:, 0] >= C_SAFE),
                color=C_Q4, alpha=0.06, zorder=1)
ax.axhline(C_SAFE, color=C_THR, ls="--", lw=1.8, zorder=3,
           label=f"安全阈值 {C_SAFE} kg/kg（达标线）")
ax.axvline(TS_Q4 / 3600, color="#9467bd", ls=":", lw=1.6, zorder=3,
           label=f"表面首次达标 $t_s$ = {TS_Q4/3600:.2f} h")
ax.axvline(TF_Q4 / 3600, color="#2ca02c", ls="-.", lw=1.8, zorder=3,
           label=f"烘干完成 $t_f$ = {TF_Q4/3600:.2f} h")
ax.scatter([TF_Q4 / 3600], [C_SAFE], color=C_THR, s=140, zorder=7,
           edgecolors="white", linewidths=1.8)

ax.set_yscale("log")
ax.set_ylim(*_ylim)
ax.set_xlim(0, TF_Q4 / 3600 * 1.06)
_yt = [0.02, 0.05, 0.1, 0.15, 0.3, 0.6, 1.2, 2.4]
ax.set_yticks(_yt)
ax.set_yticklabels([f"{v:g}" for v in _yt])
ax.minorticks_off()

# ---- t_s 标注（竖线左侧，避让两条曲线） ----
ax.annotate(f"$t_s$ = {TS_Q4/3600:.2f} h",
            xy=(TS_Q4 / 3600, 2.55), xytext=(TS_Q4 / 3600 - 0.9, 2.55),
            ha="right", va="center", fontsize=11.5, color="#9467bd", zorder=8,
            arrowprops=dict(arrowstyle="->", color="#9467bd", lw=1.6))

# ---- t_f 标注（右侧中部，箭头指向 0.15 阈值交点） ----
ax.annotate(f"$t_f$ = {TF_Q4/3600:.2f} h（≈ {TF_Q4/86400:.2f} 天）",
            xy=(TF_Q4 / 3600 * 0.998, C_SAFE * 1.02),
            xytext=(TF_Q4 / 3600 - 4.6, 0.45),
            ha="right", va="center", fontsize=12, fontweight="bold",
            color=C_THR, zorder=8,
            bbox=dict(boxstyle="round,pad=0.42", fc="#FFF5F5", ec=C_THR,
                      alpha=0.95),
            arrowprops=dict(arrowstyle="->", color=C_THR, lw=1.9))

# ---- 左上角数据卡（只放一组，不与图例重复） ----
ax.text(0.30, 0.975,
        f"$t_f$ = {TF_Q4/3600:.2f} h ≈ {TF_Q4/86400:.2f} 天"
        f"（中心降至 {C_SAFE} kg/kg）\n"
        f"表面→中心时滞 $t_f - t_s$ = {(TF_Q4-TS_Q4)/3600:.2f} h\n"
        f"初始 $C_0$ = {C4[0,0]:.2f} kg/kg，初始 $R_0$ = 2.00 cm\n"
        f"$t_f$ 时刻 $R$ = {R_of(TF_Q4)*100:.3f} cm"
        f"（$(R/R_0)^2$ = {(R_of(TF_Q4)/dm.R)**2:.3f}，体积缩至 "
        f"{(R_of(TF_Q4)/dm.R)**2*100:.1f}%）",
        transform=ax.transAxes, fontsize=11.5, va="top", ha="left", zorder=8,
        bbox=dict(boxstyle="round,pad=0.5", fc="#F7F7F7", ec="#CCCCCC",
                  alpha=0.96))

ax.set_xlabel("时间 t (h)")
ax.set_ylabel("水分浓度 C (kg/kg)")
ax.legend(loc="lower left", frameon=False, fontsize=11)
ax.set_title("图3  中心与表面水分浓度演化及烘干完成时间（含收缩修正）",
             fontsize=16, fontweight="bold")
plt.tight_layout()
plt.savefig(os.path.join(BASE_DIR, "fig43.pdf"), dpi=DPI,
            bbox_inches="tight", facecolor="white")
plt.close()
print("      fig43.pdf 已保存")


# ============================================================
# 图4：每 6 h 径向 C 分布折线族（横轴至当前表面）
# ============================================================
print("[5/6] 图4 径向剖面族 ……")
_H_LIST = [6, 12, 18, 24, 30, 36, 42]
_idx_h = [int(np.argmin(np.abs(T4 - h * 3600))) for h in _H_LIST]
_idx_f = len(T4) - 1
_ROWS = _idx_h + [_idx_f]
_LAB_H = [f"{h} h" for h in _H_LIST] + [f"$t_f$ = {TF_Q4/3600:.2f} h"]

fig, ax = plt.subplots(figsize=(12.5, 7))
cmap = plt.get_cmap("viridis")
for k, i in enumerate(_ROWS):
    Rt = R4_CM[i]
    r_phys = MAT_CM / R0_CM * Rt                    # 物理半径（cm）
    ax.plot(r_phys, C4[i], color=cmap(k / max(1, len(_ROWS) - 1)), lw=2.4,
            marker="o", ms=3.4,
            label=f"$t$ = {_LAB_H[k]}（$R$ = {Rt:.3f} cm）")
    ax.scatter([Rt], [C4[i, -1]], color=cmap(k / max(1, len(_ROWS) - 1)), s=55,
               zorder=5, edgecolors="white", linewidths=1.0)
ax.axhline(C_SAFE, color=C_THR, ls="--", lw=1.8, label=f"安全阈值 {C_SAFE} kg/kg")
ax.annotate("曲线右端 = 当前表面\n（随收缩向左移动）",
            xy=(R4_CM[_idx_f], C4[_idx_f, -1]),
            xytext=(1.42, 1.35), fontsize=11.5, color="#D85A30",
            arrowprops=dict(arrowstyle="->", color="#D85A30", lw=1.7))
ax.set_xlabel("到中心距离 r (cm)（按当前几何）")
ax.set_ylabel("水分浓度 C (kg/kg)")
ax.set_xlim(0, 2.05)
ax.set_ylim(0, 2.72)
ax.legend(loc="upper right", frameon=False, fontsize=10.5, ncol=2)
ax.set_title("图4  每 6 h 的径向水分浓度剖面族（横轴至当前药材表面）",
             fontsize=16, fontweight="bold")
plt.tight_layout()
plt.savefig(os.path.join(BASE_DIR, "fig44.pdf"), dpi=DPI,
            bbox_inches="tight", facecolor="white")
plt.close()
print("      fig44.pdf 已保存")


# ============================================================
# 图5：归因分解 —— 三条 C(0,t) 曲线
# ============================================================
print("[6/6] 图5 归因分解 / 图6 物性对比 ……")
fig, ax = plt.subplots(figsize=(12.5, 7))
ax.plot(T3 / 3600, C3, color=C_Q3, lw=2.8,
        label=f"问题三：附录3 + 固定几何（$t_f$ = {TF_Q3/3600:.2f} h）")
ax.plot(RES_FIX["times"] / 3600, RES_FIX["C"][:, 0], color=C_FIX, lw=2.8,
        label=f"附录4 + 固定几何（$t_f$ = {TF_FIX/3600:.2f} h）")
ax.plot(T4 / 3600, C4[:, 0], color=C_Q4, lw=2.8,
        label=f"附录4 + 收缩 $R(t)$（$t_f$ = {TF_Q4/3600:.2f} h）")
ax.axhline(C_SAFE, color=C_THR, ls="--", lw=1.8, label=f"安全阈值 {C_SAFE} kg/kg")
for tf, cc in [(TF_Q3, C_Q3), (TF_FIX, C_FIX), (TF_Q4, C_Q4)]:
    ax.axvline(tf / 3600, color=cc, ls="-.", lw=1.5, alpha=0.85)
    ax.scatter([tf / 3600], [C_SAFE], color=cc, s=95, zorder=6,
               edgecolors="white", linewidths=1.4)
ax.annotate(f"收缩效应\n−{(TF_FIX-TF_Q4)/3600:.2f} h",
            xy=(TF_Q4 / 3600, C_SAFE), xytext=(TF_Q4 / 3600 - 15.5, 0.52),
            fontsize=11.5, color=C_Q4,
            arrowprops=dict(arrowstyle="->", color=C_Q4, lw=1.8))
ax.annotate(f"物性效应（附录3→4）\n+{(TF_FIX-TF_Q3)/3600:.2f} h",
            xy=(TF_FIX / 3600, C_SAFE), xytext=(TF_FIX / 3600 - 8.5, 1.55),
            fontsize=11.5, color=C_FIX,
            arrowprops=dict(arrowstyle="->", color=C_FIX, lw=1.8))
ax.text(0.030, 0.965,
        f"$\\Delta t_f$（附录4 固定 → 收缩） = −{(TF_FIX-TF_Q4)/3600:.2f} h "
        f"（−{(TF_FIX-TF_Q4)/TF_FIX*100:.1f}%）\n"
        f"$\\Delta t_f$（附录3 → 附录4 固定） = +{(TF_FIX-TF_Q3)/3600:.2f} h "
        f"（+{(TF_FIX-TF_Q3)/TF_Q3*100:.1f}%）\n"
        f"净效应：{TF_Q4/3600:.2f} h（相对问题三 "
        f"{(TF_Q4-TF_Q3)/TF_Q3*100:+.2f}%，{TF_Q4/86400:.2f} 天）",
        transform=ax.transAxes, fontsize=11.5, va="top",
        bbox=dict(boxstyle="round,pad=0.5", fc="#F7F7F7", ec="#CCCCCC", alpha=0.95))
ax.set_xlabel("时间 t (h)")
ax.set_ylabel("中心水分浓度 $C(0,t)$ (kg/kg)")
ax.set_yscale("log")
ax.set_ylim(1.5e-2, 3.2)
ax.set_xlim(0, max(TF_Q3, TF_FIX, TF_Q4) / 3600 * 1.03)
ax.legend(loc="lower left", frameon=False, fontsize=11)
ax.set_title("图5  收缩效应与物性效应的归因分解（三条中心浓度曲线）",
             fontsize=16, fontweight="bold")
plt.tight_layout()
plt.savefig(os.path.join(BASE_DIR, "fig45.pdf"), dpi=DPI,
            bbox_inches="tight", facecolor="white")
plt.close()
print("      fig45.pdf 已保存")


# ============================================================
# 图6：附录3 vs 附录4 的 D(C) 物性对比
# ============================================================
_Cg = np.linspace(C_SAFE, dm.C0, 400)
fig, axes = plt.subplots(1, 2, figsize=(15, 5.8))

ax = axes[0]
for T_C, ls in [(28.0, "--"), (50.0, "-")]:
    ax.plot(_Cg, dm.D3(_Cg, T_C + 273.15), color="#2ca02c", ls=ls, lw=2.5,
            label=f"附录3  $D_3$（T = {T_C:.0f} ℃）")
    ax.plot(_Cg, [4.2e-4 * np.exp(-0.30 / c) * np.exp(-3850.0 / (T_C + 273.15))
                  for c in _Cg], color=C_Q4, ls=ls, lw=2.5,
            label=f"附录4  $D_4$（T = {T_C:.0f} ℃）")
ax.set_xlabel("水分浓度 C (kg/kg)")
ax.set_ylabel(r"扩散系数 $D$ (m²/s)")
ax.set_yscale("log")
ax.set_xlim(C_SAFE, dm.C0)
ax.set_ylim(2e-11, 3e-8)
ax.legend(frameon=False, fontsize=10.5)
ax.set_title("(a) 扩散系数随含水率与温度的变化", fontweight="bold")

ax = axes[1]
_ratio = dm.D3(_Cg, 323.15) / (4.2e-4 * np.exp(-0.30 / _Cg)
                               * np.exp(-3850.0 / 323.15))
ax.plot(_Cg, _ratio, color="#8e44ad", lw=2.8)
ax.fill_between(_Cg, 2.10, _ratio, alpha=0.10, color="#8e44ad")
ax.axhline(_ratio[0], color=C_MARK, ls=":", lw=1.5)
ax.axhline(_ratio[-1], color=C_MARK, ls=":", lw=1.5)
ax.annotate(f"$C$ = {_Cg[0]:.2f}：比值 {_ratio[0]:.2f}", xy=(_Cg[0], _ratio[0]),
            xytext=(0.62, 2.55), fontsize=11.5, color="#8e44ad",
            arrowprops=dict(arrowstyle="->", color="#8e44ad", lw=1.6))
ax.annotate(f"$C$ = {_Cg[-1]:.2f}：比值 {_ratio[-1]:.2f}", xy=(_Cg[-1], _ratio[-1]),
            xytext=(1.10, 4.62), fontsize=11.5, color="#8e44ad",
            arrowprops=dict(arrowstyle="->", color="#8e44ad", lw=1.6))
ax.text(0.04, 0.30,
        r"$D_3/D_4 = 5.71\,e^{-0.15/C}$" + "\n（与温度无关）\n"
        f"全程比值 ≈ {_ratio[-1]:.2f} ~ {_ratio[0]:.2f}",
        transform=ax.transAxes, fontsize=12,
        bbox=dict(boxstyle="round,pad=0.5", fc="#F7F0FB", ec="#8e44ad", alpha=0.95))
ax.set_xlabel("水分浓度 C (kg/kg)")
ax.set_ylabel(r"扩散系数比值 $D_3 / D_4$")
ax.set_xlim(C_SAFE, dm.C0)
ax.set_ylim(1.6, 6.4)
ax.set_title("(b) 附录4 的扩散系数更小（2–5 倍）", fontweight="bold")

fig.suptitle("图6  附录3 与附录4 的物性对比（$D$–$C$ 曲线）",
             fontsize=16, fontweight="bold")
plt.tight_layout()
plt.savefig(os.path.join(BASE_DIR, "fig46.pdf"), dpi=DPI,
            bbox_inches="tight", facecolor="white")
plt.close()
print("      fig46.pdf 已保存")

# 快速模式：只重绘图形，跳过网格收敛/双算例等额外算例与表格重写
# 用法：Q4_FAST=1 python generate_figures4.py
if os.environ.get("Q4_FAST", "") == "1":
    print()
    print("=" * 60)
    print("[FAST] 已跳过网格收敛/双算例，保留既有 tables_Q4.xlsx")
    print(f"图形已保存至 {BASE_DIR}：fig41–fig46.pdf")
    print("=" * 60)
    raise SystemExit(0)


# ============================================================
# 附：网格收敛表 与 双算例表（需要额外算例）
# ============================================================
print("[表] 网格收敛 / 双算例 ……")
# 显式格式稳定性数 4·αmax·Δt/(R_min·Δξ)²（判据 ≤ 1，见 solve_problem4.run_case）
_rho4f, _cp4f, _k4f, _D4f = make_props4(dm.C_CLIP_LO)
_Cg = np.linspace(dm.C_SAFE, dm.C0, 64)
ALPHA_MAX = float(np.max(_k4f(_Cg) / (_rho4f(_Cg) * _cp4f(_Cg))))
R_MIN_M = R_of(1e9)


def stab_num(NN, DTT):
    """内部显式推进的稳定性数（轴心节点最严）。"""
    return 4.0 * ALPHA_MAX * DTT / (R_MIN_M * (1.0 / NN)) ** 2


_CONV = [("基准", RES_Q4["N"], RES_Q4["DT"], TF_Q4)]
for tag, NN, DTT in [("加密时间步", 20, 0.25),
                     ("加密网格（Δt 同步 ×1/4）", 40, 0.125),
                     ("粗化", 10, 1.0)]:
    rr = run_case("q4", N=NN, DT=DTT)
    _CONV.append((tag, NN, DTT, rr["t_f"]))
    print(f"      N={NN:>2}, dt={DTT:<6} → t_f = {rr['t_f']/3600:.4f} h"
          f"（稳定性数 {stab_num(NN, DTT):.3f}）")

_R_CLIP = run_case("q4", clip_lo=C_SAFE)
print(f"      clip=0.15 → t_f = {_R_CLIP['t_f']/3600:.4f} h")


# ============================================================
# 表格汇总：tables_Q4.xlsx
# ============================================================
def _tf_h(tmp_tf):
    return tmp_tf / 3600.0


def _interp_phys(mat_cm, C_row, R_cm, r_star):
    """把材料坐标解插值到固定物理半径 r_star；超出当前表面返回 None。"""
    if r_star > R_cm + 1e-12:
        return None
    return float(np.interp(r_star, mat_cm / R0_CM * R_cm, C_row))


_tbl_rows = [6, 12, 18, 24, 30, 36, 42]
_tbl_t = [t * 3600 for t in _tbl_rows] + [TF_Q4]
_tbl_C = [C4[int(np.argmin(np.abs(T4 - t)))] for t in _tbl_t[:-1]] + [RES_Q4["C_tf"]]

# --- 表6（材料坐标版，推荐用于正文） ---
_col_mat = [0, 5, 10, 15, 20]
_lbl_mat = [f"{XI_NODES[j]*R0_CM:.1f}" for j in _col_mat[:-1]] + ["药材表面"]
_rows_mat = []
for th, Cv, tv in zip(_tbl_rows + [round(TF_Q4 / 3600, 2)], _tbl_C, _tbl_t):
    _rows_mat.append([th] + [round(float(Cv[j]), 4) for j in _col_mat]
                     + [round(R_of(tv) * 100, 3)])
df6m = pd.DataFrame(_rows_mat,
                    columns=["时间/h"] + _lbl_mat + ["R(t)/cm（附注）"])

# --- 表6（物理距离版，超出当前表面的格填 "—"） ---
_col_phys = [0.0, 0.5, 1.0, 1.5]
_rows_phys = []
for th, Cv, tv in zip(_tbl_rows + [round(TF_Q4 / 3600, 2)], _tbl_C, _tbl_t):
    R_cm = R_of(tv) * 100
    vals = []
    for r in _col_phys:
        v = _interp_phys(MAT_CM, Cv, R_cm, r)
        vals.append("—" if v is None else round(v, 4))
    vals.append(round(float(Cv[-1]), 4))
    _rows_phys.append([th] + vals + [round(R_cm, 3)])
df6p = pd.DataFrame(_rows_phys,
                    columns=["时间/h"] + [f"{r:.1f}" for r in _col_phys]
                    + ["药材表面", "R(t)/cm（附注）"])

# --- t_f 对比表（归因） ---
df_tf = pd.DataFrame([
    ["问题三（附录3 + 固定几何）", round(_tf_h(TF_Q3), 4), None, None,
     round(_tf_h(TS_Q3), 4), "基准（result3.xlsx）"],
    ["附录4 + 固定几何", round(_tf_h(TF_FIX), 4),
     round(_tf_h(TF_FIX - TF_Q3), 4),
     round((TF_FIX - TF_Q3) / TF_Q3 * 100, 2),
     round(_tf_h(TS_FIX), 4), "仅换物性（附录3→附录4），隔离收缩效应"],
    ["附录4 + 收缩 R(t)（问题四）", round(_tf_h(TF_Q4), 4),
     round(_tf_h(TF_Q4 - TF_Q3), 4),
     round((TF_Q4 - TF_Q3) / TF_Q3 * 100, 2),
     round(_tf_h(TS_Q4), 4), "物性 + 几何收缩，净效应"],
], columns=["模型", "t_f/h", "相对问题三 Δt_f/h", "相对变化/%",
            "表面达标 t_s/h", "说明"])

# --- 网格收敛表 ---
_CONV_NOTE = {
    "基准": "生产配置（result4.xlsx 即此配置）",
    "加密时间步": "仅 Δt 减半，稳定性数随之减半",
    "加密网格（Δt 同步 ×1/4）": "Δξ 减半须 Δt ×1/4 才保持稳定",
    "粗化": "粗网格偏差 −1.4%，说明 20×0.5 已足够细",
}
df_conv = pd.DataFrame([
    [tag, NN, DTT, round(stab_num(NN, DTT), 4), round(_tf_h(tf), 4),
     "—" if tag == "基准" else round((tf - TF_Q4) / TF_Q4 * 100, 3),
     _CONV_NOTE[tag]]
    for tag, NN, DTT, tf in _CONV
], columns=["算例", "N（ξ 网格）", "Δt/s",
            "显式稳定性数 4αΔt/(R·Δξ)²", "t_f/h", "相对基准偏差/%", "备注"])

# --- 双算例表（物性下界） ---
df_clip = pd.DataFrame([
    ["自由外推（当前口径）", dm.C_CLIP_LO, round(_tf_h(TF_Q4), 4),
     round(_tf_h(TS_Q4), 4), round(RES_Q4["rel"], 4),
     "物性下界仅防除零，晚期 D 可外推到更低浓度"],
    ["夹紧到有效区间下限", C_SAFE, round(_tf_h(_R_CLIP["t_f"]), 4),
     round(_tf_h(_R_CLIP["t_s"]), 4), round(_R_CLIP["rel"], 4),
     "C < 0.15 时以 0.15 代入物性，干壳不再“过度封闭”"],
], columns=["算例", "物性下界 C_prop", "t_f/h", "t_s/h", "守恒残差/%", "说明"])

_xlsx = os.path.join(BASE_DIR, "tables_Q4.xlsx")
with pd.ExcelWriter(_xlsx, engine="openpyxl") as wr:
    df6m.to_excel(wr, sheet_name="表6-材料坐标", index=False)
    df6p.to_excel(wr, sheet_name="表6-物理距离", index=False)
    df_tf.to_excel(wr, sheet_name="tf对比", index=False)
    df_conv.to_excel(wr, sheet_name="网格收敛", index=False)
    df_clip.to_excel(wr, sheet_name="双算例", index=False)

print()
print("=" * 60)
print("表6（材料坐标版）")
print("=" * 60)
print(df6m.to_string(index=False))
print()
print("表6（物理距离版，超出当前表面填 —）")
print(df6p.to_string(index=False))
print()
print("t_f 对比表")
print(df_tf.to_string(index=False))
print()
print("网格收敛表")
print(df_conv.to_string(index=False))
print()
print("双算例表")
print(df_clip.to_string(index=False))
print()
print("=" * 60)
print(f"全部图表已保存至 {BASE_DIR}")
print(f"  fig41–fig46.pdf + tables_Q4.xlsx")
print("=" * 60)
