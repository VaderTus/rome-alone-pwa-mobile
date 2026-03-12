# scripts/run_god_factory.py
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

W_KING = {'amphi': 635.6, 'senate': 586.1, 'arc': 493.5, 'pan': 209.1, 'conq_base': 282.3, 'conq_arc': 392.9, 'trib': 71.6, 'top_cul': 33.3, 'top_mil': 28.5, 'top_ind': 23.5}

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

def solve_seed(seed, repo, base_width=3000):
    engine = RomeEngine(repo, seed=seed)
    s_init = engine.new_game(seed=seed)
    
    cycle_deck = list(s_init.deck)
    full_deck = cycle_deck + cycle_deck + cycle_deck
    
    current_beams = [(s_init, [], 0.0)]
    
    for turn_idx in range(21):
        next_beams = []
        seen_states = set()
        
        hand_start = turn_idx * 3
        current_hand = full_deck[hand_start : hand_start+3]
        
        for state, history, _ in current_beams:
            if state.game_lost or state.invasions_resolved >= 3: continue
                
            legal_actions = engine.legal_actions(state, current_hand)
            for act in legal_actions:
                next_s = copy.deepcopy(state)
                engine.apply_action(next_s, current_hand, act)
                
                if (turn_idx + 1) % 7 == 0:
                    engine.resolve_invasion_if_needed(next_s)
                
                state_fingerprint = (
                    next_s.culture, next_s.military, next_s.industry,
                    next_s.occupied_regions(),
                    tuple(sorted(next_s.built_buildings)),
                    tuple(sorted(next_s.monument_progress.items()))
                )
                
                if state_fingerprint in seen_states: continue
                seen_states.add(state_fingerprint)
                
                # 精简历史记录，节约内存
                step_desc = f"{act['mode'][0].upper()}_{act['kind'][:4]}_{act['card_id']}"
                next_beams.append((next_s, history + [step_desc], evaluate_state_heuristic(next_s)))
        
        next_beams.sort(key=lambda x: x[2], reverse=True)
        # 前期动作少，不需要太宽；后期爆炸式增长，需要更宽
        dynamic_width = int(base_width * (1 + (turn_idx / 21.0)))
        current_beams = next_beams[:dynamic_width]

    best_score = -1
    best_path = []
    for state, history, _ in current_beams:
        final_score = engine.score(state) if not state.game_lost else 0
        if final_score > best_score:
            best_score = final_score
            best_path = history

    return best_score, best_path

def start_god_factory(batch_size=100):
    repo = DataRepo(Path("data"))
    out_file = Path("outputs/god_limits.csv")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    
    results = []
    
    # 尝试读取已有的记录，断点续传
    if out_file.exists():
        df_old = pd.read_csv(out_file)
        results = df_old.to_dict('records')
        print(f"📦 已加载 {len(results)} 条历史记录...")

    print(f"🏭 [上帝车间] 启动！开始流水线解算 {batch_size} 个随机种子...")
    
    for i in range(batch_size):                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         
        “？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？
        seed = random.randint(10000000, 99999999)
        print(f"\n[{i+1}/{batch_size}] 正在暴力拆解 Seed: {seed} ...", end=" ", flush=True)
        
        score, path = solve_seed(seed, repo, base_width=2000) # 2000 宽度既能保质量又够快
        
        print(f"✅ 最高分: {score}")
        
        results.append({
            "seed": seed,
            "max_score": score,
            "perfect_path": "|".join(path)
        })
        
        # 每跑完 5 个存一次档，防断电
        if (i+1) % 5 == 0:
            pd.DataFrame(results).to_csv(out_file, index=False)
            
    # 最终保存与总结
    df = pd.DataFrame(results)
    df.to_csv(out_file, index=False)
    
    print("\n" + "="*50)
    print(f"🏆 车间任务完成！本次共解算 {batch_size} 局。")
    print(f"📈 理论平均最高分: {df['max_score'].mean():.2f}")
    print(f"🔥 发现的最高分: {df['max_score'].max()}")
    print("="*50)

if __name__ == "__main__":
    # 你可以把 100 改成 1000 让他挂机跑一天
    start_god_factory(batch_size=100)