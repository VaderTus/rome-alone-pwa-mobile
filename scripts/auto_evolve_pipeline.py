# scripts/auto_evolve_pipeline.py
import sys
import time
import copy
from pathlib import Path
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset, random_split

# 动态加载项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.loader import DataRepo
from core.engine import RomeEngine
from core.encoder import RomeStateEncoder
from scripts.train_deep_value_net_v2 import RomeValueBrainV2

# ==========================================
# ⚙️ 核心配置 (您可以随意修改)
# ==========================================
HARVEST_GAMES = 10000    # 每代自己打多少局来生成教材
EVAL_GAMES = 10000       # 每代考多少局来定级
MAX_EPOCHS = 40          # 每代最多炼丹多少轮
PATIENCE = 5             # 考试成绩不提升几轮就早停
START_GEN = 3            # 我们现在已经有 V3 了，接下来训练 V4
MAX_GENERATIONS = 10     # 计划自动进化多少代

# ==========================================
# 🧠 统一的 AI 决策中枢
# ==========================================
def get_action(engine, state, hand, legal_actions, brain, encoder, device):
    if not legal_actions: return {"card_id": hand[0], "mode": "top", "kind": "TopResource", "meta": {}}
    best_action = None
    max_value = -float('inf')
    for act in legal_actions:
        next_state = copy.deepcopy(state)
        engine.apply_action(next_state, hand, act)
        
        # 死亡红线
        if len(next_state.deck) == 0:
            engine.resolve_invasion_if_needed(next_state, policy_name="non_random")
            if next_state.game_lost: continue 
                
        tensor_state = encoder.encode(next_state).to(device)
        with torch.no_grad():
            val = brain(tensor_state).item()
        if val > max_value:
            max_value = val
            best_action = act
    return best_action if best_action else legal_actions[0]

# ==========================================
# 🚜 阶段一：自动挖掘高质量数据
# ==========================================
def harvest_data(gen_name, source_model_path, num_games):
    print(f"\n" + "▼"*50)
    print(f"🚜 [阶段 1/3] {gen_name} 正在高强度打谱收集教材...")
    repo = DataRepo(PROJECT_ROOT / "data")
    engine = RomeEngine(repo)
    encoder = RomeStateEncoder()
    
    brain = RomeValueBrainV2()
    brain.load_state_dict(torch.load(source_model_path, weights_only=True))
    brain.eval()
    device = torch.device("cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu")
    brain = brain.to(device)
    
    X_data, Y_data = [], []
    total_score, deaths = 0, 0
    start_time = time.time()
    
    for i in range(num_games):
        state = engine.new_game(seed=int(time.time() * 1000) % 1000000 + i)
        history = []
        while not state.game_lost and state.invasions_resolved < 3:
            state.turn_count += 1
            hand = engine.draw_hand(state)
            if not hand: break
            
            history.append(encoder.encode(state))
            legal_acts = engine.legal_actions(state, hand)
            action = get_action(engine, state, hand, legal_acts, brain, encoder, device)
            engine.apply_action(state, hand, action)
            engine.resolve_invasion_if_needed(state, policy_name="auto")
            
        score = engine.score(state) if not state.game_lost else 0.0
        total_score += score
        if state.game_lost: deaths += 1
        
        for t in history:
            X_data.append(t)
            Y_data.append(float(score))
            
        if (i + 1) % 2000 == 0:
            print(f"   ↳ 进度: {i+1}/{num_games} | 耗时: {time.time()-start_time:.1f}s | 实时均分: {total_score/(i+1):.2f}")
            
    print(f"✅ 教材采集完毕！共 {len(X_data)} 条残局数据。")
    return torch.stack(X_data), torch.tensor(Y_data, dtype=torch.float32).unsqueeze(1)

