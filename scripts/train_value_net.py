# scripts/train_value_net.py
import sys
import time
from pathlib import Path
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import numpy as np

# 动态加载项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.loader import DataRepo
from core.engine import RomeEngine
from core.encoder import RomeStateEncoder
from policies.mcts_distilled_final import select_action as coach_policy

# ==========================================
# 🧠 1. 定义我们真正的“直觉大脑” (40维输入)
# ==========================================
class RomeValueBrain(nn.Module):
    def __init__(self):
        super(RomeValueBrain, self).__init__()
        # 40 维视神经接入 -> 256个神经元的第一层思考
        self.fc1 = nn.Linear(40, 256)
        self.ln1 = nn.LayerNorm(256)
        self.fc2 = nn.Linear(256, 128)
        self.ln2 = nn.LayerNorm(128)
        self.fc3 = nn.Linear(128, 64)
        # 最终输出一个标量：对这局游戏最终得分的“预测期望值”
        self.output = nn.Linear(64, 1)

    def forward(self, x):
        x = F.leaky_relu(self.ln1(self.fc1(x)))
        x = F.leaky_relu(self.ln2(self.fc2(x)))
        x = F.leaky_relu(self.fc3(x))
        return self.output(x)

# ==========================================
# ⚔️ 2. 现场榨取纯净数据 (Self-Play Data Generation)
# ==========================================
def generate_training_data(num_games=2000):
    print(f"⏳ 正在呼叫 V39 教官，开始高强度打谱 {num_games} 局...")
    repo = DataRepo(PROJECT_ROOT / "data")
    engine = RomeEngine(repo)
    encoder = RomeStateEncoder()
    
    X_data = []
    Y_data = []
    
    start_time = time.time()
    for i in range(num_games):
        # 随机种子保证每一局牌序不同
        state = engine.new_game(seed=int(time.time() * 1000) % 1000000 + i)
        history_tensors = []
        
        # 模拟一局游戏
        while (not state.game_lost) and state.invasions_resolved < 3:
            state.turn_count += 1
            hand = engine.draw_hand(state)
            if not hand: break
            legal_acts = engine.legal_actions(state, hand)
            
            # 拍照：记录走这步之前的 40维 局面
            state_tensor = encoder.encode(state)
            history_tensors.append(state_tensor)
            
            # 老教官代打
            action = coach_policy(engine, state, hand, legal_acts)
            engine.apply_action(state, hand, action)
            engine.resolve_invasion_if_needed(state, policy_name="coach")
            
        # 结算这局的最终得分 (死了就是0分)
        final_score = engine.score(state)
        
        # 把最终得分贴在这局游戏拍的所有照片背面
        for tensor in history_tensors:
            X_data.append(tensor)
            Y_data.append(float(final_score))
            
        if (i + 1) % 500 == 0:
            print(f"  已打谱 {i + 1} 局，收集残局样本: {len(X_data)} 条...")
            
    print(f"✅ 打谱完毕！耗时 {time.time() - start_time:.1f} 秒。共榨取绝对纯净样本 {len(X_data)} 条。")
    return torch.stack(X_data), torch.tensor(Y_data, dtype=torch.float32).unsqueeze(1)

# ==========================================
# 🔥 3. 启动炼丹炉 (Training Loop)
# ==========================================
def train():
    print("\n" + "="*40)
    print("🔥 孤城罗马 AI 实验室 - 神经网络炼丹炉启动 🔥")
    print("="*40)
    
    # 1. 准备数据
    X, Y = generate_training_data(num_games=2000) # 若嫌慢可改为 1000
    dataset = TensorDataset(X, Y)
    loader = DataLoader(dataset, batch_size=256, shuffle=True)
    
    # 2. 准备大脑和优化器
    brain = RomeValueBrain()
    optimizer = optim.Adam(brain.parameters(), lr=0.001)
    criterion = nn.MSELoss() # 均方误差：预测分和真实分的差距
    
    epochs = 10
    print(f"\n🚀 开始训练 (Epochs: {epochs}, Batch Size: 256)...")
    
    # 3. 开始炼丹
    for epoch in range(epochs):
        brain.train()
        total_loss = 0
        for batch_x, batch_y in loader:
            optimizer.zero_grad()
            pred_y = brain(batch_x)
            loss = criterion(pred_y, batch_y)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
            
        avg_loss = total_loss / len(loader)
        print(f"  [Epoch {epoch+1:02d}/{epochs}] Loss (平均预测误差平方): {avg_loss:.4f}")
        
    # 4. 封存切片
    models_dir = PROJECT_ROOT / "models"
    models_dir.mkdir(exist_ok=True)
    save_path = models_dir / "value_brain_40d_v1.pth"
    torch.save(brain.state_dict(), save_path)
    print(f"\n🎉 炼丹成功！完美的直觉大脑已封存至: {save_path}")
    print("长官，我们拥有了一个能瞬间看透局势的雷达！准备进入第三步！")

if __name__ == "__main__":
    train()