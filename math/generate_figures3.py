"""
问题 3 图表生成：烘干过程的水分浓度演化与烘干完成时间确定。

输入：result3.xlsx（由 solve_problem3.py 生成）
输出：fig31.pdf 中心水分浓度与烘干完成时间
      fig32.pdf 各层水分浓度演化 + 安全阈值
      fig33.pdf 水分场时空演化热力图
"""

import os

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import dry_model as dm

# ---------- 绘图风格 ----------
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

# ============================================================
# 读取结果
# ============================================================
path = dm.locate("result3.xlsx")
df = pd.read_excel(path, sheet_name=0, index_col=0)
df.index = df.index.astype(float)
df.columns = df.columns.astype(float)

t = df.index.values
dist = df.columns.values.astype(float)
C_all = df.values
C_center = C_all[:, 0]

# 烘干完成时刻：中心水分首次降至阈值（末行即越过阈值后的达标状态）
below = np.where(C_center <= C_SAFE)[0]
if below.size == 0:
    raise ValueError("result3.xlsx 中中心水分浓度未降到安全阈值，请先运行 solve_problem3.py")
i_f = below[0]
if i_f == 0:
    t_f, C_f = t[0], C_center[0]
else:
    c0, c1 = C_center[i_f - 1], C_center[i_f]
    frac = (c0 - C_SAFE) / (c0 - c1) if c0 != c1 else 0.0
    t_f = t[i_f - 1] + (t[i_f] - t[i_f - 1]) * frac
    C_f = C_center[i_f]
t_f_h = t_f / 3600

print(f"烘干完成时间 t_f = {t_f_h:.2f} h（≈ {t_f_h/24:.2f} 天）")
print(f"中心水分 C(0, t_f) = {C_center[i_f]:.4f} kg/kg"
      f"（末行时间 {t[-1]/3600:.2f} h，各处最大 C = {C_all[-1].max():.4f}）")


# ============================================================
# 图1：中心水分浓度随时间变化
# ============================================================
fig, ax = plt.subplots(figsize=(12, 7))

ax.plot(t / 3600, C_center, color="#1f77b4", linewidth=2.5,
        label=r"中心水分浓度 $C(0, t)$", zorder=3)
ax.axhline(C_SAFE, color="#d62728", linewidth=1.8, linestyle="--",
           label=f"安全阈值 $C_{{\\rm safe}}$ = {C_SAFE} kg/kg", zorder=2)
ax.axvline(t_f_h, color="#2ca02c", linewidth=1.8, linestyle="-.",
           label=f"烘干完成 $t_f$ = {t_f_h:.2f} h", zorder=2)
ax.scatter([t_f_h], [C_SAFE], color="#d62728", s=120, zorder=5,
           edgecolors="white", linewidths=1.5)

ax.annotate(f"$t_f$ = {t_f_h:.2f} h（≈ {t_f_h/24:.2f} 天）",
            xy=(t_f_h, C_SAFE), xytext=(t_f_h * 0.45, C_SAFE + 0.45),
            fontsize=13, fontweight="bold", color="#d62728",
            arrowprops=dict(arrowstyle="->", color="#d62728", lw=2),
            bbox=dict(boxstyle="round,pad=0.4", fc="#FFF5F5",
                      ec="#d62728", alpha=0.9))

ax.scatter([0], [C_center[0]], color="gray", s=60, zorder=4)
ax.annotate(f"初始 $C_0$ = {C_center[0]:.2f}", (0, C_center[0]),
            textcoords="offset points", xytext=(15, -20),
            fontsize=11, color="gray")

ax.fill_between(t[:i_f + 1] / 3600, C_center[:i_f + 1], C_SAFE,
                alpha=0.08, color="#1f77b4")

ax.set_xlabel("时间 t (h)")
ax.set_ylabel(r"水分浓度 $C$ (kg/kg)")
ax.set_title(r"图1  中心处（$r = 0$）水分浓度随时间变化及烘干完成时间",
             fontsize=16, fontweight="bold")
