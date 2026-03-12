# scripts/test_v3_agent.py
import sys
import time
import copy
from pathlib import Path
import torch

# 动态加载项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.loader import DataRepo
from core.engine import RomeEngine
from core.encoder import RomeStateEncoder
# V3 用的是和 V2 完全一样的脑神经结构，只是里面的记忆权重不同了
from scripts.train_deep_value_net_v2 import RomeValueBrainV2

# ==========================================
# 🧠 1. 唤醒 V3 究极大脑
# ==========================================
_BRAIN_V3 = None
_ENCODER = None

def get_v3_brain():
    global _BRAIN_V3, _ENCODER
    if _BRAIN_V3 is None:
        _ENCODER = RomeStateEncoder()
        _BRAIN_V3 = RomeValueBrainV2()
        
        # ⚠️ 注意：这里加载的是刚刚诞生的 v3 权重！
        model_path = PROJECT_ROOT / "models" / "value_brain_40d_v3.pth"
        if not model_path.exists():
            raise FileNotFoundError("❌ 找不到 V3 大脑！请确认它已生成。")
        
        _BRAIN_V3.load_state_dict(torch.load(model_path, weights_only=True))
        _BRAIN_V3.eval() 
        
        if torch.cuda.is_available():
            _BRAIN_V3 = _BRAIN_V3.cuda()
        elif torch.backends.mps.is_available():
            _BRAIN_V3 = _BRAIN_V3.to("mps")
            
    return _BRAIN_V3, _ENCODER

def v3_policy(engine, state, hand, legal_actions, device):
    if not legal_actions:
        return {"card_id": hand[0], "mode": "top", "kind": "TopResource", "meta": {}}

    brain, encoder = get_v3_brain()
    best_action = None
    max_value = -float('inf')

    for act in legal_actions:
        next_state = copy.deepcopy(state)
        engine.apply_action(next_state, hand, act)
        
        # 物理防暴毙红线
        if len(next_state.deck) == 0:
            engine.resolve_invasion_if_needed(next_state, policy_name="non_random")
            if next_state.game_lost:
                continue 
                
        tensor_state = encoder.encode(next_state).to(device)
        with torch.no_grad():
            predicted_score = brain(tensor_state).item()

        if predicted_score > max_value:
            max_value = predicted_score
            best_action = act

    return best_action if best_action else legal_actions[0]

# ==========================================
# 📊 2. V3 万局实战
# ==========================================
def run_v3_grand_test(num_games=10000):
    print("="*50)
    print(f"👑 启动 V3 究极大脑 - 万局大考 👑")
    print("目标：超越 12.128 分！")
    print("="*50)
    
    repo = DataRepo(PROJECT_ROOT / "data")
    engine = RomeEngine(repo)
    brain, _ = get_v3_brain()
    device = next(brain.parameters()).device
    
    total_score = 0
    deaths = 0
    score_distribution = { "0-5": 0, "6-10": 0, "11-15": 0, "16-20+": 0 }
    
    start_time = time.time()
    
    for i in range(num_games):
        # 用全新的种子，防止它背题
        state = engine.new_game(seed=i + 777777) 
        
        while (not state.game_lost) and state.invasions_resolved < 3:
            state.turn_count += 1
            hand = engine.draw_hand(state)
            if not hand: break
            
            legal_acts = engine.legal_actions(state, hand)
            action = v3_policy(engine, state, hand, legal_acts, device)
            
            engine.apply_action(state, hand, action)
            engine.resolve_invasion_if_needed(state, policy_name="non_random")
            
        final_score = engine.score(state)
        if state.game_lost:
            deaths += 1
            final_score = 0
            
        total_score += final_score
        
        if final_score <= 5: score_distribution["0-5"] += 1
        elif final_score <= 10: score_distribution["6-10"] += 1
        elif final_score <= 15: score_distribution["11-15"] += 1
        else: score_distribution["16-20+"] += 1
        
        if (i + 1) % 500 == 0:
            elapsed = time.time() - start_time
            current_avg = total_score / (i + 1)
            print(f"  [进度 {(i+1):05d}/{num_games}] 耗时: {elapsed:.1f}s | 实时均分: {current_avg:.3f}")
            
    print("\n" + "="*50)
    print("🏆 V3 究极大脑大考出炉 🏆")
    print("="*50)
    print(f"综合盲打均分 : {total_score / num_games:.3f} 分")
    print(f"绝对暴毙概率 : {deaths / num_games * 100:.2f}% ({deaths} 局)")
    print(f"分 数 段 分 布 :")
    print(f"  🤡 0-5 分  : {score_distribution['0-5']}")
    print(f"  🥉 6-10 分 : {score_distribution['6-10']}")
    print(f"  🥇 11-15 分: {score_distribution['11-15']}")
    print(f"  👑 16分以上: {score_distribution['16-20+']}")
    print("="*50)

if __name__ == "__main__":
    run_v3_grand_test(10000)