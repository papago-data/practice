"""
2024数学建模C题 - 农作物种植策略 问题一
完整代码：数据读取 + 线性规划建模 + 求解 + 表格12~15 + 图表1~4
修正版：情况2超产部分降价50%出售，体现在目标函数中
"""

import numpy as np
import pandas as pd
from scipy.optimize import linprog
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import warnings
import os
warnings.filterwarnings('ignore')

# ============================================================
# 0. 配置
# ============================================================
ATTACHMENT1_PATH = "C:\\Users\\UserPro\\Documents\\WPSDrive\\附件1.xlsx"
ATTACHMENT2_PATH = "C:\\Users\\UserPro\\Documents\\WPSDrive\\附件2.xlsx"

# ★ 输出目录（修改为你需要的路径）
OUTPUT_DIR = r"C:\Users\UserPro\Documents\WPSDrive"
os.makedirs(OUTPUT_DIR, exist_ok=True)

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'WenQuanYi Micro Hei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# ============================================================
# 1. 读取附件1：作物相关数据
# ============================================================
print("正在读取附件1...")
crop_data = {}
df_crop = pd.read_excel(ATTACHMENT1_PATH, sheet_name='作物')
crop_ids = []
for _, row in df_crop.iterrows():
    cid = row['作物编号']
    crop_ids.append(cid)
    crop_data[cid] = {
        '名称': row['作物名称'],
        '类型': row['作物类型'],
        '亩产_2023': row['亩产_2023'],
        '单价_2023': row['单价_2023'],
        '种植成本': row['种植成本'],
        '预期销售量_2023': row['预期销售量_2023']
    }

# 读取地块信息
df_plot = pd.read_excel(ATTACHMENT1_PATH, sheet_name='地块')
plot_names = df_plot['地块名称'].tolist()
plot_types = df_plot['地块类型'].tolist()
plot_areas = df_plot['地块面积'].values

# 读取2023年种植数据
df_plant23 = pd.read_excel(ATTACHMENT1_PATH, sheet_name='2023年种植情况')

# ============================================================
# 2. 读取附件2：2024-2030年预期数据
# ============================================================
print("正在读取附件2...")
df_future = pd.read_excel(ATTACHMENT2_PATH)
years = list(range(2024, 2031))

# 构建每年数据：Y(亩产), P(单价), C(成本), S(预期销售量)
n_plots = len(plot_names)
n_crops = len(crop_ids)

Y_all = {}   # 亩产矩阵
P_all = {}   # 单价矩阵
C_all = {}   # 成本矩阵
S_all = {}   # 预期销售量矩阵

for year in years:
    Y = np.zeros((n_plots, n_crops))
    P = np.zeros((n_plots, n_crops))
    C = np.zeros((n_plots, n_crops))
    S = np.zeros((n_plots, n_crops))
    
    for pi in range(n_plots):
        for cj, cid in enumerate(crop_ids):
            # 从附件2获取该年份数据
            mask = (df_future['年份'] == year) & (df_future['作物编号'] == cid)
            if mask.any():
                row = df_future[mask].iloc[0]
                Y[pi, cj] = row['亩产']
                P[pi, cj] = row['单价']
                C[pi, cj] = row['种植成本']
                S[pi, cj] = row['预期销售量']
            else:
                # 回退到2023年数据
                Y[pi, cj] = crop_data[cid]['亩产_2023']
                P[pi, cj] = crop_data[cid]['单价_2023']
                C[pi, cj] = crop_data[cid]['种植成本']
                S[pi, cj] = crop_data[cid]['预期销售量_2023']
    
    Y_all[year] = Y
    P_all[year] = P
    C_all[year] = C
    S_all[year] = S

