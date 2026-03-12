# scripts/analyze_mcts_defense_logic.py
from pathlib import Path
import json
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
CASE_DIR = ROOT / "logs" / "mcts_deep_study"

def main():
    files = list(CASE_DIR.glob("case_seed*.json"))
    if not files:
        print("未找到 JSON 轨迹文件。")
        return

    records = []
    for fp in files:
        data = json.loads(fp.read_text(encoding="utf-8"))
        score = data["score"]
        for step in data["trace"]:
            before = step["before"]
            chosen = step["chosen_action"]
            legal = step["legal_actions"]
            
            # 逻辑：是否有“建纪念物”或“征服”可选，但它选了“TopResource”？
            can_build = any(a["kind"] == "Build_Monument" for a in legal)
            can_conquest = any(a["kind"] == "Conquest" for a in legal)
            chose_resource = (chosen["mode"] == "top")
            
            # “忍耐”时刻
            is_patience_move = chose_resource and (can_build or can_conquest)
            
            records.append({
                "final_score": score,
                "turn": step["turn"],
                "military": before["military"],
                "deck_left": before["deck_left"],
                "is_patience": int(is_patience_move),
                "regions": before["occupied_regions"]
            })

    df = pd.DataFrame(records)
    
    # 我们看不同分数段的人，在什么军事水平下会选择“忍耐”
    print("=== MCTS 防御逻辑分析 ===")
    # 统计当选择“忍耐”时，平均手里剩多少军事
    patience_summary = df[df["is_patience"] == 1].groupby(pd.cut(df["final_score"], [0, 8, 12, 20]))["military"].mean()
    print("\n[忍耐时刻] 的平均军事存量（按终局分数段）:")
    print(patience_summary)
    
    # 统计当选择“冲分”时，平均手里剩多少军事
    action_summary = df[df["is_patience"] == 0].groupby(pd.cut(df["final_score"], [0, 8, 12, 20]))["military"].mean()
    print("\n[果断冲分] 的平均军事存量:")
    print(action_summary)

    out_csv = CASE_DIR / "defense_logic_results.csv"
    df.to_csv(out_csv, index=False)
    print(f"\n详细分析已导出至: {out_csv}")

if __name__ == "__main__":
    main()