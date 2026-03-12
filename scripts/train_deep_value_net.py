# scripts/train_deep_value_net.py
import sys
from pathlib import Path
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset, random_split

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
from scripts.train_value_net import RomeValueBrain

def deep_train():
    print("="*50)
    print("🔥 启动深层炼丹炉 | 目标: 榨干 40 维神经网络潜力")
    print("="*50)
    
    data_path = PROJECT_ROOT / "data" / "_legacy_datasets" / "massive_40d_dataset.pt"
    if not data_path.exists():
        print("❌ 找不到数据！请先运行 scripts/harvest_neural_data.py")
        return
        
    print("⏳ 正在加载海量数据入内存...")
    dataset_dict = torch.load(data_path, weights_only=True)
    X, Y = dataset_dict["X"], dataset_dict["Y"]
    full_dataset = TensorDataset(X, Y)
    
    # 💥 专业操作：切分 80% 训练集(做题)，20% 验证集(考试，防止死记硬背)
    train_size = int(0.8 * len(full_dataset))
    val_size = len(full_dataset) - train_size
    train_dataset, val_dataset = random_split(full_dataset, [train_size, val_size])
    
    train_loader = DataLoader(train_dataset, batch_size=512, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=512, shuffle=False)
    
    print(f"📚 训练集: {train_size} 条 | 📈 验证集: {val_size} 条")
    
    brain = RomeValueBrain()
    optimizer = optim.Adam(brain.parameters(), lr=0.001)
    # 动态学习率：如果验证集考试成绩不再提升，就降低学习率进行微调
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, 'min', patience=3, factor=0.5)
    criterion = nn.MSELoss()
    
    epochs = 30
    best_val_loss = float('inf')
    best_model_weights = None
    
    print("\n🚀 开始深度训练 (Epochs: 30)...")
    for epoch in range(epochs):
        # --- 训练阶段 ---
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
        
        # --- 考试评估阶段 ---
        brain.eval()
        val_loss = 0
        with torch.no_grad():
            for batch_x, batch_y in val_loader:
                pred = brain(batch_x)
                loss = criterion(pred, batch_y)
                val_loss += loss.item()
        avg_val_loss = val_loss / len(val_loader)
        
        # 更新学习率
        scheduler.step(avg_val_loss)
        
        print(f"  [Epoch {epoch+1:02d}/{epochs}] 训练误差: {avg_train_loss:.4f} | 考试误差: {avg_val_loss:.4f}")
        
        # 保存最聪明的那个瞬间
        if avg_val_loss < best_val_loss:
            best_val_loss = avg_val_loss
            best_model_weights = brain.state_dict().copy()
            
    # 封存真正的完全体
    models_dir = PROJECT_ROOT / "models"
    save_path = models_dir / "value_brain_40d_deep.pth"
    torch.save(best_model_weights, save_path)
    print(f"\n🎉 深度炼丹大功告成！最佳考试误差: {best_val_loss:.4f}")
    print(f"💾 终极直觉大脑已封存于: {save_path}")

if __name__ == "__main__":
    deep_train()