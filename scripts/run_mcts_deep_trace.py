# scripts/run_mcts_deep_trace.py
from pathlib import Path
import json
import pandas as pd
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))

from core.loader import DataRepo
from core.engine import RomeEngine
from policies.registry import POLICIES

def snapshot_state(s):
    return {
        "turn": s.turn_count,
        "culture": s.culture,
        "military": s.military,
        "industry": s.industry,
        "occupied_regions": s.occupied_regions(),
        "invasions_resolved": s.invasions_resolved,
        "deck_left": len(s.deck),
        "built_buildings": list(s.built_buildings),
        "monument_progress": dict(s.monument_progress),
        "game_lost": s.game_lost,
    }

def main():
    repo = DataRepo(ROOT / "data")
    engine = RomeEngine(repo, seed=42)
    policy_fn = POLICIES["mcts_policy"]
    
    # 我们跑 1000 局，涵盖各种分数段
    games = 1000
    seed_base = 9600000
    out_dir = ROOT / "logs" / "mcts_deep_study"
    out_dir.mkdir(parents=True, exist_ok=True)

    summary_rows = []

    print(f"正在模拟 {games} 局 MCTS，请稍候（这可能需要几分钟）...")

    for i in range(games):
        seed = seed_base + i
        s = engine.new_game(seed=seed)
        trace = []

        while (not s.game_lost) and s.invasions_resolved < 3:
            s.turn_count += 1
            hand = engine.draw_hand(s)
            if not hand: break

            legal = engine.legal_actions(s, hand)
            before = snapshot_state(s)
            
            # MCTS 决策
            action = policy_fn(engine, s, hand, legal)
            
            engine.apply_action(s, hand, action)
            engine.resolve_invasion_if_needed(s, policy_name="mcts_policy")
            
            after = snapshot_state(s)

            trace.append({
                "turn": s.turn_count,
                "hand": hand,
                "legal_actions": legal, # 记录所有可选动作
                "chosen_action": action,
                "before": before,
                "after": after
            })

        score = engine.score(s)
        summary_rows.append({"seed": seed, "score": score, "lost": s.game_lost})

        # 每 100 局保存一个详细 JSON 样本，用于后续脚本分析
        if i % 5 == 0: # 抽样保存，防止硬盘爆掉
            case_file = out_dir / f"case_seed{seed}_score{score}.json"
            case_file.write_text(json.dumps({"seed":seed, "score":score, "trace":trace}, ensure_ascii=False), encoding="utf-8")

    pd.DataFrame(summary_rows).to_csv(out_dir / "mcts_study_summary.csv", index=False)
    print(f"✅ 模拟完成，数据存放在: {out_dir}")

if __name__ == "__main__":
    main()