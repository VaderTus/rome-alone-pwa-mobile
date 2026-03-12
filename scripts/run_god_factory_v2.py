# scripts/run_god_factory_v2.py
import copy
from pathlib import Path
import sys
import random
import pandas as pd
import json

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from core.loader import DataRepo
from core.engine import RomeEngine

# --- 引导波束搜索方向的基础权重 ---
W_KING = {'amphi': 635.6, 'senate': 586.1, 'arc': 493.5, 'pan': 209.1, 'conq_base': 282.3, 'conq_arc': 392.9, 'trib': 71.6, 'top_cul': 33.3, 'top_mil': 28.5, 'top_ind': 23.5}

BUILDINGS = ["B_KaiXuanDiaoSu", "B_DiGuoYinShuiDao", "B_JunTuanYaoSai", "B_DiGuoJinKuang", "B_YuanXingJingJiChang"]
MONUMENTS = ["M_WanShenMiao", "M_LuoMaDouShouChang", "M_DiGuoGuangChang", "M_HaDeLiangLingQin", "M_KaiXuanMen", "M_TuLaZhenShiChang"]
ALL_CARDS = [f"C{i:02d}" for i in range(1, 22)]

def evaluate_state_heuristic(s):
    if s.game_lost: return -99999
    val = s.occupied_regions() * 100
    val += s.culture * W_KING['top_cul'] + s.military * W_KING['top_mil'] + s.industry * W_KING['top_ind']
    for b in s.built_buildings:
        if b in ["B_YuanXingJingJiChang", "B_JunTuanYaoSai", "B_DiGuoJinKuang"]: val += 300
        else: val += 100
    for mid, prog in s.monument_progress.items():
        if prog == 1: val += 150
        if prog == 2: val += 500
    return val

def extract_38d_features(s):
    """提取 38 维神经网络感官特征"""
    feat = [
        s.turn_count / 21.0,
        s.culture / 9.0, s.military / 9.0, s.industry / 9.0,
        s.occupied_regions() / 7.0, s.invasions_resolved / 2.0
    ]
    for b in BUILDINGS: feat.append(1.0 if b in s.built_buildings else 0.0)
    for m in MONUMENTS: feat.append(s.monument_progress.get(m, 0) / 2.0)
    for c in ALL_CARDS: feat.append(1.0 if c in s.discard else 0.0)
    return feat

def solve_seed(seed, repo, base_width=3000):
    engine = RomeEngine(repo, seed=seed)
    s_init = engine.new_game(seed=seed)
    
    cycle_deck = list(s_init.deck)
    full_deck = cycle_deck + cycle_deck + cycle_deck
    
    # beam 结构: (状态对象, 该状态的38维特征历史列表, 启发式评分)
    current_beams = [(s_init, [], 0.0)]
    
    for turn_idx in range(21):
        next_beams = []
        seen_states = set()
        
        hand_start = turn_idx * 3
        current_hand = full_deck[hand_start : hand_start+3]
        
        for state, feat_history, _ in current_beams:
            if state.game_lost or state.invasions_resolved >= 3: continue
                
            legal_actions = engine.legal_actions(state, current_hand)
            for act in legal_actions:
                next_s = copy.deepcopy(state)
                engine.apply_action(next_s, current_hand, act)
                
                if (turn_idx + 1) % 7 == 0:
                    engine.resolve_invasion_if_needed(next_s)
                
                # 状态去重
                state_fingerprint = (
                    next_s.culture, next_s.military, next_s.industry,
                    next_s.occupied_regions(),
                    tuple(sorted(next_s.built_buildings)),
                    tuple(sorted(next_s.monument_progress.items()))
                )
                if state_fingerprint in seen_states: continue
                seen_states.add(state_fingerprint)
                
                # 💡 核心：在动作发生后，记录这个“有潜力的新状态”的 38 维特征
                new_feat = extract_38d_features(next_s)
                
                score = evaluate_state_heuristic(next_s)
                next_beams.append((next_s, feat_history + [new_feat], score))
        
        # 波束剪枝 (动态宽度：后期分叉多，稍微放宽)
        next_beams.sort(key=lambda x: x[2], reverse=True)
        dynamic_width = int(base_width * (1 + (turn_idx / 21.0) * 0.5))
        current_beams = next_beams[:dynamic_width]

    # --- 结算寻找真理 ---
    best_score = -1
    best_feat_path = []
    
    for state, feat_history, _ in current_beams:
        final_score = engine.score(state) if not state.game_lost else 0
        if final_score > best_score:
            best_score = final_score
            best_feat_path = feat_history

    return best_score, best_feat_path

def start_god_factory(target_games=5000):
    repo = DataRepo(Path("data"))
    out_file = Path("data/god_value_training_v1.csv")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"🔥 [普罗米修斯计划] 启动！")
    print(f"目标: 挖掘 {target_games} 局 16+ 分神级剧本，构建真理矩阵...")
    
    records = []
    # 如果断电了，可以接着跑（简单读取已有的数据量，防覆盖逻辑暂略，可手动改种子段）
    base_seed = random.randint(10000000, 90000000)
    
    success_count = 0
    attempts = 0
    
    while success_count < target_games:
        seed = base_seed + attempts
        attempts += 1
        
        print(f"[{success_count}/{target_games}] 正在拆解 Seed: {seed} ...", end=" ", flush=True)
        
        # 宽度设为 1500 是速度与质量的黄金平衡
        score, feat_path = solve_seed(seed, repo, base_width=1500) 
        
        # 💡 只要真正的神之操作 (16分以上)
        if score >= 16 and feat_path:
            success_count += 1
            print(f"✅ 神迹降临! 得分: {score}")
            
            # 把这 21 个完美状态，打上“通往神界(归一化分数)”的标签，存入记录
            target_value = score / 22.0 # 假设 22 分是 1.0 满分
            for feat in feat_path:
                records.append(feat + [target_value])
            
            # 每 10 个神级局存一次盘，防止数据丢失
            if success_count % 10 == 0:
                df = pd.DataFrame(records)
                df.to_csv(out_file, index=False, header=False)
        else:
            print(f"❌ 平庸 ({score}分)，抛弃。")
            
    print(f"\n==========================================")
    print(f"🏆 教材制作完毕！共提取了 {len(records)} 条绝对真理。")
    print(f"请使用这些数据训练 RomeValueBrain。")
    print(f"==========================================")

if __name__ == "__main__":
    # 为了保证神经网络有足够的数据量（至少十万条），我们需要大约 5000 局 16+ 的录像
    # 如果你的电脑跑得慢，可以先改成 1000 局试试水
    start_god_factory(target_games=1000)