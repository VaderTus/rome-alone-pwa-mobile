# scripts/analyze_v5_god.py
import sys
import copy
from pathlib import Path
import torch
from collections import Counter

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.loader import DataRepo
from core.engine import RomeEngine
from core.encoder import RomeStateEncoder
from scripts.train_deep_value_net_v2 import RomeValueBrainV2

def load_v5_brain():
    encoder = RomeStateEncoder()
    brain = RomeValueBrainV2()
    model_path = PROJECT_ROOT / "models" / "value_brain_40d_v5.pth"
    if not model_path.exists():
        print("❌ 找不到 V5 大脑！请确保 value_brain_40d_v5.pth 存在。")
        sys.exit(1)
        
    brain.load_state_dict(torch.load(model_path, weights_only=True))
    brain.eval()
    device = torch.device("cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu")
    brain = brain.to(device)
    return brain, encoder, device

def get_action(engine, state, hand, legal_actions, brain, encoder, device):
    if not legal_actions: return legal_actions[0] if legal_actions else {"card_id": hand[0], "mode": "top", "kind": "TopResource", "meta": {}}
    best_action = None
    max_value = -float('inf')
    for act in legal_actions:
        next_state = copy.deepcopy(state)
        engine.apply_action(next_state, hand, act)
        if len(next_state.deck) == 0:
            engine.resolve_invasion_if_needed(next_state, policy_name="non_random")
            if next_state.game_lost: continue 
        tensor_state = encoder.encode(next_state).to(device)
        with torch.no_grad(): val = brain(tensor_state).item()
        if val > max_value:
            max_value = val
            best_action = act
    return best_action if best_action else legal_actions[0]

def analyze_behavior(num_games=1000):
    print("="*50)
    print("🔬 启动 V5 神经行为学解剖手术...")
    print(f"观测样本: {num_games} 局")
    print("="*50)
    
    repo = DataRepo(PROJECT_ROOT / "data")
    engine = RomeEngine(repo)
    brain, encoder, device = load_v5_brain()
    
    # 统计探头
    first_building_stats = Counter()
    completed_monuments_stats = Counter()
    invasion_choices = {"pay_military": 0, "lose_region": 0}
    total_score = 0
    
    for i in range(num_games):
        state = engine.new_game(seed=i + 333333)
        first_building_logged = False
        
        while not state.game_lost and state.invasions_resolved < 3:
            state.turn_count += 1
            hand = engine.draw_hand(state)
            if not hand: break
            
            legal_acts = engine.legal_actions(state, hand)
            action = get_action(engine, state, hand, legal_acts, brain, encoder, device)
            engine.apply_action(state, hand, action)
            
            # 探头 1：它造的第一个建筑是什么？
            if not first_building_logged and len(state.built_buildings) > 0:
                first_b = list(state.built_buildings)[0] # 简单取集合里的第一个
                first_building_stats[repo.building_by_id[first_b]["Building_Name"]] += 1
                first_building_logged = True
            
            # 探头 2：面对入侵的抉择 (通过观察扣除前后的资源变化来判断)
            if len(state.deck) == 0:
                mil_before = state.military
                reg_before = state.occupied_regions()
                engine.resolve_invasion_if_needed(state, policy_name="eval")
                
                if not state.game_lost:
                    if state.military < mil_before:
                        invasion_choices["pay_military"] += 1
                    elif state.occupied_regions() < reg_before:
                        invasion_choices["lose_region"] += 1
                        
        total_score += engine.score(state) if not state.game_lost else 0
        
        # 探头 3：最终建成了哪些奇观？
        if not state.game_lost:
            for mid, prog in state.monument_progress.items():
                if prog >= 2:
                    completed_monuments_stats[repo.monument_by_id[mid]["Monument_Name"]] += 1

    # 打印机密报告
    print("\n" + "█"*50)
    print(f" 📜 《V5 机械神明战术解剖报告》")
    print(f" 综合均分: {total_score/num_games:.2f} 分")
    print("█"*50)
    
    print("\n📌 [战术 1：起手式偏好] (最爱建的第一个建筑)")
    for b_name, count in first_building_stats.most_common():
        print(f"  - {b_name}: {count/num_games*100:.1f}%")

    print("\n📌 [战术 2：终极信仰] (完工次数最多的奇观)")
    for m_name, count in completed_monuments_stats.most_common():
        print(f"  - {m_name}: {count} 次 (局均建成率 {count/num_games*100:.1f}%)")
        
    print("\n📌 [战术 3：底线法则] (面对野蛮人入侵的处理方式)")
    total_inv = sum(invasion_choices.values())
    if total_inv > 0:
        pay_ratio = invasion_choices['pay_military'] / total_inv * 100
        lose_ratio = invasion_choices['lose_region'] / total_inv * 100
        print(f"  - 🛡️ 花钱消灾 (扣除军事): {pay_ratio:.1f}%")
        print(f"  - 🩸 割地求生 (丢弃地区): {lose_ratio:.1f}%")
    
    print("\n长官，神明的底牌已被掀开。")

if __name__ == "__main__":
    analyze_behavior(1000)