# scripts/auto_alphazero_pipeline.py
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
# ⚙️ 挂机参数 (专为笔记本通宵优化)
# ==========================================
HARVEST_GAMES = 2000     # 师傅用深搜打多少局 (深搜很慢，2000局刚好够提纯)
EVAL_GAMES = 2000        # 徒弟用快搜考多少局来定级
NUM_FUTURES = 5          # 深搜时，预测几种未来的发牌可能
MAX_GENERATIONS = 20     # 一晚上最多让他跑多少代
CURRENT_BEST_SCORE = 14.339 # 我们的守门神 V5 的分数

# ==========================================
# 🌌 核心算法：师傅的深度搜索 (看 2 步)
# ==========================================
def deep_search_policy(engine, state, hand, legal_actions, brain, encoder, device):
    if not legal_actions: return {"card_id": hand[0], "mode": "top", "kind": "TopResource", "meta": {}}

    best_action = None
    max_expected_value = -float('inf')

    for act in legal_actions:
        # 【第 1 步】走当前这步
        next_state = copy.deepcopy(state)
        engine.apply_action(next_state, hand, act)
        
        # 物理防暴毙兜底
        if len(next_state.deck) == 0:
            engine.resolve_invasion_if_needed(next_state, policy_name="non_random")
            if next_state.game_lost: continue
                
        if next_state.game_lost: continue
        if next_state.invasions_resolved >= 3:
            val = engine.score(next_state)
            if val > max_expected_value:
                max_expected_value = val; best_action = act
            continue

        # 【第 2 步】开启平行宇宙，预测下回合
        total_future_value = 0.0
        valid_futures = 0
        
        for _ in range(NUM_FUTURES):
            future_state = copy.deepcopy(next_state)
            engine.rng.shuffle(future_state.deck) # 打乱未来牌堆
            
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
                
                # 让神明给最终的残局打分
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

    return best_action if best_action else legal_actions[0]

# ==========================================
# ⚡ 核心算法：徒弟的快搜直觉 (只看 1 步)
# ==========================================
def fast_policy(engine, state, hand, legal_actions, brain, encoder, device):
    if not legal_actions: return {"card_id": hand[0], "mode": "top", "kind": "TopResource", "meta": {}}
    best_act = None
    max_val = -float('inf')
    for act in legal_actions:
        ns = copy.deepcopy(state)
        engine.apply_action(ns, hand, act)
        if len(ns.deck) == 0:
            engine.resolve_invasion_if_needed(ns, policy_name="non_random")
            if ns.game_lost: continue
        tensor = encoder.encode(ns).to(device)
        with torch.no_grad(): val = brain(tensor).item()
        if val > max_val: max_val = val; best_act = act
    return best_act if best_act else legal_actions[0]

# ==========================================
# 🚜 流水线阶段 1：深度挖掘
# ==========================================
def harvest_deep_data(model_path, num_games):
    print(f"\n🚜 [阶段 1] 正在使用深搜 (Depth-2) 挖掘 {num_games} 局高级棋谱...")
    repo = DataRepo(PROJECT_ROOT / "data")
    engine = RomeEngine(repo)
    encoder = RomeStateEncoder()
    brain = RomeValueBrainV2()
    brain.load_state_dict(torch.load(model_path, weights_only=True))
    brain.eval()
    device = torch.device("cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu")
    brain = brain.to(device)
    
    X, Y = [], []
    t_score = 0
    start = time.time()
    for i in range(num_games):
        state = engine.new_game(seed=int(time.time() * 1000) % 1000000 + i)
        history = []
        while not state.game_lost and state.invasions_resolved < 3:
            state.turn_count += 1
            hand = engine.draw_hand(state)
            if not hand: break
            history.append(encoder.encode(state))
            legal_acts = engine.legal_actions(state, hand)
            # 使用深搜打牌
            act = deep_search_policy(engine, state, hand, legal_acts, brain, encoder, device)
            engine.apply_action(state, hand, act)
            engine.resolve_invasion_if_needed(state, policy_name="auto")
            
        score = engine.score(state) if not state.game_lost else 0
        t_score += score
        for h in history:
            X.append(h); Y.append(float(score))
            
        if (i+1) % 100 == 0:
            print(f"   ↳ 挖掘进度: {i+1}/{num_games} | 耗时: {(time.time()-start)/60:.1f}分 | 师傅深搜均分: {t_score/(i+1):.2f}")
    
    return torch.stack(X), torch.tensor(Y, dtype=torch.float32).unsqueeze(1)

