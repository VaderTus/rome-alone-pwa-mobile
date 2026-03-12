# scripts/analyze_opening_secrets.py
import json
import pandas as pd
from pathlib import Path
from collections import Counter

PROJECT_ROOT = Path(__file__).resolve().parents[1]
JSON_PATH = PROJECT_ROOT / "outputs" / "harvest" / "mcts_patterns_data.json"

def get_action_code(kind, mode):
    if mode == "top": return "R" # 拿资源
    if kind == "Conquest": return "C" # 征服
    if kind == "Tribute": return "T" # 征收
    if kind == "Build_Building": return "B" # 建筑
    if kind == "Build_Monument": return "M" # 奇观
    return "?"

def analyze():
    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 筛选两组样本
    perfect = [c for c in data if c['total_score'] >= 18]
    standard = [c for c in data if 11 <= c['total_score'] <= 12]

    def get_stats(cases):
        seqs = []
        action_counts = Counter()
        for c in cases:
            # 拿到前 7 手的动作序列
            s = "".join([get_action_code(a['action_kind'], a['mode']) for a in c['first_cycle_actions']])
            seqs.append(s)
            for char in s: action_counts[code_to_name(char)] += 1
        return seqs, action_counts

    def code_to_name(c):
        return {"R":"拿资源","C":"征服","T":"征收","B":"建筑","M":"奇观"}[c]

    p_seqs, p_counts = get_stats(perfect)
    s_seqs, s_counts = get_stats(standard)

    print("\n" + "="*60)
    print("🏆 18分局 vs 12分局：第一大回合(前7手)本质区别")
    print("="*60)

    print(f"\n【18分局】(样本数:{len(perfect)}):")
    print(f" - 最强开局剧本: {Counter(p_seqs).most_common(1)[0][0]}")
    for act, count in p_counts.items():
        print(f"   ∟ {act}: 平均每局出现 {count/len(perfect):.2f} 次")

    print(f"\n【12分局】(样本数:{len(standard)}):")
    print(f" - 平庸开局剧本: {Counter(s_seqs).most_common(1)[0][0]}")
    for act, count in s_counts.items():
        print(f"   ∟ {act}: 平均每局出现 {count/len(standard):.2f} 次")

if __name__ == "__main__":
    analyze()