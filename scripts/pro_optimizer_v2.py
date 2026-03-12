# scripts/pro_optimizer_v2.py
from pathlib import Path
import sys
import random
import pandas as pd
import numpy as np
import time

# 路径修复
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.loader import DataRepo
from core.engine import RomeEngine

# --- V5 逻辑核心（已参数化） ---
def distilled_v5_logic(engine, state, hand, legal_actions, w):
    if not legal_actions:
        return {"card_id": hand[0], "mode": "top", "kind": "TopResource", "meta": {}}
    turn = state.turn_count
    regions = state.occupied_regions()
    inv_cost, _ = (int(engine.repo.invasions[engine.repo.invasions["Invasion_Order"] == min(state.invasions_resolved+1, 3)].iloc[0]["Pay_Military_To_Avoid"]), 0)
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
            s += w['conq_arc'] if state.monument_progress.get("M_KaiXuanMen", 0) >= 2 else (w['conq_base'] if regions < 4 else 60)
        if kind == "Tribute": s += w['trib'] if regions >= 3 else 30
        if mode == "top":
            tc, tm, ti = int(c_card["Top_Culture"]), int(c_card["Top_Military"]), int(c_card["Top_Industry"])
            if state.culture + tc > 9: s -= 40
            if state.military + tm > 9: s -= 40
            if state.military < red_line: s += tm * 400 + tc * 20
            else: s += tc * (w['top_cul'] if senate_active else w['top_cul']-10) + tm * w['top_mil'] + ti * w['top_ind']
            s += 20
        return s
    return max(legal_actions, key=score_action)

def run_pro_optimization(iterations=100, games_per_iter=5000):
    repo = DataRepo(Path("data"))
    engine = RomeEngine(repo)
    
    # 当前最优（初始设为 V25 的结果）
    current_best_w = {
        'amphi': 712.0, 'senate': 579.0, 'arc': 462.4, 'pan': 191.9, 
        'conq_base': 223.8, 'conq_arc': 413.5, 'trib': 73.6, 
        'top_cul': 35.8, 'top_mil': 27.4, 'top_ind': 21.2
    }
    
    global_best_score = 0
    history = []
    out_file = Path("outputs/pro_optimization_v2.csv")
    out_file.parent.mkdir(parents=True, exist_ok=True)

    print(f"🧬 开启专业演化模型 V2.0")
    print(f"每轮样本: {games_per_iter} | 步长: ±3%~5% | 抗过拟合: 动态种子\n")

    for i in range(iterations):
        # 产生细微波动 (Mutation)
        # 50% 概率进行小步长(3%)，50% 概率进行中步长(8%)
        step = 0.03 if random.random() > 0.5 else 0.08
        mutated_w = {k: v * random.uniform(1-step, 1+step) for k, v in current_best_w.items()}
        
        # 动态种子区间：每轮使用完全不同的 5000 个种子，防止死记硬背
        base_seed = random.randint(1000000, 9000000)
        
        scores = []
        fails = 0
        for g in range(games_per_iter):
            res = engine.play_game(
                lambda e, s, h, l: distilled_v5_logic(e, s, h, l, mutated_w),
                seed=base_seed + g
            )
            scores.append(res['总分'])
            if res['是否失败']: fails += 1

        avg_s = np.mean(scores)
        fail_r = fails / games_per_iter

        # 演化判定：如果这组权重在新的随机种子下依然表现优异 (且不崩盘)
        # 我们设定一个基准线，比如 11.6
        if avg_s > global_best_score:
            global_best_score = avg_s
            current_best_w = mutated_w
            print(f"✨ 发现优良基因组! 迭代 {i+1:03d} | 平均分: {avg_s:.4f} | 失败率: {fail_r:.2%}")
            # 记录历史
            log_entry = {**mutated_w, "avg_score": avg_s, "fail_rate": fail_r, "iteration": i+1}
            history.append(log_entry)
            pd.DataFrame(history).to_csv(out_file, index=False)
        else:
            if (i+1) % 5 == 0:
                print(f"进度: {i+1}/{iterations} | 当前最高均分: {global_best_score:.4f}")

    print(f"\n✅ 演化完成！最终最优基因组已保存。")

if __name__ == "__main__":
    run_pro_optimization(iterations=100, games_per_iter=5000)