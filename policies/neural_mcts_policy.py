# policies/neural_mcts_policy.py
import sys
import copy
import random
from pathlib import Path
import torch

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.encoder import RomeStateEncoder
from scripts.train_value_net import RomeValueBrain

# ==========================================
# 🧠 1. 全局单例模式加载大脑 (防止每走一步都重新读取硬盘)
# ==========================================
_BRAIN = None
_ENCODER = None

def get_brain_and_encoder():
    global _BRAIN, _ENCODER
    if _BRAIN is None:
        _ENCODER = RomeStateEncoder()
        _BRAIN = RomeValueBrain()
        # ⚠️ 这里我们调用最初的 v1 大脑，它见识过所有的好局和烂局，刻度尺最准
        model_path = PROJECT_ROOT / "models" / "value_brain_40d_v1.pth"
        if not model_path.exists():
            raise FileNotFoundError("❌ 找不到 v1 大脑！请确保 models/value_brain_40d_v1.pth 存在。")
        _BRAIN.load_state_dict(torch.load(model_path, weights_only=True))
        _BRAIN.eval() # 锁定为推理模式
    return _BRAIN, _ENCODER

# ==========================================
# 🌌 2. 平行宇宙评估核心
# ==========================================
def evaluate_universe(engine, state, brain, encoder, universes=3):
    """
    在当前残局下，随机抽未来的一手牌 (3张)，用神经网络评估其期望价值。
    universes = 3 代表测试 3 种平行的脸黑/脸白情况。
    """
    if state.game_lost: return -999.0
    if state.invasions_resolved >= 3: return engine.score(state)
    
    deck_copy = list(state.deck)
    if not deck_copy: return engine.score(state)
    
    total_val = 0.0
    valid_u = 0
    
    for _ in range(universes):
        # 模拟一种未来的发牌可能
        sim_state = copy.deepcopy(state)
        engine.rng.shuffle(sim_state.deck) # 打乱未来
        
        sim_state.turn_count += 1
        hand = engine.draw_hand(sim_state)
        
        # 物理防暴毙检测 (如果抽完牌发现立刻要被野蛮人砍死)
        if len(sim_state.deck) == 0:
            engine.resolve_invasion_if_needed(sim_state, policy_name="non_random")
            if sim_state.game_lost:
                total_val += -100.0 # 必死宇宙，扣大分
                valid_u += 1
                continue
                
        # 让神经网络睁开眼睛，给这个平行宇宙的残局打分
        tensor_state = encoder.encode(sim_state)
        with torch.no_grad():
            val = brain(tensor_state).item()
            
        total_val += val
        valid_u += 1
        
    return total_val / valid_u if valid_u > 0 else 0.0

# ==========================================
# ⚔️ 3. 策略入口 (兼容 Engine)
# ==========================================
def select_action(engine, state, hand, legal_actions):
    if not legal_actions:
        return {"card_id": hand[0], "mode": "top", "kind": "TopResource", "meta": {}}

    brain, encoder = get_brain_and_encoder()
    
    best_action = None
    max_expected_value = -float('inf')

    # 遍历当前手中这 3 张牌能做的所有动作
    for act in legal_actions:
        # 创造动作发生后的残局
        next_state = copy.deepcopy(state)
        engine.apply_action(next_state, hand, act)
        
        # 防暴毙兜底机制（如果在当前回合末就会死，直接抛弃）
        if len(next_state.deck) == 0:
            engine.resolve_invasion_if_needed(next_state, policy_name="non_random")
            if next_state.game_lost:
                continue
                
        # ✨ 开启 3 个平行宇宙，让大脑去梦见未来
        expected_value = evaluate_universe(engine, next_state, brain, encoder, universes=3)
        
        if expected_value > max_expected_value:
            max_expected_value = expected_value
            best_action = act

    return best_action if best_action else legal_actions[0]