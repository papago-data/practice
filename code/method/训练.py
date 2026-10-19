"""
2024C数学建模 - 农作物种植优化模型（最终优化版）
根据附件1.xlsx和附件2.xlsx实际结构精准解析
"""

import pandas as pd
import numpy as np
from itertools import product
import warnings
warnings.filterwarnings('ignore')

# ============================================================
# 文件路径配置
# ============================================================
ATTACHMENT1_PATH = r"C:\Users\UserPro\Documents\WPSDrive\附件1.xlsx"
ATTACHMENT2_PATH = r"C:\Users\UserPro\Documents\WPSDrive\附件2.xlsx"

# ============================================================
# 第一部分：通用工具函数
# ============================================================

def safe_float(value, default=None):
    """安全转换为float"""
    if value is None:
        return default
    if isinstance(value, (int, float, np.integer, np.floating)):
        if pd.isna(value):
            return default
        return float(value)
    if isinstance(value, str):
        s = value.strip().replace(',', '').replace('，', '').replace(' ', '')
        if not s:
            return default
        try:
            return float(s)
        except (ValueError, TypeError):
            return default
    return default


def safe_int(value, default=None):
    """安全转换为int"""
    f = safe_float(value, default)
    if f is None:
        return default
    return int(f)


def safe_str(value):
    """安全转换为字符串"""
    if value is None or pd.isna(value):
        return ''
    return str(value).strip()


def is_note_or_empty(row):
    """判断行是否为备注行或空行"""
    if row is None:
        return True
    # 收集所有非空文本
    texts = []
    for v in row:
        s = safe_str(v)
        if s:
            texts.append(s)
    if not texts:
        return True  # 全空行
    # 检查是否包含备注关键词
    full = ' '.join(texts)
    note_kw = ['注：', '注:', '(1)', '(2)', '(3)', '(4)', '(5)', '(6)', '(7)',
               '该数据是', '表中省略', '说明', '备注', '附注', '合计', '总计']
    for kw in note_kw:
        if kw in full:
            return True
    return False


# ============================================================
# 第二部分：读取附件1
# 工作表1: "乡村的现有耕地" → 列: 地块名称 | 地块类型 | 地块面积/亩 | 说明
# 工作表2: "乡村种植的农作物" → 列: 作物编号 | 作物名称 | 作物类型 | 种植耕地 | 说明
# ============================================================

def read_attachment1(filepath):
    """读取附件1：地块信息 + 作物信息"""
    print(f"正在读取附件1: {filepath}")
    
    xls = pd.ExcelFile(filepath)
    sheet_names = xls.sheet_names
    print(f"  工作表: {sheet_names}")
    
    land_data = {}      # {地块名称: (地块类型, 面积)}
    crop_info = {}      # {作物编号: (作物名称, 作物类型, [(地块类型, 季次), ...])}
    
    # --- 工作表1: 乡村的现有耕地 ---
    sheet1 = sheet_names[0] if len(sheet_names) > 0 else None
    if sheet1:
        print(f"  处理工作表: '{sheet1}'")
        df1 = pd.read_excel(filepath, sheet_name=sheet1, header=None)
        n_rows = len(df1)
        print(f"    原始行数: {n_rows}")
        
        valid = 0
        for i in range(n_rows):
            row = df1.iloc[i].tolist()
            
            # 跳过空行和备注行
            if is_note_or_empty(row):
                continue
            
            # 跳过标题行(有"地块名称"关键词)
            r0 = safe_str(row[0])
            if '地块名称' in r0 or '地块' not in r0 and '名称' in r0:
                continue
            
            land_id = r0                           # 如 A1, B2, ...
            land_type = safe_str(row[1])           # 如 平旱地, 梯田, ...
            land_area = safe_float(row[2])         # 如 80, 55, ...
            
            if land_id and land_type and land_area is not None and land_area > 0:
                land_data[land_id] = (land_type, land_area)
                valid += 1
        
        print(f"    有效地块: {valid} 个")
    
    # --- 工作表2: 乡村种植的农作物 ---
    sheet2 = sheet_names[1] if len(sheet_names) > 1 else None
    if sheet2:
        print(f"  处理工作表: '{sheet2}'")
        df2 = pd.read_excel(filepath, sheet_name=sheet2, header=None)
        n_rows = len(df2)
        print(f"    原始行数: {n_rows}")
        
        valid = 0
        for i in range(n_rows):
            row = df2.iloc[i].tolist()
            
            # 跳过空行和备注行
            if is_note_or_empty(row):
                continue
            
            # 跳过标题行
            r0 = safe_str(row[0])
            if '作物编号' in r0 or '编号' == r0:
                continue
            
            crop_id = safe_int(row[0])             # 如 1, 2, ...
            crop_name = safe_str(row[1])           # 如 黄豆, 黑豆, ...
            crop_type = safe_str(row[2])           # 如 粮食（豆类）, 蔬菜, ...
            land_str = safe_str(row[3])            # 如 "平旱地\n梯田\n山坡地"
            
            if crop_id is None or crop_id <= 0 or not crop_name:
                continue
            
            # 解析种植耕地字段：格式如 "平旱地\n梯田\n山坡地" 或 "水浇地    第一季"
            # 需要解析出 (地块类型, 季次) 的组合
            allowed_combos = parse_land_constraint(land_str)
            
            crop_info[crop_id] = (crop_name, crop_type, allowed_combos)
            valid += 1
        
        print(f"    有效作物: {valid} 种")
    
    print(f"\n  总计: 地块 {len(land_data)} 个, 作物 {len(crop_info)} 种")
    return land_data, crop_info


