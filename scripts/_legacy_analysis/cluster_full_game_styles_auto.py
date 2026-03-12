# scripts/cluster_full_game_styles_final.py
import json
import pandas as pd
from pathlib import Path
from sklearn.cluster import KMeans
import numpy as np

JSON_PATH = Path("outputs/full_knowledge/full_mcts_data.json")

def extract_features():
    if not JSON_PATH.exists():
        print("❌ 错误：找不到全量数据文件，请先运行 harvest_full_knowledge.py")
        return None, None
        
    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    features = []
    metadata = []
    for c in data:
        if c['lost']: continue
        
        # 15 维特征向量 (3阶段 * 5动作)
        counts = []
        for stage in [c['history'][:7], c['history'][7:14], c['history'][14:21]]:
            s_counts = {'R':0, 'C':0, 'T':0, 'B':0, 'M':0}
            for act in stage:
                # 🛠️ 修正后的精准识别逻辑
                if act['mode'] == 'top': code = 'R'
                elif act['action'] == 'Conquest': code = 'C'
                elif act['action'] == 'Tribute': code = 'T'
                elif act['action'] == 'Build_Building': code = 'B'
                elif act['action'] == 'Build_Monument': code = 'M'
                else: code = 'R'
                
                s_counts[code] += 1
            counts.extend([s_counts['R'], s_counts['C'], s_counts['T'], s_counts['B'], s_counts['M']])
        
        features.append(counts)
        metadata.append({'seed': c['seed'], 'score': c['score']})
        
    return np.array(features), metadata

def find_best_k(X):
    print("🧪 正在重新探测自然分类边界 (1-10)...")
    sse = []
    for k in range(1, 11):
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        kmeans.fit(X)
        sse.append(kmeans.inertia_)
    
    deltas = np.diff(sse)
    double_deltas = np.diff(deltas)
    best_k = np.argmax(double_deltas) + 2 
    return best_k

def run_final_clustering():
    X, meta = extract_features()
    if X is None: return
    
    k = find_best_k(X)
    print(f"✨ 修正后发现：数据中存在 {k} 种核心战术基因。\n")
    
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10).fit(X)
    
    cols = [f"{s}_{a}" for s in ['P1','P2','P3'] for a in ['资源','征服','征收','建筑','奇观']]
    df = pd.DataFrame(X, columns=cols)
    df['style'] = kmeans.labels_
    df['score'] = [m['score'] for m in meta]
    df['seed'] = [m['seed'] for m in meta]

    print(f"==========================================")
    print(f"🌍 MCTS 全周期战术流派 - 终极聚类报告")
    print(f"==========================================\n")

    for i in range(k):
        style_data = df[df['style'] == i]
        print(f"人格风格 #{i} (占比 {len(style_data)/len(df)*100:.1f}%):")
        print(f" - 平均得分: {style_data['score'].mean():.2f}")
        
        # 描述该流派的“战术特征”
        p1_r = style_data['P1_资源'].mean()
        p2_c = style_data['P2_征服'].mean()
        p3_m = style_data['P3_奇观'].mean()
        print(f" - 行为指纹: 阶段1拿资源({p1_r:.1f}) | 阶段2征服({p2_c:.1f}) | 阶段3奇观({p3_m:.1f})")
        
        # 该流派的 18 分 Seed
        god_seeds = style_data[style_data['score'] >= 18]['seed'].head(3).tolist()
        if god_seeds: print(f" - 🏆 18分种子: {god_seeds}")
        print("-" * 40)

if __name__ == "__main__":
    run_final_clustering()