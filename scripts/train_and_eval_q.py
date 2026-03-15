# scripts/train_and_eval_q.py
import sys
import copy
import time
from pathlib import Path
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset, random_split

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.loader import DataRepo
from core.engine import RomeEngine
from core.encoder import RomeStateEncoder
from scripts.harvest_q_data import encode_action

# ==========================================
# 🧠 1. 全新的 Q 动作价值网络 (67 维 -> 1 维)
# ==========================================
class RomeQBrain(nn.Module):
    def __init__(self):
        super(RomeQBrain, self).__init__()
        # 40维状态 + 27维动作 = 67维输入
        self.fc1 = nn.Linear(67, 256)
        self.ln1 = nn.LayerNorm(256)
        self.fc2 = nn.Linear(256, 128)
        self.ln2 = nn.LayerNorm(128)
        self.fc3 = nn.Linear(128, 64)
        self.output = nn.Linear(64, 1)

    def forward(self, state_tensor, action_tensor):
        x = torch.cat([state_tensor, action_tensor], dim=1) # 融合状态和动作
        x = F.leaky_relu(self.ln1(self.fc1(x)))
        x = F.leaky_relu(self.ln2(self.fc2(x)))
        x = F.leaky_relu(self.fc3(x))
        return self.output(x)

# ==========================================
# 🔥 2. Q-Learning 炼丹炉
# ==========================================
def train_q_brain():
    print("="*60)
    print("🔥 启动 Q(s,a) 动作价值蒸馏炉...")
    data_path = PROJECT_ROOT / "data" / "_legacy_datasets" / "q_dataset_v1.pt"
    if not data_path.exists():
        print("❌ 找不到 Q 值金矿！请先运行 scripts/harvest_q_data.py")
        return
    
    data = torch.load(data_path, weights_only=True)
    dataset = TensorDataset(data["S"], data["A"], data["Q"])
    
    train_size = int(0.8 * len(dataset))
    train_ds, val_ds = random_split(dataset, [train_size, len(dataset) - train_size])
    train_loader = DataLoader(train_ds, batch_size=256, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=256, shuffle=False)
    
    device = torch.device("cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu")
    q_brain = RomeQBrain().to(device)
    
    optimizer = optim.Adam(q_brain.parameters(), lr=0.001, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, 'min', patience=2, factor=0.5)
    criterion = nn.MSELoss()
    
    best_val = float('inf')
    target_path = PROJECT_ROOT / "models" / "q_brain_v1.pth"
    patience = 0
    
    for epoch in range(30):
        q_brain.train()
        for bs, ba, bq in train_loader:
            bs, ba, bq = bs.to(device), ba.to(device), bq.to(device)
            optimizer.zero_grad()
            loss = criterion(q_brain(bs, ba), bq)
            loss.backward()
            optimizer.step()
            
        q_brain.eval()
        val_loss = 0
        with torch.no_grad():
            for bs, ba, bq in val_loader:
                bs, ba, bq = bs.to(device), ba.to(device), bq.to(device)
                val_loss += criterion(q_brain(bs, ba), bq).item()
                
        avg_val = val_loss / len(val_loader)
        scheduler.step(avg_val)
        
        mark = ""
        if avg_val < best_val:
            best_val = avg_val; patience = 0
            torch.save(q_brain.state_dict(), target_path)
            mark = "⭐ 刷新!"
        else: patience += 1
        
        sys.stdout.write(f"\r   ↳ Epoch {epoch+1:02d} | 动作拟合误差: {avg_val:.4f} {mark}")
        sys.stdout.flush()
        if patience >= 4: break
        
    print(f"\n🎉 Q-Brain 炼丹完成！已封存于 {target_path}")

# ==========================================
# ⚔️ 3. Q-Brain 实战策略 (单步极速，对齐深搜)
# ==========================================
def q_policy(engine, state, hand, legal_actions, q_brain, encoder, device):
    if not legal_actions: return {"card_id": hand[0], "mode": "top", "kind": "TopResource", "meta": {}}

    best_act = None
    max_q = -float('inf')
    state_tensor = encoder.encode(state).unsqueeze(0).to(device) # 增加 batch 维度
    
    for act in legal_actions:
        # 物理兜底，防止低级错误
        ns = copy.deepcopy(state)
        engine.apply_action(ns, hand, act)
        if len(ns.deck) == 0:
            engine.resolve_invasion_if_needed(ns, policy_name="non_random")
            if ns.game_lost: continue
            
        # 🧠 直接问 Q-Brain：这步值多少分？
        act_tensor = encode_action(act).unsqueeze(0).to(device)
        with torch.no_grad():
            q_val = q_brain(state_tensor, act_tensor).item()
            
        if q_val > max_q:
            max_q = q_val
            best_act = act

    return best_act if best_act else legal_actions[0]

# ==========================================
# 📊 4. Q-Brain 万局盲打大考
# ==========================================
def evaluate_q_brain(num_games=10000):
    print("="*60)
    print(f"👑 Q-Brain (动作价值大脑) 万局大考启动 👑")
    
    repo = DataRepo(PROJECT_ROOT / "data")
    engine = RomeEngine(repo)
    encoder = RomeStateEncoder()
    device = torch.device("cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu")
    
    q_brain = RomeQBrain()
    q_brain.load_state_dict(torch.load(PROJECT_ROOT / "models" / "q_brain_v1.pth", weights_only=True))
    q_brain.eval()
    q_brain = q_brain.to(device)
    
    t_score, deaths = 0, 0
    start = time.time()
    
    for i in range(num_games):
        state = engine.new_game(seed=i + 888888)
        while not state.game_lost and state.invasions_resolved < 3:
            state.turn_count += 1
            hand = engine.draw_hand(state)
            if not hand: break
            legal_acts = engine.legal_actions(state, hand)
            
            # 使用极速的 Q-Policy
            act = q_policy(engine, state, hand, legal_acts, q_brain, encoder, device)
            engine.apply_action(state, hand, act)
            engine.resolve_invasion_if_needed(state, policy_name="eval_q")
            
        score = engine.score(state) if not state.game_lost else 0
        t_score += score
        if state.game_lost: deaths += 1
        
        if (i+1) % 1000 == 0:
            print(f"   ↳ 批改中: {i+1}/{num_games} | 耗时: {(time.time()-start):.1f}s | 实时均分: {t_score/(i+1):.3f}")
            
    print("="*60)
    print(f"🏆 Q-Brain 万局盲打均分: {t_score/num_games:.3f} 分！")
    print(f"💀 暴毙率: {deaths/num_games*100:.2f}%")
    print("="*60)

if __name__ == "__main__":
    train_q_brain()
    evaluate_q_brain(10000)