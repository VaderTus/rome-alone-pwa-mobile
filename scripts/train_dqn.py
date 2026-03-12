# scripts/train_dqn.py
import math
import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
import random
import numpy as np
from collections import deque
from pathlib import Path
import sys
import copy

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
from core.loader import DataRepo
from core.engine import RomeEngine

# ==========================================
# 1. 神经网络大脑 (Value Estimator)
# ==========================================
class RomeDQN(nn.Module):
    def __init__(self, input_size=11):
        super(RomeDQN, self).__init__()
        # 使用 3 层小型网络，学习速度极快且不易过拟合
        self.fc1 = nn.Linear(input_size, 128)
        self.fc2 = nn.Linear(128, 128)
        self.out = nn.Linear(128, 1) # 输出当前局面的“未来期望得分”

    def forward(self, x):
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        return self.out(x)

# ==========================================
# 2. 特征提取器
# ==========================================
BUILDINGS = ["B_YuanXingJingJiChang", "B_JunTuanYaoSai", "B_DiGuoJinKuang"]
MONUMENTS = ["M_DiGuoGuangChang", "M_KaiXuanMen", "M_WanShenMiao"]

def extract_state(state, engine):
    feat = [
        state.turn_count / 21.0,
        state.culture / 9.0, state.military / 9.0, state.industry / 9.0,
        state.occupied_regions() / 7.0
    ]
    for b in BUILDINGS: feat.append(1.0 if b in state.built_buildings else 0.0)
    for m in MONUMENTS: feat.append(state.monument_progress.get(m, 0) / 2.0)
    return torch.tensor(feat, dtype=torch.float32)

# ==========================================
# 3. 记忆回放池 (让 AI 不会变成金鱼脑)
# ==========================================
class ReplayMemory:
    def __init__(self, capacity=10000):
        self.buffer = deque(maxlen=capacity)
    def push(self, state, reward, next_state, done):
        self.buffer.append((state, reward, next_state, done))
    def sample(self, batch_size):
        batch = random.sample(self.buffer, batch_size)
        state, reward, next_state, done = zip(*batch)
        return torch.stack(state), torch.tensor(reward, dtype=torch.float32), \
               torch.stack(next_state), torch.tensor(done, dtype=torch.float32)
    def __len__(self): return len(self.buffer)

# ==========================================
# 4. 训练主循环
# ==========================================
def train_dqn(episodes=2000):
    repo = DataRepo(Path("data"))
    engine = RomeEngine(repo)
    
    policy_net = RomeDQN()
    target_net = RomeDQN()
    target_net.load_state_dict(policy_net.state_dict())
    
    optimizer = optim.Adam(policy_net.parameters(), lr=0.001)
    memory = ReplayMemory()
    
    batch_size = 64
    gamma = 0.99  # 对未来的重视程度极高
    epsilon_start = 1.0
    epsilon_end = 0.05
    epsilon_decay = 500 # 在 500 局内逐步从瞎玩变成认真玩
    
    print(f"🌌 启动深度强化学习 (DQN)！AI 将在 {episodes} 局中自我悟道...")
    scores = []
    
    for ep in range(episodes):
        s = engine.new_game(seed=random.randint(0, 999999))
        
        # 衰减探索率
        epsilon = epsilon_end + (epsilon_start - epsilon_end) * math.exp(-1. * ep / epsilon_decay)
        
        while (not s.game_lost) and s.invasions_resolved < 3:
            hand = engine.draw_hand(s); legal = engine.legal_actions(s, hand)
            state_tensor = extract_state(s, engine)
            
            # --- 决策阶段 ---
            if random.random() < epsilon:
                # 探索：随便打
                action = random.choice(legal)
                next_s = copy.deepcopy(s)
                engine.apply_action(next_s, hand, action)
            else:
                # 利用：用大脑评估每一种未来
                max_q = -float('inf'); best_act = None
                with torch.no_grad():
                    for act in legal:
                        temp_s = copy.deepcopy(s)
                        engine.apply_action(temp_s, hand, act)
                        # 如果这步作死，直接给极低分
                        if temp_s.game_lost: q_val = -100
                        else: q_val = policy_net(extract_state(temp_s, engine)).item()
                        
                        if q_val > max_q: max_q = q_val; best_act = act; next_s = temp_s
                action = best_act

            # 处理游戏状态流转
            engine.resolve_invasion_if_needed(next_s)
            
            # --- 奖励塑形 (最关键的教导) ---
            done = next_s.game_lost or next_s.invasions_resolved >= 3
            if next_s.game_lost: reward = -20.0 # 严惩死亡
            elif done: reward = engine.score(next_s) * 2.0 # 游戏结束，奖励分数
            else: reward = 0.5 # 活着就有小奖励，鼓励存活
            
            # 存入记忆库
            memory.push(state_tensor, reward, extract_state(next_s, engine), done)
            s = next_s
            
            # --- 神经网络学习阶段 ---
            if len(memory) > batch_size:
                b_s, b_r, b_ns, b_d = memory.sample(batch_size)
                # 计算当前状态的价值预测
                state_action_values = policy_net(b_s).squeeze()
                # 计算未来状态的最大真实价值 (目标值)
                with torch.no_grad():
                    next_state_values = target_net(b_ns).squeeze()
                    expected_state_action_values = b_r + (gamma * next_state_values * (1 - b_d))
                
                # Huber Loss：防止因为极端分数导致的梯度爆炸
                loss = F.smooth_l1_loss(state_action_values, expected_state_action_values)
                optimizer.zero_grad()
                loss.backward()
                # 梯度裁剪：死死锁住，绝不爆 e+89
                torch.nn.utils.clip_grad_norm_(policy_net.parameters(), 1.0)
                optimizer.step()
        
        scores.append(engine.score(s) if not s.game_lost else 0)
        
        # 每 10 局，把学到的知识同步给老教授 (目标网络)
        if ep % 10 == 0: target_net.load_state_dict(policy_net.state_dict())
        
        if (ep + 1) % 50 == 0:
            print(f"局数 {ep+1:04d} | 近50局均分: {np.mean(scores[-50:]):.2f} | 探索率: {epsilon:.2f} | 记忆库: {len(memory)}")

    out_path = PROJECT_ROOT / "data" / "dqn_brain_final.pth"
    torch.save(policy_net.state_dict(), out_path)
    print(f"\n✅ DQN 训练圆满结束！无敌的硅基大脑已封印至: {out_path}")

if __name__ == "__main__":
    train_dqn(episodes=2000)