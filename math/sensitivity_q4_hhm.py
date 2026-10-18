import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import FuncFormatter

import dry_model as dm
import solve_problem4 as sp4

plt.rcParams.update({
    "font.sans-serif": ["Microsoft YaHei", "SimHei", "DejaVu Sans"],
    "axes.unicode_minus": False,
    "mathtext.fontset": "stix",
    "font.size": 13,
    "axes.titlesize": 15,
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

HM0 = 8e-7
H0 = 25.0
C_PROP = 0.15
R0 = dm.R
D_REF = 2.5e-9
K_REF = 0.20

HM_MULTS = [0.125, 0.25, 0.7, 0.8, 0.9, 1.1, 1.2, 1.3, 4.0]
H_MULTS = [0.5, 0.7, 0.8, 0.9, 1.1, 1.2, 1.3, 2.0]

C_HM = "#1f77b4"
C_H = "#D85A30"
C_REF = "#111111"


def solve_one(param, mult):
    sp4.HM_CONV = HM0
    sp4.H_CONV = H0
    if param == "hm":
        sp4.HM_CONV = HM0 * mult
    elif param == "h":
        sp4.H_CONV = H0 * mult
    return sp4.run_case("q4", clip_lo=C_PROP)


def run_all():
    records = []

    def add(param, mult, res):
        hm_val = HM0 * mult if param == "hm" else HM0
        h_val = H0 * mult if param == "h" else H0
        records.append({
            "param": param, "mult": mult,
            "hm_value": hm_val, "h_value": h_val,
            "t_f_h": res["t_f"] / 3600.0,
            "dmass_pct": res["rel"],
        })

    add("base", 1.0, solve_one("base", 1.0))
    for m in HM_MULTS:
        add("hm", m, solve_one("hm", m))
    for m in H_MULTS:
        add("h", m, solve_one("h", m))

    sp4.HM_CONV, sp4.H_CONV = HM0, H0
    return records


def plot_figA(records):
    tf_ref = [r for r in records if r["param"] == "base"][0]["t_f_h"]

    fig, axes = plt.subplots(1, 2, figsize=(13, 6))
    fig.subplots_adjust(left=0.085, right=0.97, top=0.88, bottom=0.13, wspace=0.28)

    panels = [
        ("hm", C_HM, r"对流传质系数档位 $h_m/h_{m,0}$",
         r"(a) $t_f$ 对 $h_m$ 的响应：下调敏感、上调饱和"),
        ("h", C_H, r"对流换热系数档位 $h/h_0$",
         r"(b) $t_f$ 对 $h$ 的响应：全程近水平（不敏感）"),
    ]

    for ax, (param, col, xlab, title) in zip(axes, panels):
        seq = sorted([r for r in records if r["param"] == param], key=lambda z: z["mult"])
        xs = [r["mult"] for r in seq]
        ys = [r["t_f_h"] for r in seq]

        xmin, xmax = 0.85 * min(xs), 1.15 * max(xs)
        # 分区底纹（裁剪到数据范围内，避免退化）
        if param == "hm":
            b1 = 1.0 * D_REF / (HM0 * R0)
            b2 = 10.0 * D_REF / (HM0 * R0)
        else:
            b1 = 1.0 * K_REF / (H0 * R0)
            b2 = 10.0 * K_REF / (H0 * R0)
        b1 = max(b1, xmin)
        b2 = min(b2, xmax)
        if b1 > xmin:
            ax.axvspan(xmin, b1, color="#F6D9D9", alpha=0.7, zorder=0)
        if b2 > b1:
            ax.axvspan(b1, b2, color="#FFF6D9", alpha=0.7, zorder=0)
        if xmax > b2:
            ax.axvspan(b2, xmax, color="#DCEFDC", alpha=0.7, zorder=0)

        ax.plot(xs, ys, color=col, lw=2.5, marker="o", ms=8, zorder=5,
                markerfacecolor="white", markeredgewidth=2.2)

        for i, r in enumerate(seq):
            if r["mult"] == 1.0:
                continue
            up = (i % 2 == 0)
            ax.annotate(f"{r['t_f_h']:.3f}", xy=(r["mult"], r["t_f_h"]),
                        xytext=(0, 14 if up else -16),
                        textcoords="offset points", ha="center",
                        va="bottom" if up else "top",
                        fontsize=10.5, color=col, fontweight="bold", zorder=7)

        # 基准点：用大圆点标注，不画贯穿竖线
        ax.scatter([1.0], [tf_ref], color=C_REF, s=160, zorder=7,
                   edgecolors="white", linewidths=1.5)
        ax.annotate(f"基准 $t_f$={tf_ref:.4f} h", xy=(1.0, tf_ref),
                    xytext=(1.3, tf_ref), fontsize=11.5, color=C_REF,
                    fontweight="bold", zorder=7,
                    arrowprops=dict(arrowstyle="->", color=C_REF, lw=1.4),
                    annotation_clip=False)

        y_range = max(ys) - min(ys) + 1e-9
        ax.set_ylim(max(0, min(ys) - y_range * 0.25),
                    max(ys) + y_range * 0.35)
        ax.set_xscale("log")
        ax.set_xlim(xmin, xmax)
        ticks = [0.125, 0.25, 0.5, 1, 2, 4] if param == "hm" else [0.5, 0.7, 1, 1.3, 2]
        ax.set_xticks([t for t in ticks if xmin <= t <= xmax])
        ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"×{v:g}"))
        ax.xaxis.set_minor_formatter(FuncFormatter(lambda v, _: ""))
        ax.set_xlabel(xlab)
        ax.set_ylabel(r"烘干完成时间 $t_f$ (h)")
        ax.tick_params(labelsize=12)
        ax.set_title(title, fontweight="bold", fontsize=13.5)

        if param == "h":
            _lo, _hi = ax.get_ylim()
            ax.text(0.5, 0.06,
                    f"纵轴范围仅 {_hi - _lo:.2f} h\n"
                    r"$\times$0.5~$\times$2 全程 $|\Delta t_f|$ ≤ 0.19%",
                    transform=ax.transAxes, ha="center", va="bottom",
                    fontsize=11, color="#444444", zorder=9,
                    bbox=dict(boxstyle="round,pad=0.4", fc="#F5F5F5",
                              ec="#BBBBBB", alpha=0.95))

    fig.text(0.5, 0.955,
             r"图A  烘干完成时间对对流系数的响应（单因素扫描，$C_\mathrm{prop}$=" + f"{C_PROP}）",
             ha="center", va="center", fontsize=15, fontweight="bold")

    out = os.path.join(BASE, "figA_tf_hhm.pdf")
    plt.savefig(out, dpi=DPI, bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"[完成] {out}")


if __name__ == "__main__":
    print("运行扫描矩阵 ...")
    recs = run_all()
    print(f"完成 {len(recs)} 组算例")
    plot_figA(recs)
