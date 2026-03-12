# scripts/test_neural_agent.py
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
from scripts.train_value_net import RomeValueBrain  # 导入我们的大脑结构

# 1. 唤醒封存的大脑
def load_brain():
    brain = RomeValueBrain()
    model_path = PROJECT_ROOT / "models" / "value_brain_40d_v1.pth"
    if not model_path.exists():
        print("❌ 找不到大脑权重！请先运行 train_value_net.py")
        sys.exit(1)
    brain.load_state_dict(torch.load(model_path, weights_only=True))
    brain.eval() # 切换到推理模式（不训练）
    return brain

# 2. 定义神谕决策逻辑 (1-Step Lookahead + Neural Value)
def neural_policy(engine, state, hand, legal_actions, brain, encoder):
    if not legal_actions:
        return {"card_id": hand[0], "mode": "top", "kind": "TopResource", "meta": {}}

    best_action = None
    max_value = -float('inf')

    # 穷举手里这几张牌的合法动作
    for act in legal_actions:
        # 在脑海中创建一个平行宇宙
        next_state = copy.deepcopy(state)
        engine.apply_action(next_state, hand, act)
        
        # ⚠️ 物理防暴毙兜底：如果这一步走完立刻迎来入侵，看看会不会死
        if len(next_state.deck) == 0:
            engine.resolve_invasion_if_needed(next_state, policy_name="non_random")
            if next_state.game_lost:
                continue # 绝对不走这条必死之路

        # 让视神经拍下这个平行宇宙的画面
        tensor_state = encoder.encode(next_state)
        
        # 让大脑给这个画面打分 (直觉估值)
        with torch.no_grad():
            predicted_score = brain(tensor_state).item()

        if predicted_score > max_value:
            max_value = predicted_score
            best_action = act

    # 如果所有动作都会导致死亡（极其罕见），只能苟延残喘随便走一步
    return best_action if best_action else legal_actions[0]

# 3. 实战考核
def run_evaluation(num_games=100):
    print(f"🤖 唤醒初级直觉大脑... 开始 {num_games} 局盲打考核！")
    repo = DataRepo(PROJECT_ROOT / "data")
    engine = RomeEngine(repo)
    encoder = RomeStateEncoder()
    brain = load_brain()
    
    total_score = 0
    deaths = 0
    
    for i in range(num_games):
        state = engine.new_game(seed=i + 9999) # 用新种子，防止背板
        
        while (not state.game_lost) and state.invasions_resolved < 3:
            state.turn_count += 1
            hand = engine.draw_hand(state)
            if not hand: break
            
            legal_acts = engine.legal_actions(state, hand)
            action = neural_policy(engine, state, hand, legal_acts, brain, encoder)
            
            engine.apply_action(state, hand, action)
            engine.resolve_invasion_if_needed(state, policy_name="non_random")
            
        score = engine.score(state)
        if state.game_lost:
            deaths += 1
            score = 0
            
        total_score += score
        
    avg_score = total_score / num_games
    print("="*40)
    print(f"📊 考核完毕！共测试 {num_games} 局")
    print(f"💀 暴毙率: {deaths / num_games * 100:.1f}%")
    print(f"🏆 盲打均分: {avg_score:.2f} 分")
    print("="*40)

if __name__ == "__main__":
    run_evaluation(num_games=100)