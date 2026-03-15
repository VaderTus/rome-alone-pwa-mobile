# scripts/evolve_deep_blue.py
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
# ⚙️ 深蓝挂机参数 (半小时迭代一代，极其解压)
# ==========================================
GAMES_PER_GEN = 1000      # 每代产卵和考试的局数 (因为 2 步搜很慢，1000局最合理)
NUM_FUTURES = 5           # 偷看 5 种平行宇宙
MAX_GENERATIONS = 20      # 计划繁衍多少代
STARTING_SCORE = 14.500   # 我们的守门基准线 (深搜V5的均分约在14.5~14.7)

# ==========================================
# 🌌 核心算法：真正的深蓝引擎 (Depth-2 + 5 Futures)
# ==========================================
def deep_blue_policy(engine, state, hand, legal_actions, brain, encoder, device):
    if not legal_actions: return {"card_id": hand[0], "mode": "top", "kind": "TopResource", "meta": {}}

    best_action = None
    max_expected_value = -float('inf')

    for act in legal_actions:
        next_state = copy.deepcopy(state)
        engine.apply_action(next_state, hand, act)
        
        # 物理兜底
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

    return best_action if best_action else legal_actions[0]

# ==========================================
# 🚜 阶段 1：深搜采集数据
# ==========================================
def harvest_deep_blue(model_path, num_games):
    print(f"\n🚜 [深蓝采集] 正在用 Depth-2 穷举 {num_games} 局宇宙可能...")
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
            act = deep_blue_policy(engine, state, hand, legal_acts, brain, encoder, device)
            engine.apply_action(state, hand, act)
            engine.resolve_invasion_if_needed(state, policy_name="deep_auto")
            
        score = engine.score(state) if not state.game_lost else 0
        t_score += score
        for h in history: X.append(h); Y.append(float(score))
            
        if (i+1) % 50 == 0:
            sys.stdout.write(f"\r   ↳ 进度: {i+1}/{num_games} | 耗时: {(time.time()-start)/60:.1f}m | 实时深搜均分: {t_score/(i+1):.3f}")
            sys.stdout.flush()
            
    print(f"\n✅ 采集完毕！获得 {len(X)} 条带有深搜基因的高级残局。")
    return torch.stack(X), torch.tensor(Y, dtype=torch.float32).unsqueeze(1)

# ==========================================
# 🔥 阶段 2：深层压缩炼丹
# ==========================================
def train_deep_blue(X, Y, base_model_path, target_model_path):
    print(f"\n🔥 [深蓝提纯] 正在重塑神经网络，融合平行宇宙的智慧...")
    dataset = TensorDataset(X, Y)
    train_size = int(0.8 * len(dataset))
    train_ds, val_ds = random_split(dataset, [train_size, len(dataset) - train_size])
    train_loader = DataLoader(train_ds, batch_size=256, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=256, shuffle=False)
    
    brain = RomeValueBrainV2()
    brain.load_state_dict(torch.load(base_model_path, weights_only=True))
    device = torch.device("cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu")
    brain = brain.to(device)
    
    # 极低的学习率，防止它把以前学到的东西给忘了
    optimizer = optim.Adam(brain.parameters(), lr=0.0003, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, 'min', patience=2, factor=0.5)
    criterion = nn.MSELoss()
    
    best_val, patience = float('inf'), 0
    for epoch in range(30):
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
            torch.save(brain.state_dict(), target_model_path)
        else: patience += 1
        
        sys.stdout.write(f"\r   ↳ Epoch {epoch+1:02d} | 考试误差: {val_loss:.4f} " + ("⭐进化!" if patience==0 else f"({patience}/4)"))
        sys.stdout.flush()
        if patience >= 4: break
    print("\n   🛑 潜能榨干，炼丹结束。")

# ==========================================
# 📊 阶段 3：深蓝同台竞技大考
# ==========================================
def evaluate_deep_blue(model_path, num_games, current_best):
    print(f"\n📊 [深蓝大考] 徒弟上考场！使用【深搜模式】盲打 {num_games} 局...")
    repo = DataRepo(PROJECT_ROOT / "data")
    engine = RomeEngine(repo)
    encoder = RomeStateEncoder()
    brain = RomeValueBrainV2()
    brain.load_state_dict(torch.load(model_path, weights_only=True))
    brain.eval()
    device = torch.device("cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu")
    brain = brain.to(device)
    
    t_score = 0
    start = time.time()
    for i in range(num_games):
        state = engine.new_game(seed=i + 777777) 
        while not state.game_lost and state.invasions_resolved < 3:
            state.turn_count += 1
            hand = engine.draw_hand(state)
            if not hand: break
            legal_acts = engine.legal_actions(state, hand)
            
            # 考场上依然用深搜！保证学以致用
            act = deep_blue_policy(engine, state, hand, legal_acts, brain, encoder, device)
            engine.apply_action(state, hand, act)
            engine.resolve_invasion_if_needed(state, policy_name="eval_deep")
            
        t_score += engine.score(state) if not state.game_lost else 0
        if (i+1) % 50 == 0:
            sys.stdout.write(f"\r   ↳ 批改中: {i+1}/{num_games} | 耗时: {(time.time()-start)/60:.1f}m")
            sys.stdout.flush()
            
    avg = t_score / num_games
    print("\n" + "="*50)
    print(f"🏆 大考揭榜！新神明深搜均分: {avg:.3f} (守门线: {current_best:.3f})")
    
    if avg > current_best:
        print("🟢 判定：成功超越！允许繁衍！")
        return True, avg
    else:
        print("🔴 判定：考核失败！走火入魔。直接抛弃，退回上一代！")
        return False, current_best

# ==========================================
# 🌌 永动机主引擎
# ==========================================
def run_deep_blue_pipeline():
    print("="*60)
    print("🌌 Deep Blue (深蓝) 迭代引擎已点火 🌌")
    print("="*60)
    
    current_gen = 5
    current_best = STARTING_SCORE
    models_dir = PROJECT_ROOT / "models"
    
    for _ in range(MAX_GENERATIONS):
        next_gen = current_gen + 1
        base_model = models_dir / f"value_brain_40d_v{current_gen}.pth"
        next_model = models_dir / f"value_brain_40d_v{next_gen}.pth"
        
        print("\n" + "🌟"*20)
        print(f"  正在孕育深蓝第 {next_gen} 世代 (DeepBlue Gen {next_gen})")
        print("🌟"*20)
        
        X, Y = harvest_deep_blue(base_model, GAMES_PER_GEN)
        train_deep_blue(X, Y, base_model, next_model)
        
        passed, new_score = evaluate_deep_blue(next_model, GAMES_PER_GEN, current_best)
        
        if passed:
            current_gen = next_gen
            current_best = new_score
        else:
            print(f"⚠️ 第 {next_gen} 代已被粉碎。系统重置环境，继续榨取 V{current_gen} 的潜能...")

if __name__ == "__main__":
    run_deep_blue_pipeline()