# ============================================================
# 3. 辅助函数
# ============================================================
def build_constraints(year, case_label):
    """
    构建线性规划约束矩阵
    case_label: '情况1' 或 '情况2'
    情况1: 产量 ≤ 预期销售量
    情况2: 产量可超过预期销售量，超出部分降价50%出售
    """
    Y = Y_all[year]
    S = S_all[year]
    
    n_vars = n_plots * n_crops
    A_ub = []
    b_ub = []
    
    # ---- 约束1: 每块地总面积不超过地块面积 ----
    for pi in range(n_plots):
        row = np.zeros(n_vars)
        for cj in range(n_crops):
            row[pi * n_crops + cj] = 1
        A_ub.append(row)
        b_ub.append(plot_areas[pi])
    
    # ---- 约束2: 情况1下产量不能超过预期销售量 ----
    if case_label == '情况1':
        for cj in range(n_crops):
            row = np.zeros(n_vars)
            for pi in range(n_plots):
                idx = pi * n_crops + cj
                row[idx] = Y[pi, cj]  # 产量 = 面积 × 亩产
            A_ub.append(row)
            b_ub.append(S[:, cj].sum())  # 该作物总预期销售量
    
    # ---- 约束3: 轮作约束（豆类作物至少轮作一年） ----
    # 简化：豆类作物占比不超过50%
    legume_ids = [cid for cid in crop_ids if crop_data[cid]['类型'] == '豆类']
    legume_indices = [crop_ids.index(cid) for cid in legume_ids]
    for pi in range(n_plots):
        row = np.zeros(n_vars)
        for cj in legume_indices:
            row[pi * n_crops + cj] = 1
        A_ub.append(row)
        b_ub.append(0.5 * plot_areas[pi])
    
    # ---- 约束4: 水浇地只能种水稻或蔬菜 ----
    for pi in range(n_plots):
        if plot_types[pi] == '水浇地':
            for cj, cid in enumerate(crop_ids):
                if crop_data[cid]['类型'] not in ['水稻', '蔬菜']:
                    row = np.zeros(n_vars)
                    row[pi * n_crops + cj] = 1
                    A_ub.append(row)
                    b_ub.append(0)
    
    # ---- 约束5: 每种作物至少种植一定面积 ----
    for cj in range(n_crops):
        row = np.zeros(n_vars)
        for pi in range(n_plots):
            row[pi * n_crops + cj] = 1
        A_ub.append(-row)  # 转为 ≥ 约束
        b_ub.append(-1)     # 至少1亩
    
    return np.array(A_ub), np.array(b_ub)


def build_objective(year, case_label):
    """
    构建目标函数系数（利润最大化 → 取负号求最小化）
    
    情况1: 利润 = min(产量, 预期销售量) × 单价 - 成本
           超过部分浪费，收益为0
    
    情况2: 利润 = min(产量, 预期销售量) × 单价 
                 + max(0, 产量 - 预期销售量) × 单价 × 0.5 
                 - 成本
           即：不超过部分原价，超过部分半价
    """
    Y = Y_all[year]
    P = P_all[year]
    C = C_all[year]
    S = S_all[year]
    
    n_vars = n_plots * n_crops
    c = np.zeros(n_vars)
    
    for pi in range(n_plots):
        for cj in range(n_crops):
            idx = pi * n_crops + cj
            ypm = Y[pi, cj]       # 亩产
            price = P[pi, cj]     # 单价
            cost = C[pi, cj]      # 成本
            area = plot_areas[pi]
            
            if ypm <= 0:
                c[idx] = 0
                continue
            
            # 该地块该作物的预期销售量
            expected_sales = S[pi, cj]
            
            if case_label == '情况1':
                # 情况1：产量超过预期则浪费
                # 实际收益 = min(产量, 预期) × 单价
                # 但LP无法处理min，所以用约束"产量 ≤ 预期"来保证
                # 目标函数中正常计算
                if expected_sales > 0:
                    c[idx] = -(ypm * price - cost)
                else:
                    c[idx] = cost  # 只付出成本，无收入
                    
            elif case_label == '情况2':
                # 情况2：产量超过预期部分半价出售
                # 单位面积收益 = min(ypm, 预期/面积) × price 
                #               + max(0, ypm - 预期/面积) × price × 0.5
                #               - cost
                
                # 计算单位面积预期销售量
                exp_sales_per_mu = expected_sales / area if area > 0 else 0
                
                if ypm <= exp_sales_per_mu:
                    # 全部原价卖出
                    revenue_per_mu = ypm * price
                else:
                    # 部分原价 + 部分半价
                    revenue_per_mu = (exp_sales_per_mu * price 
                                      + (ypm - exp_sales_per_mu) * price * 0.5)
                
                c[idx] = -(revenue_per_mu - cost)
    
    return c


