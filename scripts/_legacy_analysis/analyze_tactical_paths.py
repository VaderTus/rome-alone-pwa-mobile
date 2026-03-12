# scripts/analyze_tactical_paths.py
from pathlib import Path
import json
import pandas as pd
from collections import Counter

PROJECT_ROOT = Path(__file__).resolve().parents[1]
JSON_PATH = PROJECT_ROOT / "outputs" / "harvest" / "mcts_patterns_data.json"

def get_action_code(kind, mode):
    if mode == "top": return "R" # Resource (拿资源)
    if kind == "Conquest": return "C" # Conquest (征服)
    if kind == "Tribute": return "T" # Tribute (征收)
    if kind == "Build_Building": return "B" # Building (盖建筑)
    if kind == "Build_Monument": return "M" # Monument (盖纪念物)
    return "?"

def analyze_paths():
    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    results = []
    for c in data:
        # 1. 判定得分流派
        brk = c['score_breakdown']
        total = c['total_score']
        if brk['monuments'] >= 9: arch = "极限奇观流 (High-Monu)"
        elif brk['regions'] >= 10: arch = "硬核扩张流 (Aggro-Exp)"
        else: arch = "稳健均衡流 (Standard)"

        # 2. 提取前 7 手的动作剧本
        seq = "".join([get_action_code(act['action_kind'], act['mode']) for act in c['first_cycle_actions']])
        
        # 3. 记录起手牌特征（是否有核心引擎）
        has_engine = any(cid in ["C03", "C04", "C05"] for cid in c['opening_hand'])

        results.append({
            "archetype": arch,
            "score": total,
            "pattern": seq,
            "opening": tuple(sorted(c['opening_hand'])),
            "has_engine": has_engine
        })

    df = pd.DataFrame(results)
    
    print("\n" + "="*70)
    print("🎬 MCTS 绝密剧本库 (Top Scripts)")
    print("="*70)

    for name, group in df.groupby("archetype"):
        print(f"\n战术流派: {name}")
        print(f" - 胜场数: {len(group)}")
        print(f" - 18分达成率: {len(group[group['score']>=18]) / len(group)*100:.1f}%")
        
        # 提取这个流派最常用的前 7 手“剧本”
        common_patterns = Counter(group['pattern']).most_common(3)
        print(f" - 最优剧本 Top 3 (R=资源, C=征服, T=征收, B=建筑, M=纪念物):")
        for p, count in common_patterns:
            print(f"   ∟ {p} (使用 {count} 次)")
        
        # 这种流派喜欢什么样的起手？
        common_openings = Counter(group['opening']).most_common(2)
        print(f" - 核心配套场景 (起手牌):")
        for o, count in common_openings:
            print(f"   ∟ {list(o)} ({count} 次)")

    print("\n" + "="*70)
    print("💡 最终集成算法逻辑建议：")
    print("1. 识别起手：如果有两张 Monument 牌 -> 锁死【极限奇观流】剧本。")
    print("2. 识别节奏：第一大回合的核心在于 R-R-B-C-M-R-M 这种穿插节奏。")
    print("3. 如果起手有 C03/C04 -> 走【稳健均衡流】，先补引擎再扩张。")

if __name__ == "__main__":
    analyze_paths()