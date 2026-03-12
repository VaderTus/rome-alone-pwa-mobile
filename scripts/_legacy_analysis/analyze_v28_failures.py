# scripts/analyze_v28_failures.py
from pathlib import Path
import sys
import importlib

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.loader import DataRepo
from core.engine import RomeEngine

def find_failures(policy_name, games=2000):
    repo = DataRepo(Path("data"))
    engine = RomeEngine(repo)
    policy_fn = importlib.import_module("policies.mcts_distilled_final").select_action
    
    print(f"🕵️ 正在搜寻 {policy_name} 的失败案例...")
    
    fail_count = 0
    for i in range(games):
        seed = 4000000 + i # 使用全新的种子段
        s = engine.new_game(seed=seed)
        
        history = []
        while (not s.game_lost) and s.invasions_resolved < 3:
            s.turn_count += 1
            hand = engine.draw_hand(s); legal = engine.legal_actions(s, hand)
            action = policy_fn(engine, s, hand, legal)
            
            # 记录关键状态
            history.append({
                "turn": s.turn_count,
                "res": f"C{s.culture}M{s.military}I{s.industry}",
                "act": action['kind'],
                "card": repo.card_by_id[action['card_id']]['Card_Name']
            })
            
            engine.apply_action(s, hand, action)
            engine.resolve_invasion_if_needed(s)
            
        if s.game_lost:
            fail_count += 1
            print(f"\n❌ 发现失败局! Seed: {seed} | 回合: {s.turn_count}")
            # 打印死前最后 3 个动作
            for h in history[-3:]:
                print(f"  ∟ T{h['turn']:02d} | 资源: {h['res']} | 动作: {h['act']} ({h['card']})")
            if fail_count >= 5: break # 抓 5 个典型就行

if __name__ == "__main__":
    find_failures("V28_Integrated")