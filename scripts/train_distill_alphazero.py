# scripts/train_distill_alphazero.py
import sys
import copy
import time
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
# ⚙️ 实验参数 (速通验证版)
# ==========================================
HARVEST_GAMES = 500       # 提纯 500 局，足以验证理论
NUM_FUTURES = 5           # 师傅算 5 种未来
EVAL_GAMES = 2000         # 徒弟考试，跑 2000 局挤干水分

# ==========================================
# 🌌 核心：带“读心术”的深蓝引擎
# ==========================================
def deep_search_with_value(engine, state, hand, legal_actions, brain, encoder, device):
    """
    不仅返回最佳动作，还返回师傅算出来的【绝对期望分】！
    """
    if not legal_actions: 
        return {"card_id": hand[0], "mode": "top", "kind": "TopResource", "meta": {}}, 0.0

    best_action = None
    max_expected_value = -float('inf')

    for act in legal_actions:
        next_state = copy.deepcopy(state)
        engine.apply_action(next_state, hand, act)
        
        if len(next_state.deck) == 0:
            engine.resolve_invasion_if_needed(next_state, policy_name="non_random")
            if next_state.game_lost: continue
                
        if next_state.game_lost: continue
        if next_state.invasions_resolved >= 3:
            val = engine.score(next_state)
            if val > max_expected_value:
                max_expected_value = val; best_action = act
            continue

        total_future_value = 0.0
        valid_futures = 0
        
        for _ in range(NUM_FUTURES):
            future_state = copy.deepcopy(next_state)
            engine.rng.shuffle(future_state.deck) 
            
            future_state.turn_count += 1
            future_hand = engine.draw_hand(future_state)
            if not future_hand: break
            
            future_legals = engine.legal_actions(future_state, future_hand)
            if not future_legals: continue
            
            best_future_val = -float('inf')
            
            for f_act in future_legals:
                sim_state = copy.deepcopy(future_state)
                engine.apply_action(sim_state, future_hand, f_act)
                if len(sim_state.deck) == 0:
                    engine.resolve_invasion_if_needed(sim_state, policy_name="non_random")
                    if sim_state.game_lost: continue
                
                tensor = encoder.encode(sim_state).to(device)
                with torch.no_grad(): val = brain(tensor).item()
                if val > best_future_val: best_future_val = val
                    
            if best_future_val != -float('inf'):
                total_future_value += best_future_val
                valid_futures += 1
                
        expected_val = (total_future_value / valid_futures) if valid_futures > 0 else 0.0
        
        if expected_val > max_expected_value:
            max_expected_value = expected_val
            best_action = act

    # 🚨 返回 动作 和 期望分
    if best_action is None: return legal_actions[0], 0.0
    return best_action, max_expected_value

# ==========================================
# 🚜 阶段 1：纯净神谕采集
# ==========================================
def harvest_distilled_data():
    print(f"\n🚜 [神谕采集] V5 正在推演 {HARVEST_GAMES} 局纯净期望值...")
    repo = DataRepo(PROJECT_ROOT / "data")
    engine = RomeEngine(repo)
    encoder = RomeStateEncoder()
    brain = RomeValueBrainV2()
    
    # 强制用 V5 打底
    model_path = PROJECT_ROOT / "models" / "value_brain_40d_v5.pth"
    brain.load_state_dict(torch.load(model_path, weights_only=True))
    brain.eval()
    device = torch.device("cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu")
    brain = brain.to(device)
    
    X, Y = [], []
    start = time.time()
    
    for i in range(HARVEST_GAMES):
        state = engine.new_game(seed=int(time.time() * 1000) % 1000000 + i)
        
        while not state.game_lost and state.invasions_resolved < 3:
            state.turn_count += 1
            hand = engine.draw_hand(state)
            if not hand: break
            
            # 记录此时的视野
            current_tensor = encoder.encode(state)
            legal_acts = engine.legal_actions(state, hand)
            
            # 🚨 神奇的读心术：不仅拿到动作，还拿到师傅内心的期望分！
            action, expected_score = deep_search_with_value(engine, state, hand, legal_acts, brain, encoder, device)
            
            # 无论这局结局如何，把期望分作为绝对真理保存下来
            X.append(current_tensor)
            Y.append(float(expected_score))
            
            engine.apply_action(state, hand, action)
            engine.resolve_invasion_if_needed(state, policy_name="deep_auto")
            
        if (i+1) % 20 == 0:
            sys.stdout.write(f"\r   ↳ 挖掘进度: {i+1}/{HARVEST_GAMES} | 耗时: {(time.time()-start)/60:.1f}m")
            sys.stdout.flush()
            
    print(f"\n✅ 神谕采集完毕！获得 {len(X)} 条纯净深搜基因。")
    return torch.stack(X), torch.tensor(Y, dtype=torch.float32).unsqueeze(1)

