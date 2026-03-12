# scripts/rl_finetune_vomega.py
import torch
import torch.nn as nn
import torch.optim as optim
import random
import copy
from pathlib import Path
import sys
import numpy as np
from collections import deque

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
from core.loader import DataRepo
from core.engine import RomeEngine
from policies.neural_brain import RomeValueBrain

# 导入左脑的规则
from policies.mcts_distilled_final import W_BASE, get_next_inv_info

MODEL_PATH = PROJECT_ROOT / "data" / "oracle_brain.pth"
BUILDINGS = ["B_KaiXuanDiaoSu", "B_DiGuoYinShuiDao", "B_JunTuanYaoSai", "B_DiGuoJinKuang", "B_YuanXingJingJiChang"]
MONUMENTS = ["M_WanShenMiao", "M_LuoMaDouShouChang", "M_DiGuoGuangChang", "M_HaDeLiangLingQin", "M_KaiXuanMen", "M_TuLaZhenShiChang"]
ALL_CARDS = [f"C{i:02d}" for i in range(1, 22)]

# ==========================================
# 1. 提取状态的通用函数 (对齐 V-Omega)
# ==========================================
def extract_state_feature(state, act):
    # 删除了导致 Bug 的 c_card 占位行，因为后面的特征提取不需要它
    
    base_feat = [
        state.turn_count / 21.0, state.culture / 9.0, state.military / 9.0, state.industry / 9.0,
        state.occupied_regions() / 7.0, state.invasions_resolved / 2.0
    ]
    for b in BUILDINGS: base_feat.append(1.0 if b in state.built_buildings else 0.0)
    for m in MONUMENTS: base_feat.append(state.monument_progress.get(m, 0) / 2.0)
    for c in ALL_CARDS: base_feat.append(1.0 if c in state.discard else 0.0)
    
    act_feat = [
        1.0 if act['mode'] == 'top' else 0.0,
        1.0 if act['kind'] == 'Conquest' else 0.0,
        1.0 if act['kind'] == 'Tribute' else 0.0,
        1.0 if act['kind'] == 'Build_Building' else 0.0,
        1.0 if act['kind'] == 'Build_Monument' else 0.0
    ]
    # 这里的长度刚好是 6 + 5 + 6 + 21 + 5 = 43维
    return torch.tensor([base_feat + act_feat], dtype=torch.float32)

# ==========================================
# 2. 强化学习主训练环 (RL Loop)
# ==========================================
def run_rl_finetune(episodes=5000):
    repo = DataRepo(Path("data"))
    engine = RomeEngine(repo)
    
    # 加载我们通过 MCTS 录像训练出的“半成品”脑子
    brain = RomeValueBrain(input_size=43)
    if MODEL_PATH.exists():
        brain.load_state_dict(torch.load(MODEL_PATH, weights_only=True))
    else:
        print("❌ 找不到基础脑模型，无法进行微调！")
        return
        
    brain.train()
    # 使用极小的学习率进行微调 (Fine-tuning)，以免破坏已有的知识
    optimizer = optim.Adam(brain.parameters(), lr=1e-5)
    criterion = nn.MSELoss()
    
    memory = deque(maxlen=20000)
    batch_size = 128
    epsilon = 0.1 # 10% 的时间不听脑子的，尝试新路子
    
    print("🚀 启动【教官约束下的自我进化】... 目标：超越 MCTS 的 12 分天花板！")
    
    scores = []
    
    for ep in range(episodes):
        s = engine.new_game(seed=random.randint(0, 999999))
        history_for_this_game = []
        
        while (not s.game_lost) and s.invasions_resolved < 3:
            hand = engine.draw_hand(s)
            legal_actions = engine.legal_actions(s, hand)
            
            # --- 🛡️ 老教官：执行生存初筛 ---
            turn = s.turn_count
            inv_cost, _ = get_next_inv_info(engine, s)
            deck_left = len(s.deck)
            senate_active = s.monument_progress.get("M_DiGuoGuangChang", 0) >= 2
            
            if turn >= 19: red_line = 0
            elif deck_left >= 6: red_line = 1
            elif deck_left >= 3: red_line = max(1, inv_cost - 2)
            else: red_line = inv_cost
            
            safe_actions = []
            for act in legal_actions:
                c_card = repo.card_by_id[act["card_id"]]
                est_m = s.military; est_c = s.culture
                if act['kind'] == "Conquest": est_m -= s.occupied_regions()
                elif act['mode'] == "bottom":
                    est_m -= int(c_card.get("Cost_Military", 0))
                    est_c -= int(c_card.get("Cost_Culture", 0))
                eff_m = (est_m + est_c) if senate_active else est_m
                
                # 如果过了安检，加入安全列表
                if not (turn < 19 and eff_m < red_line and act['kind'] != "TopResource"):
                    safe_actions.append(act)
                    
            if not safe_actions: safe_actions = legal_actions # 必死局，随便选
            
            # --- 🧠 学生：在安全选项里做决定 ---
            best_act = None
            if random.random() < epsilon:
                # 探索：闭着眼瞎选一个安全动作
                best_act = random.choice(safe_actions)
            else:
                # 利用：用脑子给每个安全动作打分
                max_val = -float('inf')
                for act in safe_actions:
                    feat = extract_state_feature(s, act)
                    with torch.no_grad():
                        val = brain(feat).item()
                    if val > max_val:
                        max_val = val
                        best_act = act
            
            # 记录这一手的特征
            chosen_feat = extract_state_feature(s, best_act)
            history_for_this_game.append(chosen_feat)
            
            engine.apply_action(s, hand, best_act)
            engine.resolve_invasion_if_needed(s)
            
        # --- 🎮 游戏结束：复盘与学习 ---
        final_score = engine.score(s)
        scores.append(final_score if not s.game_lost else 0)
        
        # 定义真实价值：18 分 = 1.0, 如果死了就是 -0.5
        real_value = (final_score / 18.0) if not s.game_lost else -0.5
        
        # 只有好局（>=14分）或者惨败局，才存入记忆库进行强化记忆
        if final_score >= 14 or s.game_lost:
            for feat in history_for_this_game:
                memory.append((feat, real_value))
                
        # --- 🏋️ 开始撸铁 (训练大脑) ---
        if len(memory) > batch_size * 5:
            batch = random.sample(memory, batch_size)
            bx = torch.cat([m[0] for m in batch])
            by = torch.tensor([m[1] for m in batch], dtype=torch.float32).view(-1, 1)
            
            optimizer.zero_grad()
            preds = brain(bx)
            loss = criterion(preds, by)
            loss.backward()
            optimizer.step()
            
        # 打印进度
        if (ep + 1) % 100 == 0:
            avg_s = np.mean(scores[-100:])
            win_r = sum(1 for x in scores[-100:] if x > 0) / 100
            high_r = sum(1 for x in scores[-100:] if x >= 14) / 100
            print(f"🧬 进化代数 {ep+1:05d} | 均分: {avg_s:.2f} | 存活率: {win_r:.0%} | 14+率: {high_r:.0%}")
            
            # 如果有了极其明显的进步，存盘！
            if avg_s > 11.5:
                torch.save(brain.state_dict(), PROJECT_ROOT / "data" / "rl_god_brain.pth")

if __name__ == "__main__":
    run_rl_finetune(episodes=50000) # 可以挂机跑 5 万局