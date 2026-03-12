# scripts/cluster_mcts_strategies_v2.py
import json
import pandas as pd
from pathlib import Path
from sklearn.cluster import KMeans
import numpy as np
import matplotlib.pyplot as plt # 选装，用于可视化

JSON_PATH = Path("outputs/harvest/mcts_patterns_data.json")

def extract_features():
    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    features = []
    seeds = []
    for c in data:
        actions = c['first_cycle_actions'][:10]
        counts = {'R': 0, 'C': 0, 'T': 0, 'B': 0, 'M': 0}
        for a in actions:
            code = 'R' if a['mode'] == 'top' else a['action_kind'][0]
            if code in counts: counts[code] += 1
        features.append([counts['R'], counts['C'], counts['T'], counts['B'], counts['M']])
        seeds.append(c['seed'])
    return np.array(features), seeds, data

def find_optimal_k(X):
    print("🧪 正在探测数据的自然分类边界 (1-10)...")
    sse = []
    for k in range(1, 11):
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        kmeans.fit(X)
        sse.append(kmeans.inertia_)
    
    # 自动计算斜率变化最大的点 (简易手肘判定)
    deltas = np.diff(sse)
    double_deltas = np.diff(deltas)
    optimal_k = np.argmax(double_deltas) + 2 # 数学上的拐点近似
    return optimal_k, sse

def run_natural_clustering():
    X, seeds, raw_data = extract_features()
    
    # 第一步：让数据自己说话，找到最优分类数
    k, sse = find_optimal_k(X)
    print(f"✨ 数学分析结果：这批高分对局中，天然存在 {k} 种核心战术流派。\n")
    
    # 第二步：按自然分类数进行聚类
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10).fit(X)
    labels = kmeans.labels_
    
    results = pd.DataFrame(X, columns=['拿资源(R)','征服(C)','征收(T)','建筑(B)','奇观(M)'])
    results['label'] = labels
    results['seed'] = seeds
    
    print(f"==========================================")
    print(f"📊 MCTS 行为聚类报告 (自然演化版)")
    print(f"==========================================\n")
    
    for i in range(k):
        cluster_data = results[results['label'] == i]
        print(f"人格风格 #{i}:")
        print(f" - 发现样本数: {len(cluster_data)}")
        print(f" - 战术偏好: R={cluster_data['拿资源(R)'].mean():.1f}, C={cluster_data['征服(C)'].mean():.1f}, T={cluster_data['征收(T)'].mean():.1f}, B={cluster_data['建筑(B)'].mean():.1f}, M={cluster_data['奇观(M)'].mean():.1f}")
        
        sample_seeds = cluster_data.sort_index().head(3)['seed'].tolist()
        print(f" - 典型种子示例: {sample_seeds}")
        print("-" * 40)

if __name__ == "__main__":
    run_natural_clustering()