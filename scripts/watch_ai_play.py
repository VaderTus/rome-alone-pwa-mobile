# scripts/watch_ai_play.py
import time
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from core.loader import DataRepo
from core.engine import RomeEngine
from policies.neural_pure_agent import select_action

def watch():
    repo = DataRepo(Path("data"))
    # 随机种子，看 AI 的真实随机表现
    engine = RomeEngine(repo, seed=int(time.time())) 
    s = engine.new_game()
    
    print("\n📺 正在直播【纯粹神经网络】对局...")
    print("AI 此时完全依靠神经元权重决策，无任何手写规则。")
    print("="*50)

    while (not s.game_lost) and s.invasions_resolved < 3:
        # ✅ 环境修复：让游戏引擎的回合数正常增长
        s.turn_count += 1
        
        hand = engine.draw_hand(s)
        legal = engine.legal_actions(s, hand)
        
        # AI 思考（此时调用的是下方纯净版的 select_action）
        action = select_action(engine, s, hand, legal)
        
        print(f"T{s.turn_count:02d} | 资源: C{s.culture}M{s.military}I{s.industry} | 地区: {s.occupied_regions()}")
        card_name = repo.card_by_id[action['card_id']]['Card_Name']
        print(f"   ∟ 🧠 权重驱动决策: {card_name} ({action['kind']})")
        
        engine.apply_action(s, hand, action)
        engine.resolve_invasion_if_needed(s)
        time.sleep(0.3)

    print("\n" + "="*50)
    if s.game_lost: print(f"💀 罗马陷落... 最终得分: 0")
    else: print(f"🏆 终局得分: {engine.score(s)}")

if __name__ == "__main__":
    watch()