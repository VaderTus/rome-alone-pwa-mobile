# scripts/analyze_mcts_efficiency.py
from pathlib import Path
import json
import numpy as np

JSON_PATH = Path("outputs/harvest/mcts_patterns_data.json")

def analyze_efficiency():
    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    perfect_cases = [c for c in data if c['total_score'] >= 18]
    
    print(f"📊 正在分析 {len(perfect_cases)} 个 18 分神级局的资源效率...\n")
    
    regions = []
    monus = []
    
    for c in perfect_cases:
        regions.append(c['score_breakdown']['regions'])
        monus.append(c['score_breakdown']['monuments'])
        
    print(f"平均占领地区: {np.mean(regions):.2f}")
    print(f"平均修成奇观数: {np.mean([len(c['monuments_completed']) for c in perfect_cases]):.2f}")
    
    # 统计 18 分局最常修完的奇观 Top 3
    all_monus = []
    for c in perfect_cases:
        all_monus.extend(c['monuments_completed'])
    from collections import Counter
    print(f"18分局最爱修的奇观: {Counter(all_monus).most_common(3)}")

if __name__ == "__main__":
    analyze_efficiency()