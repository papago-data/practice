"""
问题四 灵敏度分析一：物性有效下界 C_prop（论文规格产出）

模板依据：《问题四灵敏度分析一写作模板》§8.1–8.4
    - 求解器：solve_problem4.run_case(mode="q4", clip_lo=C_prop)   ← 单一变量
    - 判据阈值 C_SAFE = 0.15 **不动**（判据阈值与物性下界解耦，见 solve_problem3.py 模块说明）
    - 8 档：0.105 / 0.120 / 0.135 / 0.150(基准) / 0.165 / 0.180 / 0.195 / 自由外推
    - 其余参数（N=20、Δt=0.5 s、两阶段分界 2 h、h、h_m）一律不动

产出（均写入桌面）：
    sweep_results.csv            8 行汇总（模板 §8.1 字段）
    sweep_C0_series/*.csv        每个 run 的中心 C(0,t) 序列
    sensitivity_Q4.xlsx          表 X（主口径）+ 对照生产基准
    figA_D_C.pdf                 图A D–C 低 C 段放大 + 7 档夹紧位置 + 自由外推分支
    figB_tf_Cprop.pdf            图B t_f–C_prop 响应折线（8 点）+ Q3 参考线 + 反转区
    figC_C0t.pdf                 图C 中心 C(0,t) 基准 vs 自由外推

用法：python sensitivity_q4.py
"""

import csv
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import dry_model as dm
from solve_problem4 import run_case

# ============================================================
# 绘图风格（与问题1–4 图表一致）
# ============================================================
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

BASE = dm.BASE_DIR
DPI = 300

C_REF = 0.15                     # 基准（也是判据阈值，但两者在代码里是解耦的量）
T_DRY_C = dm.T_INF_C             # 恒温段环境温度，用于图A 的 D–C 曲线
T_DRY_K = T_DRY_C + 273.15

# 档位：(标签, C_prop, 相对基准, 配色)
LEVELS = [
    ("−30%", 0.105, -0.30, "#08306B"),
    ("−20%", 0.120, -0.20, "#2171B5"),
    ("−10%", 0.135, -0.10, "#6BAED6"),
    ("基准 0%", 0.150, 0.00, "#111111"),
    ("+10%", 0.165, +0.10, "#FDAE6B"),
    ("+20%", 0.180, +0.20, "#E6550D"),
    ("+30%", 0.195, +0.30, "#A63603"),
]
EXTREME = ("外推(−100%)", 1e-14, -1.00, "#7B3294")

C_THR = "#d62728"
C_Q3 = "#2ca02c"


def D4(C, T_K=T_DRY_K):
    """附录4 扩散系数（不夹紧，自由外推口径）。"""
    C = np.asarray(C, dtype=float)
    return 4.2e-4 * np.exp(-0.30 / np.maximum(C, 1e-300)) \
        * np.exp(-3850.0 / np.clip(T_K, 250.0, 400.0))


# ============================================================
# 1. 跑 8 个算例
# ============================================================
print("=" * 74)
print("问题四 灵敏度分析一：物性有效下界 C_prop")
print("=" * 74)

Q3_TF = None
try:
    _p3 = dm.locate("result3.xlsx")
    _df3 = pd.read_excel(_p3, sheet_name=0, index_col=0)
    _t3 = _df3.index.values.astype(float)
    _c3 = _df3.values[:, 0]
    _b = np.where(_c3 <= dm.C_SAFE)[0]
    if _b.size:
        _i = int(_b[0])
        _fr = ((_c3[_i - 1] - dm.C_SAFE) / (_c3[_i - 1] - _c3[_i])
               if _i > 0 and _c3[_i - 1] != _c3[_i] else 0.0)
        Q3_TF = float(_t3[_i - 1] + (_t3[_i] - _t3[_i - 1]) * _fr)
    print(f"[Q3 参照] result3.xlsx：t_f = {Q3_TF/3600:.4f} h")
except Exception as exc:                                     # noqa: BLE001
    print(f"[Q3 参照] 未读到 result3.xlsx（{exc}）")

RUNS = [("run1", "基准 0%", C_REF, 0.00, "#111111"),
        ("run2", "−10%", 0.135, -0.10, "#6BAED6"),
        ("run3", "−20%", 0.120, -0.20, "#2171B5"),
        ("run4", "−30%", 0.105, -0.30, "#08306B"),
        ("run5", "+10%", 0.165, +0.10, "#FDAE6B"),
        ("run6", "+20%", 0.180, +0.20, "#E6550D"),
        ("run7", "+30%", 0.195, +0.30, "#A63603"),
        ("run8", "外推(−100%)", 1e-14, -1.00, "#7B3294")]

