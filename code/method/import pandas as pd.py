import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns

# 读取数据文件
def load_data():
    """
    加载所有城市的空气质量数据
    """
    shanghai_df = pd.read_excel(r'C:\Users\UserPro\Downloads\上海空气质量.xlsx')
    london_df = pd.read_excel(r'C:\Users\UserPro\Downloads\伦敦空气质量.xlsx')
    beijing_df = pd.read_excel(r'C:\Users\UserPro\Downloads\北京空气质量.xlsx')
    washington_df = pd.read_excel(r'C:\Users\UserPro\Downloads\华盛顿空气质量.xlsx')
    
    # 为每个DataFrame添加城市标识
    shanghai_df['city'] = '上海'
    london_df['city'] = '伦敦'
    beijing_df['city'] = '北京'
    washington_df['city'] = '华盛顿'
    
    # 合并所有数据
    all_data = pd.concat([shanghai_df, london_df, beijing_df, washington_df], ignore_index=True)
    
    return all_data

def add_time_features(df):
    df = df.copy()
    df['date'] = pd.to_datetime(df['date'])
    df['year'] = df['date'].dt.year
    df['month'] = df['date'].dt.month
    df['day'] = df['date'].dt.day
    df['hour'] = df['date'].dt.hour
    df['season'] = df['month'].map({12: '冬季', 1: '冬季', 2: '冬季',
                                   3: '春季', 4: '春季', 5: '春季',
                                   6: '夏季', 7: '夏季', 8: '夏季',
                                   9: '秋季', 10: '秋季', 11: '秋季'})
    return df

def calculate_air_quality_stats(df):
    """
    计算空气质量统计指标
    """
    print("="*50)
    print("空气质量统计指标")
    print("="*50)
    
    # 全体数据统计
    print("\n【全体数据统计】")
    numeric_cols = ['pm10', 'pm2.5', 'SO2', 'O3', 'CO', 'CO2', 'NO2']
    print(df[numeric_cols].describe())
    
    # 按城市分组统计
    print("\n【按城市分组统计】")
    city_stats = df.groupby('city')[numeric_cols].agg(['mean', 'std', 'min', 'max', 'median']).round(2)
    print(city_stats)
    
    # 按月份分组统计
    print("\n【按月份分组统计PM2.5平均值】")
    monthly_pm25 = df.groupby(['month', 'city'])['pm2.5'].agg(['mean', 'count']).round(2)
    print(monthly_pm25)
    
    # 按季节分组统计
    print("\n【按季节分组统计主要污染物】")
    seasonal_stats = df.groupby(['season', 'city'])[['pm10', 'pm2.5', 'SO2']].mean().round(2)
    print(seasonal_stats)
    
    return city_stats, monthly_pm25, seasonal_stats

def analyze_pollutant_relationships(df):
    """
    分析污染物与气象变量之间的关系
    """
    print("\n" + "="*50)
    print("污染物关系分析")
    print("="*50)
    
    # 相关系数矩阵
    print("\n【污染物相关系数矩阵】")
    numeric_cols = ['pm10', 'pm2.5', 'SO2', 'O3', 'CO', 'CO2', 'NO2']
    corr_matrix = df[numeric_cols].corr()
    print(corr_matrix.round(3))
    
    # PM2.5和PM10的相关性分析
    pm_corr = np.corrcoef(df['pm2.5'], df['pm10'])[0, 1]
    print(f"\nPM2.5与PM10的相关系数: {pm_corr:.3f}")
    
    # 各城市污染物相关性对比
    print("\n【各城市PM2.5与PM10相关性】")
    for city in df['city'].unique():
        city_data = df[df['city'] == city]
        if len(city_data) > 1:
            corr = np.corrcoef(city_data['pm2.5'], city_data['pm10'])[0, 1] if len(city_data['pm2.5'].dropna()) > 1 else np.nan
            print(f"{city}: {corr:.3f}")
    
    return corr_matrix