def build_plan_detail(X, year, case_label):
    """
    从解矩阵 X 构建详细种植方案表
    """
    Y = Y_all[year]
    P = P_all[year]
    C = C_all[year]
    S = S_all[year]
    
    records = []
    for pi in range(n_plots):
        for cj, cid in enumerate(crop_ids):
            area = X[pi, cj]
            if area > 0.01:  # 忽略极小面积
                yield_amount = area * Y[pi, cj]
                expected = S[pi, cj]
                
                if case_label == '情况1':
                    actual_sales = min(yield_amount, expected)
                    waste = max(0, yield_amount - expected)
                    discount_sales = 0
                else:
                    # 情况2
                    if yield_amount <= expected:
                        actual_sales = yield_amount
                        discount_sales = 0
                    else:
                        actual_sales = expected
                        discount_sales = yield_amount - expected
                    waste = 0
                
                revenue = actual_sales * P[pi, cj] + discount_sales * P[pi, cj] * 0.5
                total_cost = area * C[pi, cj]
                profit = revenue - total_cost
                
                records.append({
                    '地块': plot_names[pi],
                    '作物': crop_data[cid]['名称'],
                    '种植面积(亩)': round(area, 2),
                    '亩产(斤/亩)': Y[pi, cj],
                    '总产量(斤)': round(yield_amount, 2),
                    '预期销售量(斤)': expected,
                    '原价销售(斤)': round(actual_sales, 2),
                    '半价销售(斤)': round(discount_sales, 2),
                    '浪费(斤)': round(waste, 2),
                    '单价(元/斤)': P[pi, cj],
                    '总收入(元)': round(revenue, 2),
                    '总成本(元)': round(total_cost, 2),
                    '利润(元)': round(profit, 2)
                })
    
    return pd.DataFrame(records)


def build_econ_summary(all_plans, case_label):
    """
    构建经济指标汇总表
    """
    summary = []
    for year, df in all_plans.items():
        summary.append({
            '年份': year,
            '总种植面积(亩)': round(df['种植面积(亩)'].sum(), 2),
            '总产量(斤)': round(df['总产量(斤)'].sum(), 2),
            '原价销售(斤)': round(df['原价销售(斤)'].sum(), 2),
            '半价销售(斤)': round(df['半价销售(斤)'].sum(), 2),
            '浪费(斤)': round(df['浪费(斤)'].sum(), 2),
            '总收入(元)': round(df['总收入(元)'].sum(), 2),
            '总成本(元)': round(df['总成本(元)'].sum(), 2),
            '总利润(元)': round(df['利润(元)'].sum(), 2)
        })
    return pd.DataFrame(summary)


# ============================================================
# 4. 主求解循环
# ============================================================
print("\n" + "="*60)
print("开始求解线性规划模型...")
print("="*60)

all_plans_1 = {}  # 情况1每年方案
all_plans_2 = {}  # 情况2每年方案

