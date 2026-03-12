import random
from core.state import GameState

MID_SENATE = "M_DiGuoGuangChang"
MID_COLOSSEUM = "M_LuoMaDouShouChang"
BID_CAMP = "B_JunTuanYaoSai"
BID_AMPHI = "B_YuanXingJingJiChang"
BID_MINE = "B_DiGuoJinKuang"

class RomeEngine:
    def __init__(self, repo, seed=42):
        self.repo = repo
        self.rng = random.Random(seed)

    def new_game(self, seed=None):
        if seed is not None:
            self.rng.seed(seed)
        s = GameState()
        for mid in self.repo.monument_by_id:
            s.monument_progress[mid] = 0
        deck = list(self.repo.cards["Card_ID"])
        self.rng.shuffle(deck)
        s.deck = deck
        return s

    def senate_active(self, s):
        return s.monument_progress.get(MID_SENATE, 0) >= 2

    def colosseum_active(self, s):
        return s.monument_progress.get(MID_COLOSSEUM, 0) >= 2

    def can_pay(self, s, c, m, i):
        if s.industry < i:
            return False
        if self.senate_active(s):
            return (s.culture + s.military) >= (c + m)
        return s.culture >= c and s.military >= m

    def pay(self, s, c, m, i):
        s.industry -= i
        if not self.senate_active(s):
            s.culture -= c
            s.military -= m
            return
        need = c + m
        while need > 0:
            if s.culture >= s.military and s.culture > 0:
                s.culture -= 1
            elif s.military > 0:
                s.military -= 1
            elif s.culture > 0:
                s.culture -= 1
            need -= 1

    def add_resource(self, s, rt, amt):
        if amt <= 0:
            return 0
        if rt == "Culture":
            b = s.culture; s.culture = min(s.max_resource, s.culture + amt); return s.culture - b
        if rt == "Military":
            b = s.military; s.military = min(s.max_resource, s.military + amt); return s.military - b
        if rt == "Industry":
            b = s.industry; s.industry = min(s.max_resource, s.industry + amt); return s.industry - b
        return 0

    def _senate_total_cm_gain(self, s, base_cm):
        if base_cm <= 0:
            return 0
        total = base_cm
        if BID_AMPHI in s.built_buildings:
            total += 2
        if BID_CAMP in s.built_buildings:
            total += 2
        return total

    def gain_with_triggers(self, s, gain, senate_cm_to_culture=None):
        c0 = int(gain.get("Culture", 0))
        m0 = int(gain.get("Military", 0))
        i0 = int(gain.get("Industry", 0))

        gi = self.add_resource(s, "Industry", i0)
        if gi > 0 and BID_MINE in s.built_buildings:
            self.add_resource(s, "Industry", 2)

        if not self.senate_active(s):
            gc = self.add_resource(s, "Culture", c0)
            gm = self.add_resource(s, "Military", m0)
            if gc > 0 and BID_AMPHI in s.built_buildings: self.add_resource(s, "Culture", 2)
            if gm > 0 and BID_CAMP in s.built_buildings: self.add_resource(s, "Military", 2)
            return

        # Senate 激活：Culture/Military 图标可互换（获得端）
        base_cm = c0 + m0
        total_cm = self._senate_total_cm_gain(s, base_cm)
        if total_cm <= 0:
            return

        if senate_cm_to_culture is None:
            # 默认保持“原文化倾向”，并把圆形竞技场加成计入文化偏好（兼容旧策略）
            prefer_c = c0 + (2 if BID_AMPHI in s.built_buildings and base_cm > 0 else 0)
            c_take = max(0, min(total_cm, prefer_c))
        else:
            c_take = max(0, min(total_cm, int(senate_cm_to_culture)))

        m_take = total_cm - c_take
        self.add_resource(s, "Culture", c_take)
        self.add_resource(s, "Military", m_take)

    def draw_hand(self, s):
        n = min(3, len(s.deck))
        return [s.deck.pop() for _ in range(n)]

    def legal_actions(self, s, hand):
        acts = []
        senate = self.senate_active(s)

        for cid in hand:
            r = self.repo.card_by_id[cid]

            tc = int(r["Top_Culture"]); tm = int(r["Top_Military"]); ti = int(r["Top_Industry"])
            top_base_cm = tc + tm
            if senate and top_base_cm > 0:
                top_total_cm = self._senate_total_cm_gain(s, top_base_cm)
                for c_take in range(top_total_cm + 1):
                    acts.append({
                        "card_id": cid,
                        "mode": "top",
                        "kind": "TopResource",
                        "meta": {"senate_cm_to_culture": c_take}
                    })
            else:
                acts.append({"card_id": cid, "mode": "top", "kind": "TopResource", "meta": {}})

            btype = str(r["Bottom_ActionType"])
            c = int(r["Cost_Culture"]); m = int(r["Cost_Military"]); i = int(r["Cost_Industry"])

            if btype == "Conquest":
                need = s.occupied_regions()
                if self.can_pay(s, 0, need, 0):
                    if s.unoccupied_culture_regions() > 0:
                        if senate:
                            cm_total = self._senate_total_cm_gain(s, 1)
                            for c_take in range(cm_total + 1):
                                acts.append({
                                    "card_id": cid, "mode": "bottom", "kind": "Conquest",
                                    "meta": {"target": "Culture", "senate_cm_to_culture": c_take}
                                })
                        else:
                            acts.append({"card_id": cid, "mode": "bottom", "kind": "Conquest", "meta": {"target": "Culture"}})
                    if s.unoccupied_industry_regions() > 0:
                        acts.append({"card_id": cid, "mode": "bottom", "kind": "Conquest", "meta": {"target": "Industry"}})

            elif btype == "Tribute":
                t = str(r["Bottom_TargetResource"])
                if senate and t in {"Culture", "Military"}:
                    cm_total = self._senate_total_cm_gain(s, s.occupied_regions())
                    for c_take in range(cm_total + 1):
                        acts.append({
                            "card_id": cid, "mode": "bottom", "kind": "Tribute",
                            "meta": {"target": t, "senate_cm_to_culture": c_take}
                        })
                else:
                    acts.append({"card_id": cid, "mode": "bottom", "kind": "Tribute", "meta": {"target": t}})

            elif btype == "Build_Building":
                bid = str(r["Ref_Building_ID"]) if r["Ref_Building_ID"] == r["Ref_Building_ID"] else ""
                if bid and (bid not in s.built_buildings) and self.can_pay(s, c, m, i):
                    acts.append({"card_id": cid, "mode": "bottom", "kind": "Build_Building", "meta": {"building_id": bid}})

            elif btype == "Build_Monument":
                mid = str(r["Ref_Monument_ID"]) if r["Ref_Monument_ID"] == r["Ref_Monument_ID"] else ""
                if mid and s.monument_progress[mid] < 2 and self.can_pay(s, c, m, i):
                    acts.append({"card_id": cid, "mode": "bottom", "kind": "Build_Monument", "meta": {"monument_id": mid}})
        return acts

    def apply_action(self, s, hand, a):
        cid = a["card_id"]
        card = self.repo.card_by_id[cid]
        kind = a["kind"]
        senate_cm_to_culture = a.get("meta", {}).get("senate_cm_to_culture")

        if a["mode"] == "top":
            self.gain_with_triggers(
                s,
                {"Culture": int(card["Top_Culture"]), "Military": int(card["Top_Military"]), "Industry": int(card["Top_Industry"])},
                senate_cm_to_culture=senate_cm_to_culture
            )
            for x in hand: s.discard.append(x)
            return

        if kind == "Conquest":
            need = s.occupied_regions()
            self.pay(s, 0, need, 0)
            t = a["meta"]["target"]
            if t == "Culture":
                s.occupied_culture_regions += 1
                self.gain_with_triggers(s, {"Culture": 1}, senate_cm_to_culture=senate_cm_to_culture)
            else:
                s.occupied_industry_regions += 1
                self.gain_with_triggers(s, {"Industry": 1}, senate_cm_to_culture=senate_cm_to_culture)
            for x in hand: s.discard.append(x)
            return

        if kind == "Tribute":
            t = a["meta"]["target"]
            amt = s.occupied_regions()
            g = {"Culture": 0, "Military": 0, "Industry": 0}
            g[t] = amt
            self.gain_with_triggers(s, g, senate_cm_to_culture=senate_cm_to_culture)
            for x in hand: s.discard.append(x)
            return

        if kind == "Build_Building":
            self.pay(s, int(card["Cost_Culture"]), int(card["Cost_Military"]), int(card["Cost_Industry"]))
            s.built_buildings.add(a["meta"]["building_id"])
            for x in hand:
                if x != cid: s.discard.append(x)
            return

        if kind == "Build_Monument":
            self.pay(s, int(card["Cost_Culture"]), int(card["Cost_Military"]), int(card["Cost_Industry"]))
            mid = a["meta"]["monument_id"]
            s.monument_progress[mid] = min(2, s.monument_progress[mid] + 1)
            for x in hand: s.discard.append(x)
            return

    def lose_regions(self, s, n):
        for _ in range(n):
            non_rome = s.occupied_culture_regions + s.occupied_industry_regions
            if non_rome > 0:
                if s.occupied_culture_regions >= s.occupied_industry_regions and s.occupied_culture_regions > 0:
                    s.occupied_culture_regions -= 1
                elif s.occupied_industry_regions > 0:
                    s.occupied_industry_regions -= 1
                else:
                    s.occupied_culture_regions -= 1
            else:
                s.rome_occupied = False
                s.game_lost = True
                return

    def resolve_invasion_if_needed(self, s, policy_name="non_random"):
        if len(s.deck) > 0 or s.invasions_resolved >= 3:
            return
        idx = s.invasions_resolved + 1
        row = self.repo.invasions[self.repo.invasions["Invasion_Order"] == idx].iloc[0]
        pay_m = int(row["Pay_Military_To_Avoid"]); lose_n = int(row["Lose_Regions_If_Not_Paid"])

        if self.colosseum_active(s):
            s.invasions_resolved += 1
            self.rng.shuffle(s.discard); s.deck = s.discard; s.discard = []
            return

        can_pay = self.can_pay(s, 0, pay_m, 0)
        choose_pay = can_pay if policy_name != "random_policy" else (can_pay and self.rng.choice([True, False]))
        if choose_pay: self.pay(s, 0, pay_m, 0)
        else: self.lose_regions(s, lose_n)

        s.invasions_resolved += 1
        self.rng.shuffle(s.discard); s.deck = s.discard; s.discard = []

    def score(self, s):
        if s.game_lost: return 0
        total = s.occupied_regions()
        for bid in s.built_buildings:
            total += int(self.repo.building_by_id[bid]["Immediate_GP"])
        for mid, p in s.monument_progress.items():
            if p < 2: continue
            m = self.repo.monument_by_id[mid]
            st = str(m["Score_Type"]); v = int(m["Score_Value"])
            if st == "FlatGP": total += v
            elif st == "PerBuilding": total += v * len(s.built_buildings)
            elif st == "PerRegion": total += v * s.occupied_regions()
            elif st == "MinResource": total += v * min(s.culture, s.military, s.industry)
        return total

    def play_game(self, policy_fn, seed=None, policy_name="policy"):
        s = self.new_game(seed=seed)
        while (not s.game_lost) and s.invasions_resolved < 3:
            s.turn_count += 1
            hand = self.draw_hand(s)
            if not hand: break
            legal = self.legal_actions(s, hand)
            action = policy_fn(self, s, hand, legal)
            self.apply_action(s, hand, action)
            self.resolve_invasion_if_needed(s, policy_name=policy_name)
        score = self.score(s)
        return {"策略": policy_name, "是否失败": s.game_lost, "总分": score, "回合数": s.turn_count}