# ==========================================
# 🔥 阶段 2：闪电炼丹 (不看结局，只学直觉)
# ==========================================
def train_distilled_brain(X, Y):
    print(f"\n🔥 [基因蒸馏] 正在重塑 V6 神经网络...")
    dataset = TensorDataset(X, Y)
    train_size = int(0.8 * len(dataset))
    train_ds, val_ds = random_split(dataset, [train_size, len(dataset) - train_size])
    train_loader = DataLoader(train_ds, batch_size=128, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=128, shuffle=False)
    
    brain = RomeValueBrainV2()
    # 继承 V5
    brain.load_state_dict(torch.load(PROJECT_ROOT / "models" / "value_brain_40d_v5.pth", weights_only=True))
    device = torch.device("cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu")
    brain = brain.to(device)
    
    # 极低学习率，精雕细琢
    optimizer = optim.Adam(brain.parameters(), lr=0.0002, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, 'min', patience=2, factor=0.5)
    criterion = nn.MSELoss()
    
    best_val, patience = float('inf'), 0
    target_path = PROJECT_ROOT / "models" / "value_brain_40d_v6.pth"
    
    for epoch in range(25):
        brain.train()
        for bx, by in train_loader:
            optimizer.zero_grad()
            loss = criterion(brain(bx.to(device)), by.to(device))
            loss.backward()
            optimizer.step()
            
        brain.eval()
        val_loss = sum(criterion(brain(bx.to(device)), by.to(device)).item() for bx, by in val_loader) / len(val_loader)
        scheduler.step(val_loss)
        
        if val_loss < best_val:
            best_val = val_loss; patience = 0
            torch.save(brain.state_dict(), target_path)
        else: patience += 1
        
        sys.stdout.write(f"\r   ↳ Epoch {epoch+1:02d} | 考试误差(拟合度): {val_loss:.4f} " + ("⭐契合!" if patience==0 else f"({patience}/3)"))
        sys.stdout.flush()
        if patience >= 3: break
    print("\n   🛑 直觉同步完成。")

# ==========================================
# 📊 阶段 3：V6 单步直觉验收
# ==========================================
def evaluate_v6_fast(num_games):
    print(f"\n📊 [验收大考] V6 徒弟上考场！使用【单步快搜】盲打 {num_games} 局...")
    repo = DataRepo(PROJECT_ROOT / "data")
    engine = RomeEngine(repo)
    encoder = RomeStateEncoder()
    brain = RomeValueBrainV2()
    brain.load_state_dict(torch.load(PROJECT_ROOT / "models" / "value_brain_40d_v6.pth", weights_only=True))
    brain.eval()
    device = torch.device("cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu")
    brain = brain.to(device)
    
    t_score, deaths = 0, 0
    start = time.time()
    for i in range(num_games):
        state = engine.new_game(seed=i + 555555) 
        while not state.game_lost and state.invasions_resolved < 3:
            state.turn_count += 1
            hand = engine.draw_hand(state)
            if not hand: break
            legal_acts = engine.legal_actions(state, hand)
            
            # 🚨 徒弟考试，只准看 1 步！
            best_act = None; max_val = -float('inf')
            for act in legal_acts:
                ns = copy.deepcopy(state)
                engine.apply_action(ns, hand, act)
                if len(ns.deck) == 0:
                    engine.resolve_invasion_if_needed(ns, policy_name="non_random")
                    if ns.game_lost: continue
                with torch.no_grad(): val = brain(encoder.encode(ns).to(device)).item()
                if val > max_val: max_val = val; best_act = act
            
            action = best_act if best_act else legal_acts[0]
            engine.apply_action(state, hand, action)
            engine.resolve_invasion_if_needed(state, policy_name="eval_fast")
            
        score = engine.score(state) if not state.game_lost else 0
        t_score += score
        if state.game_lost: deaths += 1
        
        if (i+1) % 500 == 0:
            sys.stdout.write(f"\r   ↳ 批改中: {i+1}/{num_games} | 耗时: {(time.time()-start):.1f}s")
            sys.stdout.flush()
            
    print("\n" + "="*50)
    print(f"🏆 神谕蒸馏完毕！V6 单步盲打均分: {t_score/num_games:.3f} 分")
    print(f"💀 暴毙率: {deaths/num_games*100:.2f}%")
    print("="*50)

if __name__ == "__main__":
    X, Y = harvest_distilled_data()
    train_distilled_brain(X, Y)
    evaluate_v6_fast(EVAL_GAMES)