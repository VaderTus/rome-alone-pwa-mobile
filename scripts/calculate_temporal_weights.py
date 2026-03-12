# scripts/calculate_temporal_weights.py
import json
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.linear_model import LinearRegression

PROJECT_ROOT = Path(__file__).resolve().parents[1]
JSON_PATH = PROJECT_ROOT / "outputs" / "full_knowledge" / "full_mcts_data.json"

def calculate_matrix():
    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 提取特征
    records = []
    for case in data:
        if case['lost']: continue
        final_score = case['score']
        for step in case['history']:
            records.append({
                "turn": step['turn'],
                "action": step['action'],
                "mode": step['mode'],
                "final_score": final_score
            })
    
    df = pd.DataFrame(records)
    
    print("📊 正在通过回归分析，计算 21 个回合的动态战术权重...")
    
    # 我们分三个阶段（早、中、晚）计算每个动作对最终分数的贡献度（相关系数）
    matrix = {}
    for turn in range(1, 22):
        turn_data = df[df['turn'] == turn]
        # 对该回合的所有动作进行 One-hot 编码
        encoded = pd.get_dummies(turn_data[['action', 'mode']])
        # 计算每个动作与最终分数的线性相关性
        correlations = encoded.corrwith(turn_data['final_score'])
        matrix[turn] = correlations.to_dict()

    # 转化为整洁的矩阵
    res_df = pd.DataFrame(matrix).T.fillna(0)
    res_df.to_csv(PROJECT_ROOT / "data/temporal_priority_matrix.csv")
    print(f"✅ 战术矩阵已生成！保存至: data/temporal_priority_matrix.csv")
    
    # 打印前 5 回合的优先级发现
    print("\n💡 专家发现：前 5 回合与最终高分最相关的动作：")
    for t in range(1, 6):
        top_act = res_df.loc[t].idxmax()
        print(f"  T{t:02d}: {top_act}")

if __name__ == "__main__":
    calculate_matrix()