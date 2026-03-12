# scripts/evolution_chamber.py
import torch
import torch.nn as nn
import torch.optim as optim
from pathlib import Path
import random
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from core.loader import DataRepo
from core.engine import RomeEngine
from policies.neural_brain import RomeValueBrain
from policies.neural_pure_agent import select_action, BUILDINGS, MONUMENTS, ALL_CARDS

def run_evolution(epochs=50, games_per_epoch=200):
    repo = DataRepo(Path("data"))
    engine = RomeEngine(repo)
    
    # 1. 加载我们在预处理阶段训练出的“基础脑”
    MODEL_PATH = PROJECT_ROOT / "data" / "oracle_brain.pth"
    brain = RomeValueBrain(input_size=43)
    if MODEL_PATH.exists():
        brain.load_state_dict(torch.load(MODEL_PATH))
    
    # 切换到训练模式
    brain.train()
    optimizer = optim.Adam(brain.parameters(), lr=0.0001) # 极小的学习率，做微调
    criterion = nn.MSELoss()

    print(f"🧬 开启进化舱！AI 将通过自我搏杀来补全生存本能...")

    for epoch in range(epochs):
        memory = []
        
        # --- 阶段 A：自我对弈，收集经验 ---
        for _ in range(games_per_epoch):
            s = engine.new_game(seed=random.randint(0, 999999))
            history = []
            
            while (not s.game_lost) and s.invasions_resolved < 3:
                hand = engine.draw_hand(s)
                legal = engine.legal_actions(s, hand)
                
                # 💡 探索机制 (Epsilon-Greedy)
                # 15% 的几率，AI 会放弃直觉，去尝试一些它平时不敢干的事
                if random.random() < 0.15:
                    action = random.choice(legal)
                else:
                    action = select_action(engine, s, hand, legal)
                
                # 记录这一手的状态和选择的动作
                # (复用 neural_pure_agent 中的状态构造逻辑)
                base_feat = [
                    s.turn_count / 21.0, s.culture / 9.0, s.military / 9.0, s.industry / 9.0,
                    s.occupied_regions() / 7.0, s.invasions_resolved / 2.0
                ]
                for b in BUILDINGS: base_feat.append(1.0 if b in s.built_buildings else 0.0)
                for m in MONUMENTS: base_feat.append(s.monument_progress.get(m, 0) / 2.0)
                for card_id in ALL_CARDS: base_feat.append(1.0 if card_id in s.discard else 0.0)
                
                act_feat = [
                    1.0 if action['mode'] == 'top' else 0.0,
                    1.0 if action['kind'] == 'Conquest' else 0.0,
                    1.0 if action['kind'] == 'Tribute' else 0.0,
                    1.0 if action['kind'] == 'Build_Building' else 0.0,
                    1.0 if action['kind'] == 'Build_Monument' else 0.0
                ]
                
                full_feat = base_feat + act_feat
                history.append(full_feat)
                
                engine.apply_action(s, hand, action)
                engine.resolve_invasion_if_needed(s)
                
            # --- 评价这局游戏，打上“痛觉”或“快感”标签 ---
            if s.game_lost:
                reward = -1.0  # 痛入骨髓的惩罚
            else:
                score = engine.score(s)
                # 只要及格了就给一点奖励，如果能上 14 分，给巨额奖励
                if score >= 14: reward = 1.0
                elif score >= 10: reward = 0.5
                else: reward = 0.0 # 平庸不奖不罚

            for feat in history:
                memory.append((feat, reward))

        # --- 阶段 B：闭关反思 (反向传播更新大脑) ---
        if memory:
            random.shuffle(memory) # 打乱记忆，防止遗忘
            X = torch.tensor([m[0] for m in memory], dtype=torch.float32)
            y = torch.tensor([m[1] for m in memory], dtype=torch.float32).view(-1, 1)
            
            # 分批次学习
            batch_size = 64
            total_loss = 0
            for i in range(0, len(X), batch_size):
                batch_X = X[i : i+batch_size]
                batch_y = y[i : i+batch_size]
                
                optimizer.zero_grad()
                predictions = brain(batch_X)
                loss = criterion(predictions, batch_y)
                loss.backward()
                optimizer.step()
                total_loss += loss.item()

            print(f"🔄 进化轮次 {epoch+1:02d} | 采样记忆: {len(memory)} 条 | 神经网络痛觉(Loss): {total_loss / (len(X)//batch_size + 1):.4f}")

    # 保存进化后的大脑
    torch.save(brain.state_dict(), MODEL_PATH)
    print("\n✅ 进化完成！新的神经元链路已固化。")

if __name__ == "__main__":
    run_evolution()