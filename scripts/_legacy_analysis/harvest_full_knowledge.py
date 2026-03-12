# scripts/harvest_full_knowledge.py
from pathlib import Path
import sys
import json
import pandas as pd
import importlib

# === 路径修复 ===
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.loader import DataRepo
from core.engine import RomeEngine

def run_full_harvest(total_games=2000, start_seed=5000000):
    repo = DataRepo(Path("data"))
    engine = RomeEngine(repo, seed=42)
    mcts_mod = importlib.import_module("policies.mcts_policy")
    mcts_fn = mcts_mod.select_action
    
    all_cases = []
    
    print(f"🚀 开始全量知识收割 (T01-T21 | 全分段)...")
    
    for i in range(total_games):
        seed = start_seed + i
        s = engine.new_game(seed=seed)
        
        initial_deck = list(s.deck)
        opening_hand = initial_deck[-3:]
        
        full_game_history = []
        
        while (not s.game_lost) and s.invasions_resolved < 3:
            s.turn_count += 1
            hand = engine.draw_hand(s)
            legal = engine.legal_actions(s, hand)
            action = mcts_fn(engine, s, hand, legal)
            
            # 记录每一手的详细信息
            c_name = repo.card_by_id[action['card_id']]['Card_Name']
            full_game_history.append({
                "turn": s.turn_count,
                "action": action['kind'],
                "mode": action['mode'],
                "card": c_name,
                "res_before": {"C": s.culture, "M": s.military, "I": s.industry},
                "reg_before": s.occupied_regions()
            })
            
            engine.apply_action(s, hand, action)
            engine.resolve_invasion_if_needed(s)
            
        final_score = engine.score(s)
        
        # 记录所有对局，无论分高低
        all_cases.append({
            "seed": seed,
            "score": final_score,
            "lost": s.game_lost,
            "opening_hand": opening_hand,
            "history": full_game_history,
            "breakdown": {
                "regions": s.occupied_regions(),
                "buildings": len(s.built_buildings),
                "monuments": [m for m, p in s.monument_progress.items() if p >= 2]
            }
        })
        
        if (i + 1) % 50 == 0:
            print(f"进度: {i+1}/{total_games}")

    out_dir = Path("outputs/full_knowledge")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    with open(out_dir / "full_mcts_data.json", 'w', encoding='utf-8') as f:
        json.dump(all_cases, f, ensure_ascii=False, indent=4)

    print(f"\n✅ 全量收割完成！数据已保存在: {out_dir}/full_mcts_data.json")

if __name__ == "__main__":
    run_full_harvest(total_games=2000) # 先跑2000局作为全样分析