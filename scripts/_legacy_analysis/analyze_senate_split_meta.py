# scripts/analyze_senate_split_meta.py
from pathlib import Path
import argparse
import importlib
import sys

# === 路径修复：确保从 scripts 直接运行时也能 import core/policies ===
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd

from core.loader import DataRepo
from core.engine import RomeEngine

MID_SENATE = "M_DiGuoGuangChang"
BID_AMPHI = "B_YuanXingJingJiChang"
BID_CAMP = "B_JunTuanYaoSai"


def load_policy_fn(policy_name: str):
    try:
        reg = importlib.import_module("policies.registry")
        if hasattr(reg, "get_policy_fn"):
            return reg.get_policy_fn(policy_name)
        if hasattr(reg, "get_policy"):
            return reg.get_policy(policy_name)
    except Exception:
        pass

    mod = importlib.import_module(f"policies.{policy_name}")
    if hasattr(mod, "select_action"):
        return mod.select_action
    raise ValueError(f"无法加载策略: {policy_name}")


def get_next_inv_info(engine, state):
    idx = min(state.invasions_resolved + 1, 3)
    row = engine.repo.invasions[engine.repo.invasions["Invasion_Order"] == idx].iloc[0]
    return int(row["Pay_Military_To_Avoid"]), int(row["Lose_Regions_If_Not_Paid"])


def senate_total_cm_gain(state, base_cm):
    if base_cm <= 0:
        return 0
    total = base_cm
    if BID_AMPHI in state.built_buildings:
        total += 2
    if BID_CAMP in state.built_buildings:
        total += 2
    return total


def cm_total_for_action(engine, state, action):
    """
    返回该动作在 Senate 语义下可分配的 CM 总量（Culture+Military pool）
    若不涉及 CM 拆分，返回 0
    """
    kind = action["kind"]
    mode = action["mode"]
    meta = action.get("meta", {})
    card = engine.repo.card_by_id[action["card_id"]]

    if mode == "top":
        tc = int(card["Top_Culture"])
        tm = int(card["Top_Military"])
        return senate_total_cm_gain(state, tc + tm)

    if kind == "Conquest":
        if meta.get("target") == "Culture":
            return senate_total_cm_gain(state, 1)
        return 0

    if kind == "Tribute":
        t = meta.get("target")
        if t in {"Culture", "Military"}:
            return senate_total_cm_gain(state, state.occupied_regions())
        return 0

    return 0


def run_and_collect(policy_name, games, seed_start):
    repo = DataRepo(Path("data"))
    policy_fn = load_policy_fn(policy_name)

    game_rows = []
    action_rows = []

    for i in range(games):
        seed = seed_start + i
        engine = RomeEngine(repo, seed=seed)
        s = engine.new_game(seed=seed)

        senate_completed_turn = None
        cm_c_total = 0
        cm_m_total = 0
        cm_c_urgent = 0
        cm_m_urgent = 0

        while (not s.game_lost) and s.invasions_resolved < 3:
            s.turn_count += 1
            hand = engine.draw_hand(s)
            if not hand:
                break

            legal = engine.legal_actions(s, hand)
            action = policy_fn(engine, s, hand, legal)

            senate_active_before = s.monument_progress.get(MID_SENATE, 0) >= 2
            inv_cost, _ = get_next_inv_info(engine, s)
            military_urgent = s.military < inv_cost

            # 记录 Senate 拆分动作
            alloc_c = action.get("meta", {}).get("senate_cm_to_culture", None)
            total_cm = 0
            alloc_m = 0

            if senate_active_before and alloc_c is not None:
                total_cm = cm_total_for_action(engine, s, action)
                if total_cm > 0:
                    alloc_c = max(0, min(total_cm, int(alloc_c)))
                    alloc_m = total_cm - alloc_c
                    cm_c_total += alloc_c
                    cm_m_total += alloc_m
                    if military_urgent:
                        cm_c_urgent += alloc_c
                        cm_m_urgent += alloc_m

            action_rows.append({
                "seed": seed,
                "turn": s.turn_count,
                "senate_active_before": senate_active_before,
                "kind": action["kind"],
                "mode": action["mode"],
                "target": action.get("meta", {}).get("target", ""),
                "senate_cm_to_culture": action.get("meta", {}).get("senate_cm_to_culture", ""),
                "cm_total": total_cm,
                "cm_alloc_culture": alloc_c if total_cm > 0 else "",
                "cm_alloc_military": alloc_m if total_cm > 0 else "",
                "military_urgent": military_urgent,
                "military_before": s.military,
                "culture_before": s.culture,
                "industry_before": s.industry,
                "regions_before": s.occupied_regions()
            })

            # 应用动作 + 入侵
            engine.apply_action(s, hand, action)
            engine.resolve_invasion_if_needed(s, policy_name=policy_name)

            # 检测 Senate 完成回合
            if senate_completed_turn is None and s.monument_progress.get(MID_SENATE, 0) >= 2:
                senate_completed_turn = s.turn_count

        score = engine.score(s)

        game_rows.append({
            "seed": seed,
            "score": score,
            "lost": s.game_lost,
            "turns": s.turn_count,
            "senate_completed": senate_completed_turn is not None,
            "senate_completed_turn": senate_completed_turn if senate_completed_turn is not None else "",
            "cm_total_culture_alloc": cm_c_total,
            "cm_total_military_alloc": cm_m_total,
            "cm_total_alloc": cm_c_total + cm_m_total,
            "cm_urgent_culture_alloc": cm_c_urgent,
            "cm_urgent_military_alloc": cm_m_urgent,
            "cm_urgent_total_alloc": cm_c_urgent + cm_m_urgent
        })

    return pd.DataFrame(game_rows), pd.DataFrame(action_rows)


