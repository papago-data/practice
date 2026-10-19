import numpy as np

def fuzzy_comprehensive_evaluation(R, W):
    """
    模糊综合评价核心计算函数
    :param R: 模糊评价矩阵 (m x n)，m为因素个数，n为评语等级个数
    :param W: 因素权重向量 (1 x m)
    :return: 综合评价结果向量 B (1 x n)
    """
    # 核心运算：权重向量与评价矩阵相乘 (B = W * R)
    B = np.dot(W, R)
    
    # 归一化处理，使结果总和为1
    B_normalized = B / np.sum(B)
    return B_normalized

# ================= 案例演示：某款手机的综合评价 =================
# 1. 确定评语集（评价等级）
# 评语集 V = {优秀, 良好, 一般, 较差}

# 2. 确定因素集与权重（权重之和需为1）
# 因素集 U = {性能, 价格, 售后服务}
W = np.array([0.4, 0.3, 0.3])  

# 3. 构建模糊评价矩阵 R
# 每一行代表一个因素在各个评语等级下的隶属度（通常由专家打分或统计得出）
R = np.array([
    [0.6, 0.3, 0.1, 0.0],  # "性能"被评为 优/良/中/差 的比例
    [0.2, 0.5, 0.2, 0.1],  # "价格"被评为 优/良/中/差 的比例
    [0.3, 0.4, 0.2, 0.1]   # "售后"被评为 优/良/中/差 的比例
])

# 4. 执行模糊综合评价
result = fuzzy_comprehensive_evaluation(R, W)

# 5. 输出结果
grade_names = ["优秀", "良好", "一般", "较差"]
print("=== 模糊综合评价结果 ===")
for grade, score in zip(grade_names, result):
    print(f"属于 [{grade}] 的隶属度: {score:.4f}")

# 根据最大隶属度原则得出最终结论
best_grade_index = np.argmax(result)
print(f"\n🏆 最终评价结论: {grade_names[best_grade_index]}")