# scripts/find_mcts_distilled_mismatch.py
from pathlib import Path
import argparse
import importlib
import pandas as pd

from core.loader import DataRepo
from core.engine import RomeEngine


def load_policy_fn(policy_name: str):
    """
    兼容两种项目写法：
    1) policies/registry.py 提供 get_policy / get_policy_fn
    2) 直接 policies/{policy_name}.py 里有 select_action
    """
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


def run_one(policy_fn, policy_name, seed):
    repo = DataRepo(Path("data"))
    engine = RomeEngine(repo, seed=seed)
    return engine.play_game(policy_fn, seed=seed, policy_name=policy_name)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--games", type=int, default=300)
    parser.add_argument("--seed-start", type=int, default=9900000)
    parser.add_argument("--policy-a", type=str, default="mcts_policy")
    parser.add_argument("--policy-b", type=str, default="mcts_distilled_final")
    parser.add_argument("--diff-threshold", type=int, default=4)
    args = parser.parse_args()

    print("正在进行双策略同场竞技分析...")

    fn_a = load_policy_fn(args.policy_a)
    fn_b = load_policy_fn(args.policy_b)

    rows = []
    for i in range(args.games):
        seed = args.seed_start + i
        ra = run_one(fn_a, args.policy_a, seed)
        rb = run_one(fn_b, args.policy_b, seed)

        rows.append({
            "seed": seed,
            f"score_{args.policy_a}": int(ra["总分"]),
            f"score_{args.policy_b}": int(rb["总分"]),
            f"lost_{args.policy_a}": bool(ra["是否失败"]),
            f"lost_{args.policy_b}": bool(rb["是否失败"]),
            "diff": int(ra["总分"]) - int(rb["总分"])
        })

    df = pd.DataFrame(rows)

    avg_a = df[f"score_{args.policy_a}"].mean()
    avg_b = df[f"score_{args.policy_b}"].mean()

    big = df[df["diff"] >= args.diff_threshold].sort_values("diff", ascending=False)

    print("\n=== 策略差异分析报告 ===")
    print(f"平均分 - {args.policy_a}: {avg_a:.2f}, {args.policy_b}: {avg_b:.2f}")
    print(f"发现 {len(big)} 个重大差异样本(差距>={args.diff_threshold}分)")

    show_cols = ["seed", f"score_{args.policy_a}", f"score_{args.policy_b}", "diff"]
    if len(big) > 0:
        print(big[show_cols].head(10).to_string(index=False))
    else:
        print("无重大差异样本。")

    out_dir = Path("outputs")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_all = out_dir / f"mismatch_{args.policy_a}_vs_{args.policy_b}_all.csv"
    out_big = out_dir / f"mismatch_{args.policy_a}_vs_{args.policy_b}_big.csv"
    df.to_csv(out_all, index=False, encoding="utf-8-sig")
    big.to_csv(out_big, index=False, encoding="utf-8-sig")

    print(f"\n已导出:\n- {out_all}\n- {out_big}")


if __name__ == "__main__":
    main()