# scripts/train_deep_value_net_v2.py
import sys
from pathlib import Path
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset, random_split

# 动态加载项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# ==========================================
# 🧠 升级版大脑：加入 Dropout 防止死记硬背
# ==========================================
class RomeValueBrainV2(nn.Module):
    def __init__(self):
        super(RomeValueBrainV2, self).__init__()
        # 40维视神经 -> 256
        self.fc1 = nn.Linear(40, 256)
        self.ln1 = nn.LayerNorm(256)
        self.drop1 = nn.Dropout(p=0.2) # 🎲 随机丢弃 20% 神经元
        
        # 256 -> 128
        self.fc2 = nn.Linear(256, 128)
        self.ln2 = nn.LayerNorm(128)
        self.drop2 = nn.Dropout(p=0.2) # 🎲
        
        # 128 -> 64
        self.fc3 = nn.Linear(128, 64)
        self.drop3 = nn.Dropout(p=0.1) # 🎲 微量丢弃
        
        # 最终输出
        self.output = nn.Linear(64, 1)

    def forward(self, x):
        x = F.leaky_relu(self.ln1(self.fc1(x)))
        x = self.drop1(x) # 训练时生效，实战时会自动关闭
        
        x = F.leaky_relu(self.ln2(self.fc2(x)))
        x = self.drop2(x)
        
        x = F.leaky_relu(self.fc3(x))
        x = self.drop3(x)
        
        return self.output(x)

# ==========================================
# 🔥 稳健型炼丹流程
# ==========================================
def train_v2():
    print("="*50)
    print("🔥 启动 V2 稳健型炼丹炉 | 目标: 抗过拟合，追求泛化能力")
    print("   (包含: Dropout, Weight Decay, Early Stopping)")
    print("="*50)
    
    # 1. 加载数据
    data_path = PROJECT_ROOT / "data" / "_legacy_datasets" / "massive_40d_dataset.pt"
    if not data_path.exists():
        print("❌ 找不到数据！请先运行 scripts/harvest_neural_data.py")
        return
    
    print("⏳ 加载数据中...")
    dataset_dict = torch.load(data_path, weights_only=True)
    full_dataset = TensorDataset(dataset_dict["X"], dataset_dict["Y"])
    
    # 切分数据集: 80% 训练，20% 考试
    train_size = int(0.8 * len(full_dataset))
    val_size = len(full_dataset) - train_size
    train_dataset, val_dataset = random_split(full_dataset, [train_size, val_size])
    
    train_loader = DataLoader(train_dataset, batch_size=512, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=512, shuffle=False)
    
    print(f"📚 训练集: {train_size} 条 | 📈 验证集: {val_size} 条")
    
    # 2. 初始化 V2 大脑
    brain = RomeValueBrainV2()
    
    # ⚙️ 优化器升级：加入 weight_decay (L2正则化)，惩罚过大的权重
    optimizer = optim.Adam(brain.parameters(), lr=0.001, weight_decay=1e-4)
    
    # ⚠️ 修复：移除新版 PyTorch 不支持的 verbose 参数
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, 'min', patience=3, factor=0.5)
    criterion = nn.MSELoss()
    
    # 3. 训练配置
    epochs = 50 # 设大一点，反正有早停
    patience_limit = 7 # 如果连续 7 轮考试成绩没提升，就触发早停
    patience_counter = 0
    best_val_loss = float('inf')
    
    models_dir = PROJECT_ROOT / "models"
    models_dir.mkdir(exist_ok=True)
    best_model_path = models_dir / "value_brain_40d_v2.pth"
    
    print(f"\n🚀 开始 V2 训练 (Max Epochs: {epochs}, Patience: {patience_limit})...")
    
    for epoch in range(epochs):
        # --- 训练模式 (Dropout 生效，增加学习难度) ---
        brain.train()
        train_loss = 0
        for batch_x, batch_y in train_loader:
            optimizer.zero_grad()
            pred = brain(batch_x)
            loss = criterion(pred, batch_y)
            loss.backward()
            optimizer.step()
            train_loss += loss.item()
        avg_train_loss = train_loss / len(train_loader)
        
        # --- 考试模式 (Dropout 关闭，全力输出) ---
        brain.eval()
        val_loss = 0
        with torch.no_grad():
            for batch_x, batch_y in val_loader:
                pred = brain(batch_x)
                loss = criterion(pred, batch_y)
                val_loss += loss.item()
        avg_val_loss = val_loss / len(val_loader)
        
        # 通知调度器根据考试成绩调整学习率
        scheduler.step(avg_val_loss)
        
        # --- 状态打印与早停逻辑 ---
        improvement_mark = ""
        if avg_val_loss < best_val_loss:
            best_val_loss = avg_val_loss
            # 只有创了新纪录，才存盘！保证存在硬盘里的永远是最巅峰的状态
            torch.save(brain.state_dict(), best_model_path)
            patience_counter = 0
            improvement_mark = "⭐ 刷新纪录，已存盘!"
        else:
            patience_counter += 1
            improvement_mark = f"(未提升 {patience_counter}/{patience_limit})"
            
        print(f"  [Epoch {epoch+1:02d}] 训练误差: {avg_train_loss:.4f} | 考试误差: {avg_val_loss:.4f} {improvement_mark}")
        
        # 触发早停
        if patience_counter >= patience_limit:
            print(f"\n🛑 触发早停机制！模型在第 {epoch + 1 - patience_limit} 轮后不再进化。防止过拟合，提前结束。")
            break

    print(f"\n🎉 V2 炼丹大功告成！最佳考试误差锁定在: {best_val_loss:.4f}")
    print(f"💾 经过抗过拟合武装的【V2 大脑】已封存于: {best_model_path}")

if __name__ == "__main__":
    train_v2()