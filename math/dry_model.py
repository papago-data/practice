"""
公共模块：物理模型、数值格式、阶段判定、网格与输出工具。

三个阶段参数（附录2 / 附录3 / 附录4）与阶段切换条件集中在此，
供 solve_problem1/2/3.py 与画图脚本共同引用，避免各处重复定义。
"""

import os
import numpy as np
import pandas as pd
from scipy.interpolate import PchipInterpolator

# ============================================================
# 几何与初始条件
# ============================================================
R = 0.02          # 药材半径 (m)
L = 0.25          # 药材长度 (m)
T0_C = 28.0       # 初始温度 (°C)
T0_K = T0_C + 273.15
C0 = 2.55         # 初始水分浓度，干基 (kg/kg)
C_SAFE = 0.15     # 烘干完成判据：各处水分浓度低于该值 (kg/kg)

# ============================================================
# 阶段切换条件（由附件1 环境数据标定）
#   附件1 中环境温度服从一阶惯性 T_a = T_inf - (T_inf - T_0) * exp(-t/tau)，
#   拟合得 T_inf = 50.153 °C、tau = 0.493 h。
#   取 t_c = 2 h（约 4 倍时间常数）时 |T_a - T_inf| < 0.1 K，
#   环境温度变化已降至测量噪声量级，此后进入恒温干燥阶段。
# ============================================================
T_INF_C = 50.153      # 环境温度渐近值 (°C)
TAU_T = 0.4934 * 3600.0   # 环境温度时间常数 (s)
T_SWITCH = 2.0 * 3600.0   # 预热平衡 → 恒温干燥 切换时刻 t_c = 2 h (s)
T_SWITCH_BAND = (1.8 * 3600.0, 2.2 * 3600.0)   # 切换点不确定带 (s)

# 干燥介质含湿量的两阶段水平
C_A_PRE = 0.050653    # 预热阶段末端：盘内湿气积累后的含湿量渐近值 (kg/kg)
C_A_DRY = 0.01963     # 恒温阶段：除湿机组持续运行，含湿量被压低至附件1 起始水平
C_INF = C_A_DRY       # 恒温干燥阶段的环境含湿量
C_A_RAMP = 0.5 * 3600.0   # 附件末端到除湿工况的过渡时长 (s)

# ============================================================
# 附件定位与读取
# ============================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

_SEARCH_DIRS = [
    BASE_DIR,
    os.path.join(BASE_DIR, "附件"),
    os.path.join(BASE_DIR, "A题", "附件"),
    os.path.join(BASE_DIR, "..", "附件"),
]


def locate(filename):
    """在若干候选目录中查找附件，找不到时明确报错。"""
    for d in _SEARCH_DIRS:
        p = os.path.join(d, filename)
        if os.path.exists(p):
            return p
    raise FileNotFoundError(
        f"未找到 {filename}。已搜索：\n" + "\n".join(f"  - {d}" for d in _SEARCH_DIRS)
    )


def load_attachment1():
    """读取附件1，返回 (时间, 温度, 水分浓度) 原始数组。"""
    df = pd.read_excel(locate("附件1.xlsx"))
    return (
        df["时间"].values.astype(float),
        df["温度"].values.astype(float),
        df["水分浓度"].values.astype(float),
    )


def make_env(use_extrapolation=True):
    """
    构造环境条件函数 T_a(t)、C_a(t)。

    附件1 仅覆盖 0~14400 s（即预热平衡阶段）。
    预热阶段直接使用附件1 实测曲线；恒温干燥阶段环境趋于定常：
    温度以一阶惯性式平滑趋向渐近值 T_inf，
    含湿量在 [t_max, T_SWITCH] 内线性过渡到除湿工况下的低水平
    C_A_DRY（避免在附件末端出现阶跃），此后保持恒定。
    返回 (Ta, Ca, t_att_max)
    """
    t_d, T_d, C_d = load_attachment1()
    t_max = t_d[-1]
    pT = PchipInterpolator(t_d, T_d, extrapolate=False)
    pC = PchipInterpolator(t_d, C_d, extrapolate=False)
    c_end = float(pC(np.clip(t_max, t_d[0], t_max)))
    T_end = float(pT(np.clip(t_max, t_d[0], t_max)))

    def Ta(t):
        """环境温度：预热段实测，其后一阶惯性外推至 T_inf。"""
        if t <= t_max:
            return float(pT(np.clip(t, t_d[0], t_max)))
        if not use_extrapolation:
            return T_end
        return float(T_INF_C + (T_end - T_INF_C) * np.exp(-(t - t_max) / TAU_T))

    def Ca(t):
        """环境含湿量：预热段实测；其后在 C_A_RAMP 内线性过渡到除湿工况低水平。"""
        if t <= t_max:
            return float(pC(np.clip(t, t_d[0], t_max)))
        t_ramp = t_max + C_A_RAMP
        if t >= t_ramp:
            return C_A_DRY
        frac = (t - t_max) / C_A_RAMP
        return float(c_end + (C_A_DRY - c_end) * frac)

    return Ta, Ca, t_max


