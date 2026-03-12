# scripts/train_dqn_selfplay.py
import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
import random
import numpy as np
from collections import deque
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
from core.loader import DataRepo
from core.engine import RomeEngine
import copy

# ==========================================
# 1. 定义深度神经网络大脑 (Value Network)
# ==========================================
class DeepQNetwork(nn.Module):
    def __init__(self, input_size=17):
        super(DeepQNetwork, self).__init__()
        self.fc1 = nn.Linear(input_size, 256)
        self.fc2 = nn.Linear(256, 256)
        self.fc3 = nn.Linear(256, 128)
        self.out = nn.Linear(128, 1) # 输出当前局面的“未来期望总分”

    def forward(self, x):
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        x = F.relu(self.fc3(x))
        return self.out(x)

# ==========================================
# 2. 状态提取器 (将局面变成 17 维张量)
# ==========================================
BUILDINGS = ["B_KaiXuanDiaoSu", "B_DiGuoYinShuiDao", "B_JunTuanYaoSai", "B_DiGuoJinKuang", "B_YuanXingJingJiChang"]
MONUMENTS = ["M_WanShenMiao", "M_LuoMaDouShouChang", "M_DiGuoGuangChang", "M_HaDeLiangLingQin", "M_KaiXuanMen", "M_TuLaZhenShiChang"]

def get_state_vector(state):
    feat = [
        state.turn_count / 21.0,
        state.culture / 9.0, state.military / 9.0, state.industry / 9.0,
        state.occupied_regions() / 7.0,
        state.invasions_resolved / 3.0
    ]
    for b in BUILDINGS: feat.append(1.0 if b in state.built_buildings else 0.0)
    for m in MONUMENTS: feat.append(state.monument_progress.get(m, 0) / 2.0)
    return torch.tensor(feat, dtype=torch.float32)

# ==========================================
# 3. 经验回放池 (防止 AI 走火入魔)
# ==========================================
class ReplayBuffer:
    def __init__(self, capacity=50000):
        self.buffer = deque(maxlen=capacity)
    
    def push(self, state, reward, next_state, done):
        self.buffer.append((state, reward, next_state, done))
        
    def sample(self, batch_size):
        batch = random.sample(self.buffer, batch_size)
        state, reward, next_state, done = map(np.stack, zip(*batch))
        return torch.tensor(state), torch.tensor(reward, dtype=torch.float32), \
               torch.tensor(next_state), torch.tensor(done, dtype=torch.float32)
    
    def __len__(self):
        return len(self.buffer)

# ==========================================
# 4. DQN 训练主循环
# ==========================================
def run_dqn_training(episodes=10000):
    repo = DataRepo(Path("data"))
    engine = RomeEngine(repo)
    
    # 初始化大脑
    policy_net = DeepQNetwork()
    target_net = DeepQNetwork()
    target_net.load_state_dict(policy_net.state_dict())
    target_net.eval()
    
    optimizer = optim.Adam(policy_net.parameters(), lr=0.0005)
    memory = ReplayBuffer()
    
    # 超参数
    BATCH_SIZE = 128
    GAMMA = 0.95 # 对未来的重视程度 (0-1)
    epsilon = 1.0 # 初始 100% 瞎玩探索
    epsilon_min = 0.05
    epsilon_decay = 0.999 # 探索率缓慢衰减
    
    print(f"🌌 启动深度强化学习 (DQN)！AI 开始在 {episodes} 局中自我进化...")
    
    scores = []
    
    for ep in range(episodes):
        s = engine.new_game(seed=random.randint(0, 999999))
        
        while (not s.game_lost) and s.invasions_resolved < 3:
            hand = engine.draw_hand(s)
            legal = engine.legal_actions(s, hand)
            
            # --- 决策阶段 ---
            best_act = None
            if random.random() < epsilon:
                # 探索：瞎选
                best_act = random.choice(legal)
                next_s = copy.deepcopy(s)
                engine.apply_action(next_s, hand, best_act)
            else:
                # 利用：用神经网络评估每一个动作后的未来状态
                max_q = -float('inf')
                for act in legal:
                    temp_s = copy.deepcopy(s)
                    engine.apply_action(temp_s, hand, act)
                    q_val = policy_net(get_state_vector(temp_s)).item()
                    if q_val > max_q:
                        max_q = q_val
                        best_act = act
                        next_s = temp_s
            
            # 结算入侵
            engine.resolve_invasion_if_needed(next_s)
            
            # --- 奖励塑造 (Reward Shaping) 极度重要 ---
            done = next_s.game_lost or next_s.invasions_resolved >= 3
            reward = 0.0
            
            if next_s.game_lost:
                reward = -20.0 # 死亡惩罚
            elif done:
                reward = engine.score(next_s) * 2.0 # 游戏通关，根据得分给大奖
            else:
                # 存活小奖励，鼓励它活下去
                reward = 0.1 

            # 存入记忆库
            memory.push(get_state_vector(s).numpy(), reward, get_state_vector(next_s).numpy(), done)
            
            s = next_s # 状态推进
            
            # --- 学习阶段 ---
            if len(memory) > BATCH_SIZE:
                b_states, b_rewards, b_next_states, b_dones = memory.sample(BATCH_SIZE)
                
                # 计算当前的 Q 值
                q_values = policy_net(b_states).squeeze()
                
                # 计算目标的 Q 值 (使用老教授 Target Net)
                with torch.no_grad():
                    next_q_values = target_net(b_next_states).squeeze()
                    target_q = b_rewards + (GAMMA * next_q_values * (1 - b_dones))
                
                # 计算误差并反向传播
                loss = F.mse_loss(q_values, target_q)
                optimizer.zero_grad()
                loss.backward()
                # 🚨 梯度裁剪：防止爆炸！
                torch.nn.utils.clip_grad_norm_(policy_net.parameters(), max_norm=1.0)
                optimizer.step()

        # 衰减探索率
        epsilon = max(epsilon_min, epsilon * epsilon_decay)
        
        # 记录分数
        final_s = engine.score(s) if not s.game_lost else 0
        scores.append(final_s)

        # 定期更新老教授大脑 (Target Net)
        if ep % 20 == 0:
            target_net.load_state_dict(policy_net.state_dict())

        # 打印日志
        if (ep + 1) % 50 == 0:
            avg_score = np.mean(scores[-50:])
            print(f"第 {ep+1:05d} 局 | 近50局均分: {avg_score:.2f} | 探索率: {epsilon:.2f} | 记忆库: {len(memory)}")

    # 保存最终神级大脑
    save_path = PROJECT_ROOT / "data" / "dqn_brain_final.pth"
    torch.save(policy_net.state_dict(), save_path)
    print(f"\n✅ DQN 训练圆满结束！无敌的硅基大脑已封印至: {save_path}")

if __name__ == "__main__":
    run_dqn_training(episodes=10000)