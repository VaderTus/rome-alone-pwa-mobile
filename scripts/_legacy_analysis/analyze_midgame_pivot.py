# scripts/analyze_midgame_pivot.py
import json
import pandas as pd
from pathlib import Path
from collections import Counter

PROJECT_ROOT = Path(__file__).resolve().parents[1]
JSON_PATH = PROJECT_ROOT / "outputs" / "harvest" / "mcts_patterns_data.json"

def analyze_midgame():
    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 我们对比 18分局 (神级) 和 12分局 (平庸) 在中场的表现
    perfect_cases = [c for c in data if c['total_score'] >= 18]
    normal_cases = [c for c in data if 11 <= c['total_score'] <= 12]

    def get_cycle_behavior(cases, cycle_num=2):
        """分析特定轮次的动作偏好"""
        all_actions = []
        for c in cases:
            # 简化判定：第8-14手通常是第二大回合的开始
            mid_actions = c['first_cycle_actions'][7:14] if len(c['first_cycle_actions']) > 14 else []
            for a in mid_actions:
                code = 'R' if a['mode'] == 'top' else a['action_kind'][0]
                all_actions.append(code)
        return Counter(all_actions)

    print("📊 第二大回合 (T08-T14) 行为对比：")
    
    p_stats = get_cycle_behavior(perfect_cases)
    n_stats = get_cycle_behavior(normal_cases)
    
    print(f"\n【18分神级局】动作频率:")
    total_p = sum(p_stats.values())
    for k, v in p_stats.most_common():
        print(f" - {k}: {v/total_p*100:.1f}%")

    print(f"\n【12分平庸局】动作频率:")
    total_n = sum(n_stats.values())
    for k, v in n_stats.most_common():
        print(f" - {k}: {v/total_n*100:.1f}%")

if __name__ == "__main__":
    analyze_midgame()