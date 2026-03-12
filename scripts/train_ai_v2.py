# scripts/train_ai_v2.py
import torch
import torch.nn as nn
import torch.optim as optim
import pandas as pd
from pathlib import Path
from torch.utils.data import DataLoader, TensorDataset
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
from policies.neural_brain import RomeValueBrain

def train():
    data_path = PROJECT_ROOT / "data" / "hd_training_data_v2.csv"
    if not data_path.exists():
        print("❌ 找不到训练数据！请确保 harvest_hd_data_v2.py 已跑完。")
        return

    print("📊 正在加载几十万条全知视角对局数据...")
    df = pd.read_csv(data_path)
    
    # 提取输入特征 X 和目标预测值 y
    X = torch.tensor(df.drop('target_value', axis=1).values, dtype=torch.float32)
    y = torch.tensor(df['target_value'].values, dtype=torch.float32).view(-1, 1)
    
    loader = DataLoader(TensorDataset(X, y), batch_size=512, shuffle=True)
    model = RomeValueBrain(input_size=X.shape[1]) # 自动匹配维度
    
    criterion = nn.MSELoss()
    optimizer = optim.AdamW(model.parameters(), lr=0.001, weight_decay=1e-4)

    print(f"🔥 启动神经网络深度灌录... (特征维度: {X.shape[1]})")
    for epoch in range(100):
        model.train()
        total_loss = 0
        for bx, by in loader:
            optimizer.zero_grad()
            loss = criterion(model(bx), by)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
        
        if (epoch+1) % 5 == 0:
            print(f"修炼进度: {epoch+1}/100 | 平均预测误差(Loss): {total_loss/len(loader):.6f}")

    torch.save(model.state_dict(), PROJECT_ROOT / "data" / "oracle_brain.pth")
    print("✅ 大脑已固化，保存为 oracle_brain.pth")

if __name__ == "__main__":
    train()