def parse_land_constraint(land_str):
    """
    解析种植耕地约束字符串，返回 [(地块类型, 季次), ...] 列表
    
    示例:
    "平旱地\n梯田\n山坡地" → [('平旱地', '单季'), ('梯田', '单季'), ('山坡地', '单季')]
    "水浇地    第一季\n普通大棚  第一季\n智慧大棚  第一季、第二季" → 
        [('水浇地', '第一季'), ('普通大棚', '第一季'), ('智慧大棚', '第一季'), ('智慧大棚', '第二季')]
    "水浇地    第二季" → [('水浇地', '第二季')]
    "普通大棚  第二季" → [('普通大棚', '第二季')]
    """
    if not land_str:
        return []
    
    # 按换行分割
    lines = [l.strip() for l in land_str.replace('\n', '\n').split('\n') if l.strip()]
    
    result = []
    for line in lines:
        # 分离地块类型和季次
        # 格式: "水浇地    第一季" 或 "水浇地"
        parts = line.split()
        if len(parts) == 0:
            continue
        
        land_type = parts[0]
        
        if len(parts) >= 2:
            # 有季次信息，如 "第一季"、"第二季"、"第一季、第二季"
            season_part = ' '.join(parts[1:])
            # 分割 "第一季、第二季"
            seasons = season_part.replace('、', ',').replace('，', ',').split(',')
            for s in seasons:
                s = s.strip()
                if s in ['第一季', '第二季', '单季']:
                    result.append((land_type, s))
        else:
            # 只有地块类型，默认单季（平旱地、梯田、山坡地、水浇地单季种水稻）
            result.append((land_type, '单季'))
    
    return result


# ============================================================
# 第三部分：读取附件2
# 工作表1: "2023年的农作物种植情况" → 列: 种植地块 | 作物编号 | 作物名称 | 作物类型 | 种植面积/亩 | 种植季次
# 工作表2: "2023年统计的相关数据" → 列: 序号 | 作物编号 | 作物名称 | 地块类型 | 种植季次 | 亩产量/斤 | 种植成本/(元/亩) | 销售单价/(元/斤)
# ============================================================

