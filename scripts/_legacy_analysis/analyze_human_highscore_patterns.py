from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
IN_STEPS = ROOT / "logs" / "processed" / "human_all_steps.csv"
OUT_DIR = ROOT / "logs" / "processed"
OUT_DIR.mkdir(parents=True, exist_ok=True)

def main():
    if not IN_STEPS.exists():
        print(f"缺少文件: {IN_STEPS}")
        print("请先运行: python .\\scripts\\merge_all_human_logs.py")
        return

    df = pd.read_csv(IN_STEPS, encoding="utf-8-sig")

    # 会话终局分（取每个session最后一步 after_score）
    last_step = (
        df.sort_values(["session_id", "turn"])
          .groupby("session_id", as_index=False)
          .tail(1)
          .copy()
    )

    # 阈值
    high = set(last_step[last_step["after_score"] >= 14]["session_id"].tolist())
    mid = set(last_step[last_step["after_score"] >= 12]["session_id"].tolist())

    df["is_12_plus_session"] = df["session_id"].isin(mid).astype(int)
    df["is_14_plus_session"] = df["session_id"].isin(high).astype(int)

    # 动作分布（按会话）
    action_dist = (
        df.groupby(["session_id", "action_kind"]).size().unstack(fill_value=0).reset_index()
    )

    # 合并会话分数
    score_map = last_step[["session_id", "after_score"]].rename(columns={"after_score": "final_score"})
    feat = action_dist.merge(score_map, on="session_id", how="left")

    # 归一化动作占比
    action_cols = [c for c in feat.columns if c not in ["session_id", "final_score"]]
    feat["total_actions"] = feat[action_cols].sum(axis=1)
    for c in action_cols:
        feat[f"pct_{c}"] = feat[c] / feat["total_actions"].replace(0, 1)

    # 高分组 vs 普通组比较
    feat["group"] = feat["final_score"].apply(lambda x: "14_plus" if x >= 14 else ("12_13" if x >= 12 else "below_12"))
    cmp = feat.groupby("group")[[c for c in feat.columns if c.startswith("pct_")]].mean().reset_index()

    # 保存
    out1 = OUT_DIR / "human_final_scores.csv"
    out2 = OUT_DIR / "human_action_mix_by_group.csv"

    last_step[["session_id", "after_score"]].rename(columns={"after_score": "final_score"}).to_csv(
        out1, index=False, encoding="utf-8-sig"
    )
    cmp.to_csv(out2, index=False, encoding="utf-8-sig")

    print("✅ 分析完成")
    print(f"终局分列表: {out1}")
    print(f"动作占比对比: {out2}")
    print("\n分组数量：")
    print(feat["group"].value_counts())

if __name__ == "__main__":
    main()