# scripts/debug_mcts_essence.py
from pathlib import Path
import sys
import importlib

# 路径修复
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.loader import DataRepo
from core.engine import RomeEngine

def main():
    repo = DataRepo(Path("data"))
    engine = RomeEngine(repo, seed=42)
    
    # 追踪这个 18 分的神级 Seed
    target_seed = 1200078 
    
    print(f"==========================================")
    print(f"🔍 深度解剖 MCTS 高分局 | Seed: {target_seed}")
    print(f"==========================================\n")
    
    mcts_mod = importlib.import_module("policies.mcts_policy")
    mcts_fn = mcts_mod.select_action
    
    s = engine.new_game(seed=target_seed)
    
    while (not s.game_lost) and s.invasions_resolved < 3:
        s.turn_count += 1
        hand = engine.draw_hand(s)
        legal = engine.legal_actions(s, hand)
        
        # 获取 MCTS 的决策
        action = mcts_fn(engine, s, hand, legal)
        
        # 记录当前状态快照
        status = f"T{s.turn_count:02d} | 资源: C={s.culture} M={s.military} I={s.industry} | 地区: {s.occupied_regions()}"
        
        # 记录建设进度
        b_list = ",".join([b.replace("B_", "") for b in s.built_buildings]) if s.built_buildings else "无"
        m_list = ",".join([f"{m.replace('M_', '')}({p})" for m,p in s.monument_progress.items() if p > 0])
        
        print(status)
        print(f"   ∟ 已建建筑: [{b_list}] | 纪念物进度: [{m_list}]")
        
        # 记录具体动作
        card_name = repo.card_by_id[action['card_id']]['Card_Name']
        act_desc = f"{action['mode'].upper()} - {action['kind']}"
        if action['meta']:
            act_desc += f" ({action['meta']})"
        
        print(f"   ∟ 🚀 MCTS选择: {card_name} | {act_desc}")
        
        # 执行
        engine.apply_action(s, hand, action)
        engine.resolve_invasion_if_needed(s)
        print("-" * 60)

    print(f"\n✅ 游戏结束！最终得分: {engine.score(s)} | 失败: {s.game_lost}")

if __name__ == "__main__":
    main()