def stage_of(t):
    """返回时刻 t 所属阶段名称。"""
    return "预热平衡" if t < T_SWITCH else "恒温干燥"


# ============================================================
# 阶段化物性函数
#   问题1 用附录2 常物性；问题2/3 用附录3 变物性。
#   两阶段分别持有各自的参数组，使「预热平衡与恒温干燥参数有所不同」
#   在模型中真实存在：预热阶段换热/传质以显式对流为主，
#   恒温阶段环境趋于恒定、边界条件退化为准稳态 Robin 条件。
# ============================================================
C_CLIP_LO = 1e-4   # 纯数值保护下界，与烘干判据 C_SAFE 无关
C_CLIP_HI = C0


class PhaseParams:
    """一个阶段的物性与边界参数集合。"""

    def __init__(self, name, rho_f, cp_f, k_f, D_f, h, hm):
        self.name = name
        self.rho = rho_f
        self.cp = cp_f
        self.k = k_f
        self.D = D_f
        self.h = h
        self.hm = hm

    @property
    def rho_cp(self):
        """返回体积热容函数。"""
        return lambda C: self.rho(C) * self.cp(C)


def _clip(C):
    """水分浓度数值保护：仅防除零，不改变物理量级。"""
    return np.clip(C, C_CLIP_LO, C_CLIP_HI)


# ---------- 附录2：问题1 常物性 ----------
RHO1, CP1, K1 = 820.0, 2600.0, 0.36
D0_1 = 7e-9


def D1(C):
    """附录2 扩散系数 D = 7e-9 * exp(-0.89/C)。"""
    return D0_1 * np.exp(-0.89 / _clip(C))


PARAMS_Q1 = PhaseParams(
    "附录2-常物性",
    lambda C: np.full_like(np.asarray(C, dtype=float), RHO1),
    lambda C: np.full_like(np.asarray(C, dtype=float), CP1),
    lambda C: np.full_like(np.asarray(C, dtype=float), K1),
    D1,
    h=25.0,
    hm=8e-7,
)

# ---------- 附录3：问题2/3 变物性 ----------


def rho3(C):
    return 650.0 + 128.0 * _clip(C)


def cp3(C):
    Cp = _clip(C)
    return 1450.0 + 2736.0 * Cp / (Cp + 1.0)


def k3(C):
    Cp = _clip(C)
    return 0.21 + 0.38 * Cp / (Cp + 1.0)


def D3(C, T_K):
    """附录3 扩散系数 D = 2.4e-3 * exp(-0.45/C) * exp(-3850/T)。"""
    return 2.4e-3 * np.exp(-0.45 / _clip(C)) * np.exp(-3850.0 / np.clip(T_K, 250.0, 400.0))


PARAMS_PRE = PhaseParams("附录3-预热平衡", rho3, cp3, k3, D3, h=25.0, hm=8e-7)
PARAMS_DRY = PhaseParams("附录3-恒温干燥", rho3, cp3, k3, D3, h=25.0, hm=8e-7)


def params_at(t):
    """按时刻返回该阶段的物性参数组。"""
    return PARAMS_PRE if t < T_SWITCH else PARAMS_DRY


# ============================================================
# 数值工具
# ============================================================
def tdma(a, b, c, d):
    """追赶法求解三对角线性方程组。"""
    n = len(b)
    cp_ = np.zeros(n)
    dp_ = np.zeros(n)
    x = np.zeros(n)
    if n == 1:
        return np.array([d[0] / b[0]])

    cp_[0] = c[0] / b[0]
    dp_[0] = d[0] / b[0]

    # 前向消元
    for i in range(1, n):
        m = b[i] - a[i] * cp_[i - 1]
        if i < n - 1:
            cp_[i] = c[i] / m
        dp_[i] = (d[i] - a[i] * dp_[i - 1]) / m

    # 回代
    x[-1] = dp_[-1]
    for i in range(n - 2, -1, -1):
        x[i] = dp_[i] - cp_[i] * x[i + 1]
    return x


def harm_mean(v0, v1):
    """界面系数调和平均（串联阻力模型），仅适用于两侧为不同材料的情形。"""
    return 2.0 * v0 * v1 / (v0 + v1 + 1e-30)