def print_summary(df_game: pd.DataFrame):
    n = len(df_game)
    avg_score = df_game["score"].mean()
    fail_rate = (df_game["lost"].mean() * 100.0) if n > 0 else 0.0
    senate_rate = (df_game["senate_completed"].mean() * 100.0) if n > 0 else 0.0

    done = df_game[df_game["senate_completed"] == True]
    avg_done_turn = done["senate_completed_turn"].astype(float).mean() if len(done) > 0 else float("nan")

    cm_c = df_game["cm_total_culture_alloc"].sum()
    cm_m = df_game["cm_total_military_alloc"].sum()
    cm_all = cm_c + cm_m
    c_ratio = (cm_c / cm_all * 100.0) if cm_all > 0 else 0.0
    m_ratio = (cm_m / cm_all * 100.0) if cm_all > 0 else 0.0

    u_c = df_game["cm_urgent_culture_alloc"].sum()
    u_m = df_game["cm_urgent_military_alloc"].sum()
    u_all = u_c + u_m
    u_c_ratio = (u_c / u_all * 100.0) if u_all > 0 else 0.0
    u_m_ratio = (u_m / u_all * 100.0) if u_all > 0 else 0.0

    print("\n=== Senate 拆分元策略分析 ===")
    print(f"样本局数: {n}")
    print(f"平均分: {avg_score:.3f}")
    print(f"失败率: {fail_rate:.2f}%")
    print(f"Senate 完成率: {senate_rate:.2f}%")
    if len(done) > 0:
        print(f"Senate 平均完成回合: {avg_done_turn:.2f}")
    else:
        print("Senate 平均完成回合: N/A")

    print(f"CM 总拆分: Culture={cm_c}, Military={cm_m}, 占比=({c_ratio:.1f}% / {m_ratio:.1f}%)")
    print(f"军事紧急窗口 CM 拆分: Culture={u_c}, Military={u_m}, 占比=({u_c_ratio:.1f}% / {u_m_ratio:.1f}%)")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--policy", type=str, default="mcts_policy")
    parser.add_argument("--games", type=int, default=2000)
    parser.add_argument("--seed-start", type=int, default=1300000)
    args = parser.parse_args()

    df_game, df_action = run_and_collect(
        policy_name=args.policy,
        games=args.games,
        seed_start=args.seed_start
    )

    print_summary(df_game)

    out_dir = Path("outputs")
    out_dir.mkdir(parents=True, exist_ok=True)

    game_path = out_dir / f"senate_meta_games_{args.policy}_{args.games}.csv"
    action_path = out_dir / f"senate_meta_actions_{args.policy}_{args.games}.csv"

    df_game.to_csv(game_path, index=False, encoding="utf-8-sig")
    df_action.to_csv(action_path, index=False, encoding="utf-8-sig")

    print(f"\n已导出:\n- {game_path}\n- {action_path}")


if __name__ == "__main__":
    main()