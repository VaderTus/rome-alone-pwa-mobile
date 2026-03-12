# scripts/test_v2_agent.py
import sys
import copy
from pathlib import Path
import torch

# 动态加载项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.loader import DataRepo
from core.engine import RomeEngine
from core.encoder import RomeStateEncoder
from scripts.train_deep_value_net_v2 import RomeValueBrainV2  # 导入全新的 V2 大脑

# ==========================================
# 🧠 1. 唤醒 V2 巅峰大脑
# ==========================================
_BRAIN_V2 = None
_ENCODER = None

def get_v2_brain():
    global _BRAIN_V2, _ENCODER
    if _BRAIN_V2 is None:
        _ENCODER = RomeStateEncoder()
        _BRAIN_V2 = RomeValueBrainV2()
        model_path = PROJECT_ROOT / "models" / "value_brain_40d_v2.pth"
        if not model_path.exists():
            raise FileNotFoundError("❌ 找不到 V2 大脑！")
        # 加载抗过拟合巅峰权重
        _BRAIN_V2.load_state_dict(torch.load(model_path, weights_only=True))
        _BRAIN_V2.eval() # 锁定为实战推理模式，自动关闭 Dropout
    return _BRAIN_V2, _ENCODER

# ==========================================
# ⚔️ 2. 大道至简的 V2 决策逻辑
# ==========================================
def v2_policy(engine, state, hand, legal_actions):
    if not legal_actions:
        return {"card_id": hand[0], "mode": "top", "kind": "TopResource", "meta": {}}

    brain, encoder = get_v2_brain()
    
    best_action = None
    max_value = -float('inf')

    for act in legal_actions:
        # 物理宇宙前瞻 1 步
        next_state = copy.deepcopy(state)
        engine.apply_action(next_state, hand, act)
        
        # 🛡️ 绝对死亡红线兜底：如果不幸走到这步会立刻被砍死，直接一票否决
        if len(next_state.deck) == 0:
            engine.resolve_invasion_if_needed(next_state, policy_name="non_random")
            if next_state.game_lost:
                continue 
                
        # 让 V2 大脑看一眼残局
        tensor_state = encoder.encode(next_state)
        with torch.no_grad():
            predicted_score = brain(tensor_state).item()

        if predicted_score > max_value:
            max_value = predicted_score
            best_action = act

    return best_action if best_action else legal_actions[0]

# ==========================================
# 📊 3. 百局盲打大考
# ==========================================
def run_v2_evaluation(num_games=100):
    print("="*50)
    print(f"🤖 唤醒 V2 巅峰大脑... 开启 {num_games} 局终极盲打考核！")
    print("="*50)
    
    repo = DataRepo(PROJECT_ROOT / "data")
    engine = RomeEngine(repo)
    
    total_score = 0
    deaths = 0
    
    # 强制预热大脑
    get_v2_brain()
    
    for i in range(num_games):
        # 使用全新的种子，保证它绝对没背过题
        state = engine.new_game(seed=i + 55555) 
        
        while (not state.game_lost) and state.invasions_resolved < 3:
            state.turn_count += 1
            hand = engine.draw_hand(state)
            if not hand: break
            
            legal_acts = engine.legal_actions(state, hand)
            # 交给 V2 决策
            action = v2_policy(engine, state, hand, legal_acts)
            
            engine.apply_action(state, hand, action)
            engine.resolve_invasion_if_needed(state, policy_name="non_random")
            
        score = engine.score(state)
        if state.game_lost:
            deaths += 1
            score = 0
            
        total_score += score
        
    avg_score = total_score / num_games
    print(f"\n✅ 考核完毕！")
    print(f"💀 暴毙率: {deaths / num_games * 100:.1f}%")
    print(f"🏆 盲打均分: {avg_score:.2f} 分")
    print("="*50)

if __name__ == "__main__":
    run_v2_evaluation(num_games=100)