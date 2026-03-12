# scripts/cluster_mcts_strategies.py
import json
import pandas as pd
from pathlib import Path
from sklearn.cluster import KMeans
import numpy as np

JSON_PATH = Path("outputs/harvest/mcts_patterns_data.json")

def extract_features():
    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    features = []
    seeds = []
    
    for c in data:
        # 我们只分析前 10 手的动作分布
        actions = c['first_cycle_actions'][:10]
        counts = {
            'R': 0, # Resource
            'C': 0, # Conquest
            'T': 0, # Tribute
            'B': 0, # Building
            'M': 0  # Monument
        }
        for a in actions:
            code = 'R' if a['mode'] == 'top' else a['action_kind'][0]
            if code in counts: counts[code] += 1
        
        # 将频率转化为特征向量
        features.append([counts['R'], counts['C'], counts['T'], counts['B'], counts['M']])
        seeds.append(c['seed'])
        
    return np.array(features), seeds, data

def run_clustering(n_clusters=5):
    X, seeds, raw_data = extract_features()
    
    # 使用 K-Means 将 10000 局游戏自动分为 5 类
    kmeans = KMeans(n_clusters=n_clusters, random_state=42).fit(X)
    labels = kmeans.labels_
    
    results = pd.DataFrame(X, columns=['R','C','T','B','M'])
    results['label'] = labels
    results['seed'] = seeds
    
    print(f"==========================================")
    print(f"📊 MCTS 行为聚类分析报告 (发现 {n_clusters} 种潜在大脑)")
    print(f"==========================================\n")
    
    for i in range(n_clusters):
        cluster_data = results[results['label'] == i]
        print(f"人格风格 #{i}:")
        print(f" - 样本数: {len(cluster_data)}")
        print(f" - 典型动作(前10手): Resource={cluster_data['R'].mean():.1f}, Conquest={cluster_data['C'].mean():.1f}, Tribute={cluster_data['T'].mean():.1f}")
        
        # 找出该人格对应的高分 Seed 示例
        sample_seeds = cluster_data.sort_index().head(3)['seed'].tolist()
        print(f" - 匹配种子示例: {sample_seeds}")
        print("-" * 40)

if __name__ == "__main__":
    # 我们尝试挖掘 5 种人格
    run_clustering(n_clusters=5)