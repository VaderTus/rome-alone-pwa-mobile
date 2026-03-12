from pathlib import Path
import argparse
import json
import pandas as pd
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))

from core.loader import DataRepo
from core.engine import RomeEngine
from policies.registry import POLICIES


def snapshot_state(s):
    return {
        "turn": s.turn_count,
        "culture": s.culture,
        "military": s.military,
        "industry": s.industry,
        "occupied_regions": s.occupied_regions(),
        "occupied_culture_regions": s.occupied_culture_regions,
        "occupied_industry_regions": s.occupied_industry_regions,
        "invasions_resolved": s.invasions_resolved,
        "deck_left": len(s.deck),
        "discard_size": len(s.discard),
        "built_buildings": sorted(list(s.built_buildings)),
        "monument_progress": dict(s.monument_progress),
        "game_lost": s.game_lost,
    }


def run_one_game_with_trace(engine, policy_fn, seed, policy_name):
    s = engine.new_game(seed=seed)
    trace = []

    while (not s.game_lost) and s.invasions_resolved < 3:
        s.turn_count += 1
        hand = engine.draw_hand(s)
        if not hand:
            break

        legal = engine.legal_actions(s, hand)
        before = snapshot_state(s)
        inv_before = s.invasions_resolved

        action = policy_fn(engine, s, hand, legal)
        engine.apply_action(s, hand, action)
        engine.resolve_invasion_if_needed(s, policy_name=policy_name)

        after = snapshot_state(s)
        inv_after = s.invasions_resolved

        trace.append({
            "turn": s.turn_count,
            "hand": hand,
            "legal_count": len(legal),
            "chosen_action": action,
            "before": before,
            "after": after,
            "invasion_happened": int(inv_after > inv_before),
        })

    final_score = engine.score(s)
    final = snapshot_state(s)
    return final_score, final, trace


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--policy", type=str, default="arc_policy")
    parser.add_argument("--games", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=2000000)
    parser.add_argument("--score-threshold", type=int, default=16)
    parser.add_argument("--max-cases", type=int, default=30)
    args = parser.parse_args()

    if args.policy not in POLICIES:
        raise ValueError(f"未知策略: {args.policy}, 可选: {list(POLICIES.keys())}")

    repo = DataRepo(ROOT / "data")
    engine = RomeEngine(repo, seed=42)
    policy_fn = POLICIES[args.policy]

    # Pass 1: 快速扫分数
    rows = []
    for i in range(args.games):
        seed = args.seed + i
        res = engine.play_game(policy_fn, seed=seed, policy_name=args.policy)
        rows.append({"seed": seed, "score": res["总分"], "lost": res["是否失败"]})

    df = pd.DataFrame(rows)
    max_score = int(df["score"].max())
    top_df = df[df["score"] >= args.score_threshold].sort_values(["score", "seed"], ascending=[False, True])

    if len(top_df) > args.max_cases:
        top_df = top_df.head(args.max_cases)

    out_dir = ROOT / "logs" / "strategy_cases" / args.policy
    out_dir.mkdir(parents=True, exist_ok=True)

    # 保存总览
    summary_path = out_dir / f"summary_{args.policy}_{args.games}games.csv"
    df.to_csv(summary_path, index=False, encoding="utf-8-sig")

    # Pass 2: 导出高分详细轨迹
    case_rows = []
    for _, r in top_df.iterrows():
        seed = int(r["seed"])
        score, final, trace = run_one_game_with_trace(engine, policy_fn, seed, args.policy)

        payload = {
            "policy": args.policy,
            "seed": seed,
            "score": score,
            "final": final,
            "trace": trace,
            # 在 trace.append 里面确保记录了 legal_actions
            "legal_actions": legal
        }

        case_file = out_dir / f"case_score{score}_seed{seed}.json"
        case_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

        case_rows.append({
            "seed": seed,
            "score": score,
            "turns": final["turn"],
            "lost": final["game_lost"],
            "final_regions": final["occupied_regions"],
            "final_culture": final["culture"],
            "final_military": final["military"],
            "final_industry": final["industry"],
            "final_built_count": len(final["built_buildings"]),
            "final_completed_monuments": sum(1 for v in final["monument_progress"].values() if v >= 2),
            "case_file": case_file.name,
        })

    cases_csv = out_dir / f"top_cases_{args.policy}.csv"
    pd.DataFrame(case_rows).to_csv(cases_csv, index=False, encoding="utf-8-sig")

    print("✅ 运行完成")
    print(f"策略: {args.policy}")
    print(f"总局数: {args.games}")
    print(f"最高分: {max_score}")
    print(f"阈值>= {args.score_threshold} 的案例数: {len(case_rows)}")
    print(f"总览: {summary_path}")
    print(f"案例索引: {cases_csv}")
    print(f"案例JSON目录: {out_dir}")


if __name__ == "__main__":
    main()