# ==========================================
# 🔥 流水线阶段 2：训练徒弟
# ==========================================
def train_new_brain(X, Y, base_model_path, target_model_path):
    print(f"\n🔥 [阶段 2] 启动炼丹炉，将深搜智慧压缩至 V6 神经网络...")
    dataset = TensorDataset(X, Y)
    train_size = int(0.8 * len(dataset))
    train_ds, val_ds = random_split(dataset, [train_size, len(dataset) - train_size])
    train_loader = DataLoader(train_ds, batch_size=512, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=512, shuffle=False)
    
    brain = RomeValueBrainV2()
    brain.load_state_dict(torch.load(base_model_path, weights_only=True))
    device = torch.device("cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu")
    brain = brain.to(device)
    
    optimizer = optim.Adam(brain.parameters(), lr=0.0005, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, 'min', patience=2, factor=0.5)
    criterion = nn.MSELoss()
    
    best_val_loss, patience = float('inf'), 0
    for epoch in range(30):
        brain.train()
        for bx, by in train_loader:
            bx, by = bx.to(device), by.to(device)
            optimizer.zero_grad()
            loss = criterion(brain(bx), by)
            loss.backward()
            optimizer.step()
            
        brain.eval()
        val_loss = 0
        with torch.no_grad():
            for bx, by in val_loader:
                val_loss += criterion(brain(bx.to(device)), by.to(device)).item()
        
        avg_val = val_loss / len(val_loader)
        scheduler.step(avg_val)
        
        if avg_val < best_val_loss:
            best_val_loss = avg_val; patience = 0
            torch.save(brain.state_dict(), target_model_path)
        else: patience += 1
        
        print(f"   ↳ Epoch {epoch+1:02d} | 考试误差: {avg_val:.4f}")
        if patience >= 4: break

# ==========================================
# 📊 流水线阶段 3：快搜大考与残酷淘汰
# ==========================================
def evaluate_and_gate(model_path, num_games, current_best):
    print(f"\n📊 [阶段 3] 徒弟上考场！使用单步直觉盲打 {num_games} 局...")
    repo = DataRepo(PROJECT_ROOT / "data")
    engine = RomeEngine(repo)
    encoder = RomeStateEncoder()
    brain = RomeValueBrainV2()
    brain.load_state_dict(torch.load(model_path, weights_only=True))
    brain.eval()
    device = torch.device("cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu")
    brain = brain.to(device)
    
    t_score = 0
    for i in range(num_games):
        state = engine.new_game(seed=i + 888888) 
        while not state.game_lost and state.invasions_resolved < 3:
            state.turn_count += 1
            hand = engine.draw_hand(state)
            if not hand: break
            legal_acts = engine.legal_actions(state, hand)
            # 考试时只准用快搜！
            act = fast_policy(engine, state, hand, legal_acts, brain, encoder, device)
            engine.apply_action(state, hand, act)
            engine.resolve_invasion_if_needed(state, policy_name="eval")
        t_score += engine.score(state) if not state.game_lost else 0
        
    avg_score = t_score / num_games
    print("="*50)
    print(f"🏆 阅卷完毕！新大脑盲打均分: {avg_score:.3f} (守门员 V5 分数: {current_best})")
    
    if avg_score > current_best:
        print("🟢 判定：成功超越！新神诞生，允许繁衍下一代！")
        return True, avg_score
    else:
        print("🔴 判定：考核失败！它被平行宇宙的噪音干扰了。斩杀此脑，退回上一代！")
        return False, current_best

# ==========================================
# 🌌 永动机主引擎
# ==========================================
def run_night_pipeline():
    print("="*60)
    print("🌌 AlphaZero 通宵无人值守引擎已点火 🌌")
    print("="*60)
    
    current_gen = 5
    current_best_score = CURRENT_BEST_SCORE
    models_dir = PROJECT_ROOT / "models"
    
    for _ in range(MAX_GENERATIONS):
        next_gen = current_gen + 1
        base_model = models_dir / f"value_brain_40d_v{current_gen}.pth"
        next_model = models_dir / f"value_brain_40d_v{next_gen}.pth"
        
        print("\n" + "🌟"*20)
        print(f"  正在孕育第 {next_gen} 世代 (Generation {next_gen})")
        print("🌟"*20)
        
        X, Y = harvest_deep_data(base_model, HARVEST_GAMES)
        train_new_brain(X, Y, base_model, next_model)
        
        # 严苛的晋级赛
        passed, new_score = evaluate_and_gate(next_model, EVAL_GAMES, current_best_score)
        
        if passed:
            current_gen = next_gen
            current_best_score = new_score
        else:
            print(f"⚠️ 第 {next_gen} 代已被废弃。系统将使用 V{current_gen} 重新尝试深搜挖掘。")
            # 不更新 current_gen，下一轮继续用老模型产生数据

if __name__ == "__main__":
    run_night_pipeline()