# scripts/cluster_full_game_styles.py
import json
import pandas as pd
from pathlib import Path
from sklearn.cluster import KMeans
import numpy as np

JSON_PATH = Path("outputs/full_knowledge/full_mcts_data.json")

def analyze_natural_styles(k=3):
    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 提取特征：我们要看全 21 回合的动作分布
    features = []
    seeds = []
    for c in data:
        if c['lost']: continue # 排除失败对局
        
        # 将 21 回合分为三段，每段记录 R,C,T,B,M 的频次 (15维特征)
        counts = []
        for stage in [c['history'][:7], c['history'][7:14], c['history'][14:21]]:
            s_counts = {'R':0, 'C':0, 'T':0, 'B':0, 'M':0}
            for act in stage:
                code = 'R' if act['mode'] == 'top' else act['action'][0]
                if code in s_counts: s_counts[code] += 1
            counts.extend([s_counts['R'], s_counts['C'], s_counts['T'], s_counts['B'], s_counts['M']])
        
        features.append(counts)
        seeds.append(c['seed'])

    X = np.array(features)
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10).fit(X)
    
    results = pd.DataFrame(X, columns=[f"{s}_{a}" for s in ['P1','P2','P3'] for a in ['R','C','T','B','M']])
    results['style'] = kmeans.labels_
    results['seed'] = seeds
    results['score'] = [c['score'] for c in data if not c['lost']]

    print(f"==========================================")
    print(f"🧠 MCTS 全时段战术人格自动发现 (K={k})")
    print(f"==========================================\n")

    for i in range(k):
        style_data = results[results['style'] == i]
        print(f"人格类型 #{i}:")
        print(f" - 样本数: {len(style_data)}")
        print(f" - 平均分: {style_data['score'].mean():.2f}")
        # 打印各阶段最显著的动作特征
        p1_r = style_data['P1_R'].mean()
        p2_m = style_data['P2_M'].mean()
        p3_m = style_data['P3_M'].mean()
        print(f" - 战术标签: 阶段1拿资源={p1_r:.1f} | 阶段2造奇观={p2_m:.1f} | 阶段3造奇观={p3_m:.1f}")
        
        # 看看这种流派的 18 分 Seed 是哪些
        god_seeds = style_data[style_data['score'] >= 18]['seed'].head(3).tolist()
        print(f" - 18分种子示例: {god_seeds}")
        print("-" * 40)

if __name__ == "__main__":
    analyze_natural_styles(k=3) # 先尝试分 3 类主干