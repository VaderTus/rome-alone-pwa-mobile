# scripts/generate_mistake_book.py
from pathlib import Path
import sys
import importlib

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.loader import DataRepo
from core.engine import RomeEngine

def audit_seed(seed):
    repo = DataRepo(Path("data"))
    engine = RomeEngine(repo, seed=42)
    
    # 加载两个策略
    mcts = importlib.import_module("policies.mcts_policy").select_action
    v5 = importlib.import_module("policies.mcts_distilled_final").select_action
    
    print(f"\n" + "="*80)
    print(f"📊 错题本审计 | Seed: {seed}")
    print(f"{'回合':<4} | {'当前资源':<15} | {'MCTS 决策':<25} | {'V5 决策':<25}")
    print("-" * 80)

    # 模拟 MCTS 路径（作为标准答案）
    s = engine.new_game(seed=seed)
    while (not s.game_lost) and s.invasions_resolved < 3:
        s.turn_count += 1
        hand = engine.draw_hand(s)
        legal = engine.legal_actions(s, hand)
        
        # 同时询问两个策略，但不执行 V5 的，只记录它会选什么
        act_mcts = mcts(engine, s, hand, legal)
        act_v5 = v5(engine, s, hand, legal)
        
        res_str = f"C{s.culture}M{s.military}I{s.industry}"
        m_name = repo.card_by_id[act_mcts['card_id']]['Card_Name']
        v_name = repo.card_by_id[act_v5['card_id']]['Card_Name']
        
        # 标记差异
        diff_mark = "❌ DIFF" if act_mcts['card_id'] != act_v5['card_id'] or act_mcts['mode'] != act_v5['mode'] else ""
        
        print(f"T{s.turn_count:02d} | {res_str:<15} | {m_name[:10]:<15}({act_mcts['mode'].upper()}) | {v_name[:10]:<15}({act_v5['mode'].upper()}) | {diff_mark}")
        
        # 执行 MCTS 的动作继续
        engine.apply_action(s, hand, act_mcts)
        engine.resolve_invasion_if_needed(s)

    print(f"="*80)

if __name__ == "__main__":
    # 选一个 V5 表现不佳但 MCTS 18 分的种子
    # 比如 2000002 或你之前 summary 里的高分种子
    audit_seed(2000002)