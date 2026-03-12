# scripts/analyze_full_strategy.py
from pathlib import Path
import json
import pandas as pd
from collections import Counter

PROJECT_ROOT = Path(__file__).resolve().parents[1]
JSON_PATH = PROJECT_ROOT / "outputs" / "full_knowledge" / "full_mcts_data.json"

def get_action_code(kind, mode):
    if mode == "top": return "R"  # 拿资源
    if kind == "Conquest": return "C"
    if kind == "Tribute": return "T"
    if kind == "Build_Building": return "B"
    if kind == "Build_Monument": return "M"
    return "?"

def analyze_full_data():
    if not JSON_PATH.exists():
        print(f"❌ 找不到文件: {JSON_PATH}")
        return

    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 1. 按照表现对局进行分类
    god_tier = [c for c in data if c['score'] >= 18]      # 神级 (18)
    high_tier = [c for c in data if 14 <= c['score'] < 18] # 高分 (14-17)
    mid_tier = [c for c in data if 11 <= c['score'] < 14]  # 平庸 (11-13)
    
    def process_group(group_data, label):
        if not group_data: return
        
        n = len(group_data)
        # 统计三个阶段的动作序列
        # 第一阶段 T1-7 | 第二阶段 T8-14 | 第三阶段 T15-21
        p1_actions, p2_actions, p3_actions = Counter(), Counter(), Counter()
        # 统计阶段转换时的资源储备
        res_at_t8 = {"C": 0, "M": 0, "I": 0}
        res_at_t15 = {"C": 0, "M": 0, "I": 0}

        for c in group_data:
            h = c['history']
            for i, act in enumerate(h):
                code = get_action_code(act['action'], act['mode'])
                if i < 7: p1_actions[code] += 1
                elif i < 14: p2_actions[code] += 1
                else: p3_actions[code] += 1
                
                # 记录阶段开始时的资源
                if i == 7: # T8 开始
                    for k in "CMI": res_at_t8[k] += act['res_before'][k]
                if i == 14: # T15 开始
                    for k in "CMI": res_at_t15[k] += act['res_before'][k]

        print(f"\n【{label}】(样本数: {n})")
        print(f" - 阶段1 (T1-7) 偏好: " + ", ".join([f"{k}:{v/n:.1f}" for k, v in p1_actions.most_common()]))
        print(f" - T8 开始时平均资源: C={res_at_t8['C']/n:.1f} M={res_at_t8['M']/n:.1f} I={res_at_t8['I']/n:.1f}")
        print(f" - 阶段2 (T8-14) 偏好: " + ", ".join([f"{k}:{v/n:.1f}" for k, v in p2_actions.most_common()]))
        print(f" - T15 开始时平均资源: C={res_at_t15['C']/n:.1f} M={res_at_t15['M']/n:.1f} I={res_at_t15['I']/n:.1f}")
        print(f" - 阶段3 (T15-21) 偏好: " + ", ".join([f"{k}:{v/n:.1f}" for k, v in p3_actions.most_common()]))

    print("\n" + "="*70)
    print("🌍 孤城罗马：全生命周期战略透视报告")
    print("="*70)
    
    process_group(god_tier, "神级局 18分")
    process_group(high_tier, "高分局 14-17分")
    process_group(mid_tier, "平庸局 11-13分")
    
    print("\n" + "="*70)
    print("💡 行动代码说明: R=拿资源, C=征服, T=征收, B=建筑, M=奇观")

if __name__ == "__main__":
    analyze_full_data()