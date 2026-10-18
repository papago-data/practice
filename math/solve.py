import os
import numpy as np
import pandas as pd
from scipy.interpolate import PchipInterpolator

# 物性参数
rho = 820.0
cp = 2600.0
k = 0.36
h = 25.0
hm = 8e-7
D0 = 7e-9
Lv = 2.26e6

# 几何与时间
R = 0.02
N = 20
dr = R / N
dt = 0.1
t_end = 1800.0
T0 = 28.0
C0 = 2.55
sample_dt = 1.0

# 读取附件1
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
att1_path = os.path.join(BASE_DIR, "C:\\Users\\UserPro\\Desktop\\A题\\附件\\附件1.xlsx")
if not os.path.exists(att1_path):
    att1_path = os.path.join(BASE_DIR, "附件", "C:\\Users\\UserPro\\Desktop\\A题\\附件\\附件1.xlsx")
df = pd.read_excel(att1_path)
t_data = df["时间"].values.astype(float)
T_data = df["温度"].values.astype(float)
C_data = df["水分浓度"].values.astype(float)

pchip_T = PchipInterpolator(t_data, T_data, extrapolate=False)
pchip_C = PchipInterpolator(t_data, C_data, extrapolate=False)
t_min, t_max = t_data[0], t_data[-1]

def Ta(t):
    return float(pchip_T(np.clip(t, t_min, t_max)))

def Ca(t):
    return float(pchip_C(np.clip(t, t_min, t_max)))

# 扩散系数
def D_func(C):
    C = np.maximum(C, 1e-12)
    return D0 * np.exp(-0.89 / C)

# TDMA 求解三对角方程
def tdma(a, b, c, d):
    n = len(b)
    cp_ = np.zeros(n)
    dp_ = np.zeros(n)
    x = np.zeros(n)
    cp_[0] = c[0] / b[0]
    dp_[0] = d[0] / b[0]
    for i in range(1, n):
        m = b[i] - a[i] * cp_[i - 1]
        if i < n - 1:
            cp_[i] = c[i] / m
        dp_[i] = (d[i] - a[i] * dp_[i - 1]) / m
    x[-1] = dp_[-1]
    for i in range(n - 2, -1, -1):
        x[i] = dp_[i] - cp_[i] * x[i + 1]
    return x

# 网格
r = np.linspace(0, R, N + 1)
r_int = r[1:N]
r_half_p = 0.5 * (r[1:N] + r[2:N + 1])
r_half_m = 0.5 * (r[0:N - 1] + r[1:N])
alpha = k / (rho * cp)

# 初始化
T = np.full(N + 1, T0)
C = np.full(N + 1, C0)
times_out = [0.0]
T_out = [T.copy()]
C_out = [C.copy()]
next_sample = sample_dt

# 时间推进
nsteps = int(round(t_end / dt))
for step in range(1, nsteps + 1):
    t_next = step * dt

    # 水分扩散
    a = np.zeros(N + 1)
    b = np.zeros(N + 1)
    c = np.zeros(N + 1)
    d = np.zeros(N + 1)
    D_node = D_func(C)
    for i in range(1, N):
        ri = r_int[i - 1]
        rhp = r_half_p[i - 1]
        rhm = r_half_m[i - 1]
        D_ip = 2 * D_node[i] * D_node[i + 1] / (D_node[i] + D_node[i + 1] + 1e-30)
        D_im = 2 * D_node[i - 1] * D_node[i] / (D_node[i - 1] + D_node[i] + 1e-30)
        coeff_p = dt * rhp * D_ip / (ri * dr ** 2)
        coeff_m = dt * rhm * D_im / (ri * dr ** 2)
        a[i] = -coeff_m
        b[i] = 1.0 + coeff_p + coeff_m
        c[i] = -coeff_p
        d[i] = C[i]
    b[0] = 1.0 + 4.0 * D_node[0] * dt / dr ** 2
    c[0] = -4.0 * D_node[0] * dt / dr ** 2
    d[0] = C[0]
    Ca_next = Ca(t_next)
    D_s = D_node[N]
    coeff_self_c = dr / (2.0 * dt)
    a[N] = -D_s / dr
    b[N] = coeff_self_c + hm + D_s / dr
    d[N] = coeff_self_c * C[N] + hm * Ca_next
    C = tdma(a, b, c, d)

    # 温度场
    a = np.zeros(N + 1)
    b = np.zeros(N + 1)
    c = np.zeros(N + 1)
    d = np.zeros(N + 1)
    for i in range(1, N):
        ri = r_int[i - 1]
        coeff_p = alpha * dt * (1.0 / dr ** 2 + 1.0 / (2 * ri * dr))
        coeff_m = alpha * dt * (1.0 / dr ** 2 - 1.0 / (2 * ri * dr))
        a[i] = -coeff_m
        b[i] = 1.0 + coeff_p + coeff_m
        c[i] = -coeff_p
        d[i] = T[i]
    b[0] = 1.0 + 4.0 * alpha * dt / dr ** 2
    c[0] = -4.0 * alpha * dt / dr ** 2
    d[0] = T[0]
    Ta_next = Ta(t_next)
    coeff_self_T = rho * cp * dr / (2.0 * dt)
    q_evap = Lv * hm * (C[N] - Ca_next)
    a[N] = -k / dr
    b[N] = coeff_self_T + h + k / dr
    d[N] = coeff_self_T * T[N] + h * Ta_next - q_evap
    T = tdma(a, b, c, d)

    # 采样
    if t_next >= next_sample - 1e-12:
        times_out.append(next_sample)
        T_out.append(T.copy())
        C_out.append(C.copy())
        next_sample += sample_dt

# 保存结果
times_out = np.array(times_out)
T_out = np.array(T_out)
C_out = np.array(C_out)
distances = np.round(r * 100, 1)
out_path = os.path.join(BASE_DIR, "result1_latent.xlsx")
with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
    df_T = pd.DataFrame(np.round(T_out, 4), columns=distances)
    df_T.insert(0, "时间", times_out.astype(int))
    df_T.to_excel(writer, sheet_name="温度", index=False)
    df_C = pd.DataFrame(np.round(C_out, 4), columns=distances)
    df_C.insert(0, "时间", times_out.astype(int))
    df_C.to_excel(writer, sheet_name="水分浓度", index=False)

# 打印表格
table_times = [100, 300, 600, 900, 1200, 1500, 1800]
table_dists = [0.0, 0.5, 1.0, 1.5, 2.0]

def find_col(d):
    return int(np.argmin(np.abs(distances - d)))

def find_row(t_val):
    return int(np.argmin(np.abs(times_out - t_val)))

print("表1  30分钟内药材的温度 (°C)")
print("时间/s", *[f"{d}cm" for d in table_dists])
for t_val in table_times:
    idx = find_row(t_val)
    print(t_val, *[f"{T_out[idx, find_col(d)]:.4f}" for d in table_dists])

print("\n表2  30分钟内药材的水分浓度 (kg/kg)")
print("时间/s", *[f"{d}cm" for d in table_dists])
for t_val in table_times:
    idx = find_row(t_val)
    print(t_val, *[f"{C_out[idx, find_col(d)]:.4f}" for d in table_dists])