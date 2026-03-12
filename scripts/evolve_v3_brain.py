# scripts/evolve_v3_brain.py
import sys
import time
import copy
from pathlib import Path
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset, random_split

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.loader import DataRepo
from core.engine import RomeEngine
from core.encoder import RomeStateEncoder
from scripts.train_deep_value_net_v2 import RomeValueBrainV2
from scripts.run_grand_test import get_v2_brain, v2_policy_fast

# ==========================================
# 🚜 1. 用 12.1分 的 V2 大脑自己打谱，产出高级教材
# ==========================================
def harvest_v2_data(num_games=10000):
    print("="*50)
    print(f"🧬 Alpha 进化启动：让 V2 大脑自己打 {num_games} 局生成高级教材")
    print("="*50)
    
    repo = DataRepo(PROJECT_ROOT / "data")
    engine = RomeEngine(repo)
    encoder = RomeStateEncoder()
    brain_v2, _ = get_v2_brain()
    device = next(brain_v2.parameters()).device
    
    X_data, Y_data = [], []
    total_score = 0
    start_time = time.time()
    
    for i in range(num_games):
        state = engine.new_game(seed=int(time.time() * 1000) % 1000000 + i)
        history_tensors = []
        
        while (not state.game_lost) and state.invasions_resolved < 3:
            state.turn_count += 1
            hand = engine.draw_hand(state)
            if not hand: break
            
            history_tensors.append(encoder.encode(state))
            
            # 使用 V2 的绝顶直觉下棋
            legal_acts = engine.legal_actions(state, hand)
            action = v2_policy_fast(engine, state, hand, legal_acts, device)
            
            engine.apply_action(state, hand, action)
            engine.resolve_invasion_if_needed(state, policy_name="v2_policy")
            
        final_score = engine.score(state) if not state.game_lost else 0.0
        total_score += final_score
        
        for tensor in history_tensors:
            X_data.append(tensor)
            Y_data.append(float(final_score))
            
        if (i + 1) % 1000 == 0:
            print(f"  [产卵中 {i+1}/{num_games}] 耗时: {time.time()-start_time:.1f}s | 实时均分: {total_score/(i+1):.2f}")
            
    print(f"\n✅ 高级教材收集完毕！共 {len(X_data)} 条高质量残局。")
    return torch.stack(X_data), torch.tensor(Y_data, dtype=torch.float32).unsqueeze(1)

# ==========================================
# 🔥 2. 训练更强的 V3 大脑
# ==========================================
def train_v3():
    # 1. 现场生成数据
    X, Y = harvest_v2_data(10000)
    
    full_dataset = TensorDataset(X, Y)
    train_size = int(0.8 * len(full_dataset))
    val_size = len(full_dataset) - train_size
    train_dataset, val_dataset = random_split(full_dataset, [train_size, val_size])
    
    train_loader = DataLoader(train_dataset, batch_size=512, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=512, shuffle=False)
    
    # 2. 召唤新的空白大脑 (结构和V2一样，但权重是新的，准备吸收高级知识)
    print("\n🔥 启动 V3 炼丹炉，准备吸收高级基因...")
    brain_v3 = RomeValueBrainV2()
    # 注：我们从头训练，或者您也可以基于 V2 微调。这里选择从头训练以彻底洗掉 V39 教官的遗留偏见
    
    optimizer = optim.Adam(brain_v3.parameters(), lr=0.001, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, 'min', patience=3, factor=0.5)
    criterion = nn.MSELoss()
    
    epochs = 40
    patience_limit = 6
    patience_counter = 0
    best_val_loss = float('inf')
    best_model_path = PROJECT_ROOT / "models" / "value_brain_40d_v3.pth"
    
    for epoch in range(epochs):
        brain_v3.train()
        train_loss = 0
        for batch_x, batch_y in train_loader:
            optimizer.zero_grad()
            pred = brain_v3(batch_x)
            loss = criterion(pred, batch_y)
            loss.backward()
            optimizer.step()
            train_loss += loss.item()
            
        brain_v3.eval()
        val_loss = 0
        with torch.no_grad():
            for batch_x, batch_y in val_loader:
                pred = brain_v3(batch_x)
                loss = criterion(pred, batch_y)
                val_loss += loss.item()
                
        avg_train = train_loss / len(train_loader)
        avg_val = val_loss / len(val_loader)
        scheduler.step(avg_val)
        
        if avg_val < best_val_loss:
            best_val_loss = avg_val
            torch.save(brain_v3.state_dict(), best_model_path)
            patience_counter = 0
            mark = "⭐ 刷新!"
        else:
            patience_counter += 1
            mark = f"({patience_counter}/{patience_limit})"
            
        print(f"  [Epoch {epoch+1:02d}] 训练误差: {avg_train:.4f} | 考试误差: {avg_val:.4f} {mark}")
        
        if patience_counter >= patience_limit:
            print("🛑 触发早停，V3 进化结束。")
            break
            
    print(f"\n🎉 V3 大脑诞生！已封存于 {best_model_path}。准备用它去大杀四方吧！")

if __name__ == "__main__":
    train_v3()