def read_attachment2(filepath):
    """读取附件2：2023年种植情况 + 统计数据"""
    print(f"\n正在读取附件2: {filepath}")
    
    xls = pd.ExcelFile(filepath)
    sheet_names = xls.sheet_names
    print(f"  工作表: {sheet_names}")
    
    plant_2023 = []      # [(地块, 作物编号, 作物名称, 作物类型, 面积, 季次), ...]
    stats_raw = []       # [(序号, 作物编号, 作物名称, 地块类型, 季次, 亩产量, 成本, 售价区间), ...]
    
    # --- 工作表1: 2023年的农作物种植情况 ---
    sheet1 = sheet_names[0] if len(sheet_names) > 0 else None
    if sheet1:
        print(f"  处理工作表: '{sheet1}'")
        df1 = pd.read_excel(filepath, sheet_name=sheet1, header=None)
        n_rows = len(df1)
        print(f"    原始行数: {n_rows}")
        
        valid = 0
        for i in range(n_rows):
            row = df1.iloc[i].tolist()
            
            if is_note_or_empty(row):
                continue
            
            r0 = safe_str(row[0])
            if '种植地块' in r0 or '地块' in r0 and '种植' in r0:
                continue
            
            land = r0                              # 如 A1, D1, E15, ...
            crop_id = safe_int(row[1])             # 如 6, 20, 38, ...
            crop_name = safe_str(row[2])           # 如 小麦, 土豆, ...
            crop_type = safe_str(row[3])           # 如 粮食, 蔬菜, ...
            area = safe_float(row[4])              # 如 80, 0.6, ...
            season = safe_str(row[5])              # 如 单季, 第一季, 第二季
            
            if land and crop_id is not None and crop_id > 0 and area is not None:
                plant_2023.append((land, crop_id, crop_name, crop_type, area, season))
                valid += 1
        
        print(f"    有效种植记录: {valid} 条")
    
    # --- 工作表2: 2023年统计的相关数据 ---
    sheet2 = sheet_names[1] if len(sheet_names) > 1 else None
    if sheet2:
        print(f"  处理工作表: '{sheet2}'")
        df2 = pd.read_excel(filepath, sheet_name=sheet2, header=None)
        n_rows = len(df2)
        print(f"    原始行数: {n_rows}")
        
        valid = 0
        for i in range(n_rows):
            row = df2.iloc[i].tolist()
            
            if is_note_or_empty(row):
                continue
            
            r0 = safe_str(row[0])
            if '序号' in r0 or '作物编号' in r0:
                continue
            
            seq = safe_int(row[0])                 # 序号
            crop_id = safe_int(row[1])             # 作物编号
            crop_name = safe_str(row[2])           # 作物名称
            land_type = safe_str(row[3])           # 地块类型
            season = safe_str(row[4])              # 种植季次
            yield_per_mu = safe_float(row[5])      # 亩产量/斤
            cost_per_mu = safe_float(row[6])       # 种植成本/(元/亩)
            price_range = safe_str(row[7])         # 销售单价/(元/斤), 如 "2.50-4.00"
            
            if crop_id is not None and crop_id > 0 and yield_per_mu is not None:
                stats_raw.append((seq, crop_id, crop_name, land_type, season,
                                  yield_per_mu, cost_per_mu, price_range))
                valid += 1
        
        print(f"    有效统计记录: {valid} 条")
    
    print(f"\n  总计: 种植记录 {len(plant_2023)} 条, 统计记录 {len(stats_raw)} 条")
    return plant_2023, stats_raw


# ============================================================
# 第四部分：构建参数表
# ============================================================

def parse_price_range(price_str):
    """解析售价区间: "2.50-4.00" → (2.50, 4.00)"""
    if not price_str:
        return (0, 0)
    
    s = price_str.strip()
    # 统一分隔符
    for sep in ['-', '~', '至', '到', ',', '，']:
        if sep in s:
            parts = s.split(sep)
            if len(parts) >= 2:
                p1 = safe_float(parts[0], 0)
                p2 = safe_float(parts[1], 0)
                return (min(p1, p2), max(p1, p2))
    
    p = safe_float(s, 0)
    return (p, p)


def build_params(stats_raw):
    """
    从统计数据构建参数查找表
    key = (作物编号, 地块类型, 季次)
    """
    yield_table = {}     # key → 亩产量
    cost_table = {}      # key → 种植成本
    price_table = {}     # key → (最低价, 最高价)
    
    for record in stats_raw:
        seq, crop_id, crop_name, land_type, season, y, c, p = record
        
        if crop_id is None or crop_id <= 0:
            continue
        if not land_type or not season:
            continue
        if y is None or y <= 0:
            continue
        
        key = (crop_id, land_type, season)
        yield_table[key] = y
        cost_table[key] = (c if c is not None else 0)
        price_table[key] = parse_price_range(p)
    
    return yield_table, cost_table, price_table


# ============================================================
# 第五部分：问题1 - 确定性优化
# ============================================================

