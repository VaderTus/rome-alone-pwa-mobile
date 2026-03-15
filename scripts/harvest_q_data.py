# scripts/harvest_q_data.py
import sys
import copy
import time
from pathlib import Path
import torch

# 动态加载项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.loader import DataRepo
from core.engine import RomeEngine
from core.encoder import RomeStateEncoder
from scripts.train_deep_value_net_v2 import RomeValueBrainV2

# ==========================================
# 🧩 1. 动作编码器 (Action Encoder) - 27维
# ==========================================
def encode_action(action):
    """将动作字典转化为 27 维的张量 (21张牌 + 1个上下半区 + 5种动作类型)"""
    # 1. 牌 ID One-hot (21 维)
    cid_num = int(action['card_id'][1:]) - 1
    card_vec = [0.0] * 21
    card_vec[cid_num] = 1.0
    
    # 2. 上下半区 (1 维: top=1, bottom=0)
    mode_vec = [1.0 if action['mode'] == 'top' else 0.0]
    
    # 3. 动作类型 One-hot (5 维)
    kinds = ['TopResource', 'Conquest', 'Tribute', 'Build_Building', 'Build_Monument']
    kind_idx = kinds.index(action['kind'])
    kind_vec = [0.0] * 5
    kind_vec[kind_idx] = 1.0
    
    return torch.tensor(card_vec + mode_vec + kind_vec, dtype=torch.float32)

# ==========================================
# 🔮 2. 师傅的深度期望评估 (计算 Q_target)
# ==========================================
def get_action_q_value(engine, state, hand, action, brain_v5, encoder, device, num_futures=5):
    """用 V5 + 两步搜索，精确计算某个特定动作的期望分"""
    next_state = copy.deepcopy(state)
    engine.apply_action(next_state, hand, action)
    
    # 物理兜底
    if len(next_state.deck) == 0:
        engine.resolve_invasion_if_needed(next_state, policy_name="non_random")
        if next_state.game_lost: return 0.0
            
    if next_state.game_lost: return 0.0
    if next_state.invasions_resolved >= 3: return float(engine.score(next_state))

    total_future_value = 0.0
    valid_futures = 0
    
    for _ in range(num_futures):
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
            with torch.no_grad(): val = brain_v5(tensor).item()
            if val > best_future_val: best_future_val = val
                
        if best_future_val != -float('inf'):
            total_future_value += best_future_val
            valid_futures += 1
            
    return (total_future_value / valid_futures) if valid_futures > 0 else 0.0

# ==========================================
# 🚜 3. 榨取 Q(s,a) 金矿
# ==========================================
def harvest_q_data(num_games=400):
    print("="*60)
    print(f"🚜 [Q-Learning 采矿机] 启动！目标: {num_games} 局全景动作解析")
    print("="*60)
    
    repo = DataRepo(PROJECT_ROOT / "data")
    engine = RomeEngine(repo)
    encoder = RomeStateEncoder()
    
    brain_v5 = RomeValueBrainV2()
    brain_v5.load_state_dict(torch.load(PROJECT_ROOT / "models" / "value_brain_40d_v5.pth", weights_only=True))
    brain_v5.eval()
    device = torch.device("cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu")
    brain_v5 = brain_v5.to(device)
    
    X_state, X_action, Y_q = [], [], []
    start_time = time.time()
    
    for i in range(num_games):
        state = engine.new_game(seed=i + 101010)
        
        while not state.game_lost and state.invasions_resolved < 3:
            state.turn_count += 1
            hand = engine.draw_hand(state)
            if not hand: break
            
            legal_acts = engine.legal_actions(state, hand)
            state_tensor = encoder.encode(state)
            
            best_act = None
            max_q = -float('inf')
            
            # 🔥 核心：遍历所有合法动作，算出它们的 Q 值并保存！这才是逐动作教学！
            for act in legal_acts:
                q_val = get_action_q_value(engine, state, hand, act, brain_v5, encoder, device)
                
                # 记录状态、动作编码、期望Q值
                X_state.append(state_tensor)
                X_action.append(encode_action(act))
                Y_q.append(float(q_val))
                
                # 顺便找出最好的动作，用来继续推进游戏
                if q_val > max_q:
                    max_q = q_val
                    best_act = act
                    
            engine.apply_action(state, hand, best_act if best_act else legal_acts[0])
            engine.resolve_invasion_if_needed(state, policy_name="q_harvest")
            
        if (i+1) % 10 == 0:
            elapsed = time.time() - start_time
            print(f"   ↳ 采矿进度: {i+1}/{num_games} | 耗时: {elapsed/60:.1f}m | 样本量: {len(Y_q)}")
            
    print(f"\n✅ 采矿完毕！获得 {len(Y_q)} 条极其珍贵的 Q(s,a) 动作对比数据。")
    
    save_dir = PROJECT_ROOT / "data" / "_legacy_datasets"
    save_dir.mkdir(parents=True, exist_ok=True)
    torch.save({"S": torch.stack(X_state), "A": torch.stack(X_action), "Q": torch.tensor(Y_q, dtype=torch.float32).unsqueeze(1)}, 
               save_dir / "q_dataset_v1.pt")
    print(f"💾 Q值金矿已封存于 {save_dir / 'q_dataset_v1.pt'}")

if __name__ == "__main__":
    harvest_q_data(400)