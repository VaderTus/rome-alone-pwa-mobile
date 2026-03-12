# scripts/train_ppo_rome.py
import torch
import torch.optim as optim
import torch.nn.functional as F
from pathlib import Path
import sys
import copy
import numpy as np
import random

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from core.loader import DataRepo
from core.engine import RomeEngine
from policies.ppo_brain import PPOBrain

# --- 特征提取工具 ---
BUILDINGS = ["B_YuanXingJingJiChang", "B_JunTuanYaoSai", "B_DiGuoJinKuang", "B_KaiXuanDiaoSu", "B_DiGuoYinShuiDao"]
MONUMENTS = ["M_DiGuoGuangChang", "M_KaiXuanMen", "M_WanShenMiao", "M_LuoMaDouShouChang", "M_HaDeLiangLingQin", "M_TuLaZhenShiChang"]
AMAP = {"TopResource": 0, "Conquest": 1, "Tribute": 2, "Build_Building": 3, "Build_Monument": 4}

def extract_state(state):
    feat = [
        state.turn_count / 21.0, state.culture / 9.0, state.military / 9.0, state.industry / 9.0,
        state.occupied_regions() / 7.0, state.invasions_resolved / 3.0
    ]
    for b in BUILDINGS: feat.append(1.0 if b in state.built_buildings else 0.0)
    for m in MONUMENTS: feat.append(state.monument_progress.get(m, 0) / 2.0)
    return torch.tensor(feat, dtype=torch.float32)

