# scripts/optimize_ensemble_v2.py
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

# --- 导入我们辛苦练出来的三大基因 ---
GENES = {
    'GENERAL': {'amphi': 635.4, 'senate': 594.1, 'arc': 472.9, 'pan': 226.9, 'conq_base': 268.8, 'conq_arc': 376.2, 'trib': 69.7, 'top_cul': 35.3, 'top_mil': 27.2, 'top_ind': 23.7},
    'WARLORD': {'amphi': 674.5, 'senate': 521.7, 'arc': 431.5, 'pan': 213.7, 'conq_base': 253.3, 'conq_arc': 416.6, 'trib': 71.7, 'top_cul': 32.4, 'top_mil': 29.1, 'top_ind': 25.2},
    'ARCHITECT': {'amphi': 640.9, 'senate': 530.4, 'arc': 411.0, 'pan': 197.6, 'conq_base': 264.4, 'conq_arc': 347.4, 'trib': 73.5, 'top_cul': 30.3, 'top_mil': 21.8, 'top_ind': 24.8}
}

# --- 核心：带参数的集成逻辑 ---
def ensemble_logic(engine, state, hand, legal_actions, p):
    # p 是我们要优化的“指挥参数”
    turn = state.turn_count
    regions = state.occupied_regions()
    inv_cost = int(engine.repo.invasions[engine.repo.invasions["Invasion_Order"] == min(state.invasions_resolved+1, 3)].iloc[0]["Pay_Military_To_Avoid"])
    senate_active = state.monument_progress.get("M_DiGuoGuangChang", 0) >= 2

    # 计算每个人格的话语权 (Soft Gating)
    # 战神话语权：如果军事 < 阈值，按比例增加
    w_warlord = max(0, (p['mil_threshold'] - state.military)) * p['warlord_k']
    # 建筑师话语权：如果工业 > 阈值，按比例增加
    w_architect = max(0, (state.industry - p['ind_threshold'])) * p['arch_k']
    w_general = 1.0 # 基准

    def get_score(a, w):
        kind, mode, meta = a["kind"], a["mode"], a.get("meta", {})
        c_card = engine.repo.card_by_id[a["card_id"]]
        
        # 内部生存红线判定 (使用 V26 最稳的那一套)
        est_mil = state.military; est_cul = state.culture
        if kind == "Conquest": est_mil -= regions
        elif mode == "bottom":
            est_mil -= int(c_card.get("Cost_Military", 0)); est_cul -= int(c_card.get("Cost_Culture", 0))
        effective_mil = (est_mil + est_cul) if senate_active else est_mil
        # 这里的 red_line 简化为 1，正式运行会在 engine 里校验
        if turn < 19 and effective_mil < 1 and kind != "TopResource": return -10000 

        s = 0.0
        # 基础 V5 计分结构
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
            s += w['conq_arc'] if state.monument_progress.get("M_KaiXuanMen", 0) >= 2 else (w['conq_base'] if regions < 4 else 60)
        if kind == "Tribute": s += w['trib'] if regions >= 3 else 30
        if mode == "top":
            tc, tm, ti = int(c_card["Top_Culture"]), int(c_card["Top_Military"]), int(c_card["Top_Industry"])
            if state.culture + tc > 9: s -= 40
            if state.military + tm > 9: s -= 40
            s += tc * (w['top_cul'] if senate_active else w['top_cul']-10) + tm * w['top_mil'] + ti * w['top_ind'] + 20
        return s

    # 最终加权评分
    def final_score(a):
        return get_score(a, GENES['GENERAL']) * w_general + \
               get_score(a, GENES['WARLORD']) * w_warlord + \
               get_score(a, GENES['ARCHITECT']) * w_architect

    return max(legal_actions, key=final_score)

def run_optimization(iterations=100, games_per_iter=2000):
    repo = DataRepo(Path("data"))
    engine = RomeEngine(repo)
    
    # 初始调音台设置
    current_best_p = {
        'mil_threshold': 3.0, # 军事低于3开始变战神
        'ind_threshold': 5.0, # 工业高于5开始变建筑师
        'warlord_k': 0.1,     # 战神介入的斜率
        'arch_k': 0.1         # 建筑师介入的斜率
    }
    
    global_best_score = 0
    history = []
    
    print("🎚️ 开始优化【集成大脑】操控参数...")

    for i in range(iterations):
        # 随机扰动这些“滑块”
        test_p = {
            'mil_threshold': max(1, current_best_p['mil_threshold'] + random.uniform(-1, 1)),
            'ind_threshold': max(1, current_best_p['ind_threshold'] + random.uniform(-1, 1)),
            'warlord_k': max(0, current_best_p['warlord_k'] + random.uniform(-0.05, 0.05)),
            'arch_k': max(0, current_best_p['arch_k'] + random.uniform(-0.05, 0.05))
        }
        
        base_seed = random.randint(1000000, 9000000)
        scores = []
        for g in range(games_per_iter):
            res = engine.play_game(lambda e, s, h, l: ensemble_logic(e, s, h, l, test_p), seed=base_seed + g)
            scores.append(res['总分'])
        
        avg_s = np.mean(scores)
        if avg_s > global_best_score:
            global_best_score = avg_s
            current_best_p = test_p
            print(f"✨ 找到更完美的融合参数! 迭代 {i+1:03d} | 平均分: {avg_s:.4f}")
            history.append({**test_p, "avg_score": avg_s})
            pd.DataFrame(history).to_csv("outputs/ensemble_optimized_params.csv", index=False)

if __name__ == "__main__":
    run_optimization()