def solve_problem1(land_data, crop_info, yield_table, cost_table, price_table):
    """问题1：确定性线性规划"""
    print("\n" + "="*60)
    print("问题1：确定性优化")
    print("="*60)
    
    # 子问题(1): 超产完全滞销
    print("\n子问题(1): 超产完全滞销")
    total_profit_1 = 0
    plan_1 = {}
    
    for land_id, (land_type, area) in land_data.items():
        best_profit = -float('inf')
        best_choice = None
        
        # 遍历该地块类型可种的所有作物
        for (cid, lt, season), y in yield_table.items():
            if lt != land_type:
                continue
            if y <= 0:
                continue
            
            c = cost_table.get((cid, lt, season), 0)
            p_low, p_high = price_table.get((cid, lt, season), (0, 0))
            p_mid = (p_low + p_high) / 2
            
            revenue = p_mid * y * area
            profit = revenue - c * area
            
            if profit > best_profit:
                best_profit = profit
                best_choice = (cid, season, area, profit)
        
        if best_choice:
            plan_1[land_id] = best_choice
            total_profit_1 += best_choice[3]
    
    print(f"  总收益: {total_profit_1:,.2f} 元")
    print(f"  种植地块: {len(plan_1)} 个")
    
    # 子问题(2): 超产50%折价
    print("\n子问题(2): 超产50%折价出售")
    total_profit_2 = 0
    plan_2 = {}
    discount = 0.5
    
    for land_id, (land_type, area) in land_data.items():
        best_profit = -float('inf')
        best_choice = None
        
        for (cid, lt, season), y in yield_table.items():
            if lt != land_type or y <= 0:
                continue
            
            c = cost_table.get((cid, lt, season), 0)
            p_low, p_high = price_table.get((cid, lt, season), (0, 0))
            p_mid = (p_low + p_high) / 2
            
            total_yield = y * area
            expected_sales = total_yield * 0.8
            excess = max(0, total_yield - expected_sales)
            
            revenue = p_mid * expected_sales + p_mid * discount * excess
            profit = revenue - c * area
            
            if profit > best_profit:
                best_profit = profit
                best_choice = (cid, season, area, profit)
        
        if best_choice:
            plan_2[land_id] = best_choice
            total_profit_2 += best_choice[3]
    
    print(f"  总收益: {total_profit_2:,.2f} 元")
    print(f"  种植地块: {len(plan_2)} 个")
    
    return (total_profit_1, plan_1), (total_profit_2, plan_2)


# ============================================================
# 第六部分：问题2 - 蒙特卡洛 + CVaR
# ============================================================

def solve_problem2(land_data, crop_info, yield_table, cost_table, price_table,
                   n_scenarios=200, risk_weight=0.5, alpha=0.95):
    """问题2：不确定性 + CVaR风险控制"""
    print("\n" + "="*60)
    print("问题2：不确定性 + CVaR风险控制")
    print("="*60)
    
    np.random.seed(42)
    
    print(f"  生成 {n_scenarios} 个场景...")
    scenarios = []
    
    for _ in range(n_scenarios):
        sc = {}
        for key, base_yield in yield_table.items():
            cid, lt, season = key
            # 产量波动 ±15%
            sc_yield = max(0, np.random.normal(base_yield, base_yield * 0.10))
            
            p_low, p_high = price_table.get(key, (0, 0))
            base_price = (p_low + p_high) / 2 if (p_low + p_high) > 0 else 0
            sc_price = np.random.normal(base_price, base_price * 0.12) if base_price > 0 else 0
            sc_price = max(p_low * 0.7, min(p_high * 1.3, sc_price)) if base_price > 0 else 0
            
            sales_factor = np.random.uniform(0.7, 1.3)
            sc[key] = (sc_yield, sc_price, sales_factor)
        scenarios.append(sc)
    
    print(f"  风险权重λ={risk_weight}, 置信水平={alpha}")
    plan = {}
    
    for land_id, (land_type, area) in land_data.items():
        best_score = -float('inf')
        best_crop = None
        
        for key, base_yield in yield_table.items():
            cid, lt, season = key
            if lt != land_type or base_yield <= 0:
                continue
            
            profits = []
            for sc in scenarios:
                if key in sc:
                    sc_yield, sc_price, sales_factor = sc[key]
                    total_yield = sc_yield * area
                    base_cost = cost_table.get(key, 0) * area * 1.05
                    
                    expected_sales = total_yield * sales_factor
                    excess = max(0, total_yield - expected_sales)
                    revenue = sc_price * expected_sales + sc_price * 0.5 * excess
                    profits.append(revenue - base_cost)
            
            if len(profits) == 0:
                continue
            
            profits = np.array(profits)
            expected = np.mean(profits)
            var_idx = int(len(profits) * (1 - alpha))
            cvar = np.mean(np.sort(profits)[:max(1, var_idx)])
            
            score = risk_weight * expected + (1 - risk_weight) * cvar
            
            if score > best_score:
                best_score = score
                best_crop = (cid, season, area, expected, cvar)
        
        if best_crop:
            plan[land_id] = best_crop
    
    # 全局评估
    all_profits = []
    for sc in scenarios:
        total = 0
        for land_id, (cid, season, area, _, _) in plan.items():
            lt = land_data[land_id][0]
            key = (cid, lt, season)
            if key in sc:
                sc_yield, sc_price, sales_factor = sc[key]
                total_yield = sc_yield * area
                base_cost = cost_table.get(key, 0) * area * 1.05
                expected_sales = total_yield * sales_factor
                excess = max(0, total_yield - expected_sales)
                revenue = sc_price * expected_sales + sc_price * 0.5 * excess
                total += revenue - base_cost
        all_profits.append(total)
    
    all_profits = np.array(all_profits)
    expected = np.mean(all_profits)
    var_idx = int(len(all_profits) * (1 - alpha))
    cvar = np.mean(np.sort(all_profits)[:max(1, var_idx)])
    
    print(f"\n  结果:")
    print(f"    期望收益: {expected:,.2f} 元")
    print(f"    VaR({alpha}): {np.percentile(all_profits, (1-alpha)*100):,.2f} 元")
    print(f"    CVaR({alpha}): {cvar:,.2f} 元")
    print(f"    标准差: {np.std(all_profits):,.2f} 元")
    
    return plan, expected, cvar, scenarios


