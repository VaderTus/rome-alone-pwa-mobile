# scripts/optimize_hyper_params.py
import json
import pandas as pd
import numpy as np
from pathlib import Path
import random
import sys

# 路径修复
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.loader import DataRepo
from core.engine import RomeEngine

# 固化的王者基因组
W_GATHER = {'amphi': 635.6, 'senate': 586.1, 'arc': 493.5, 'pan': 209.1, 'conq_base': 282.3, 'conq_arc': 392.9, 'trib': 71.6, 'top_cul': 33.3, 'top_mil': 28.5, 'top_ind': 23.5}
W_TEMPO = {'amphi': 612.4, 'senate': 597.3, 'arc': 491.9, 'pan': 242.3, 'conq_base': 265.8, 'conq_arc': 362.3, 'trib': 78.1, 'top_cul': 37.3, 'top_mil': 24.1, 'top_ind': 23.7}

def distilled_v5_logic(engine, state, hand, legal_actions, w):
    if not legal_actions: return {"card_id": hand[0], "mode": "top", "kind": "TopResource", "meta": {}}
    turn, regions = state.turn_count, state.occupied_regions()
    inv_row = engine.repo.invasions[engine.repo.invasions["Invasion_Order"] == min(state.invasions_resolved+1, 3)].iloc[0]
    inv_cost = int(inv_row["Pay_Military_To_Avoid"])
    deck_left = len(state.deck)
    senate_active = state.monument_progress.get("M_DiGuoGuangChang", 0) >= 2
    if turn >= 19: red_line = 0
    elif deck_left >= 6: red_line = 1
    elif deck_left >= 3: red_line = max(1, inv_cost - 2)
    else: red_line = inv_cost

    def score_action(a):
        kind, mode, meta = a["kind"], a["mode"], a.get("meta", {})
        c_card = engine.repo.card_by_id[a["card_id"]]
        est_mil = state.military; est_cul = state.culture
        if kind == "Conquest": est_mil -= regions
        elif mode == "bottom":
            est_mil -= int(c_card.get("Cost_Military", 0)); est_cul -= int(c_card.get("Cost_Culture", 0))
        effective_mil = (est_mil + est_cul) if senate_active else est_mil
        if turn < 19 and effective_mil < red_line and kind != "TopResource": return -10000 
        s = 0.0
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
            if state.monument_progress.get("M_KaiXuanMen", 0) >= 2: s += w['conq_arc']
            else: s += w['conq_base'] if regions < 4 else 60
        if kind == "Tribute": s += w['trib'] if regions >= 3 else 30
        if mode == "top":
            tc, tm, ti = int(c_card["Top_Culture"]), int(c_card["Top_Military"]), int(c_card["Top_Industry"])
            if state.culture + tc > 9: s -= 40
            if state.military + tm > 9: s -= 40
            if state.military < red_line: s += tm * 400 + tc * 20
            else:
                s += tc * (w['top_cul'] if senate_active else w['top_cul']-10) + tm * w['top_mil'] + ti * w['top_ind']
            s += 20
        return s
    return max(legal_actions, key=score_action)

def run_optimization(iterations=50, games_per_batch=2000):
    repo = DataRepo(Path("data"))
    engine = RomeEngine(repo)
    
    best_p = {'trigger_sum': 15.0, 'trigger_mil': 5.0, 'mix_ratio': 0.3}
    best_score = 0
    history = []

    print(f"🎚️ 开启【集成大脑】超参数演化...")
    
    for i in range(iterations):
        # 产生微小扰动
        test_p = {
            'trigger_sum': max(5, best_p['trigger_sum'] + random.uniform(-1.5, 1.5)),
            'trigger_mil': max(1, best_p['trigger_mil'] + random.uniform(-1, 1)),
            'mix_ratio': max(0, min(1, best_p['mix_ratio'] + random.uniform(-0.05, 0.05)))
        }
        
        # 交叉验证：使用两组完全不同的种子区间
        seeds = [random.randint(1000000, 9000000), random.randint(1000000, 9000000)]
        scores = []
        
        for base_seed in seeds:
            for g in range(games_per_batch // 2):
                res = engine.play_game(
                    lambda e, s, h, l: distilled_v5_logic(e, s, h, l, 
                        {k: W_GATHER[k]*(1-test_p['mix_ratio']) + W_TEMPO[k]*test_p['mix_ratio'] 
                         if (s.military + s.culture + s.industry) > test_p['trigger_sum'] and s.military > test_p['trigger_mil']
                         else W_GATHER[k] for k in W_GATHER}
                    ),
                    seed=base_seed + g
                )
                scores.append(res['总分'])
        
        avg_s = np.mean(scores)
        if avg_s > best_score:
            best_score = avg_s
            best_p = test_p
            print(f"✨ 迭代 {i+1:02d} | 找到更优参数: {best_p} | 平均分: {avg_s:.4f}")
            history.append({**best_p, "avg_score": avg_s})
            pd.DataFrame(history).to_csv("outputs/hyper_params_log.csv", index=False)

if __name__ == "__main__":
    run_optimization()