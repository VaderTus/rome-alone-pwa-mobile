# policies/neural_brain.py
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.distributions import Categorical

# ---------------------------------------------------------
# 1. 基础估值大脑 (用于之前的行为克隆/期望搜索，保留以防你需要跑旧代码)
# ---------------------------------------------------------
class RomeValueBrain(nn.Module):
    def __init__(self, input_size=43): 
        super(RomeValueBrain, self).__init__()
        self.fc1 = nn.Linear(input_size, 1024)
        self.ln1 = nn.LayerNorm(1024)
        self.fc2 = nn.Linear(1024, 512)
        self.ln2 = nn.LayerNorm(512)
        self.fc3 = nn.Linear(512, 256)
        self.output = nn.Linear(256, 1)

    def forward(self, x):
        x = F.leaky_relu(self.ln1(self.fc1(x)))
        x = F.leaky_relu(self.ln2(self.fc2(x)))
        x = F.leaky_relu(self.fc3(x))
        return self.output(x)

# ---------------------------------------------------------
# 2. 🚀 强化学习 PPO 专用双脑 (Actor-Critic 架构)
# ---------------------------------------------------------
class RomePPOBrain(nn.Module):
    def __init__(self, input_size=17, num_actions=5):
        super(RomePPOBrain, self).__init__()
        # 公共特征提取层：理解当前的 17 维战局
        self.shared_fc1 = nn.Linear(input_size, 256)
        self.shared_fc2 = nn.Linear(256, 256)
        
        # 🎭 Actor (演员/右脑)：负责给出行动直觉
        self.actor_fc = nn.Linear(256, 128)
        self.actor_out = nn.Linear(128, num_actions) # 输出 5 个大类的偏好
        
        # 🧐 Critic (评论家/左脑)：负责给这个局面打分，告诉 Actor 刚才那步走得对不对
        self.critic_fc = nn.Linear(256, 128)
        self.critic_out = nn.Linear(128, 1) # 输出 1 个对未来的估值

    def forward(self, x):
        # 1. 公共理解
        x = F.relu(self.shared_fc1(x))
        x = F.relu(self.shared_fc2(x))
        
        # 2. 分头行动
        actor_logits = self.actor_out(F.relu(self.actor_fc(x)))
        state_value = self.critic_out(F.relu(self.critic_fc(x)))
        
        return actor_logits, state_value

    def get_action(self, state_tensor, legal_mask):
        """
        供 PPO 训练和实战调用的核心方法。
        它会自动屏蔽不合法的动作，并吐出决策。
        """
        logits, value = self.forward(state_tensor)
        
        # 将不合法的动作概率屏蔽为极小值 (比如 -10亿)，这样 softmax 之后它的概率就是 0
        masked_logits = logits.masked_fill(~legal_mask, -1e9)
        
        # 转化为概率分布 (加减极其微小的 1e-8 防止除零崩溃)
        probs = F.softmax(masked_logits, dim=-1)
        
        # 🎲 掷骰子选动作：概率大的被选中的机会高，但偶尔也会选概率小的 (保证探索性)
        m = Categorical(probs)
        action_idx = m.sample()
        
        # 返回：选中的动作索引、这个动作的概率对数(用于计算Loss)、评论家打的分
        return action_idx.item(), m.log_prob(action_idx), value