# ============================================================
# 第七部分：问题3 - 替代/互补 + 内生联动
# ============================================================

def solve_problem3(land_data, crop_info, yield_table, cost_table, price_table):
    """问题3：作物替代性/互补性 + 价格-销量-成本内生联动"""
    print("\n" + "="*60)
    print("问题3：替代/互补 + 内生联动")
    print("="*60)
    
    all_crop_ids = sorted(set(cid for (cid, _, _) in yield_table.keys()))
    n_crops = max(all_crop_ids)
    
    # 构建替代矩阵
    print("  构建替代效应矩阵...")
    S = np.zeros((n_crops + 1, n_crops + 1))
    
    bean_groups = [[1, 2, 3, 4, 5], [17, 18, 19]]
    grain_group = list(range(6, 16))
    veg_group = list(range(20, 38))
    fungi_group = [38, 39, 40, 41]
    
    for group in bean_groups + [grain_group, veg_group, fungi_group]:
        for i in group:
            for j in group:
                if i != j and i <= n_crops and j <= n_crops:
                    S[i][j] = 0.4
    
    # 构建互补矩阵
    print("  构建互补效应矩阵...")
    C = np.zeros((n_crops + 1, n_crops + 1))
    
    all_beans = [1, 2, 3, 4, 5, 17, 18, 19]
    for i in all_beans:
        for j in grain_group:
            if i <= n_crops and j <= n_crops:
                C[i][j] = C[j][i] = -0.05
    
    # 构建协方差矩阵
    print("  构建协方差矩阵...")
    cov = np.eye(n_crops + 1) * 0.15
    for i, j in product(range(1, n_crops + 1), repeat=2):
        if i != j:
            for group in bean_groups + [grain_group, veg_group, fungi_group]:
                if i in group and j in group:
                    cov[i][j] = 0.08
    
    # 优化
    print("  执行优化...")
    plan = {}
    areas_by_crop = {}
    
    for land_id, (land_type, area) in land_data.items():
        best_profit = -float('inf')
        best_choice = None
        
        for (cid, lt, season), base_yield in yield_table.items():
            if lt != land_type or base_yield <= 0:
                continue
            
            key = (cid, lt, season)
            y = base_yield
            base_cost = cost_table.get(key, 0)
            p_low, p_high = price_table.get(key, (0, 0))
            p_mid = (p_low + p_high) / 2
            
            # 互补效应修正成本
            complement_factor = 1.0
            total_planted = sum(areas_by_crop.values())
            if total_planted > 0:
                for other_cid, other_area in areas_by_crop.items():
                    if other_cid <= n_crops and cid <= n_crops:
                        complement_factor += C[cid][other_cid] * (other_area / total_planted)
            
            # 规模效应
            scale_factor = (area / 50) ** (-0.1)
            effective_cost = base_cost * complement_factor * scale_factor
            effective_cost = max(effective_cost, base_cost * 0.5)
            
            # 替代效应修正销量
            total_yield = y * area
            base_demand = total_yield * 0.8
            effective_demand = base_demand
            for other_cid, other_area in areas_by_crop.items():
                if other_cid <= n_crops and cid <= n_crops:
                    effective_demand += S[cid][other_cid] * other_area * 0.05
            
            revenue = p_mid * min(total_yield, effective_demand)
            profit = revenue - effective_cost * area
            
            if profit > best_profit:
                best_profit = profit
                best_choice = (cid, season, area, profit)
        
        if best_choice:
            plan[land_id] = best_choice
            cid = best_choice[0]
            areas_by_crop[cid] = areas_by_crop.get(cid, 0) + area
    
    total_area = sum(a for _, _, a, _ in plan.values())
    print(f"\n  结果:")
    print(f"    总种植面积: {total_area:.2f} 亩")
    print(f"    涉及作物: {len(areas_by_crop)} 种")
    
    sorted_crops = sorted(areas_by_crop.items(), key=lambda x: x[1], reverse=True)
    print(f"    Top5作物:")
    for cid, a in sorted_crops[:5]:
        name = crop_info.get(cid, ('?', '?'))[0]
        print(f"      {name}(#{cid}): {a:.2f} 亩")
    
    return plan, areas_by_crop, S, C, cov