def iface_mean(v0, v1):
    """
    界面系数（算术平均 / 线性插值）。

    适用场景：扩散系数是「同一材料」随浓度变化的函数（如 D(C)=a·exp(-b/C)），
    界面两侧浓度连续，系数应取两侧值的线性插值。
    此时若用调和平均，会因 D 在低浓度侧急剧衰减而人为制造一道
    「零通量墙」（D→0 时调和平均→0），把内部水分彻底封死。
    """
    return 0.5 * (v0 + v1)


class Grid:
    """径向等距网格及其几何量。"""

    def __init__(self, N, R=R, L=L):
        self.N = N
        self.R = R
        self.L = L
        self.dr = R / N
        self.r = np.linspace(0.0, R, N + 1)
        self.r_int = self.r[1:N]                       # 内部节点半径
        self.r_half = self.r[:-1] + self.dr / 2.0      # 界面半径 r_{i+1/2}
        # 表面半格控制体：r ∈ [R - dr/2, R]（节点 N 落在 R，取内侧半格）
        # 与相邻内部柱壳（节点 N-1，r ∈ [R - 3dr/2, R - dr/2]）无缝互补，
        # 保证 sum(cell_volumes()) == pi*R^2*L 严格成立。
        self.V_half = np.pi * (R ** 2 - (R - self.dr / 2.0) ** 2) * L
        self.A_R = 2.0 * np.pi * R * L                      # 外表面对流面积
        self.A_inner = 2.0 * np.pi * (R - self.dr / 2.0) * L  # 半格内侧面（与 N-1 交界）

    def cell_volumes(self):
        """各节点的控制体体积（轴心半格 + 内部柱壳 + 表面半格）。"""
        vol = np.zeros(self.N + 1)
        vol[0] = np.pi * (self.dr / 2.0) ** 2 * self.L
        for i in range(1, self.N):
            rp = self.r[i] + self.dr / 2.0
            rm = self.r[i] - self.dr / 2.0
            vol[i] = np.pi * (rp ** 2 - rm ** 2) * self.L
        vol[self.N] = self.V_half
        return vol


def sample_indices(t_end, dt, sample_dt):
    """按固定采样间隔返回 (时间序列, 对应步号序列)。"""
    nsteps = int(round(t_end / dt))
    stride = max(1, int(round(sample_dt / dt)))
    steps = np.arange(0, nsteps + 1, stride, dtype=int)
    return steps * dt, steps


def interp_to_distances(r, values, target_dists):
    """把节点值插值到指定的到中心距离（单位 cm）。"""
    return np.interp(target_dists, r * 100.0, values)


# ============================================================
# 问题1 专用：常物性显式/隐式通用求解器 + 解析解工具
#   （供画图脚本做收敛性与解析解校核，与 solve_problem1.py 同格式）
# ============================================================
def solve_problem1_generic(N=20, dt=1.0, t_end=1800.0,
                           Ta_func=None, Ca_func=None, use_evap=False,
                           sample_dt=1.0):
    """
    附录2 常物性下的一维圆柱双场隐式求解器。

    内部节点全隐式、TDMA 求解；表面节点用半格控制体隐式。
    返回 (时间数组, 温度矩阵, 水分浓度矩阵, 半径数组)。
    use_evap=True 时在表面温度方程中计入水分蒸发潜热汇项。
    """
    Lv = 2.26e6                      # 水的汽化潜热 (J/kg)
    grid = Grid(N)
    n = N + 1
    dr = grid.dr
    r = grid.r
    A_R, A_in, V_h = grid.A_R, grid.A_inner, grid.V_half

    T = np.full(n, T0_C)
    C = np.full(n, C0)

    def envs(t):
        ta = Ta_func(t) if Ta_func is not None else T0_C
        ca = Ca_func(t) if Ca_func is not None else 0.0
        return float(ta), float(ca)

    steps = int(round(t_end / dt))
    stride = max(1, int(round(sample_dt / dt)))
    times = [0.0]
    T_out = [T.copy()]
    C_out = [C.copy()]

    for step in range(1, steps + 1):
        t_new = step * dt
        Ta_v, Ca_v = envs(t_new)

        # ---- 水分浓度场（全隐式 TDMA）----
        a = np.zeros(n); b = np.zeros(n); c = np.zeros(n); d = np.zeros(n)
        Dn = D1(C)
        for i in range(1, N):
            ri = r[i]
            Dp = iface_mean(Dn[i], Dn[i + 1])
            Dm = iface_mean(Dn[i - 1], Dn[i])
            cp_p = dt * (ri + dr / 2) * Dp / (ri * dr ** 2)
            cm_m = dt * (ri - dr / 2) * Dm / (ri * dr ** 2)
            a[i], b[i], c[i] = -cm_m, 1.0 + cp_p + cm_m, -cp_p
            d[i] = C[i]
        # 轴心：对称边界，半格控制体
        k0 = 4.0 * Dn[0] * dt / dr ** 2
        b[0], c[0], d[0] = 1.0 + k0, -k0, C[0]
        # 表面：半格控制体 + Robin 传质
        coeff_self = V_h / (A_R * dt)
        a[N] = -Dn[N] / dr
        b[N] = coeff_self + PARAMS_Q1.hm + Dn[N] / dr
        d[N] = coeff_self * C[N] + PARAMS_Q1.hm * Ca_v
        C = tdma(a, b, c, d)

        # ---- 温度场（全隐式 TDMA）----
        a = np.zeros(n); b = np.zeros(n); c = np.zeros(n); d = np.zeros(n)
        for i in range(1, N):
            cp_p = ALPHA * dt * (1.0 / dr ** 2 + 1.0 / (2 * r[i] * dr))
            cm_m = ALPHA * dt * (1.0 / dr ** 2 - 1.0 / (2 * r[i] * dr))
            a[i], b[i], c[i] = -cm_m, 1.0 + cp_p + cm_m, -cp_p
            d[i] = T[i]
        k0 = 4.0 * ALPHA * dt / dr ** 2
        b[0], c[0], d[0] = 1.0 + k0, -k0, T[0]
        coeff_self_T = RHO1 * CP1 * V_h / (A_R * dt)
        q_evap = Lv * PARAMS_Q1.hm * (C[N] - Ca_v) if use_evap else 0.0
        a[N] = -K1 / dr
        b[N] = coeff_self_T + PARAMS_Q1.h + K1 / dr
        d[N] = coeff_self_T * T[N] + PARAMS_Q1.h * Ta_v - q_evap
        T = tdma(a, b, c, d)

        if step % stride == 0:
            times.append(t_new)
            T_out.append(T.copy())
            C_out.append(C.copy())

    return (np.array(times), np.array(T_out),
            np.array(C_out), r)