# ==========================================
# 🔥 阶段二：自动炼丹 (微调升级)
# ==========================================
def train_new_generation(X, Y, source_model_path, target_model_path):
    print(f"\n🔥 [阶段 2/3] 开启基因重组炼丹炉...")
    dataset = TensorDataset(X, Y)
    train_size = int(0.8 * len(dataset))
    val_size = len(dataset) - train_size
    train_ds, val_ds = random_split(dataset, [train_size, val_size])
    
    train_loader = DataLoader(train_ds, batch_size=512, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=512, shuffle=False)
    
    brain = RomeValueBrainV2()
    # 继承上一代的记忆，站在巨人的肩膀上继续微调
    brain.load_state_dict(torch.load(source_model_path, weights_only=True))
    device = torch.device("cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu")
    brain = brain.to(device)
    
    # 学习率设低一点，因为是微调
    optimizer = optim.Adam(brain.parameters(), lr=0.0005, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, 'min', patience=2, factor=0.5)
    criterion = nn.MSELoss()
    
    best_val_loss = float('inf')
    patience_cnt = 0
    
    for epoch in range(MAX_EPOCHS):
        brain.train()
        train_loss = 0
        for bx, by in train_loader:
            bx, by = bx.to(device), by.to(device)
            optimizer.zero_grad()
            pred = brain(bx)
            loss = criterion(pred, by)
            loss.backward()
            optimizer.step()
            train_loss += loss.item()
            
        brain.eval()
        val_loss = 0
        with torch.no_grad():
            for bx, by in val_loader:
                bx, by = bx.to(device), by.to(device)
                val_loss += criterion(brain(bx), by).item()
                
        avg_train = train_loss / len(train_loader)
        avg_val = val_loss / len(val_loader)
        scheduler.step(avg_val)
        
        mark = ""
        if avg_val < best_val_loss:
            best_val_loss = avg_val
            torch.save(brain.state_dict(), target_model_path)
            patience_cnt = 0
            mark = "⭐ 进化!"
        else:
            patience_cnt += 1
            mark = f"({patience_cnt}/{PATIENCE})"
            
        print(f"   ↳ Epoch {epoch+1:02d} | 训练误差: {avg_train:.4f} | 考试误差: {avg_val:.4f} {mark}")
        if patience_cnt >= PATIENCE:
            print("   🛑 潜能已榨干，本世代炼丹结束。")
            break

# ==========================================
# 📊 阶段三：残酷的大考定级
# ==========================================
def evaluate_brain(model_path, num_games):
    print(f"\n📊 [阶段 3/3] 万局封神大考鉴定新大脑实力...")
    repo = DataRepo(PROJECT_ROOT / "data")
    engine = RomeEngine(repo)
    encoder = RomeStateEncoder()
    
    brain = RomeValueBrainV2()
    brain.load_state_dict(torch.load(model_path, weights_only=True))
    brain.eval()
    device = torch.device("cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu")
    brain = brain.to(device)
    
    total_score, deaths = 0, 0
    start_time = time.time()
    
    # 强制用一个固定的评测考卷种子池，保证公平对比
    for i in range(num_games):
        state = engine.new_game(seed=i + 999999) 
        while not state.game_lost and state.invasions_resolved < 3:
            state.turn_count += 1
            hand = engine.draw_hand(state)
            if not hand: break
            legal_acts = engine.legal_actions(state, hand)
            action = get_action(engine, state, hand, legal_acts, brain, encoder, device)
            engine.apply_action(state, hand, action)
            engine.resolve_invasion_if_needed(state, policy_name="eval")
            
        score = engine.score(state) if not state.game_lost else 0
        total_score += score
        if state.game_lost: deaths += 1
        
        if (i + 1) % 2000 == 0:
            print(f"   ↳ 批改中: {i+1}/{num_games} | 耗时: {time.time()-start_time:.1f}s")
            
    avg_score = total_score / num_games
    print(f"🏆 大考揭榜 -> 综合均分: {avg_score:.3f} | 暴毙率: {deaths/num_games*100:.2f}%")
    return avg_score

# ==========================================
# 🌌 主引擎循环
# ==========================================
def run_pipeline():
    print("="*60)
    print("🌌 Alpha Rome 自动化机械飞升引擎已启动 🌌")
    print("="*60)
    
    models_dir = PROJECT_ROOT / "models"
    
    current_gen = START_GEN
    current_model = models_dir / f"value_brain_40d_v{current_gen}.pth"
    
    if not current_model.exists():
        print(f"❌ 找不到初始大脑 {current_model}！请检查文件名。")
        return
        
    for _ in range(MAX_GENERATIONS):
        next_gen = current_gen + 1
        next_model = models_dir / f"value_brain_40d_v{next_gen}.pth"
        
        print("\n" + "🌟"*20)
        print(f"  开始繁衍第 {next_gen} 世代 (Generation {next_gen})")
        print("🌟"*20)
        
        # 1. 用老大脑打谱
        X, Y = harvest_data(f"V{current_gen}", current_model, HARVEST_GAMES)
        
        # 2. 训练新大脑
        train_new_generation(X, Y, current_model, next_model)
        
        # 3. 评测新大脑
        score = evaluate_brain(next_model, EVAL_GAMES)
        
        print(f"\n🎉 世代交替完成！V{next_gen} 诞生，它的战斗力定格在 {score:.3f} 分！")
        
        # 指针移动，新大脑变成老大脑
        current_gen = next_gen
        current_model = next_model

if __name__ == "__main__":
    run_pipeline()