def perform_regression_analysis(df):
    """
    执行简单的回归分析
    """
    print("\n" + "="*50)
    print("简单回归分析")
    print("="*50)
    
    from sklearn.linear_model import LinearRegression
    from sklearn.metrics import r2_score
    
    # PM2.5 对 PM10 的线性回归
    df_clean = df[['pm2.5', 'pm10']].dropna()
    if len(df_clean) > 1:
        X = df_clean[['pm10']]
        y = df_clean['pm2.5']
        
        model = LinearRegression()
        model.fit(X, y)
        y_pred = model.predict(X)
        r2 = r2_score(y, y_pred)
        
        print(f"PM2.5 对 PM10 回归:")
        print(f"  回归系数: {model.coef_[0]:.3f}")
        print(f"  截距: {model.intercept_:.3f}")
        print(f"  R² 得分: {r2:.3f}")
        
        # 各城市单独分析
        print("\n【各城市PM2.5-PM10回归分析】")
        for city in df['city'].unique():
            city_data = df[df['city'] == city][['pm2.5', 'pm10']].dropna()
            if len(city_data) > 1:
                X_city = city_data[['pm10']]
                y_city = city_data['pm2.5']
                
                model_city = LinearRegression()
                model_city.fit(X_city, y_city)
                y_pred_city = model_city.predict(X_city)
                r2_city = r2_score(y_city, y_pred_city)
                
                print(f"{city} - 斜率: {model_city.coef_[0]:.3f}, R²: {r2_city:.3f}")

def seasonal_analysis(df):
    """
    季节性分析
    """
    print("\n" + "="*50)
    print("季节性分析")
    print("="*50)
    
    # 按季节统计主要污染物
    seasonal_analysis = df.groupby(['season', 'city']).agg({
        'pm2.5': ['mean', 'std', 'max'],
        'pm10': ['mean', 'std', 'max'],
        'SO2': ['mean', 'std', 'max']
    }).round(2)
    
    print("\n【各季节各城市主要污染物统计】")
    print(seasonal_analysis)
    
    # 污染物季节变化趋势
    print("\n【各城市年均PM2.5浓度排名】")
    annual_pm25 = df.groupby('city')['pm2.5'].mean().sort_values(ascending=False)
    print(annual_pm25)

def visualize_results(df):
    """
    可视化结果（概念性）
    """
    print("\n" + "="*50)
    print("可视化分析结果（概念性）")
    print("="*50)
    
    print("建议生成以下图表：")
    print("1. 各城市PM2.5时间序列图")
    print("2. 污染物相关性热力图")
    print("3. 各城市污染物箱线图")
    print("4. PM2.5与PM10散点图及回归线")
    print("5. 按季节和城市的污染物浓度小提琴图")

def main():
    """
    主函数 - 执行完整的数据分析流程
    """
    print("开始空气质量数据分析...")
    
    # 加载数据
    df = load_data()
    print(f"数据加载完成，共 {len(df)} 条记录")
    
    # 添加时间特征
    df_with_time = add_time_features(df)
    
    # 计算统计指标
    city_stats, monthly_stats, seasonal_stats = calculate_air_quality_stats(df_with_time)
    
    # 分析污染物关系
    corr_matrix = analyze_pollutant_relationships(df_with_time)
    
    # 回归分析
    perform_regression_analysis(df_with_time)
    
    # 季节性分析
    seasonal_analysis(df_with_time)
    
    # 可视化建议
    visualize_results(df_with_time)
    
    print("\n" + "="*50)
    print("分析总结")
    print("="*50)
    print("1. 数据包含了4个城市的空气质量监测数据")
    print("2. 主要监测指标包括: PM2.5, PM10, SO2, O3, CO, CO2, NO2")
    print("3. 已完成按城市、月份、季节的统计分析")
    print("4. 完成了污染物间相关性分析和回归分析")
    print("5. 提供了可视化建议")

if __name__ == "__main__":
    main()