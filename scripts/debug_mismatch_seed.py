# scripts/debug_mismatch_seed.py
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))

from core.loader import DataRepo
from core.engine import RomeEngine
from policies.registry import POLICIES

def run_strategy(engine, policy_name, seed):
    print(f"\n>>> 运行策略: {policy_name}")
    s = engine.new_game(seed=seed)
    policy_fn = POLICIES[policy_name]
    while (not s.game_lost) and s.invasions_resolved < 3:
        hand = engine.draw_hand(s)
        if not hand: break
        legal = engine.legal_actions(s, hand)
        
        mil_before = s.military
        action = policy_fn(engine, s, hand, legal)
        
        c = engine.repo.card_by_id[action["card_id"]]
        print(f"T{s.turn_count+1}: {c['Card_Name']}({action['mode']}) | 军:{mil_before} | 牌:{len(s.deck)}")
        
        engine.apply_action(s, hand, action)
        engine.resolve_invasion_if_needed(s, policy_name=policy_name)
        
        if s.game_lost:
            print("!!! 失败 !!!")
            break
    print(f"得分: {engine.score(s)}")

def main():
    repo = DataRepo(ROOT / "data")
    engine = RomeEngine(repo, seed=42)
    target_seed = 9900141 # 你可以换成任何你关心的 seed
    
    for p in ["mcts_distilled_v3", "mcts_distilled_v5_final", "mcts_policy"]:
        run_strategy(engine, p, target_seed)

if __name__ == "__main__":
    main()