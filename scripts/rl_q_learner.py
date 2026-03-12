# scripts/rl_q_learner.py
import json
import pandas as pd
import numpy as np
from pathlib import Path
import random
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.loader import DataRepo
from core.engine import RomeEngine
import copy

# ==========================================
# 1. AI 的大脑：一组可以自我进化的“特征权重”
# ==========================================
# 初始我们给它一些最基本的常识，让它不至于开局就死
Q_WEIGHTS = {
    "val_region": 1.0,      # 地区的价值
    "val_amphi": 2.0,       # 竞技场的价值
    "val_camp": 2.0,        # 要塞的价值
    "val_mine": 1.5,        # 金矿的价值
    "val_senate": 3.0,      # 元老院的价值
    "val_arc": 4.0,         # 凯旋门的价值
    "val_colossus": 2.0,    # 万神庙的价值
    "res_culture": 0.5,     # 1点文化的价值
    "res_military": 0.8,    # 1点军事的价值
    "res_industry": 0.5,    # 1点工业的价值
    "danger_penalty": -50.0 # 死亡威胁的惩罚
}

# 保存权重的路径
WEIGHTS_PATH = PROJECT_ROOT / "data" / "q_weights.json"

def load_weights():
    global Q_WEIGHTS
    if WEIGHTS_PATH.exists():
        with open(WEIGHTS_PATH, 'r') as f:
            Q_WEIGHTS.update(json.load(f))

def save_weights():
    with open(WEIGHTS_PATH, 'w') as f:
        json.dump(Q_WEIGHTS, f, indent=4)

# ==========================================
# 2. 特征提取器：把复杂的局面变成几十个数字
# ==========================================
def extract_features(state, engine):
    """把当前局面翻译成 AI 能理解的特征字典"""
    turn = state.turn_count
    deck_left = len(state.deck)
    idx = min(state.invasions_resolved + 1, 3)
    inv_cost = int(engine.repo.invasions[engine.repo.invasions["Invasion_Order"] == idx].iloc[0]["Pay_Military_To_Avoid"])
    
    senate_active = state.monument_progress.get("M_DiGuoGuangChang", 0) >= 2
    eff_m = (state.military + state.culture) if senate_active else state.military
    
    # 距离下次入侵的紧迫感
    turns_to_inv = (deck_left // 3) + 1
    danger = 0.0
    if turn < 19 and eff_m < inv_cost:
        danger = (inv_cost - eff_m) / max(1, turns_to_inv)

    return {
        "val_region": state.occupied_regions(),
        "val_amphi": 1.0 if "B_YuanXingJingJiChang" in state.built_buildings else 0.0,
        "val_camp": 1.0 if "B_JunTuanYaoSai" in state.built_buildings else 0.0,
        "val_mine": 1.0 if "B_DiGuoJinKuang" in state.built_buildings else 0.0,
        "val_senate": state.monument_progress.get("M_DiGuoGuangChang", 0) / 2.0,
        "val_arc": state.monument_progress.get("M_KaiXuanMen", 0) / 2.0,
        "val_colossus": state.monument_progress.get("M_WanShenMiao", 0) / 2.0,
        "res_culture": state.culture,
        "res_military": state.military,
        "res_industry": state.industry,
        "danger_penalty": danger
    }

def get_state_value(features):
    """计算当前局面的总估值"""
    return sum(features[k] * Q_WEIGHTS[k] for k in features)

# ==========================================
# 3. 带着“自我学习”能力的决策代理
# ==========================================
def q_learning_agent(engine, state, hand, legal_actions, epsilon=0.0):
    """
    epsilon: 探索率。如果 > 0，AI 会偶然“发疯”去尝试新套路。
    """
    if not legal_actions: return None

    # 探索机制：一定概率随机选，为了发现新世界
    if random.random() < epsilon:
        best_act = random.choice(legal_actions)
        # 记录执行动作后的特征，用于后续学习
        next_s = copy.deepcopy(state)
        engine.apply_action(next_s, hand, best_act)
        return best_act, extract_features(next_s, engine)

    best_act = None
    max_val = -float('inf')
    best_features = None

    for act in legal_actions:
        next_s = copy.deepcopy(state)
        engine.apply_action(next_s, hand, act)
        
        # 评价执行这个动作后的“未来自己”
        features = extract_features(next_s, engine)
        val = get_state_value(features)
        
        if val > max_val:
            max_val = val
            best_act = act
            best_features = features

    return best_act, best_features

# ==========================================
# 4. 训练大循环 (让它闭关自己玩)
# ==========================================
def train_rl(episodes=5000, learning_rate=0.01):
    repo = DataRepo(Path("data"))
    engine = RomeEngine(repo)
    load_weights()

    print(f"🚀 开启强化学习 (Q-Learning)！AI 将在 {episodes} 局生死对决中自己悟道...")
    
    scores = []
    
    for ep in range(episodes):
        # 探索率随时间递减 (一开始瞎玩，后面越来越谨慎)
        epsilon = max(0.05, 0.5 - (ep / episodes) * 0.5) 
        
        s = engine.new_game(seed=random.randint(0, 999999))
        history_features = []
        
        while (not s.game_lost) and s.invasions_resolved < 3:
            hand = engine.draw_hand(s)
            legal = engine.legal_actions(s, hand)
            
            result = q_learning_agent(engine, s, hand, legal, epsilon)
            if not result: break
            
            action, features = result
            history_features.append(features)
            
            engine.apply_action(s, hand, action)
            engine.resolve_invasion_if_needed(s)
            
        # --- 核心：事后反思与大脑升级 (TD Update) ---
        # 1. 确定最终的真实奖惩
        if s.game_lost:
            final_reward = -100.0 # 罗马陷落，巨大的痛楚
        else:
            final_reward = engine.score(s) * 10.0 # 得分越高，奖励越大

        scores.append(engine.score(s) if not s.game_lost else 0)

        # 2. 时光倒流，更新权重
        # 越接近结局的动作，对结果的责任越大
        target = final_reward
        for feat in reversed(history_features):
            # 预测值与实际结果的偏差
            predicted = get_state_value(feat)
            error = target - predicted
            
            # 更新每个特征的权重！这就是“自己在玩的过程中成长”！
            for k in feat:
                Q_WEIGHTS[k] += learning_rate * error * feat[k]
            
            # 前一个状态的目标值，是后一个状态的预测值 (TD-Learning 的精髓)
            target = predicted 

        # 打印进度
        if (ep + 1) % 100 == 0:
            avg_s = np.mean(scores[-100:])
            print(f"局数 {ep+1:04d} | 近100局均分: {avg_s:.2f} | 探索率: {epsilon:.2f}")
            save_weights() # 实时保存它悟出的智慧

    print("\n✅ AI 闭关结束！它的世界观已经更新。")
    print(f"最终感悟出的权重：\n{json.dumps(Q_WEIGHTS, indent=2)}")

if __name__ == "__main__":
    train_rl(episodes=5000)