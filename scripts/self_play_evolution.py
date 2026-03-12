# scripts/self_play_evolution.py
import torch
import random
from pathlib import Path
import sys
import json

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
from core.loader import DataRepo
from core.engine import RomeEngine
from policies.neural_pure_agent import select_action

def run_self_play(num_games=1000):
    repo = DataRepo(Path("data"))
    engine = RomeEngine(repo)
    
    new_knowledge = []
    print(f"🕵️ AI 正在独自闭关，尝试寻找比大神更强的打法...")

    for i in range(num_games):
        s = engine.new_game(seed=random.randint(0, 999999))
        history = []
        while (not s.game_lost) and s.invasions_resolved < 3:
            hand = engine.draw_hand(s); legal = engine.legal_actions(s, hand)
            
            # 💡 探索：90% 时间听大脑的，10% 时间乱走（万一发现新套路呢？）
            if random.random() < 0.1:
                action = random.choice(legal)
            else:
                action = select_action(engine, s, hand, legal)
            
            history.append({
                "turn": s.turn_count,
                "res_before": {"C":s.culture, "M":s.military, "I":s.industry},
                "reg_before": s.occupied_regions(),
                "action": action['kind'],
                "mode": action['mode'],
                "card": repo.card_by_id[action['card_id']]['Card_Name']
            })
            engine.apply_action(s, hand, action)
            engine.resolve_invasion_if_needed(s)
        
        # 发现“神迹”：如果 AI 自己玩出了 16 分以上
        if engine.score(s) >= 16:
            print(f"⭐ 哇！AI 自己悟出了一个 {engine.score(s)} 分的对局！记录中...")
            new_knowledge.append({"score": engine.score(s), "lost": False, "history": history})

    # 把这些新知识存起来，以后喂给大脑
    with open(PROJECT_ROOT / "outputs/full_knowledge/self_play_data.json", 'w') as f:
        json.dump(new_knowledge, f)

if __name__ == "__main__":
    run_self_play()