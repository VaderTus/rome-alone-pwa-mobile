from pathlib import Path
import json
import pandas as pd
from collections import Counter

ROOT = Path(__file__).resolve().parent.parent
CASE_DIR = ROOT / "logs" / "strategy_cases" / "mcts_policy"

def main():
    files = sorted(CASE_DIR.glob("case_score*_seed*.json"))
    if not files:
        print("未找到 case JSON。")
        return

    rows = []
    
    for fp in files:
        data = json.loads(fp.read_text(encoding="utf-8"))
        trace = data.get("trace", [])
        score = data.get("score", 0)
        
        # 只看 16 分及以上的“神局”
        if score < 16:
            continue
            
        # 1. 前3回合（可见前9张牌）
        opening_9_cards = []
        for step in trace[:3]:
            opening_9_cards.extend(step.get("hand", []))
            
        # 2. 统计前3回合卡牌类型分布
        counts = Counter()
        for cid in opening_9_cards:
            # 简单分类：建筑B, 动作A, 纪念物M
            if cid in ["C01","C02","C03","C04","C05"]: counts["Building"] += 1
            elif cid in ["C06","C07","C08","C09"]: counts["Action"] += 1
            else: counts["Monument"] += 1

        # 3. 统计关键牌露面时间
        def get_turn(target_cid):
            for step in trace:
                if target_cid in step.get("hand", []): return step["turn"]
            return 99

        rows.append({
            "seed": data.get("seed"),
            "score": score,
            "turn1_cards": "|".join(trace[0].get("hand", [])),
            "turn2_cards": "|".join(trace[1].get("hand", [])) if len(trace)>1 else "",
            "opening_building_cnt": counts["Building"],
            "opening_monument_cnt": counts["Monument"],
            "opening_action_cnt": counts["Action"],
            # 核心“运势”指标：竞技场和帝国广场什么时候来
            "turn_seen_Amphi": get_turn("C05"), 
            "turn_seen_Senate1": get_turn("C14"),
            "turn_seen_Senate2": get_turn("C15"),
            "turn_seen_Arc1": get_turn("C18"),
            "turn_seen_Arc2": get_turn("C19"),
        })

    df = pd.DataFrame(rows)
    
    out_csv = CASE_DIR / "mcts_opening_luck_analysis.csv"
    df.to_csv(out_csv, index=False, encoding="utf-8-sig")
    
    # 计算均值画像
    luck_summary = df[[
        "opening_building_cnt", "opening_monument_cnt", "opening_action_cnt",
        "turn_seen_Amphi", "turn_seen_Senate1", "turn_seen_Senate2"
    ]].mean().to_frame("16plus_mean")
    
    print("✅ 开局运势分析完成")
    print(f"明细表: {out_csv}")
    print("\n--- 16分局开局特征均值 ---")
    print(luck_summary)

if __name__ == "__main__":
    main()