# policies/mcts_distilled_final.py
import math
import copy

# ==========================================
# 🏆 黄金基因库：50万局 MCTS 提炼出的人类顶级直觉
# ==========================================
W_BASE = {
    'amphi': 635.6, 'senate': 586.1, 'arc': 493.5, 'pan': 209.1, 
    'conq_base': 282.3, 'conq_arc': 392.9, 'trib': 71.6, 
    'top_cul': 33.3, 'top_mil': 28.5, 'top_ind': 23.5
}

def get_next_inv_info(engine, state):
    idx = min(state.invasions_resolved + 1, 3)
    row = engine.repo.invasions[engine.repo.invasions["Invasion_Order"] == idx].iloc[0]
    return int(row["Pay_Military_To_Avoid"]), int(row["Lose_Regions_If_Not_Paid"])

def evaluate_state(engine, s, c_card, kind, mode, meta):
    """纯粹的即时价值评估"""
    turn = s.turn_count
    regions = s.occupied_regions()
    senate_active = s.monument_progress.get("M_DiGuoGuangChang", 0) >= 2
    
    score = 0.0
    if kind == "Build_Building":
        bid = meta.get("building_id")
        if bid == "B_YuanXingJingJiChang": score += W_BASE['amphi'] if turn <= 10 else 150
        elif bid in {"B_KaiXuanDiaoSu", "B_DiGuoYinShuiDao"}: score += 160 if turn >= 14 else 40
    if kind == "Build_Monument":
        mid = meta.get("monument_id")
        if mid == "M_DiGuoGuangChang": score += W_BASE['senate'] if turn <= 12 else 150
        elif mid == "M_KaiXuanMen": score += W_BASE['arc'] if turn >= 6 else 100
        elif mid == "M_WanShenMiao": score += W_BASE['pan'] if turn >= 14 else 60
    if kind == "Conquest":
        if s.monument_progress.get("M_KaiXuanMen", 0) >= 2: score += W_BASE['conq_arc']
        else: score += W_BASE['conq_base'] if regions < 4 else 60
    if kind == "Tribute":
        score += W_BASE['trib'] if regions >= 3 else 30
        
    if mode == "top":
        tc, tm, ti = int(c_card["Top_Culture"]), int(c_card["Top_Military"]), int(c_card["Top_Industry"])
        # 防止溢出的智慧
        if s.culture + tc > 9: score -= 40
        if s.military + tm > 9: score -= 40
        score += tc * (W_BASE['top_cul'] if senate_active else W_BASE['top_cul']-10) + \
                 tm * W_BASE['top_mil'] + ti * W_BASE['top_ind']
        score += 20

    return score

def select_action(engine, state, hand, legal_actions):
    if not legal_actions: return {"card_id": hand[0], "mode": "top", "kind": "TopResource", "meta": {}}

    turn = state.turn_count
    inv_cost, _ = get_next_inv_info(engine, state)
    deck_left = len(state.deck)
    senate_active = state.monument_progress.get("M_DiGuoGuangChang", 0) >= 2

    # 🛡️ 绝对生存红线：雷打不动，保底之王
    if turn >= 19: red_line = 0
    elif deck_left >= 6: red_line = 1
    elif deck_left >= 3: red_line = max(1, inv_cost - 2)
    else: red_line = inv_cost

    best_act = None
    max_score = -float('inf')

    for act in legal_actions:
        kind, mode, meta = act["kind"], act["mode"], act.get("meta", {})
        c_card = engine.repo.card_by_id[act["card_id"]]
        
        # 1. 死亡剪枝
        est_mil = state.military; est_cul = state.culture
        if kind == "Conquest": est_mil -= state.occupied_regions()
        elif mode == "bottom":
            est_mil -= int(c_card.get("Cost_Military", 0))
            est_cul -= int(c_card.get("Cost_Culture", 0))
        effective_mil = (est_mil + est_cul) if senate_active else est_mil
        
        if turn < 19 and effective_mil < red_line and kind != "TopResource":
            continue 

        # 2. 基础估值
        base_score = evaluate_state(engine, state, c_card, kind, mode, meta)
        
        # 3. 引擎潜力补偿 (Look-ahead Potential)
        potential = 0.0
        has_camp = "B_JunTuanYaoSai" in state.built_buildings or (kind == "Build_Building" and meta.get("building_id") == "B_JunTuanYaoSai")
        has_amphi = "B_YuanXingJingJiChang" in state.built_buildings or (kind == "Build_Building" and meta.get("building_id") == "B_YuanXingJingJiChang")
        
        if has_camp: potential += 30
        if has_amphi: potential += 30

        total_score = base_score + potential

        if total_score > max_score:
            max_score = total_score
            best_act = act

    return best_act if best_act else legal_actions[0]