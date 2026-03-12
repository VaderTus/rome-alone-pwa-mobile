# scripts/harvest_master_bible.py
from pathlib import Path
import sys
import json
import importlib

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.loader import DataRepo
from core.engine import RomeEngine

def run_harvest(target_count=100):
    repo = DataRepo(Path("data"))
    engine = RomeEngine(repo, seed=42)
    mcts_fn = importlib.import_module("policies.mcts_policy").select_action
    
    bible = []
    found = 0
    seed = 6000000 # 从新的种子段开始

    print(f"📡 正在寻找 {target_count} 组【上帝之手】范本 (目标分数 >= 17)...")

    while found < target_count:
        s = engine.new_game(seed=seed)
        history = []
        
        while (not s.game_lost) and s.invasions_resolved < 3:
            s.turn_count += 1
            hand = engine.draw_hand(s); legal = engine.legal_actions(s, hand)
            
            # 记录此时的所有状态，包括手牌
            state_snapshot = {
                "turn": s.turn_count,
                "hand": hand,
                "c": s.culture, "m": s.military, "i": s.industry,
                "reg": s.occupied_regions()
            }
            
            action = mcts_fn(engine, s, hand, legal)
            
            # 记录决策
            state_snapshot["choice"] = {
                "card": action['card_id'],
                "mode": action['mode'],
                "kind": action['kind']
            }
            history.append(state_snapshot)
            
            engine.apply_action(s, hand, action)
            engine.resolve_invasion_if_needed(s)
            
        final_score = engine.score(s)
        
        # 只要神级对局
        if final_score >= 17 and not s.game_lost:
            found += 1
            bible.append({
                "seed": seed,
                "score": final_score,
                "steps": history
            })
            print(f"✨ 找到第 {found}/{target_count} 组范本 | Seed: {seed} | 分数: {final_score}")
            
            # 每找到 10 组就存一次盘，防止断电
            with open(PROJECT_ROOT / "data/master_bible.json", 'w', encoding='utf-8') as f:
                json.dump(bible, f, indent=4)
        
        seed += 1

if __name__ == "__main__":
    run_harvest(100)