# scripts/analyze_harvested_json.py
from pathlib import Path
import json
import pandas as pd
from collections import Counter

# === 路径设置 ===
PROJECT_ROOT = Path(__file__).resolve().parents[1]
JSON_PATH = PROJECT_ROOT / "outputs" / "harvest" / "mcts_patterns_data.json"

def analyze():
    if not JSON_PATH.exists():
        print(f"❌ 找不到数据文件: {JSON_PATH}")
        return

    print(f"🔍 正在读取并解剖 {JSON_PATH.name} ...")
    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    total_samples = len(data)
    if total_samples == 0:
        print("⚠️ 文件中没有高分样本。")
        return

    # 1. 分数分布
    scores = [c['total_score'] for c in data]
    score_dist = Counter(scores)

    # 2. 开局手牌分析 (T1 的 3 张牌)
    opening_patterns = []
    for c in data:
        # 排序后作为 key，保证顺序不同但牌一样时能合并统计
        hand = tuple(sorted(c['opening_hand']))
        opening_patterns.append(hand)
    top_openings = Counter(opening_patterns).most_common(10)

    # 3. 核心节点：什么时候修完关键奇观？
    monument_turns = {"M_DiGuoGuangChang": [], "M_KaiXuanMen": [], "M_WanShenMiao": []}
    for c in data:
        for act in c['first_cycle_actions']:
            if act['action_kind'] == 'Build_Monument':
                mid = act['meta'].get('monument_id')
                if mid in monument_turns:
                    monument_turns[mid].append(act['turn'])

    # 4. 提取一个 18 分局的“标准模版”
    best_case = max(data, key=lambda x: x['total_score'])
    
    # === 输出报告 ===
    print("\n" + "="*50)
    print("📊 MCTS 高分行为洞察报告 (脱水版)")
    print("="*50)
    print(f"样本总数: {total_samples}")
    print(f"分数分布: {dict(sorted(score_dist.items(), reverse=True))}")
    
    print("\n✅ 最容易出高分的 Top 5 起手牌型:")
    for hand, count in top_openings[:5]:
        print(f" - {list(hand)}: 出现 {count} 次")

    print("\n✅ 关键奇观修成平均回合 (第一大回合内):")
    for mid, turns in monument_turns.items():
        if turns:
            avg_t = sum(turns) / len(turns)
            print(f" - {mid}: 平均第 {avg_t:.2f} 手")
        else:
            print(f" - {mid}: 第一大回合内从未修成")

    print("\n✅ 18分局 (Seed: " + str(best_case['seed']) + ") 的动作链路:")
    for act in best_case['first_cycle_actions']:
        print(f" T{act['turn']:02d}: {act['mode'].upper()} - {act['action_kind']} ({act['card_name']})")
    
    print("="*50)
    print("\n💡 请复制以上【控制台输出】的内容贴给我即可！")

if __name__ == "__main__":
    analyze()