# ============================================================
# 第八部分：主程序
# ============================================================

def main():
    """主程序入口"""
    print("="*70)
    print("  2024C 数学建模 - 农作物种植优化系统")
    print("  根据附件实际结构精准解析")
    print("="*70)
    print(f"  附件1: {ATTACHMENT1_PATH}")
    print(f"  附件2: {ATTACHMENT2_PATH}")
    print("="*70)
    
    # 1. 读取附件1 —— 地块和作物信息
    print("\n>>> 步骤1: 读取附件1")
    land_data, crop_info = read_attachment1(ATTACHMENT1_PATH)
    
    if not land_data:
        print("⚠ 警告: 未读取到地块数据！")
    if not crop_info:
        print("⚠ 警告: 未读取到作物数据！")
    
    # 2. 读取附件2 —— 2023种植和统计数据
    print("\n>>> 步骤2: 读取附件2")
    plant_2023, stats_raw = read_attachment2(ATTACHMENT2_PATH)
    
    if not stats_raw:
        print("⚠ 警告: 未读取到统计数据！")
    
    # 3. 构建参数表
    print("\n>>> 步骤3: 构建参数表")
    yield_table, cost_table, price_table = build_params(stats_raw)
    print(f"  产量参数: {len(yield_table)} 条")
    print(f"  成本参数: {len(cost_table)} 条")
    print(f"  价格参数: {len(price_table)} 条")
    
    if len(yield_table) == 0:
        print("⚠ 无法构建参数表，请检查附件2数据格式")
        return None
    
    # 4. 问题1
    print("\n>>> 步骤4: 求解问题1")
    (profit_1a, plan_1a), (profit_1b, plan_1b) = solve_problem1(
        land_data, crop_info, yield_table, cost_table, price_table
    )
    
    # 5. 问题2
    print("\n>>> 步骤5: 求解问题2")
    plan_2, exp_2, cvar_2, _ = solve_problem2(
        land_data, crop_info, yield_table, cost_table, price_table,
        n_scenarios=200
    )
    
    # 6. 问题3
    print("\n>>> 步骤6: 求解问题3")
    plan_3, areas_3, S_3, C_3, cov_3 = solve_problem3(
        land_data, crop_info, yield_table, cost_table, price_table
    )
    
    # 汇总
    print("\n" + "="*70)
    print("  汇总结果")
    print("="*70)
    print(f"  问题1-子问题(1) 总收益: {profit_1a:,.2f} 元")
    print(f"  问题1-子问题(2) 总收益: {profit_1b:,.2f} 元")
    print(f"  问题2-期望收益: {exp_2:,.2f} 元")
    print(f"  问题2-CVaR(95%): {cvar_2:,.2f} 元")
    print(f"  问题3-涉及作物数: {len(areas_3)} 种")
    
    return {
        'land_data': land_data,
        'crop_info': crop_info,
        'yield_table': yield_table,
        'cost_table': cost_table,
        'price_table': price_table,
        'p1a': (profit_1a, plan_1a),
        'p1b': (profit_1b, plan_1b),
        'p2': (plan_2, exp_2, cvar_2),
        'p3': (plan_3, areas_3, S_3, C_3, cov_3),
    }


if __name__ == '__main__':
    results = main()