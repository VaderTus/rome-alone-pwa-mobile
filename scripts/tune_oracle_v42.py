# scripts/tune_oracle_v42.py
from pathlib import Path
import sys
import random
import pandas as pd
import numpy as np

# === 路径修复 ===
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.loader import DataRepo
from core.engine import RomeEngine

# 🏆 王者基因组 (V39/V26)
W_KING = {'amphi': 635.6, 'senate': 586.1, 'arc': 493.5, 'pan': 209.1, 'conq_base': 282.3, 'conq_arc': 392.9, 'trib': 71.6, 'top_cul': 33.3, 'top_mil': 28.5, 'top_ind': 23.5}

def oracle_logic(engine, state, hand, legal_actions, p):
    if not legal_actions: return {"card_id": hand[0], "mode": "top", "kind": "TopResource", "meta": {}}
    
    turn, regions = state.turn_count, state.occupied_regions()
    inv_cost = int(engine.repo.invasions[engine.repo.invasions["Invasion_Order"] == min(state.invasions_resolved+1, 3)].iloc[0]["Pay_Military_To_Avoid"])
    deck_left = len(state.deck)
    senate_active = state.monument_progress.get("M_DiGuoGuangChang", 0) >= 2

    # --- 神谕感应器 ---
    conq_rem = sum(1 for cid in state.deck if cid in ["C06", "C07"])
    trib_rem = sum(1 for cid in state.deck if cid in ["C08", "C09"])
    
    # 动态倍率
    c_mul = p['conq_m'] if (trib_rem > 0 and conq_rem > 0) else 1.0
    m_mul = p['mil_m'] if (conq_rem > 0) else 1.0

    # 动态红线：如果距离洗牌步数 <= p['panic_t']，进入严格防御
    turns_left_in_cycle = (deck_left // 3) + 1
    red_line = inv_cost if turns_left_in_cycle <= p['panic_t'] else 1
    if turn >= 19: red_line = 0

    def score_action(a):
        kind, mode, meta = a["kind"], a["mode"], a.get("meta", {})
        c_card = engine.repo.card_by_id[a["card_id"]]
        
        # 风险预判
        est_m = state.military; est_c = state.culture
        if mode == "bottom":
            est_m -= (regions if kind == "Conquest" else int(c_card.get("Cost_Military", 0)))
            est_c -= int(c_card.get("Cost_Culture", 0))
        elif mode == "top":
            est_m += int(c_card.get("Top_Military", 0))
            est_c += int(c_card.get("Top_Culture", 0))

        eff_m = (est_m + est_c) if senate_active else est_m
        if turn < 19 and eff_m < red_line and kind != "TopResource": return -100000 

        s = 0.0
        w = W_KING
        if kind == "Build_Building":
            bid = meta.get("building_id")
            if bid == "B_YuanXingJingJiChang": s += w['amphi'] if turn <= 10 else 150
            elif bid in {"B_KaiXuanDiaoSu", "B_DiGuoYinShuiDao"}: s += 160 if turn >= 14 else 40
        if kind == "Build_Monument":
            mid = meta.get("monument_id")
            if mid == "M_DiGuoGuangChang": s += w['senate'] if turn <= 12 else 150
            elif mid == "M_KaiXuanMen": s += w['arc'] if turn >= 6 else 100
            elif mid == "M_WanShenMiao": s += w['pan'] if turn >= 14 else 60
        if kind == "Conquest":
            base = w['conq_arc'] if state.monument_progress.get("M_KaiXuanMen", 0) >= 2 else w['conq_base']
            s += base * c_mul
        if kind == "Tribute": s += w['trib'] if regions >= 3 else 30
        
        if mode == "top":
            tc, tm, ti = int(c_card["Top_Culture"]), int(c_card["Top_Military"]), int(c_card["Top_Industry"])
            if state.culture + tc > 9: s -= 40
            if state.military + tm > 9: s -= 40
            # 应用军事神谕加成
            s += tc * w['top_cul'] + tm * w['top_mil'] * m_mul + ti * w['top_ind'] + 20
        return s

    return max(legal_actions, key=score_action)

def run_tuning(iterations=100, games_per_iter=2000):
    repo = DataRepo(Path("data"))
    engine = RomeEngine(repo)
    
    # 初始参数滑块
    best_p = {'conq_m': 1.1, 'mil_m': 1.1, 'panic_t': 1.5}
    best_score = 0
    history = []
    
    print(f"🧬 开启【V42 神谕调参】...")
    print(f"基准: W_GATHER (11.72) | 样本: {games_per_iter} 局/迭代\n")

    for i in range(iterations):
        # 产生微调 (Mutation)
        test_p = {
            'conq_m': max(0.5, best_p['conq_m'] + random.uniform(-0.1, 0.1)),
            'mil_m': max(0.5, best_p['mil_m'] + random.uniform(-0.1, 0.1)),
            'panic_t': max(0.5, min(3.0, best_p['panic_t'] + random.uniform(-0.2, 0.2)))
        }
        
        base_seed = random.randint(1000000, 9000000)
        scores = []
        fails = 0
        
        for g in range(games_per_iter):
            res = engine.play_game(lambda e, s, h, l: oracle_logic(e, s, h, l, test_p), seed=base_seed + g)
            scores.append(res['总分'])
            if res['是否失败']: fails += 1
            
        avg_s = np.mean(scores)
        fail_r = fails / games_per_iter
        
        # 我们寻找的是：分更高，且失败率低于 0.4% 的参数
        if avg_s > best_score and fail_r < 0.005:
            best_score = avg_s
            best_p = test_p
            print(f"✨ 发现黄金参数! 迭代 {i+1:02d} | 均分: {avg_s:.4f} | 失败率: {fail_r:.2%}")
            print(f"   ∟ {best_p}")
            history.append({**test_p, "avg_score": avg_s, "fail_rate": fail_r})
            pd.DataFrame(history).to_csv("outputs/oracle_tuning_v42.csv", index=False)

if __name__ == "__main__":
    run_train = run_tuning()