from pathlib import Path

ROOT = Path(__file__).resolve().parent
(ROOT / "data").mkdir(parents=True, exist_ok=True)
(ROOT / "core").mkdir(parents=True, exist_ok=True)
(ROOT / "policies").mkdir(parents=True, exist_ok=True)
(ROOT / "experiments").mkdir(parents=True, exist_ok=True)
(ROOT / "ui").mkdir(parents=True, exist_ok=True)
(ROOT / "outputs").mkdir(parents=True, exist_ok=True)

files = {
    "requirements.txt": "pandas>=2.0.0\n",

    "core/__init__.py": "# core package\n",
    "policies/__init__.py": "# policies package\n",
    "experiments/__init__.py": "# experiments package\n",
    "ui/__init__.py": "# ui package\n",

    "core/state.py": """
from dataclasses import dataclass, field
from typing import Dict, List, Set

@dataclass
class GameState:
    culture: int = 1
    military: int = 1
    industry: int = 1
    max_resource: int = 9

    rome_occupied: bool = True
    occupied_culture_regions: int = 0
    occupied_industry_regions: int = 0
    total_culture_regions: int = 3
    total_industry_regions: int = 3

    built_buildings: Set[str] = field(default_factory=set)
    monument_progress: Dict[str, int] = field(default_factory=dict)

    deck: List[str] = field(default_factory=list)
    discard: List[str] = field(default_factory=list)

    invasions_resolved: int = 0
    game_lost: bool = False
    turn_count: int = 0

    def occupied_regions(self) -> int:
        return (1 if self.rome_occupied else 0) + self.occupied_culture_regions + self.occupied_industry_regions

    def unoccupied_culture_regions(self) -> int:
        return self.total_culture_regions - self.occupied_culture_regions

    def unoccupied_industry_regions(self) -> int:
        return self.total_industry_regions - self.occupied_industry_regions
""",

    "core/loader.py": """
from pathlib import Path
import pandas as pd

class DataRepo:
    def __init__(self, data_dir: Path):
        self.cards = pd.read_csv(data_dir / "Cards.csv", encoding="utf-8-sig")
        self.buildings = pd.read_csv(data_dir / "Buildings.csv", encoding="utf-8-sig")
        self.monuments = pd.read_csv(data_dir / "Monuments.csv", encoding="utf-8-sig")
        self.invasions = pd.read_csv(data_dir / "Invasions.csv", encoding="utf-8-sig")

        self.card_by_id = {r["Card_ID"]: r for _, r in self.cards.iterrows()}
        self.building_by_id = {r["Building_ID"]: r for _, r in self.buildings.iterrows()}
        self.monument_by_id = {r["Monument_ID"]: r for _, r in self.monuments.iterrows()}
""",

    "core/engine.py": """
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

    def gain_with_triggers(self, s, gain):
        gc = self.add_resource(s, "Culture", gain.get("Culture", 0))
        gm = self.add_resource(s, "Military", gain.get("Military", 0))
        gi = self.add_resource(s, "Industry", gain.get("Industry", 0))
        if gc > 0 and BID_AMPHI in s.built_buildings: self.add_resource(s, "Culture", 2)
        if gm > 0 and BID_CAMP in s.built_buildings: self.add_resource(s, "Military", 2)
        if gi > 0 and BID_MINE in s.built_buildings: self.add_resource(s, "Industry", 2)

    def draw_hand(self, s):
        n = min(3, len(s.deck))
        return [s.deck.pop() for _ in range(n)]

    def legal_actions(self, s, hand):
        acts = []
        for cid in hand:
            r = self.repo.card_by_id[cid]
            acts.append({"card_id": cid, "mode": "top", "kind": "TopResource", "meta": {}})

            btype = str(r["Bottom_ActionType"])
            c = int(r["Cost_Culture"]); m = int(r["Cost_Military"]); i = int(r["Cost_Industry"])

            if btype == "Conquest":
                need = s.occupied_regions()
                if self.can_pay(s, 0, need, 0):
                    if s.unoccupied_culture_regions() > 0:
                        acts.append({"card_id": cid, "mode": "bottom", "kind": "Conquest", "meta": {"target": "Culture"}})
                    if s.unoccupied_industry_regions() > 0:
                        acts.append({"card_id": cid, "mode": "bottom", "kind": "Conquest", "meta": {"target": "Industry"}})
            elif btype == "Tribute":
                t = str(r["Bottom_TargetResource"])
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

        if a["mode"] == "top":
            self.gain_with_triggers(s, {"Culture": int(card["Top_Culture"]), "Military": int(card["Top_Military"]), "Industry": int(card["Top_Industry"])})
            for x in hand: s.discard.append(x)
            return

        if kind == "Conquest":
            need = s.occupied_regions()
            self.pay(s, 0, need, 0)
            t = a["meta"]["target"]
            if t == "Culture":
                s.occupied_culture_regions += 1
                self.gain_with_triggers(s, {"Culture": 1})
            else:
                s.occupied_industry_regions += 1
                self.gain_with_triggers(s, {"Industry": 1})
            for x in hand: s.discard.append(x)
            return

        if kind == "Tribute":
            t = a["meta"]["target"]
            amt = s.occupied_regions()
            g = {"Culture": 0, "Military": 0, "Industry": 0}
            g[t] = amt
            self.gain_with_triggers(s, g)
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
""",

    "policies/random_policy.py": """
def select_action(engine, state, hand, legal_actions):
    if not legal_actions:
        return {"card_id": hand[0], "mode": "top", "kind": "TopResource", "meta": {}}
    return engine.rng.choice(legal_actions)
""",

    "policies/arc_policy.py": """
TARGET_MONUMENTS = {"M_KaiXuanMen", "M_DiGuoGuangChang"}

def score_action(a):
    k = a["kind"]; m = a["meta"]
    if k == "Build_Monument" and m.get("monument_id") in TARGET_MONUMENTS: return 100
    if k == "Conquest": return 70
    if k == "Build_Building": return 40
    if k == "Tribute": return 20
    return 10

def select_action(engine, state, hand, legal_actions):
    if not legal_actions:
        return {"card_id": hand[0], "mode": "top", "kind": "TopResource", "meta": {}}
    return max(legal_actions, key=score_action)
""",

    "policies/pantheon_policy.py": """
TARGET_MONUMENT = "M_WanShenMiao"
GP_BUILDINGS = {"B_KaiXuanDiaoSu", "B_DiGuoYinShuiDao"}

def score_action(a):
    k = a["kind"]; m = a["meta"]
    if k == "Build_Monument" and m.get("monument_id") == TARGET_MONUMENT: return 100
    if k == "Build_Building" and m.get("building_id") in GP_BUILDINGS: return 80
    if k == "Conquest": return 35
    if k == "Build_Building": return 30
    return 10

def select_action(engine, state, hand, legal_actions):
    if not legal_actions:
        return {"card_id": hand[0], "mode": "top", "kind": "TopResource", "meta": {}}
    return max(legal_actions, key=score_action)
""",

    "policies/registry.py": """
from policies.random_policy import select_action as random_policy
from policies.arc_policy import select_action as arc_policy
from policies.pantheon_policy import select_action as pantheon_policy

POLICIES = {
    "random_policy": random_policy,
    "arc_policy": arc_policy,
    "pantheon_policy": pantheon_policy,
}
""",

    "experiments/run_single_strategy.py": """
from pathlib import Path
import argparse
import pandas as pd
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))

from core.loader import DataRepo
from core.engine import RomeEngine
from policies.registry import POLICIES

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--policy", type=str, default="pantheon_policy")
    p.add_argument("--games", type=int, default=300)
    p.add_argument("--seed", type=int, default=1200000)
    args = p.parse_args()

    if args.policy not in POLICIES:
        raise ValueError(f"未知策略: {args.policy}, 可选: {list(POLICIES.keys())}")

    repo = DataRepo(ROOT / "data")
    eng = RomeEngine(repo, seed=42)
    fn = POLICIES[args.policy]

    rows = []
    for i in range(args.games):
        rows.append(eng.play_game(fn, seed=args.seed + i, policy_name=args.policy))

    df = pd.DataFrame(rows)
    summary = {
        "策略": args.policy,
        "局数": args.games,
        "平均分": round(float(df["总分"].mean()), 3),
        "中位分": round(float(df["总分"].median()), 3),
        "最高分": int(df["总分"].max()),
        "失败率": f"{df['是否失败'].mean()*100:.2f}%"
    }

    out = ROOT / "outputs"
    out.mkdir(exist_ok=True)
    pd.DataFrame([summary]).to_csv(out / f"single_{args.policy}_summary.csv", index=False, encoding="utf-8-sig")
    df.to_csv(out / f"single_{args.policy}_detail.csv", index=False, encoding="utf-8-sig")

    print(pd.DataFrame([summary]).to_string(index=False))
    print(f"已导出到: {out}")

if __name__ == "__main__":
    main()
""",

    "ui/cli_panel.py": """
import sys
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent.parent

def main():
    print("==== Rome Alone CLI 面板 ====")
    print("策略: random_policy / arc_policy / pantheon_policy")
    policy = input("策略 [pantheon_policy]: ").strip() or "pantheon_policy"
    games = input("对局数 [300]: ").strip() or "300"
    seed = input("seed起点 [1200000]: ").strip() or "1200000"

    cmd = [
        sys.executable,
        str(ROOT / "experiments" / "run_single_strategy.py"),
        "--policy", policy,
        "--games", games,
        "--seed", seed
    ]
    subprocess.run(cmd, check=False)

if __name__ == "__main__":
    main()
"""
}

for rel, text in files.items():
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text.strip() + "\n", encoding="utf-8-sig")

print("✅ v2 基础文件已生成")
print("⚠️ 请确认 data 目录下已有 4 个CSV：Cards/Buildings/Monuments/Invasions")