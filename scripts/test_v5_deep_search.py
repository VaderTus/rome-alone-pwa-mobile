# scripts/test_v5_deep_search.py
import sys
import copy
import time
from pathlib import Path
import torch

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.loader import DataRepo
from core.engine import RomeEngine
from core.encoder import RomeStateEncoder
from scripts.train_deep_value_net_v2 import RomeValueBrainV2

# ==========================================
# 🧠 唤醒 V5 
# ==========================================
def load_v5():
    encoder = RomeStateEncoder()
    brain = RomeValueBrainV2()
    model_path = PROJECT_ROOT / "models" / "value_brain_40d_v5.pth"
    if not model_path.exists():
        print("❌ 找不到 V5 大脑！")
        sys.exit(1)
    brain.load_state_dict(torch.load(model_path, weights_only=True))
    brain.eval()
    device = torch.device("cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu")
    brain = brain.to(device)
    return brain, encoder, device

# ==========================================
# 🌌 深度期望搜索 (Depth-2 ExpectiMax)
# ==========================================
def deep_search_policy(engine, state, hand, legal_actions, brain, encoder, device, num_futures=3):
    """
    奇异博士模式：不仅看当前动作的残局，还要随机推演下回合的 N 种发牌可能，求平均最高分。
    """
    if not legal_actions:
        return {"card_id": hand[0], "mode": "top", "kind": "TopResource", "meta": {}}

    best_action = None
    max_expected_value = -float('inf')

    for act in legal_actions:
        # 第一层推演：走当前这步
        next_state = copy.deepcopy(state)
        engine.apply_action(next_state, hand, act)
        
        # 物理防暴毙 (如果当前回合末引发入侵且致死，直接抛弃)
        if len(next_state.deck) == 0:
            engine.resolve_invasion_if_needed(next_state, policy_name="non_random")
            if next_state.game_lost:
                continue
                
        # 如果游戏结束，直接返回真实分数
        if next_state.game_lost: continue
        if next_state.invasions_resolved >= 3:
            expected_val = engine.score(next_state)
            if expected_val > max_expected_value:
                max_expected_value = expected_val
                best_action = act
            continue

        # 🔮 第二层推演：开启平行宇宙，预测下回合
        total_future_value = 0.0
        valid_futures = 0
        
        for _ in range(num_futures):
            future_state = copy.deepcopy(next_state)
            engine.rng.shuffle(future_state.deck) # 打乱未知的未来牌堆
            
            future_state.turn_count += 1
            future_hand = engine.draw_hand(future_state)
            if not future_hand: break
            
            future_legals = engine.legal_actions(future_state, future_hand)
            if not future_legals: continue
            
            best_future_v5_score = -float('inf')
            
            # 在平行宇宙里，找出 V5 认为最好的一步
            for f_act in future_legals:
                sim_state = copy.deepcopy(future_state)
                engine.apply_action(sim_state, future_hand, f_act)
                
                if len(sim_state.deck) == 0:
                    engine.resolve_invasion_if_needed(sim_state, policy_name="non_random")
                    if sim_state.game_lost: continue
                
                tensor_state = encoder.encode(sim_state).to(device)
                with torch.no_grad():
                    val = brain(tensor_state).item()
                if val > best_future_v5_score:
                    best_future_v5_score = val
                    
            if best_future_v5_score != -float('inf'):
                total_future_value += best_future_v5_score
                valid_futures += 1
                
        # 期望坍缩
        expected_val = (total_future_value / valid_futures) if valid_futures > 0 else 0.0
        
        if expected_val > max_expected_value:
            max_expected_value = expected_val
            best_action = act

    return best_action if best_action else legal_actions[0]

# ==========================================
# 📊 实战测试
# ==========================================
def run_deep_test(num_games=50):
    print("="*50)
    print(f"🌌 启动 V5 奇异博士模式 (Depth-2 ExpectiMax) 🌌")
    print(f"测试局数: {num_games} 局 (计算量较大，请耐心等待)")
    print("="*50)
    
    repo = DataRepo(PROJECT_ROOT / "data")
    engine = RomeEngine(repo)
    brain, encoder, device = load_v5()
    
    total_score = 0
    deaths = 0
    start_time = time.time()
    
    for i in range(num_games):
        state = engine.new_game(seed=i + 123456)
        
        while not state.game_lost and state.invasions_resolved < 3:
            state.turn_count += 1
            hand = engine.draw_hand(state)
            if not hand: break
            
            legal_acts = engine.legal_actions(state, hand)
            
            # 使用深度搜索模式 (推演 3 个平行宇宙)
            action = deep_search_policy(engine, state, hand, legal_acts, brain, encoder, device, num_futures=3)
            
            engine.apply_action(state, hand, action)
            engine.resolve_invasion_if_needed(state, policy_name="non_random")
            
        score = engine.score(state) if not state.game_lost else 0
        total_score += score
        if state.game_lost: deaths += 1
        
        print(f"  [对局 {i+1}/{num_games}] 得分: {score} | 耗时: {time.time()-start_time:.1f}s")
        
    avg_score = total_score / num_games
    print("="*50)
    print(f"🏆 深蓝测试完毕！综合均分: {avg_score:.3f} | 暴毙率: {deaths/num_games*100:.1f}%")
    print("="*50)

if __name__ == "__main__":
    run_deep_test(50)