def train_ppo():
    repo = DataRepo(Path("data"))
    engine = RomeEngine(repo)
    brain = PPOBrain()
    optimizer = optim.Adam(brain.parameters(), lr=0.0003)
    
    # PPO 超参数
    GAMMA = 0.98        
    PPO_CLIP = 0.2      
    UPDATE_EPOCHS = 4   
    MAX_EPISODES = 50000 
    
    print("🚀 PPO 神经进化舱启动！带【生存焦虑】机制，AI 即将觉醒...")

    history_rewards = []
    
    for ep in range(1, MAX_EPISODES + 1):
        s = engine.new_game(seed=random.randint(0, 999999))
        
        # 记录一局游戏的记忆
        memory_states = []
        memory_actions = []
        memory_rewards = []
        memory_masks = []
        
        prev_regions = 1
        prev_buildings = 0
        prev_monus = 0
        
        while (not s.game_lost) and s.invasions_resolved < 3:
            state_tensor = extract_state(s)
            hand = engine.draw_hand(s)
            legal_actions = engine.legal_actions(s, hand)
            
            # 生成合法动作掩码
            legal_mask = torch.zeros(5)
            act_buckets = {i: [] for i in range(5)}
            for act in legal_actions:
                tid = AMAP.get(act['kind'], 0)
                if act['mode'] == 'top': tid = 0
                legal_mask[tid] = 1.0
                act_buckets[tid].append(act)
                
            # 大脑做决定
            with torch.no_grad():
                action_idx, log_prob, value = brain.get_action(state_tensor, legal_mask)
            
            chosen_acts = act_buckets[action_idx]
            final_act = chosen_acts[0] if chosen_acts else legal_actions[0]
            
            engine.apply_action(s, hand, final_act)
            engine.resolve_invasion_if_needed(s)
            
            # ----------------- 🍼 密集奖励塑形 (Reward Shaping) -----------------
            step_reward = 0.0
            
            # 1. 基础发展奖励
            if s.occupied_regions() > prev_regions:
                step_reward += 2.0; prev_regions = s.occupied_regions()
            if len(s.built_buildings) > prev_buildings:
                step_reward += 3.0; prev_buildings = len(s.built_buildings)
            curr_monus = sum(s.monument_progress.values())
            if curr_monus > prev_monus:
                step_reward += 4.0; prev_monus = curr_monus

            # 2. 🛡️ 核心修正：即时生存焦虑惩罚 (Survival Anxiety)
            # 不要等它死了再惩罚，一旦它发现自己没钱过冬，立刻每回合持续扣分！
            idx = min(s.invasions_resolved + 1, 3)
            inv_row = engine.repo.invasions[engine.repo.invasions["Invasion_Order"] == idx]
            inv_cost = int(inv_row.iloc[0]["Pay_Military_To_Avoid"]) if not inv_row.empty else 0
            
            senate_active = s.monument_progress.get("M_DiGuoGuangChang", 0) >= 2
            eff_mil = (s.military + s.culture) if senate_active else s.military
            
            if eff_mil < inv_cost and s.turn_count < 19:
                dist_to_inv = 7 - (s.turn_count - 1) % 7
                anxiety = (inv_cost - eff_mil) / max(1, dist_to_inv)
                step_reward -= anxiety * 2.0 # 持续电击它，直到它去拿军事资源！

            # 3. 结果奖励
            if s.game_lost: 
                step_reward -= 50.0 # 加大死亡惩罚，震慑它
            elif s.invasions_resolved >= 3: 
                step_reward += engine.score(s) * 5.0 # 活到最后，按总分发超级大奖
            # -------------------------------------------------------------------------

            # 存入纯数据记忆
            memory_states.append(state_tensor)
            memory_actions.append(action_idx)
            memory_rewards.append(step_reward)
            memory_masks.append(legal_mask)

        # --- 游戏结束，准备 PPO 学习 ---
        final_score = engine.score(s) if not s.game_lost else 0
        history_rewards.append(final_score)
        
        # 计算折扣回报
        returns = []
        R = 0
        for r in reversed(memory_rewards):
            R = r + GAMMA * R
            returns.insert(0, R)
        returns = torch.tensor(returns, dtype=torch.float32)
        returns = (returns - returns.mean()) / (returns.std() + 1e-8)
        
        # 把记忆转化为 Batch Tensor
        b_states = torch.stack(memory_states)
        b_actions = torch.tensor(memory_actions, dtype=torch.long)
        b_masks = torch.stack(memory_masks)
        
        # 记录旧策略的概率
        with torch.no_grad():
            old_action_probs, old_values = brain(b_states)
            old_masked_probs = old_action_probs * b_masks
            old_masked_probs = old_masked_probs / (old_masked_probs.sum(dim=-1, keepdim=True) + 1e-8)
            old_log_probs = torch.log(old_masked_probs.gather(1, b_actions.view(-1, 1)).squeeze(-1) + 1e-8)
            
        advantages = returns - old_values.squeeze(-1).detach()
        
        # --- PPO 更新循环 ---
        for _ in range(UPDATE_EPOCHS):
            action_probs, values = brain(b_states)
            masked_probs = action_probs * b_masks
            masked_probs = masked_probs / (masked_probs.sum(dim=-1, keepdim=True) + 1e-8)
            new_log_probs = torch.log(masked_probs.gather(1, b_actions.view(-1, 1)).squeeze(-1) + 1e-8)
            
            ratio = torch.exp(new_log_probs - old_log_probs)
            
            surr1 = ratio * advantages
            surr2 = torch.clamp(ratio, 1.0 - PPO_CLIP, 1.0 + PPO_CLIP) * advantages
            actor_loss = -torch.min(surr1, surr2).mean()
            
            critic_loss = F.mse_loss(values.squeeze(-1), returns)
            
            entropy = -(masked_probs * torch.log(masked_probs + 1e-8)).sum(dim=-1).mean()
            loss = actor_loss + 0.5 * critic_loss - 0.05 * entropy # 稍微加大探索欲
            
            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(brain.parameters(), 0.5) 
            optimizer.step()

        if ep % 100 == 0:
            avg_score = np.mean(history_rewards[-100:])
            print(f"🧬 第 {ep:05d} 代 | 近100局均分: {avg_score:.2f} | 胜率: {sum(1 for x in history_rewards[-100:] if x > 0)}%")
            torch.save(brain.state_dict(), PROJECT_ROOT / "data/ppo_brain.pth")

if __name__ == "__main__":
    train_ppo()