print()
print("-" * 74)
print(f"{'run':<6}{'档位':<14}{'C_prop':>10}{'t_f/h':>11}{'t_s/h':>10}"
      f"{'Δt/h':>9}{'残差/%':>10}")
print("-" * 74)

RECORDS = []
for rid, lab, cprop, drel, col in RUNS:
    res = run_case("q4", clip_lo=cprop)
    t_f, t_s, rel = res["t_f"], res["t_s"], res["rel"]
    lag = (t_f - t_s) / 3600.0
    # 中心 C(0,t) 序列
    times = res["times"]
    c0 = res["C"][:, 0]
    RECORDS.append({
        "run_id": rid, "C_prop_label": lab,
        "C_prop_value": cprop, "rel_perturb": drel,
        "t_f_s": t_f, "t_f_h": t_f / 3600.0,
        "t_s_s": t_s, "t_s_h": t_s / 3600.0,
        "lag_h": lag, "dmass_pct": rel,
        "rel": res, "color": col,
        "times":times,
        "C0":c0,
    })
    print(f"{rid:<6}{lab:<14}{cprop:>10.4f}{t_f/3600:>11.4f}{t_s/3600:>10.4f}"
          f"{lag:>9.4f}{rel:>10.4f}")

print("-" * 74)

# 收尾自检（模板 §8.4）
assert all(np.isfinite(r["t_f_s"]) and r["t_f_s"] > 0 for r in RECORDS), "存在无效 t_f"
assert all(np.isfinite(r["rel"]["C"]).all() for r in RECORDS), "浓度出现 NaN/Inf"
assert all((r["rel"]["C"] >= 0).all() for r in RECORDS), "出现负浓度"
assert all(abs(r["dmass_pct"]) < 0.1 for r in RECORDS), "守恒残差超限"
_ord = sorted([r for r in RECORDS if r["C_prop_value"] > 1e-3],
              key=lambda z: z["C_prop_value"])
_tf_seq = [r["t_f_h"] for r in _ord]
_mono = all(_tf_seq[i] >= _tf_seq[i + 1] - 1e-9 for i in range(len(_tf_seq) - 1))
print(f"[自检] t_f 随 C_prop 上调单调不增：{'通过' if _mono else '★不通过，需查事件检测'}")

TF_REF = [r for r in RECORDS if abs(r["C_prop_value"] - C_REF) < 1e-12][0]["t_f_h"]
TF_EXT = [r for r in RECORDS if r["C_prop_value"] == 1e-14][0]["t_f_h"]
TS_REF = [r for r in RECORDS if abs(r["C_prop_value"] - C_REF) < 1e-12][0]["t_s_h"]
# ============================================================
# 2. 图A：中心 C(0,t) 基准 vs 自由外推
# ============================================================
print("[图A] 中心浓度对比 ……")
fig, ax = plt.subplots(figsize=(12.5, 7.0))
for rid, lab, cp, drel, col in [("run1", "基准 0%", C_REF, 0.0, "#111111"),
                                ("run8", "外推(−100%)", 1e-14, -1.0, "#7B3294")]:
    r = [z for z in RECORDS if z["run_id"] == rid][0]
    th = r["rel"]["times"] / 3600.0
    ax.plot(th, r["rel"]["C"][:, 0], color=col, lw=2.8,
            label=f"$C_\\mathrm{{prop}}$ = {cp:.3f}（$t_f$ = {r['t_f_h']:.4f} h）"
                  if cp > 1e-3
                  else f"自由外推（$t_f$ = {r['t_f_h']:.4f} h）")
ax.axhline(dm.C_SAFE, color=C_THR, ls="--", lw=1.8,
           label=f"安全阈值 {dm.C_SAFE} kg/kg")
for rid, col, tag in [("run1", "#111111", "基准"), ("run8", "#7B3294", "自由外推")]:
    r = [z for z in RECORDS if z["run_id"] == rid][0]
    ax.axvline(r["t_f_h"], color=col, ls="-.", lw=1.6)
    ax.scatter([r["t_f_h"]], [dm.C_SAFE], color=col, s=110, zorder=6,
               edgecolors="white", linewidths=1.5)
    ax.annotate(f"{tag} $t_f$ = {r['t_f_h']:.2f} h",
                xy=(r["t_f_h"], 2.35), xytext=(r["t_f_h"] - 0.9, 2.35),
                ha="right", va="center", fontsize=11, color=col, zorder=7,
                arrowprops=dict(arrowstyle="->", color=col, lw=1.4))

