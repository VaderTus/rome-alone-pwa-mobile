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
    parser = argparse.ArgumentParser()
    parser.add_argument("--policy", type=str, default="pantheon_policy")
    parser.add_argument("--games", type=int, default=300)
    parser.add_argument("--seed", type=int, default=1200000)
    parser.add_argument("--topn", type=int, default=10)
    args = parser.parse_args()

    if args.policy not in POLICIES:
        raise ValueError(f"未知策略: {args.policy}, 可选: {list(POLICIES.keys())}")

    repo = DataRepo(ROOT / "data")
    engine = RomeEngine(repo, seed=42)
    policy_fn = POLICIES[args.policy]

    rows = []
    for i in range(args.games):
        seed = args.seed + i
        r = engine.play_game(policy_fn, seed=seed, policy_name=args.policy)
        r["seed"] = seed
        r["达到12+"] = int(r["总分"] >= 12)
        r["达到14+"] = int(r["总分"] >= 14)
        rows.append(r)

    df = pd.DataFrame(rows)
    fail_rate = float(df["是否失败"].mean())
    alive = df.loc[~df["是否失败"]]
    alive_avg = float(alive["总分"].mean()) if len(alive) > 0 else 0.0

    summary = {
        "策略": args.policy,
        "局数": args.games,
        "平均分": round(float(df["总分"].mean()), 3),
        "存活局平均分": round(alive_avg, 3),
        "中位分": round(float(df["总分"].median()), 3),
        "最低分": int(df["总分"].min()),
        "最高分": int(df["总分"].max()),
        "失败率": f"{fail_rate*100:.2f}%",
        "12+率": f"{df['达到12+'].mean()*100:.2f}%",
        "14+率": f"{df['达到14+'].mean()*100:.2f}%",
    }

    top_cases = df.sort_values(["总分", "seed"], ascending=[False, True]).head(args.topn)

    out_dir = ROOT / "outputs"
    out_dir.mkdir(exist_ok=True)

    summary_path = out_dir / f"single_{args.policy}_summary.csv"
    detail_path = out_dir / f"single_{args.policy}_detail.csv"
    top_path = out_dir / f"single_{args.policy}_top{args.topn}.csv"

    pd.DataFrame([summary]).to_csv(summary_path, index=False, encoding="utf-8-sig")
    df.to_csv(detail_path, index=False, encoding="utf-8-sig")
    top_cases.to_csv(top_path, index=False, encoding="utf-8-sig")

    print("\n========== 单策略结果 ==========")
    print(pd.DataFrame([summary]).to_string(index=False))
    print("\nTop seeds:")
    print(top_cases[["seed", "总分", "是否失败"]].to_string(index=False))
    print(f"\n已导出到: {out_dir}")


if __name__ == "__main__":
    main()