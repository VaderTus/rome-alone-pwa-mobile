# scripts/train_ai.py
import torch
import torch.nn as nn
import torch.optim as optim
import pandas as pd
from pathlib import Path
from torch.utils.data import DataLoader, TensorDataset
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

def train_god_policy():
    data_path = PROJECT_ROOT / "data" / "god_training_data.csv"
    if not data_path.exists():
        print("❌ 找不到上帝教材！请先运行 python scripts/prep_god_data.py")
        return

    df = pd.read_csv(data_path, header=None)
    
    # 动态获取维度：除了最后一列（标签），前面全都是特征
    input_dim = df.shape[1] - 1 
    
    X = torch.tensor(df.iloc[:, :-1].values, dtype=torch.float32)
    y = torch.tensor(df.iloc[:, -1].values, dtype=torch.long)
    
    loader = DataLoader(TensorDataset(X, y), batch_size=64, shuffle=True)
    
    class GodPolicyBrain(nn.Module):
        def __init__(self, input_size):
            super(GodPolicyBrain, self).__init__()
            self.fc1 = nn.Linear(input_size, 512)
            self.bn1 = nn.LayerNorm(512)
            self.fc2 = nn.Linear(512, 512)
            self.fc3 = nn.Linear(512, 256)
            self.output = nn.Linear(256, 5)

        def forward(self, x):
            x = torch.relu(self.bn1(self.fc1(x)))
            res = x
            x = torch.relu(self.fc2(x))
            x = x + res 
            x = torch.relu(self.fc3(x))
            return self.output(x)

    model = GodPolicyBrain(input_size=input_dim)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.AdamW(model.parameters(), lr=0.002, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=150)

    print(f"🔥 启动【神之降维】训练...")
    print(f"   输入特征: {input_dim} 维 | 样本数: {len(df)}")
    
    for epoch in range(150): 
        model.train()
        correct = 0
        total = 0
        total_loss = 0
        
        for bx, by in loader:
            optimizer.zero_grad()
            logits = model(bx)
            loss = criterion(logits, by)
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
            _, predicted = torch.max(logits.data, 1)
            total += by.size(0)
            correct += (predicted == by).sum().item()
            
        scheduler.step()
        
        if (epoch+1) % 10 == 0:
            print(f"Epoch {epoch+1:03d}/150 | 准确率: {100 * correct / total:.2f}% | Loss: {total_loss/len(loader):.4f}")

    out_path = PROJECT_ROOT / "data" / "god_brain.pth"
    torch.save(model.state_dict(), out_path)
    print(f"\n✅ 神之基因已封印！保存至: {out_path}")

if __name__ == "__main__":
    train_god_policy()# scripts/train_ai.py
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

def train_god_value():
    data_path = PROJECT_ROOT / "data" / "god_value_training_v1.csv"
    if not data_path.exists():
        print("❌ 找不到上帝教材！请先运行 run_god_factory_v2.py")
        return

    print("📊 正在加载【神级状态评估】教材...")
    # 读取 CSV，无表头
    df = pd.read_csv(data_path, header=None)
    
    # 前 38 列是输入特征 (X)，最后 1 列是上帝的最终得分归一化值 (y)
    input_dim = df.shape[1] - 1 
    
    X = torch.tensor(df.iloc[:, :-1].values, dtype=torch.float32)
    y = torch.tensor(df.iloc[:, -1].values, dtype=torch.float32).view(-1, 1)
    
    loader = DataLoader(TensorDataset(X, y), batch_size=128, shuffle=True)
    
    # 🧠 加载我们设计的 RomeValueBrain
    model = RomeValueBrain(input_size=input_dim)
    
    # 既然是预测分数（连续值），我们使用 MSELoss（均方误差）
    criterion = nn.MSELoss()
    # 使用 AdamW，加上微小的权重衰减，防止过拟合这几千局录像
    optimizer = optim.AdamW(model.parameters(), lr=0.001, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=100)

    print(f"🔥 启动【神之眼】训练... (输入特征: {input_dim} 维)")
    
    for epoch in range(100): # 100遍足够它记住这些状态了
        model.train()
        total_loss = 0
        
        for bx, by in loader:
            optimizer.zero_grad()
            pred_value = model(bx)
            loss = criterion(pred_value, by)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
            
        scheduler.step()
        
        if (epoch+1) % 10 == 0:
            avg_loss = total_loss / len(loader)
            print(f"Epoch {epoch+1:03d}/100 | 误差(MSELoss): {avg_loss:.6f}")

    out_path = PROJECT_ROOT / "data" / "god_brain.pth"
    torch.save(model.state_dict(), out_path)
    print(f"\n✅ 上帝的直觉已封印！保存至: {out_path}")

if __name__ == "__main__":
    train_god_policy = train_god_value()