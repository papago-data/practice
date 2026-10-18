"""
问题 2 图表生成：整个烘干过程（预热平衡 + 恒温干燥）的温度与水分浓度演化。

输入：result1.xlsx / result2.xlsx（由 solve_problem*.py 生成）+ 附件1.xlsx
输出：fig21.pdf 变物性曲线        fig22.pdf 温度场时空演化
      fig23.pdf 水分场时空演化    fig24.pdf 中心/表面时程曲线
      fig25.pdf 阶段切换图        fig26.pdf Q1 vs Q2 对比
      Q1_vs_Q2_t1800.xlsx
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
    "font.size": 12,
    "axes.titlesize": 14,
    "axes.labelsize": 13,
    "lines.linewidth": 2.0,
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

# 附录3 变物性（直接引用公共模块，避免重复定义）
rho_func, cp_func, k_func, D_func = dm.rho3, dm.cp3, dm.k3, dm.D3
rho_q1, cp_q1, k_q1 = dm.RHO1, dm.CP1, dm.K1


# ============================================================
# 数据读取
# ============================================================
def load_result(path_name, expect="温度"):
    """读取结果工作簿，返回 (时间索引, 距离列, 温度矩阵, 水分矩阵)。"""
    path = dm.locate(path_name)
    sheets = pd.read_excel(path, sheet_name=None, index_col=0)
    temp = conc = None
    for name, df in sheets.items():
        df.index = df.index.astype(float)
        df.columns = df.columns.astype(float)
        if "温度" in name:
            temp = df
        elif "水分" in name:
            conc = df
    if temp is None:
        raise KeyError(f"{path_name} 中未找到温度工作表")
    return (temp.index.values, temp.columns.values.astype(float),
            temp.values, None if conc is None else conc.values)


t1, r1, T1, C1 = load_result("result1.xlsx")
t2, r2, T2, C2 = load_result("result2.xlsx")
Ta_f, Ca_f, _ = dm.make_env()
print(f"读取 result1.xlsx: {T1.shape}   result2.xlsx: {T2.shape}")


# ============================================================
# 图1：变物性参数曲线
# ============================================================
def plot_fig1():
    C_arr = np.linspace(0.05, 3.0, 300)
    fig, axes = plt.subplots(2, 2, figsize=(13, 10))

    panels = [
        (rho_func, r"(a) 密度 $\rho(C)$", r"$\rho$ (kg/m$^3$)", "#1f77b4"),
        (cp_func, r"(b) 比热容 $c_p(C)$", r"$c_p$ (J/(kg·K))", "#ff7f0e"),
        (k_func, r"(c) 导热系数 $k(C)$", r"$k$ (W/(m·K))", "#2ca02c"),
    ]
    for ax, (fn, title, ylab, col) in zip(axes.ravel(), panels):
        ax.plot(C_arr, fn(C_arr), color=col, linewidth=2.5)
        y0 = fn(np.array([dm.C0]))[0]
        ax.scatter([dm.C0], [y0], color="#d62728", s=80, zorder=5)
        ax.annotate(f"$C_0$={dm.C0}\n{y0:.3g}", (dm.C0, y0),
                    textcoords="offset points", xytext=(-60, 15), fontsize=10)
        ax.set_xlabel("水分浓度 C (kg/kg)")
        ax.set_ylabel(ylab)
        ax.set_title(title, fontweight="bold")

    ax = axes[1, 1]
    for T_K, lbl, col in [(301.15, "28 °C", "#1f77b4"), (323.15, "50 °C", "#d62728")]:
        Dv = D_func(C_arr, T_K)
        ax.plot(C_arr, Dv, color=col, linewidth=2.5, label=f"T = {lbl}")
        d0 = D_func(np.array([dm.C0]), T_K)[0]
        ax.scatter([dm.C0], [d0], color=col, s=80, zorder=5)
    ax.set_xlabel("水分浓度 C (kg/kg)")
    ax.set_ylabel(r"$D$ (m$^2$/s)")
    ax.set_title(r"(d) 扩散系数 $D(C,T)$", fontweight="bold")
    ax.legend(frameon=False)
    ax.ticklabel_format(style="sci", axis="y", scilimits=(-9, -9))

    fig.suptitle("图1  变物性参数随水分浓度变化曲线（附录3）",
                 fontsize=15, fontweight="bold", y=0.98)
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig(os.path.join(BASE_DIR, "fig21.pdf"), dpi=DPI,
                bbox_inches="tight", facecolor="white")
    plt.close()
    print("  fig21.pdf 已保存")


# ============================================================
# 时空演化热力图（温度 / 水分浓度）
# ============================================================
def plot_field(t, r, data, cmap, cbar_label, title, fname, env_fn, env_label, env_color):
    fig, ax = plt.subplots(figsize=(13, 6))
    im = ax.pcolormesh(t / 3600, r, data.T, cmap=cmap, shading="auto")
    fig.colorbar(im, ax=ax, pad=0.02).set_label(cbar_label)

    if env_fn is not None:
        tf = np.linspace(t[0], t[-1], 500)
        env = np.array([env_fn(x) for x in tf])
        ax2 = ax.twinx()
        ax2.plot(tf / 3600, env, color=env_color, linewidth=2,
                 linestyle="--", label=env_label)
        ax2.set_ylabel(env_label, color=env_color)
        ax2.tick_params(axis="y", labelcolor=env_color)
        ax2.spines["right"].set_visible(True)
        ax2.legend(loc="upper left", frameon=False)

    ax.set_xlabel("时间 t (h)")
    ax.set_ylabel("到中心距离 r (cm)")
    ax.set_title(title, fontsize=15, fontweight="bold")
    plt.tight_layout()
    plt.savefig(os.path.join(BASE_DIR, fname), dpi=DPI,
                bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"  {fname} 已保存")


# ============================================================
# 图4：中心与表面时程曲线
# ============================================================
def plot_fig4():
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    t_h = t2 / 3600
    t_env = np.array([Ta_f(x) for x in t2])
    c_env = np.array([Ca_f(x) for x in t2])
    tc_h = dm.T_SWITCH / 3600

    axes[0, 0].plot(t_h, T2[:, 0], color="#1f77b4", linewidth=2.5)
    axes[0, 0].set_title("(a) 中心温度 T(0, t)", fontweight="bold")
    axes[0, 0].set_ylabel("温度 T (°C)")

    axes[0, 1].plot(t_h, T2[:, -1], color="#d62728", linewidth=2.5, label="表面温度")
    axes[0, 1].plot(t_h, t_env, color="gray", linewidth=1.5, linestyle="--",
                    label="烘房温度 $T_a(t)$")
    axes[0, 1].set_title("(b) 表面温度 T(R, t)", fontweight="bold")
    axes[0, 1].set_ylabel("温度 T (°C)")
    axes[0, 1].legend(frameon=False, loc="lower right")

    axes[1, 0].plot(t_h, C2[:, 0], color="#1f77b4", linewidth=2.5)
    axes[1, 0].set_title("(c) 中心水分 C(0, t)", fontweight="bold")
    axes[1, 0].set_xlabel("时间 t (h)")
    axes[1, 0].set_ylabel("水分浓度 C (kg/kg)")

    axes[1, 1].plot(t_h, C2[:, -1], color="#d62728", linewidth=2.5, label="表面水分")
    axes[1, 1].plot(t_h, c_env, color="gray", linewidth=1.5, linestyle="--",
                    label="烘房水分 $C_a(t)$")
    axes[1, 1].set_title("(d) 表面水分 C(R, t)", fontweight="bold")
    axes[1, 1].set_xlabel("时间 t (h)")
    axes[1, 1].set_ylabel("水分浓度 C (kg/kg)")
    axes[1, 1].legend(frameon=False, loc="upper right")

    for ax in axes.ravel():
        ax.axvline(tc_h, color="#2ca02c", linestyle="-.", linewidth=1.5, alpha=0.8)
    axes[0, 0].text(tc_h + 0.05, axes[0, 0].get_ylim()[0], f"$t_c$={tc_h:.1f} h",
                    color="#2ca02c", fontsize=9, va="bottom")

    fig.suptitle("图4  中心与表面的温度、水分浓度时程曲线",
                 fontsize=15, fontweight="bold", y=0.98)
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig(os.path.join(BASE_DIR, "fig24.pdf"), dpi=DPI,
                bbox_inches="tight", facecolor="white")
    plt.close()
    print("  fig24.pdf 已保存")


# ============================================================
# 图5：预热平衡 → 恒温干燥 的阶段切换
#     图(a) 给环境温度的阶段划分依据（偏离量衰减到阈值）
#     图(b) 给温度场与水分场的响应——升温速率与干燥速率同步衰减，
#           说明两个阶段由同一物理机制控制
# ============================================================
def smooth_series(x, window=181):
    """
    滑动平均平滑。

    逐秒采样序列（步长 1 s）直接求导会得到密集的阶梯，
    在对数轴上表现为粗色块；用约 3 min 的窗口平滑后再绘图，
    保留趋势、消除采样噪声。
    """
    w = max(3, int(window) | 1)          # 保证为奇数
    kernel = np.ones(w) / w
    y = np.convolve(x, kernel, mode="same")
    h = w // 2
    y[:h] = x[:h].mean()                 # 端点用邻域均值回填，避免尾部塌陷
    y[-h:] = x[-h:].mean()
    return y


def plot_fig25():
    t_air, T_air, _ = dm.load_attachment1()
    tc_h = dm.T_SWITCH / 3600
    t_h_all = t2 / 3600

    fig, axes = plt.subplots(1, 2, figsize=(14, 5.8))

    # (a) 环境温度：实测段 + 一阶惯性外推 + 渐近值，标出切换时刻
    tc_t = np.linspace(t_air[-1], 3 * 3600, 300)
    T_ext = dm.T_INF_C + (T_air[-1] - dm.T_INF_C) * np.exp(-(tc_t - t_air[-1]) / dm.TAU_T)
    axes[0].plot(t_air / 3600, T_air, color="#2b6cb0", linewidth=2.5, label="实测环境温度")
    axes[0].plot(tc_t / 3600, T_ext, color="#2b6cb0", linewidth=1.6,
                 linestyle=":", label="一阶惯性外推")
    axes[0].axhline(dm.T_INF_C, color="#c53030", linestyle="--", linewidth=1.8,
                    label=f"$T_\\infty$ = {dm.T_INF_C:.3f} °C")
    axes[0].axvspan(dm.T_SWITCH_BAND[0] / 3600, dm.T_SWITCH_BAND[1] / 3600,
                    color="#2ca02c", alpha=0.15, label="切换不确定带")
    axes[0].axvline(tc_h, color="#2ca02c", linestyle="-.", linewidth=2,
                    label=f"切换 $t_c$ = {tc_h:.1f} h")
    axes[0].set_xlabel("时间 t (h)")
    axes[0].set_ylabel("温度 T (°C)")
    axes[0].set_title("(a) 环境温度趋于定常（阶段划分依据）", fontweight="bold")
    axes[0].legend(frameon=False, fontsize=9, loc="lower right")
    axes[0].set_xlim(0, 3)
    axes[0].set_ylim(T_air.min() - 1.0, T_air.max() + 1.5)

    # (b) 升温速率与干燥速率：同取每小时变化量，平滑后对比衰减过程
    dT_center = smooth_series(np.abs(np.gradient(T2[:, 0], t2) * 3600))
    dC_surf = smooth_series(np.abs(np.gradient(C2[:, -1], t2) * 3600))
    dC_center = smooth_series(np.abs(np.gradient(C2[:, 0], t2) * 3600))

    axes[1].plot(t_h_all, dT_center, color="#1f77b4", linewidth=2.2,
                 label="中心升温速率 $|\\mathrm{d}T/\\mathrm{d}t|$ (°C/h)")
    axes[1].plot(t_h_all, dC_surf, color="#d62728", linewidth=2.2,
                 label="表面干燥速率 $|\\mathrm{d}C/\\mathrm{d}t|$ (kg/kg/h)")
    axes[1].plot(t_h_all, dC_center, color="#2ca02c", linewidth=2.2,
                 label="中心干燥速率 $|\\mathrm{d}C/\\mathrm{d}t|$ (kg/kg/h)")
    axes[1].axvline(tc_h, color="#805ad5", linestyle="-.", linewidth=2,
                    label=f"切换 $t_c$ = {tc_h:.1f} h")
    axes[1].axvspan(dm.T_SWITCH_BAND[0] / 3600, dm.T_SWITCH_BAND[1] / 3600,
                    color="#805ad5", alpha=0.15, label="切换不确定带")
    axes[1].set_xlabel("时间 t (h)")
    axes[1].set_ylabel("变化率 (每小时，两种量纲)")
    axes[1].set_title("(b) 升温速率与干燥速率同步衰减", fontweight="bold")
    axes[1].legend(frameon=False, fontsize=8.5, loc="lower left", ncol=1)
    axes[1].set_xlim(0, 3)
    axes[1].set_yscale("log")
    axes[1].set_ylim(0.01, 300.0)
    axes[1].grid(True, alpha=0.3, which="major")
    # 标注恒速干燥段：表面干燥速率在 0.5~3 h 保持量级不变
    i_a, i_b = int(0.55 * 3600), int(2.95 * 3600)
    rate_mean = dC_surf[i_a:i_b].mean()
    axes[1].annotate("恒速干燥段\n表面速率基本恒定",
                     xy=(1.45, rate_mean), xytext=(0.95, 18.0),
                     fontsize=9, color="#c53030", ha="center",
                     arrowprops=dict(arrowstyle="->", color="#c53030", lw=1.5,
                                     connectionstyle="arc3,rad=0.25"))

    fig.suptitle("图5  预热平衡阶段与恒温干燥阶段的切换",
                 fontsize=14, fontweight="bold", y=1.01)
    plt.tight_layout()
    plt.savefig(os.path.join(BASE_DIR, "fig25.pdf"), dpi=DPI,
                bbox_inches="tight", facecolor="white")
    plt.close()
    print("  fig25.pdf 已保存")


# ============================================================
# 图6：Q1（常物性） vs Q2（变物性）对比
# ============================================================
def plot_fig6():
    t_snap = 1800.0
    i1 = int(np.argmin(np.abs(t1 - t_snap)))
    i2 = int(np.argmin(np.abs(t2 - t_snap)))

    T_q1, T_q2 = T1[i1], T2[i2]
    C_q1, C_q2 = C1[i1], C2[i2]
    dT, dC = T_q2 - T_q1, C_q2 - C_q1

    print(f"\n  t = {int(t_snap)} s 关键距离点对比 (Q2 - Q1)：")
    print("  " + "-" * 76)
    print(f"  {'r/cm':<8}{'T_Q1':>10}{'T_Q2':>10}{'ΔT':>10}"
          f"{'C_Q1':>10}{'C_Q2':>10}{'ΔC':>10}")
    for d in [0.0, 0.5, 1.0, 1.5, 2.0]:
        i = int(np.argmin(np.abs(r2 - d)))
        print(f"  {r2[i]:<8.1f}{T_q1[i]:>10.4f}{T_q2[i]:>10.4f}{dT[i]:>+10.4f}"
              f"{C_q1[i]:>10.4f}{C_q2[i]:>10.4f}{dC[i]:>+10.4f}")

    pd.DataFrame({
        "距离/cm": r2, "T_Q1": T_q1, "T_Q2": T_q2, "ΔT": dT,
        "C_Q1": C_q1, "C_Q2": C_q2, "ΔC": dC,
    }).to_excel(os.path.join(BASE_DIR, "Q1_vs_Q2_t1800.xlsx"), index=False)
    print("  Q1_vs_Q2_t1800.xlsx 已保存")

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5))
    ax1.plot(r2, T_q1, "o--", color="#1f77b4", linewidth=2, markersize=7, label="Q1 (常物性)")
    ax1.plot(r2, T_q2, "s-", color="#d62728", linewidth=2.5, markersize=7, label="Q2 (变物性)")
    ax1.set_xlabel("到中心距离 r (cm)")
    ax1.set_ylabel("温度 T (°C)")
    ax1.set_title(f"(a) 温度径向分布 (t = {int(t_snap)} s)", fontweight="bold")
    ax1.legend(frameon=False, loc="upper left")

    ax2.plot(r2, C_q1, "o--", color="#1f77b4", linewidth=2, markersize=7, label="Q1 (常物性)")
    ax2.plot(r2, C_q2, "s-", color="#d62728", linewidth=2.5, markersize=7, label="Q2 (变物性)")
    ax2.set_xlabel("到中心距离 r (cm)")
    ax2.set_ylabel("水分浓度 C (kg/kg)")
    ax2.set_title(f"(b) 水分浓度径向分布 (t = {int(t_snap)} s)", fontweight="bold")
    ax2.legend(frameon=False, loc="upper right")

    ax1.text(0.95, 0.05, f"最大 ΔT = {np.min(dT):.2f} °C",
             transform=ax1.transAxes, ha="right", va="bottom", fontsize=10,
             color="#d62728",
             bbox=dict(boxstyle="round,pad=0.3", fc="#FFF0F0", ec="#d62728", alpha=0.9))
    ax2.text(0.05, 0.10, f"最大 ΔC = {np.min(dC):.4f}",
             transform=ax2.transAxes, ha="left", va="bottom", fontsize=10,
             color="#d62728",
             bbox=dict(boxstyle="round,pad=0.3", fc="#FFF0F0", ec="#d62728", alpha=0.9))

    fig.suptitle(f"图6  Q1(常物性) 与 Q2(变物性) 对比（t = {int(t_snap)} s）",
                 fontsize=15, fontweight="bold", y=1.02)
    plt.tight_layout()
    plt.savefig(os.path.join(BASE_DIR, "fig26.pdf"), dpi=DPI,
                bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"  fig26.pdf 已保存 (ΔT_max = {np.min(dT):.4f}, ΔC_max = {np.min(dC):.4f})")


# ============================================================
# 主流程
# ============================================================
def main():
    print("=" * 60)
    print("问题2 图表生成")
    print("=" * 60)

    plot_fig1()
    plot_field(t2, r2, T2, "jet", "温度 T (°C)",
               "图2  温度场时空演化（3 h 全过程）", "fig22.pdf",
               Ta_f, "烘房温度 $T_a$ (°C)", "red")
    plot_field(t2, r2, C2, "YlGnBu", "水分浓度 C (kg/kg)",
               "图3  水分浓度场时空演化（3 h 全过程）", "fig23.pdf",
               Ca_f, "烘房水分 $C_a$ (kg/kg)", "darkblue")
    plot_fig4()
    plot_fig25()
    plot_fig6()

    print(f"\n[完成] 所有图表已保存至 {BASE_DIR}")
    for f in ["fig21.pdf", "fig22.pdf", "fig23.pdf", "fig24.pdf",
              "fig25.pdf", "fig26.pdf", "Q1_vs_Q2_t1800.xlsx"]:
        p = os.path.join(BASE_DIR, f)
        if os.path.exists(p):
            print(f"  {f}  ({os.path.getsize(p) // 1024} KB)")


if __name__ == "__main__":
    main()