ALPHA = K1 / (RHO1 * CP1)      # 热扩散率 (m^2/s)


def bessel_eigenvalues(Bi, n_roots=20, hi=200.0, step=0.05):
    """求解圆柱第一类边界特征方程 mu*J1(mu) - Bi*J0(mu) = 0 的前若干正根。"""
    from scipy.optimize import brentq
    from scipy.special import j0, j1

    x = np.arange(step, hi, step)
    f = x * j1(x) - Bi * j0(x)
    roots = []
    for i in range(len(x) - 1):
        if f[i] * f[i + 1] < 0:
            try:
                rt = brentq(lambda m: m * j1(m) - Bi * j0(m), x[i], x[i + 1],
                            xtol=1e-12)
                if rt > 1e-6:
                    roots.append(rt)
            except ValueError:
                pass
        if len(roots) >= n_roots:
            break
    return np.array(roots)


def analytical_T_cylinder(r_arr, t_val, Ta_c, T0_c, mus, Bi, R, alpha):
    """
    无限长圆柱、第三类边界（对流）下温度场的贝塞尔级数解析解：
        T = Ta + (T0 - Ta) * Σ 2Bi/(mu_n J0(mu_n)(mu_n^2+Bi^2))
                              · J0(mu_n r/R) · exp(-mu_n^2 alpha t / R^2)
    """
    from scipy.special import j0

    theta0 = T0_c - Ta_c
    T_sol = np.full_like(np.asarray(r_arr, dtype=float), Ta_c)
    for mu in mus:
        J0 = j0(mu)
        if abs(J0) < 1e-15:
            continue
        A_n = 2.0 * Bi / (J0 * (mu ** 2 + Bi ** 2))
        T_sol += theta0 * A_n * j0(mu * r_arr / R) \
            * np.exp(-mu ** 2 * alpha * t_val / R ** 2)
    return T_sol


# ============================================================
# 输出工具
# ============================================================
TARGET_DISTS = np.arange(0.0, 2.0 + 1e-9, 0.1)


def save_result(path, sheets):
    """
    写出结果 Excel。
    sheets: [(工作表名, 时间数组, 数据矩阵, 首列标题), ...]
    """
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        cols = [f"{d:.1f}" for d in TARGET_DISTS]
        for name, times, data, first_col in sheets:
            df = pd.DataFrame(np.round(data, 4), columns=cols)
            df.insert(0, first_col, times.astype(int))
            df.to_excel(writer, sheet_name=name, index=False)


def print_table(title, row_values, col_values, col_header, values, fmt="{:.4f}"):
    """按题面格式打印表格。"""
    print(title)
    print(f"{col_header:<12}" + "".join(f"{v:>12}" for v in col_values))
    print("-" * (12 + 12 * len(col_values)))
    for rv in row_values:
        print(f"{rv:<12}" + "".join(f"{fmt.format(v):>12}" for v in values(rv)))