for year in years:
    Y = Y_all[year]
    P = P_all[year]
    C = C_all[year]
    S = S_all[year]
    
    # ========== 调试：参数快照 ==========
    print(f"\n=== {year}年 参数快照 ===")
    flat_idx = np.argmax(Y)
    max_row, max_col = np.unravel_index(flat_idx, Y.shape)
    print(f"  最高亩产作物: {crop_ids[max_col]} ({crop_data[crop_ids[max_col]]['名称']}) -> {np.max(Y):.1f} 斤/亩")
    
    flat_idx = np.argmax(P)
    max_row, max_col = np.unravel_index(flat_idx, P.shape)
    print(f"  最高单价作物: {crop_ids[max_col]} ({crop_data[crop_ids[max_col]]['名称']}) -> {np.max(P):.2f} 元/斤")
    
    C_nonzero = np.where(C > 0, C, np.inf)
    flat_idx = np.argmin(C_nonzero)
    max_row, max_col = np.unravel_index(flat_idx, C.shape)
    print(f"  最低成本作物: {crop_ids[max_col]} ({crop_data[crop_ids[max_col]]['名称']}) -> {np.min(C_nonzero):.1f} 元/亩")
    
    flat_idx = np.argmax(S)
    max_row, max_col = np.unravel_index(flat_idx, S.shape)
    print(f"  最大预期销量地块: {plot_names[max_row]} -> {np.max(S):.0f} 斤")
    
    # ========== 情况1：超产浪费 ==========
    print(f"\n  [{year}] 求解情况1（超产浪费）...", end=" ")
    
    A_ub_1, b_ub_1 = build_constraints(year, '情况1')
    c_1 = build_objective(year, '情况1')
    bounds = [(0, plot_areas[pi]) for pi in range(n_plots) for _ in range(n_crops)]
    
    try:
        res_1 = linprog(c_1, A_ub=A_ub_1, b_ub=b_ub_1, bounds=bounds, method='highs')
        if res_1.success:
            X_1 = res_1.x.reshape(n_plots, n_crops)
            opt_val_1 = -res_1.fun
            print(f"✓ 利润: {opt_val_1:,.0f} 元")
        else:
            print(f"✗ 求解失败: {res_1.message}")
            X_1 = np.zeros((n_plots, n_crops))
            opt_val_1 = 0
    except Exception as e:
        print(f"✗ 异常: {e}")
        X_1 = np.zeros((n_plots, n_crops))
        opt_val_1 = 0
    
    # ========== 情况2：超产半价出售 ==========
    print(f"  [{year}] 求解情况2（超产半价）...", end=" ")
    
    A_ub_2, b_ub_2 = build_constraints(year, '情况2')
    c_2 = build_objective(year, '情况2')
    
    try:
        res_2 = linprog(c_2, A_ub=A_ub_2, b_ub=b_ub_2, bounds=bounds, method='highs')
        if res_2.success:
            X_2 = res_2.x.reshape(n_plots, n_crops)
            opt_val_2 = -res_2.fun
            print(f"✓ 利润: {opt_val_2:,.0f} 元")
        else:
            print(f"✗ 求解失败: {res_2.message}")
            X_2 = X_1.copy()
            opt_val_2 = opt_val_1
    except Exception as e:
        print(f"✗ 异常: {e}")
        X_2 = X_1.copy()
        opt_val_2 = opt_val_1
    
    # 构建详细方案
    df_plan_1 = build_plan_detail(X_1, year, '情况1')
    df_plan_2 = build_plan_detail(X_2, year, '情况2')
    
    all_plans_1[year] = df_plan_1
    all_plans_2[year] = df_plan_2

# ============================================================
# 5. 生成汇总表
# ============================================================
print("\n" + "="*60)
print("生成汇总表...")
print("="*60)

summary_1 = build_econ_summary(all_plans_1, '情况1')
summary_2 = build_econ_summary(all_plans_2, '情况2')

print("\n--- 情况1 经济指标汇总 ---")
print(summary_1.to_string(index=False))

print("\n--- 情况2 经济指标汇总 ---")
print(summary_2.to_string(index=False))

# ============================================================
# 6. 导出Excel
# ============================================================
print("\n" + "="*60)
print("导出Excel文件...")
print("="*60)

with pd.ExcelWriter(os.path.join(OUTPUT_DIR, 'result1_1.xlsx')) as writer:
    summary_1.to_excel(writer, sheet_name='经济指标汇总', index=False)
    for year in years:
        all_plans_1[year].to_excel(writer, sheet_name=f'{year}年种植方案', index=False)
print(f"  ✓ {os.path.join(OUTPUT_DIR, 'result1_1.xlsx')}")

with pd.ExcelWriter(os.path.join(OUTPUT_DIR, 'result1_2.xlsx')) as writer:
    summary_2.to_excel(writer, sheet_name='经济指标汇总', index=False)
    for year in years:
        all_plans_2[year].to_excel(writer, sheet_name=f'{year}年种植方案', index=False)
print(f"  ✓ {os.path.join(OUTPUT_DIR, 'result1_2.xlsx')}")

# ============================================================
# 7. 绘制图表
# ============================================================
print("\n" + "="*60)
print("绘制图表...")
print("="*60)

# ---- 图表1：情况1 每年总利润 ----
fig, ax = plt.subplots(figsize=(10, 5))
profits_1 = summary_1['总利润(元)'].values / 10000
years_display = [str(y) for y in years]
bars = ax.bar(years_display, profits_1, color='#4C72B0', edgecolor='white', linewidth=0.8)
for bar, val in zip(bars, profits_1):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2,
            f'{val:.1f}万', ha='center', va='bottom', fontsize=9)