ax.legend(loc="upper right", frameon=False, fontsize=11)
ax.set_xlim(-1, t_f_h * 1.08)
ax.set_ylim(-0.02, C_center[0] * 1.08)

ax.text(0.03, 0.97,
        f"$t_f$ = {t_f_h:.2f} h ≈ {t_f_h/24:.2f} 天\n"
        f"$C(0, t_f)$ = {C_center[i_f]:.4f} kg/kg\n"
        f"初始 $C_0$ = {C_center[0]:.2f} kg/kg",
        transform=ax.transAxes, fontsize=11, verticalalignment="top",
        bbox=dict(boxstyle="round,pad=0.5", fc="#F7F7F7",
                  ec="#CCCCCC", alpha=0.9))

plt.tight_layout()
plt.savefig(os.path.join(BASE_DIR, "fig31.pdf"), dpi=DPI,
            bbox_inches="tight", facecolor="white")
plt.close()
print("  fig31.pdf 已保存")


# ============================================================
# 图2：不同径向位置的水分浓度演化
# ============================================================
fig, ax = plt.subplots(figsize=(12, 6.5))
picks = [0.0, 0.5, 1.0, 1.5, 2.0]
cmap = plt.get_cmap("viridis")

for k, d in enumerate(picks):
    j = int(np.argmin(np.abs(dist - d)))
    ax.plot(t / 3600, C_all[:, j], color=cmap(k / max(1, len(picks) - 1)),
            linewidth=2.3, label=f"r = {dist[j]:.1f} cm")

ax.axhline(C_SAFE, color="#d62728", linewidth=1.8, linestyle="--",
           label=f"安全阈值 {C_SAFE} kg/kg")
ax.axvline(t_f_h, color="#2ca02c", linewidth=1.8, linestyle="-.",
           label=f"$t_f$ = {t_f_h:.2f} h")

ax.set_xlabel("时间 t (h)")
ax.set_ylabel("水分浓度 C (kg/kg)")
ax.set_title("图2  各径向位置水分浓度演化", fontsize=16, fontweight="bold")
ax.legend(frameon=False, fontsize=10)
ax.set_xlim(0, t_f_h * 1.02)
ax.set_yscale("log")
ax.set_ylim(1e-2, 3)

plt.tight_layout()
plt.savefig(os.path.join(BASE_DIR, "fig32.pdf"), dpi=DPI,
            bbox_inches="tight", facecolor="white")
plt.close()
print("  fig32.pdf 已保存")


# ============================================================
# 图3：水分浓度场时空演化
# ============================================================
fig, ax = plt.subplots(figsize=(13, 6))
im = ax.pcolormesh(t / 3600, dist, C_all.T, cmap="YlGnBu", shading="auto")
fig.colorbar(im, ax=ax, pad=0.02).set_label("水分浓度 C (kg/kg)")

ax.axvline(t_f_h, color="#d62728", linestyle="-", linewidth=2.2,
           label=f"$t_f$ = {t_f_h:.2f} h")
ax.axhline(0.0, color="#2ca02c", linestyle="--", linewidth=1.5,
           label="中心 r = 0")
ax.legend(loc="upper right", frameon=False)

ax.set_xlabel("时间 t (h)")
ax.set_ylabel("到中心距离 r (cm)")
ax.set_title("图3  水分浓度场时空演化（至烘干完成）", fontsize=16, fontweight="bold")

plt.tight_layout()
plt.savefig(os.path.join(BASE_DIR, "fig33.pdf"), dpi=DPI,
            bbox_inches="tight", facecolor="white")
plt.close()
print("  fig33.pdf 已保存")

print("\n" + "=" * 60)
print(f"问题3 图表生成完毕：t_f = {t_f_h:.2f} h")
print("=" * 60)
