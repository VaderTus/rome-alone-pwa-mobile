# policies/ppo_brain.py
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.distributions import Categorical

class PPOBrain(nn.Module):
    def __init__(self, input_size=17, num_actions=5):
        super(PPOBrain, self).__init__()
        # 公共的感官提取层 (看懂局面)
        self.shared_fc1 = nn.Linear(input_size, 256)
        self.shared_fc2 = nn.Linear(256, 256)
        
        # 🧠 右脑：Actor (演员) - 负责输出 5 种动作的偏好
        self.actor_fc = nn.Linear(256, 128)
        self.actor_out = nn.Linear(128, num_actions)
        
        # 🧠 左脑：Critic (评论家) - 负责预测这个局面的未来总得分
        self.critic_fc = nn.Linear(256, 128)
        self.critic_out = nn.Linear(128, 1)

    def forward(self, x):
        # 公共视觉处理
        x = F.relu(self.shared_fc1(x))
        x = F.relu(self.shared_fc2(x))
        
        # 演员输出动作概率分布
        actor_logits = self.actor_out(F.relu(self.actor_fc(x)))
        action_probs = F.softmax(actor_logits, dim=-1)
        
        # 评论家输出局面的估值
        state_value = self.critic_out(F.relu(self.critic_fc(x)))
        
        return action_probs, state_value

    def get_action(self, state_tensor, legal_action_mask):
        """根据合法动作的遮罩，采样一个动作，并返回对数概率"""
        action_probs, state_value = self.forward(state_tensor)
        
        # 屏蔽掉那些不合法的动作 (比如没钱盖楼，盖楼的概率强制归0)
        masked_probs = action_probs * legal_action_mask
        if masked_probs.sum() == 0: 
            # 防止除以 0 崩溃，如果全被屏蔽了，给个平均概率
            masked_probs = legal_action_mask / (legal_action_mask.sum() + 1e-8)
        
        # 重新归一化概率
        masked_probs = masked_probs / masked_probs.sum()
        
        # 🎲 掷骰子：根据概率分布采样一个动作 (保证了 AI 具有探索精神)
        m = Categorical(masked_probs)
        action_idx = m.sample()
        
        return action_idx.item(), m.log_prob(action_idx), state_value