import numpy as np

def entropy_weight_method(data):
    """
    熵权法核心计算函数
    :param data: 原始数据矩阵 (m x n)，m为样本数，n为指标数
    :return: 各指标的权重向量
    """
    m, n = data.shape
    
    # 1. 数据非负化与归一化（消除量纲影响，防止对数计算报错）
    # 公式：P_ij = X_ij / sum(X_ij)
    # 为防止出现0导致log(0)报错，通常加一个极小值（如 1e-8）
    data_safe = data + 1e-8 
    P = data_safe / np.sum(data_safe, axis=0)
    
    # 2. 计算各指标的信息熵 E
    # 公式：E_j = -k * sum(P_ij * ln(P_ij))，其中 k = 1 / ln(m)
    k = 1.0 / np.log(m)
    # 计算信息熵 (注意：0 * ln(0) 定义为 0，numpy 会自动处理)
    E = -k * np.sum(P * np.log(P), axis=0)
    
    # 3. 计算各指标的差异系数（冗余度）D
    # 公式：D_j = 1 - E_j
    D = 1.0 - E
    
    # 4. 计算各指标的权重 W
    # 公式：W_j = D_j / sum(D_j)
    W = D / np.sum(D)
    
    return W

# ================= 案例演示：评估5名员工的综合能力 =================
# 假设原始数据：3个指标（业绩得分、出勤天数、项目完成数）
# 注意：熵权法要求所有指标必须是“正向指标”（数值越大越好）
raw_data = np.array([
    [85, 22, 4],  # 员工1
    [92, 25, 6],  # 员工2
    [78, 21, 3],  # 员工3
    [95, 26, 7],  # 员工4
    [88, 24, 5]   # 员工5
])

# 执行熵权法计算
weights = entropy_weight_method(raw_data)

# 输出结果
indicator_names = ["业绩得分", "出勤天数", "项目完成数"]
print("=== 熵权法计算结果 ===")
for name, w in zip(indicator_names, weights):
    print(f"指标 [{name}] 的客观权重: {w:.4f}")