import numpy as np

def ahp_analysis(matrix):
    """AHP 核心计算函数：返回权重和一致性比率CR"""
    n = matrix.shape[0]
    eigenvalues, eigenvectors = np.linalg.eig(matrix)
    max_index = np.argmax(np.real(eigenvalues))
    max_eigenvalue = np.real(eigenvalues[max_index])
    max_eigenvector = np.real(eigenvectors[:, max_index])
    weights = max_eigenvector / np.sum(max_eigenvector)
    
    # 随机一致性指标 RI (1-9阶)
    RI_dict = {1: 0.00, 2: 0.00, 3: 0.58, 4: 0.90, 5: 1.12, 
               6: 1.24, 7: 1.32, 8: 1.41, 9: 1.45}
    
    CI = (max_eigenvalue - n) / (n - 1)
    RI = RI_dict[n]
    CR = CI / RI if RI != 0 else 0
    return weights, CR

# ================= 1. 准则层：计算各指标权重 =================
criteria_names = ["景色", "费用", "食宿"]
criteria_matrix = np.array([
    [1,   3,   5],
    [1/3, 1,   2],
    [1/5, 1/2, 1]
])
criteria_weights, criteria_CR = ahp_analysis(criteria_matrix)

# ================= 2. 方案层：针对每个准则，对方案进行打分 =================
scheme_names = ["苏杭", "北戴河", "桂林"]

# 针对“景色”的判断矩阵 (桂林景色最好，苏杭次之，北戴河一般)
matrix_scenery = np.array([
    [1,   2,   1/3],
    [1/2, 1,   1/4],
    [3,   4,   1]
])

# 针对“费用”的判断矩阵 (北戴河最便宜，苏杭次之，桂林最贵)
matrix_cost = np.array([
    [1,   2,   1/3],
    [1/2, 1,   1/4],
    [3,   4,   1]
])

# 针对“食宿”的判断矩阵 (苏杭食宿最好，桂林次之，北戴河一般)
matrix_food = np.array([
    [1,   3,   2],
    [1/3, 1,   1/2],
    [1/2, 2,   1]
])

# 将方案层的判断矩阵放入列表，方便循环计算
scheme_matrices = [matrix_scenery, matrix_cost, matrix_food]
scheme_weights = []
scheme_CRs = []

for mat in scheme_matrices:
    w, cr = ahp_analysis(mat)
    scheme_weights.append(w)
    scheme_CRs.append(cr)

# 将方案层权重转换为 numpy 数组，方便后续矩阵乘法
scheme_weights = np.array(scheme_weights)

# ================= 3. 结果输出与综合排序 =================
print("=== 1. 准则层分析 ===")
for name, w, cr in zip(criteria_names, criteria_weights, [criteria_CR]):
    print(f"准则 [{name}] 权重: {w:.4f} (CR: {cr:.4f})")

print("\n=== 2. 方案层分析 ===")
for i, name in enumerate(criteria_names):
    print(f"在准则 [{name}] 下，各方案权重:")
    for j, s_name in enumerate(scheme_names):
        print(f"  - 方案 [{s_name}] 得分: {scheme_weights[i][j]:.4f}")
    print(f"  (该矩阵 CR: {scheme_CRs[i]:.4f})")

print("\n=== 3. 综合得分与最终排序 ===")
# 核心公式：综合得分 = 准则权重矩阵 × 方案层权重矩阵的转置
final_scores = np.dot(criteria_weights, scheme_weights)

for s_name, score in zip(scheme_names, final_scores):
    print(f"方案 [{s_name}] 的综合得分: {score:.4f}")

# 找出得分最高的方案
best_index = np.argmax(final_scores)
print(f"\n🏆 最终推荐方案: {scheme_names[best_index]}")