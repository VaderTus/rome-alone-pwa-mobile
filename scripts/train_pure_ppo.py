# scripts/train_pure_ppo.py
import torch
import torch.optim as optim
import torch.nn.functional as F
from pathlib import Path
import sys
import random
import numpy as np
import signal

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
from core.loader import DataRepo
from core.engine import RomeEngine
from policies.neural_brain import RomePPOBrain

BUILDINGS = ["B_YuanXingJingJiChang", "B_JunTuanYaoSai", "B_DiGuoJinKuang", "B_KaiXuanDiaoSu", "B_DiGuoYinShuiDao"]
MONUMENTS = ["M_DiGuoGuangChang", "M_KaiXuanMen", "M_WanShenMiao", "M_LuoMaDouShouChang", "M_HaDeLiangLingQin", "M_TuLaZhenShiChang"]
ALL_CARDS = [f"C{i:02d}" for i in range(1, 22)]
AMAP = {"TopResource": 0, "Conquest": 1, "Tribute": 2, "Build_Building": 3, "Build_Monument": 4}

def get_state_vector(state):
    feat = [
        state.turn_count / 21.0, state.culture / 9.0, state.military / 9.0, state.industry / 9.0,
        state.occupied_regions() / 7.0, state.invasions_resolved / 3.0
    ]
    for b in BUILDINGS: feat.append(1.0 if b in state.built_buildings else 0.0)
    for m in MONUMENTS: feat.append(state.monument_progress.get(m, 0) / 2.0)
    return torch.tensor(feat, dtype=torch.float32)

def compute_returns(rewards, gamma=0.98):
    returns = []
    R = 0
    for r in reversed(rewards):
        R = r + gamma * R
        returns.insert(0, R)
    returns = torch.tensor(returns, dtype=torch.float32)
    return (returns - returns.mean()) / (returns.std() + 1e-8)

