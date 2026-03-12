# scripts/auto_optimizer_v5.py
from pathlib import Path
import sys
import random
import pandas as pd
import numpy as np

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
        
        est_mil = state.military
        est_cul = state.culture
        if kind == "Conquest": est_mil -= regions
        elif kind == "Build_Building" or kind == "Build_Monument":
            est_mil -= int(c_card["Cost_Military"])
            est_cul -= int(c_card["Cost_Culture"])

        effective_mil = (est_mil + est_cul) if senate_active else est_mil
        if turn < 19 and effective_mil < red_line and kind != "TopResource":
            return -10000 

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
            if state.military < red_line:
                s += tm * 400 + tc * 20
            else:
                s += tc * (w['top_cul'] if senate_active else w['top_cul']-10) + \
                     tm * w['top_mil'] + ti * w['top_ind']
            s += 20
        return s

    return max(legal_actions, key=score_action)

def run_batch(iterations=100, games_per_iter=1000):
    repo = DataRepo(Path("data"))
    engine = RomeEngine(repo)
    
    # V5 初始权重
    base_weights = {
        'amphi': 765, 'senate': 581, 'arc': 418, 'pan': 204, 
        'conq_base': 241, 'conq_arc': 355, 'trib': 65, 
        'top_cul': 35, 'top_mil': 23, 'top_ind': 21
    }

    results = []
    out_file = Path("outputs/optimization_log.csv")
    out_file.parent.mkdir(parents=True, exist_ok=True)

    print(f"🚀 开始自动化权重演化...")
    print(f"总计迭代: {iterations} 次 | 每次测试: {games_per_iter} 局\n")

    for i in range(iterations):
        # 产生扰动：在基准权重的 80% ~ 120% 之间随机
        current_w = {k: v * random.uniform(0.8, 1.2) for k, v in base_weights.items()}
        
        scores = []
        fails = 0
        high_scores = 0 # 14+ 分局数

        for g in range(games_per_iter):
            # 运行游戏
            res = engine.play_game(
                lambda e, s, h, l: distilled_v5_logic(e, s, h, l, current_w),
                seed=3000000 + g # 保持每组迭代使用的种子库一致，才有可比性
            )
            scores.append(res['总分'])
            if res['是否失败']: fails += 1
            if res['总分'] >= 14: high_scores += 1

        avg_score = np.mean(scores)
        fail_rate = fails / games_per_iter
        high_rate = high_scores / games_per_iter

        # 记录结果
        log_entry = {**current_w, "avg_score": avg_score, "fail_rate": fail_rate, "high_rate": high_rate}
        results.append(log_entry)
        
        # 实时存盘，防止中断
        pd.DataFrame(results).to_csv(out_file, index=False)
        
        print(f"迭代 {i+1:03d} | 平均分: {avg_score:.3f} | 14+率: {high_rate:.1%} | 失败率: {fail_rate:.1%}")
        
        # 如果发现历史最佳，打印出来
        if avg_score == max([r['avg_score'] for r in results]):
            print(f" ⭐ 发现新最优权重组合！")

    print(f"\n✅ 演化完成！结果已保存至: {out_file}")

if __name__ == "__main__":
    # 你可以根据电脑性能调整：iterations 是测试多少组权重，games_per_iter 是每组跑多少局。
    # 默认 100组 * 1000局 = 10万局。
    run_batch(iterations=100, games_per_iter=1000)