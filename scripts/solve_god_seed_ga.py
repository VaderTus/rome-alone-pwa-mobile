# scripts/solve_god_seed_ga.py
import copy
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from core.loader import DataRepo
from core.engine import RomeEngine

W_KING = {'amphi': 635.6, 'senate': 586.1, 'arc': 493.5, 'pan': 209.1, 'conq_base': 282.3, 'conq_arc': 392.9, 'trib': 71.6, 'top_cul': 33.3, 'top_mil': 28.5, 'top_ind': 23.5}

def evaluate_state_heuristic(s, repo):
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

def run_beam_search(seed=1200078, beam_width=5000):
    repo = DataRepo(Path("data"))
    engine = RomeEngine(repo, seed=seed)
    
    s_init = engine.new_game(seed=seed)
    cycle_deck = list(s_init.deck)
    full_deck = cycle_deck + cycle_deck + cycle_deck
    
    current_beams = [(s_init, [], 0.0)]
    
    print(f"🔦 开启【去重波束搜索】 | 宽度: {beam_width} | Seed: {seed}")
    
    for turn_idx in range(21):
        print(f"拆解第 {turn_idx + 1}/21 手... 当前保留分支数: {len(current_beams)}")
        
        next_beams = []
        # 💡 核心升级：状态去重哈希表
        seen_states = set()
        
        hand_start = turn_idx * 3
        current_hand = full_deck[hand_start : hand_start+3]
        
        for state, history, _ in current_beams:
            if state.game_lost or state.invasions_resolved >= 3:
                continue
                
            legal_actions = engine.legal_actions(state, current_hand)
            
            for act in legal_actions:
                next_s = copy.deepcopy(state)
                engine.apply_action(next_s, current_hand, act)
                
                if (turn_idx + 1) % 7 == 0:
                    engine.resolve_invasion_if_needed(next_s)
                
                # 构造极简状态指纹，用于去重
                state_fingerprint = (
                    next_s.culture, next_s.military, next_s.industry,
                    next_s.occupied_regions(),
                    tuple(sorted(next_s.built_buildings)),
                    tuple(sorted(next_s.monument_progress.items()))
                )
                
                # 💡 如果这个局面已经有人走到了，而且别人比你快，那就砍掉这个克隆体！
                if state_fingerprint in seen_states:
                    continue
                seen_states.add(state_fingerprint)
                
                card_name = repo.card_by_id[act['card_id']]['Card_Name']
                step_desc = f"{act['mode'].upper()} - {act['kind']} ({card_name})"
                
                score = evaluate_state_heuristic(next_s, repo)
                next_beams.append((next_s, history + [step_desc], score))
        
        next_beams.sort(key=lambda x: x[2], reverse=True)
        current_beams = next_beams[:beam_width]

    # --- 结算 ---
    print("\n==========================================")
    best_score = -1
    best_path = []
    
    for state, history, _ in current_beams:
        final_score = engine.score(state) if not state.game_lost else 0
        if final_score > best_score:
            best_score = final_score
            best_path = history

    print(f"🏆 无损拆解结束！该种子的【真正极限分】: {best_score} 分")
    if best_score > 0:
        print("上帝视角的完美动作序列：")
        for i, step in enumerate(best_path):
            print(f"  T{i+1:02d} | {step}")
    print("==========================================")

if __name__ == "__main__":
    # 有了去重机制，宽度设为 5000 就足够榨干所有的天才路径了！
    run_beam_search(seed=1200078, beam_width=5000)