def train_ppo():
    repo = DataRepo(Path("data"))
    engine = RomeEngine(repo)
    brain = RomePPOBrain(input_size=17)
    
    MODEL_PATH = PROJECT_ROOT / "data" / "ppo_rome_brain.pth"
    
    if MODEL_PATH.exists():
        print(f"🔄 发现存档的 AI 大脑，正在唤醒过去的记忆...")
        brain.load_state_dict(torch.load(MODEL_PATH, weights_only=True))
    else:
        print(f"✨ 这是一个全新的婴儿 AI，开始第一次感知世界...")

    optimizer = optim.Adam(brain.parameters(), lr=3e-4)
    
    shutdown_flag = False
    def signal_handler(sig, frame):
        nonlocal shutdown_flag
        print("\n🛑 接收到中断信号！AI 正在打包记忆，请稍候...")
        shutdown_flag = True

    signal.signal(signal.SIGINT, signal_handler)

    batch_size = 2000
    PPO_EPOCHS = 4
    EPSILON = 0.2
    
    print("\n🚀 PPO 神经进化舱已启动！")
    print("💡 提示：你可以随时按 [Ctrl+C] 安全退出，AI 会自动保存进度。下次运行接着练！")
    print("="*60)
    
    episodes = 0
    scores = []
    
    # 全局记忆容器
    states, actions, logprobs, rewards, values = [], [], [], [], []
    
    while not shutdown_flag:
        s = engine.new_game(seed=random.randint(0, 999999))
        
        while (not s.game_lost) and s.invasions_resolved < 3:
            hand = engine.draw_hand(s); legal = engine.legal_actions(s, hand)
            
            mask = torch.zeros(5, dtype=torch.bool)
            buckets = {i: [] for i in range(5)}
            for a in legal:
                tid = AMAP.get(a['kind'], 0) if a['mode']!='top' else 0
                mask[tid] = True; buckets[tid].append(a)
                
            state_t = get_state_vector(s)
            
            with torch.no_grad():
                action_idx, log_prob, value = brain.get_action(state_t, mask)
                
            act = buckets[action_idx][0] if buckets[action_idx] else legal[0]
            
            # --- 🍼 即时奖励塑形 (Reward Shaping) ---
            # 为了防止死循环和瞎玩，每走一步都有明确的奖励引导
            step_r = 0.1 # 存活奖励
            
            # 记录执行动作前的情况
            prev_reg = s.occupied_regions()
            prev_bld = len(s.built_buildings)
            prev_mon = sum(s.monument_progress.values())
            
            engine.apply_action(s, hand, act)
            engine.resolve_invasion_if_needed(s)
            
            # 对比动作后的变化发放奖金
            if s.occupied_regions() > prev_reg: step_r += 2.0
            if len(s.built_buildings) > prev_bld: step_r += 3.0
            if sum(s.monument_progress.values()) > prev_mon: step_r += 4.0

            # 最终审判
            if s.game_lost: 
                step_r -= 20.0 
            elif s.invasions_resolved >= 3: 
                step_r += engine.score(s) * 5.0 # 通关大奖
            
            # 存入全局记忆池
            states.append(state_t)
            actions.append(action_idx)
            logprobs.append(log_prob)
            values.append(value)
            rewards.append(step_r)
            
            # --- 🏋️ 核心：记忆池满了，开始 PPO 撸铁 ---
            if len(states) >= batch_size:
                # 🚨 修复Bug：只对凑齐的这批 batch_size 长度的 memory_rewards 进行计算
                b_returns = compute_returns(rewards)
                
                b_states = torch.stack(states)
                b_actions = torch.tensor(actions, dtype=torch.long)
                b_old_logprobs = torch.stack(logprobs).detach()
                b_values = torch.cat(values).squeeze(-1).detach()
                
                # 确保 Advantage 的维度和长度绝对一致
                b_advantages = b_returns - b_values
                
                from torch.distributions import Categorical
                import torch.nn.functional as F
                
                for _ in range(PPO_EPOCHS):
                    logits, curr_values = brain(b_states)
                    probs = F.softmax(logits, dim=-1)
                    curr_m = Categorical(probs)
                    new_logprobs = curr_m.log_prob(b_actions)
                    
                    ratio = torch.exp(new_logprobs - b_old_logprobs)
                    surr1 = ratio * b_advantages
                    surr2 = torch.clamp(ratio, 1.0 - EPSILON, 1.0 + EPSILON) * b_advantages
                    actor_loss = -torch.min(surr1, surr2).mean()
                    
                    critic_loss = F.mse_loss(curr_values.squeeze(-1), b_returns)
                    entropy_bonus = curr_m.entropy().mean()
                    
                    loss = actor_loss + 0.5 * critic_loss - 0.01 * entropy_bonus
                    
                    optimizer.zero_grad()
                    loss.backward()
                    torch.nn.utils.clip_grad_norm_(brain.parameters(), 0.5)
                    optimizer.step()
                
                # 撸铁结束，清空记忆池
                states, actions, logprobs, rewards, values = [], [], [], [], []
                
        # 记录每局最终成绩
        episodes += 1
        scores.append(engine.score(s) if not s.game_lost else 0)
        
        # 每 100 局打印并存盘
        if episodes % 100 == 0:
            avg_s = np.mean(scores[-100:])
            surv = sum(1 for x in scores[-100:] if x > 0)
            high_r = sum(1 for x in scores[-100:] if x >= 14)
            print(f"🧬 PPO 进化代数 {episodes:05d} | 近100局均分: {avg_s:.2f} | 存活率: {surv}% | 14+胡牌率: {high_r}%")
            torch.save(brain.state_dict(), MODEL_PATH)

    # 安全退出
    print("\n✅ 已安全停止训练！当前大脑的最新形态已封印至 'ppo_rome_brain.pth'。")

if __name__ == "__main__":
    train_ppo()