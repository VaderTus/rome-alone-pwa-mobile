# scripts/run_evolution.py
import sys
import copy
import time
from pathlib import Path
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.loader import DataRepo
from core.engine import RomeEngine
from core.encoder import RomeStateEncoder
from scripts.train_value_net import RomeValueBrain
from scripts.test_neural_agent import neural_policy

# ==========================================
# 🧬 1. 基因海选：生成 AI 自己打出的数据，并只保留精英
# ==========================================
def self_play_and_filter(brain, encoder, num_games=1000, keep_ratio=0.25):
    print(f"\n⚔️ [基因海选] 现任大脑开始左右互搏打 {num_games} 局...")
    repo = DataRepo(PROJECT_ROOT / "data")
    engine = RomeEngine(repo)
    
    all_games_data = [] # 存储每局的 (score, history_tensors, history_scores)
    start_time = time.time()
    
    for i in range(num_games):
        state = engine.new_game(seed=int(time.time() * 1000) % 1000000 + i)
        history = []
        
        while (not state.game_lost) and state.invasions_resolved < 3:
            state.turn_count += 1
            hand = engine.draw_hand(state)
            if not hand: break
            
            # 记录当前残局视神经
            history.append(encoder.encode(state))
            
            # 大脑自己决策
            legal_acts = engine.legal_actions(state, hand)
            action = neural_policy(engine, state, hand, legal_acts, brain, encoder)
            
            engine.apply_action(state, hand, action)
            engine.resolve_invasion_if_needed(state, policy_name="non_random")
            
        final_score = engine.score(state) if not state.game_lost else 0
        all_games_data.append((final_score, history))
        
        if (i + 1) % 200 == 0:
            print(f"  已打 {i + 1} 局...")

    # 🏆 优胜劣汰核心逻辑：按得分从高到低排序，只取前 keep_ratio (比如前25%) 的神仙局
    all_games_data.sort(key=lambda x: x[0], reverse=True)
    keep_count = int(num_games * keep_ratio)
    elite_games = all_games_data[:keep_count]
    
    elite_threshold = elite_games[-1][0]
    best_score = elite_games[0][0]
    
    print(f"✅ 海选完毕！耗时 {time.time() - start_time:.1f} 秒。")
    print(f"👑 本次最高分: {best_score} | 录取分数线: {elite_threshold} | 录取局数: {keep_count}")
    
    X_data, Y_data = [], []
    for score, history in elite_games:
        for tensor in history:
            X_data.append(tensor)
            Y_data.append(float(score))
            
    return torch.stack(X_data), torch.tensor(Y_data, dtype=torch.float32).unsqueeze(1), elite_threshold

# ==========================================
# 🔥 2. 进化训练炉
# ==========================================
def evolve_brain(generations=5):
    print("="*50)
    print("🌌 启动 AlphaZero 级专家迭代闭环 (Expert Iteration) 🌌")
    print("="*50)
    
    model_path = PROJECT_ROOT / "models" / "value_brain_40d_v1.pth"
    brain = RomeValueBrain()
    brain.load_state_dict(torch.load(model_path, weights_only=True))
    encoder = RomeStateEncoder()
    
    optimizer = optim.Adam(brain.parameters(), lr=0.0005) # 学习率调低，进行精细微调
    criterion = nn.MSELoss()
    
    for gen in range(generations):
        print(f"\n" + "▼"*40)
        print(f"🚀 第 {gen + 1} 世代 (Generation {gen + 1}) 启动")
        
        # 1. 左右互搏并筛选精英 (打1000盘，只留前250盘)
        brain.eval()
        X, Y, threshold = self_play_and_filter(brain, encoder, num_games=1000, keep_ratio=0.25)
        
        if len(X) == 0:
            print("❌ 没有收集到有效数据，跳过本世代。")
            continue
            
        dataset = TensorDataset(X, Y)
        loader = DataLoader(dataset, batch_size=256, shuffle=True)
        
        # 2. 用精英数据重塑大脑
        print(f"🧠 开始用 {len(X)} 条精英残局基因微调大脑 (Epochs: 5)...")
        brain.train()
        for epoch in range(5):
            total_loss = 0
            for batch_x, batch_y in loader:
                optimizer.zero_grad()
                pred_y = brain(batch_x)
                loss = criterion(pred_y, batch_y)
                loss.backward()
                optimizer.step()
                total_loss += loss.item()
            print(f"  [Epoch {epoch+1}/5] Loss: {total_loss/len(loader):.4f}")
            
        # 3. 封存进化后的大脑
        save_path = PROJECT_ROOT / "models" / f"value_brain_40d_gen{gen+1}.pth"
        torch.save(brain.state_dict(), save_path)
        
        # 覆盖主脑
        torch.save(brain.state_dict(), model_path)
        print(f"🎉 第 {gen + 1} 世代进化完成！主脑已覆写。录取线稳定在: {threshold} 分。")

if __name__ == "__main__":
    # 默认跑 3 个世代的进化，您可以去泡杯咖啡，看看它能不能突破 11.5 甚至 12.0 分！
    evolve_brain(generations=3)