# 尾段拖长：两条 t_f 竖线之间的水平双箭头
ax.annotate("", xy=(TF_EXT, 0.031), xytext=(TF_REF, 0.031),
            arrowprops=dict(arrowstyle="<->", color="#7B3294", lw=2.0),
            zorder=7)
ax.text((TF_REF + TF_EXT) / 2, 0.0335,
        f"尾段拖长 {TF_EXT - TF_REF:.4f} h\n（干壳更绝 → 中心脱水变慢）",
        ha="center", va="bottom", fontsize=11.5, color="#7B3294",
        fontweight="bold", zorder=7,
        bbox=dict(boxstyle="round,pad=0.4", fc="#F7F0FB", ec="#7B3294",
                  alpha=0.95))
ax.set_xlabel("时间 t (h)")
ax.set_ylabel(r"中心水分浓度 $C(0,t)$ (kg/kg)")
ax.set_yscale("log")
ax.set_xlim(0, TF_EXT * 1.06)
ax.set_ylim(1.2e-2, 3.6)
_yt = [0.02, 0.05, 0.1, 0.15, 0.3, 0.6, 1.2, 2.4]
ax.set_yticks(_yt)
ax.set_yticklabels([f"{v:g}" for v in _yt])
ax.minorticks_off()
ax.legend(loc="lower left", frameon=False, fontsize=11)
ax.set_title("图A  中心浓度的基准/自由外推对比（其余参数与基准一致）",
             fontsize=15, fontweight="bold")
plt.tight_layout()
plt.savefig(os.path.join(BASE, "figA.pdf"), dpi=DPI,
            bbox_inches="tight", facecolor="white")
plt.close()
print("      figA.pdf 已保存")

# ============================================================
# 3. 结论所需的关键量
# ============================================================
mx = max(abs(r["t_f_h"] - TF_REF) / TF_REF * 100 for r in RECORDS)
mx30 = max(abs(r["t_f_h"] - TF_REF) / TF_REF * 100 for r in RECORDS
           if r["rel_perturb"] != -1.00)
down = max((r["t_f_h"] - TF_REF) / TF_REF * 100 for r in RECORDS
           if 0 > r["rel_perturb"] > -1.0)
up = max(abs((r["t_f_h"] - TF_REF) / TF_REF * 100) for r in RECORDS
         if r["rel_perturb"] > 0)
print()
print("=" * 74)
print("结论所需关键量")
print("=" * 74)
print(f"基准 0.150            t_f = {TF_REF:.4f} h，t_s = {TS_REF:.4f} h")
print(f"±30% 内最大变化率      {mx30:.2f}%（−30% 档）")
print(f"含极端档最大变化率     {mx:.2f}%（自由外推）")
print(f"下探方向最大变化率     {down:.2f}%   上浮方向最大变化率 {up:.2f}%"
      f"   不对称比 {down/up:.2f}")
print(f"自由外推(−100%)        t_f = {TF_EXT:.4f} h，变化 {(TF_EXT-TF_REF)/TF_REF*100:+.2f}%")
if Q3_TF:
    print(f"Q3 参照                t_f = {Q3_TF/3600:.4f} h")
    print(f"基准口径 Q4−Q3         {(TF_REF-Q3_TF/3600):+.4f} h "
          f"({(TF_REF-Q3_TF/3600)/(Q3_TF/3600)*100:+.2f}%)")
    print(f"外推口径 Q4−Q3         {(TF_EXT-Q3_TF/3600):+.4f} h "
          f"({(TF_EXT-Q3_TF/3600)/(Q3_TF/3600)*100:+.2f}%)")
    print(f"结论方向："
          f"{'版本 B（反转）' if TF_EXT > Q3_TF/3600 else '版本 A（不反转）'}")
print(f"t_s 各档极差           "
      f"{max(r['t_s_h'] for r in RECORDS)-min(r['t_s_h'] for r in RECORDS):.4f} h")
print(f"时滞 Δt 极差           "
      f"{max(r['lag_h'] for r in RECORDS)-min(r['lag_h'] for r in RECORDS):.4f} h")
print("=" * 74)
print(f"产出：{BASE}")
print("  sweep_results.csv / sensitivity_Q4.xlsx / figA–figC.pdf / sweep_C0_series/")
print("=" * 74)