ax.set_xlabel('年份', fontsize=12)
ax.set_ylabel('总利润（万元）', fontsize=12)
ax.set_title('图表1：情况1（超产浪费）每年总利润', fontsize=14, fontweight='bold')
ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f'{x:.0f}'))
ax.grid(axis='y', alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, '图表1_情况1_每年总利润.png'), dpi=150)
plt.close()
print("  ✓ 图表1")

# ---- 图表2：情况2 每年总利润 ----
fig, ax = plt.subplots(figsize=(10, 5))
profits_2 = summary_2['总利润(元)'].values / 10000
bars = ax.bar(years_display, profits_2, color='#55A868', edgecolor='white', linewidth=0.8)
for bar, val in zip(bars, profits_2):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2,
            f'{val:.1f}万', ha='center', va='bottom', fontsize=9)
ax.set_xlabel('年份', fontsize=12)
ax.set_ylabel('总利润（万元）', fontsize=12)
ax.set_title('图表2：情况2（超产半价出售）每年总利润', fontsize=14, fontweight='bold')
ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f'{x:.0f}'))
ax.grid(axis='y', alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, '图表2_情况2_每年总利润.png'), dpi=150)
plt.close()
print("  ✓ 图表2")

# ---- 图表3：情况1 vs 情况2 总利润对比 ----
fig, ax = plt.subplots(figsize=(12, 6))
x = np.arange(len(years))
width = 0.35
bars1 = ax.bar(x - width/2, profits_1, width, label='情况1：超产浪费', color='#4C72B0', edgecolor='white')
bars2 = ax.bar(x + width/2, profits_2, width, label='情况2：超产半价出售', color='#55A868', edgecolor='white')
for bar, val in zip(bars1, profits_1):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2,
            f'{val:.0f}', ha='center', va='bottom', fontsize=8)
for bar, val in zip(bars2, profits_2):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2,
            f'{val:.0f}', ha='center', va='bottom', fontsize=8)
ax.set_xlabel('年份', fontsize=12)
ax.set_ylabel('总利润（万元）', fontsize=12)
ax.set_title('图表3：情况1 vs 情况2 总利润对比', fontsize=14, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(years_display)
ax.legend(fontsize=11)
ax.grid(axis='y', alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, '图表3_情况1vs情况2_总利润对比.png'), dpi=150)
plt.close()
print("  ✓ 图表3")

# ---- 图表4：累计利润增长趋势 ----
fig, ax = plt.subplots(figsize=(10, 5))
cum_1 = np.cumsum(profits_1)
cum_2 = np.cumsum(profits_2)
ax.plot(years_display, cum_1, 'o-', color='#4C72B0', linewidth=2, markersize=8, label='情况1：超产浪费')
ax.plot(years_display, cum_2, 's-', color='#55A868', linewidth=2, markersize=8, label='情况2：超产半价出售')
for i, (v1, v2) in enumerate(zip(cum_1, cum_2)):
    ax.annotate(f'{v1:.0f}万', (years_display[i], v1), textcoords="offset points",
                xytext=(0, 12), ha='center', fontsize=8, color='#4C72B0')
    ax.annotate(f'{v2:.0f}万', (years_display[i], v2), textcoords="offset points",
                xytext=(0, -18), ha='center', fontsize=8, color='#55A868')
ax.set_xlabel('年份', fontsize=12)
ax.set_ylabel('累计利润（万元）', fontsize=12)
ax.set_title('图表4：累计利润增长趋势（2024-2030）', fontsize=14, fontweight='bold')
ax.legend(fontsize=11)
ax.grid(alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, '图表4_累计利润增长趋势.png'), dpi=150)
plt.close()
print("  ✓ 图表4")

# ============================================================
# 8. 完成
# ============================================================
print("\n" + "="*60)
print("全部完成！")
print(f"所有文件保存在: {OUTPUT_DIR}")
print("="*60)
import pandas as pd

# 查看附件1的所有工作表名称
xl = pd.ExcelFile("附件1.xlsx")
print("附件1的工作表：", xl.sheet_names)