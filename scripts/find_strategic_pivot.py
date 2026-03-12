# scripts/find_strategic_pivot.py
import json
from pathlib import Path
import pandas as pd

JSON_PATH = Path("outputs/harvest/mcts_patterns_data.json")

def find_pivot():
    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    stats = []
    for c in data:
        # 记录 18 分局的每一个关键节点
        if c['total_score'] >= 18:
            first_conq_turn = next((a['turn'] for a in c['first_cycle_actions'] if a['action_kind'] == 'Conquest'), 99)
            first_monu_turn = next((a['turn'] for a in c['first_cycle_actions'] if a['action_kind'] == 'Build_Monument'), 99)
            stats.append({
                "score": c['total_score'],
                "first_conq": first_conq_turn,
                "first_monu": first_monu_turn,
                "regions": c['score_breakdown']['regions']
            })
    
    df = pd.DataFrame(stats)
    print("\n📊 18分神级局的“节奏指纹”分析：")
    print(f"平均第一次【征服】发生在第 {df['first_conq'].mean():.2f} 手")
    print(f"平均第一次【奇观施工】发生在第 {df['first_monu'].mean():.2f} 手")
    print(f"最终平均占领地区数: {df['regions'].mean():.2f}")

if __name__ == "__main__":
    find_pivot()