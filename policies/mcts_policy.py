import copy
import random

def _next_inv_pay(engine, state):
    idx = min(state.invasions_resolved + 1, 3)
    row = engine.repo.invasions[engine.repo.invasions["Invasion_Order"] == idx].iloc[0]
    return int(row["Pay_Military_To_Avoid"])

def _heuristic_state_value(engine, s):
    if s.game_lost:
        return 0.0
    v = 0.0
    v += 3.0 * s.occupied_regions()
    v += 2.0 * len(s.built_buildings)
    v += 2.2 * sum(1 for x in s.monument_progress.values() if x >= 2)
    v += 0.3 * (s.culture + s.military + s.industry)
    v += 0.2 * min(s.culture, s.military, s.industry)
    v += 0.4 * max(0, s.military - _next_inv_pay(engine, s))
    return v

def _rollout_pick_action(engine, s, hand, legal, rng):
    if not legal:
        return {"card_id": hand[0], "mode": "top", "kind": "TopResource", "meta": {}}

    if rng.random() < 0.18:
        return rng.choice(legal)

    def score(a):
        k = a["kind"]
        if k == "Conquest":
            return 10.0 if s.military >= _next_inv_pay(engine, s) else 4.0
        if k == "Build_Monument":
            mid = a["meta"].get("monument_id")
            return 11.0 if mid in {"M_KaiXuanMen", "M_DiGuoGuangChang"} else 7.0
        if k == "Build_Building":
            bid = a["meta"].get("building_id")
            if bid == "B_YuanXingJingJiChang":
                return 10.0
            if bid in {"B_KaiXuanDiaoSu", "B_DiGuoYinShuiDao"}:
                return 8.0
            return 5.0
        if k == "TopResource":
            c = engine.repo.card_by_id[a["card_id"]]
            return int(c["Top_Culture"]) * 1.6 + int(c["Top_Military"]) * 1.4 + int(c["Top_Industry"]) * 1.0
        return 3.0

    return max(legal, key=score)

def _simulate_action(engine, s, hand, a):
    engine.apply_action(s, hand, a)
    engine.resolve_invasion_if_needed(s, policy_name="non_random")

def _rollout(engine, s, rng, max_turns=10):
    t = 0
    while (not s.game_lost) and s.invasions_resolved < 3 and t < max_turns:
        s.turn_count += 1
        hand = engine.draw_hand(s)
        if not hand:
            break
        legal = engine.legal_actions(s, hand)
        a = _rollout_pick_action(engine, s, hand, legal, rng)
        _simulate_action(engine, s, hand, a)
        t += 1

    if s.game_lost or s.invasions_resolved >= 3:
        return float(engine.score(s))
    return _heuristic_state_value(engine, s)

def select_action(engine, state, hand, legal_actions):
    if not legal_actions:
        return {"card_id": hand[0], "mode": "top", "kind": "TopResource", "meta": {}}

    iterations_per_action = 14
    rollout_horizon = 10

    best_action = None
    best_q = -10**9

    for idx, a in enumerate(legal_actions):
        total = 0.0
        rng = random.Random((state.turn_count + 1) * 10007 + idx * 97 + len(hand) * 13)

        for _ in range(iterations_per_action):
            s = copy.deepcopy(state)
            h = hand.copy()
            _simulate_action(engine, s, h, a)
            total += _rollout(engine, s, rng, max_turns=rollout_horizon)

        q = total / iterations_per_action
        if q > best_q:
            best_q = q
            best_action = a

    return best_action