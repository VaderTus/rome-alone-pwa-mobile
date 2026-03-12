from pathlib import Path
import json
import pandas as pd

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
        
        for step in trace:
            turn = step["turn"]
            before = step["before"]
            chosen = step["chosen_action"]
            legal_actions = step.get("legal_actions", []) # 如果记录了的话
            
            # 寻找“忍耐”时刻：有下半动作可选，但最终选了上半
            has_monument_option = any(a["kind"] == "Build_Monument" for a in legal_actions)
            has_conquest_option = any(a["kind"] == "Conquest" for a in legal_actions)
            
            is_wait_move = (chosen["mode"] == "top") and (has_monument_option or has_conquest_option)
            
            rows.append({
                "seed": data.get("seed"),
                "final_score": score,
                "turn": turn,
                "is_wait_move": int(is_wait_move),
                "military": before["military"],
                "culture": before["culture"],
                "industry": before["industry"],
                "deck_left": before["deck_left"],
                "invasions_resolved": before["invasions_resolved"],
                "regions": before["occupied_regions"]
            })

    df = pd.DataFrame(rows)
    
    # 分析“忍耐”时刻的统计特征
    wait_moves = df[df["is_wait_move"] == 1]
    
    print("--- MCTS 忍耐决策（放着分不拿，去拿资源）的画像 ---")
    if not wait_moves.empty:
        summary = wait_moves.groupby("final_score")[["military", "deck_left", "regions"]].mean()
        print(summary)
        
        # 核心逻辑导出
        out_csv = CASE_DIR / "mcts_risk_management_study.csv"
        df.to_csv(out_csv, index=False, encoding="utf-8-sig")
        print(f"\n全量决策记录已导出至: {out_csv}")
    else:
        print("未在当前 trace 中发现记录 legal_actions，请确保 run_single_strategy 记录了 legal。")

if __name__ == "__main__":
    main()