from pathlib import Path
import json
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
CASE_DIR = ROOT / "logs" / "strategy_cases" / "mcts_policy"

MID_ARC = "M_KaiXuanMen"
MID_SENATE = "M_DiGuoGuangChang"
MID_PANTHEON = "M_WanShenMiao"

def first_complete_turn(trace, mid):
    for step in trace:
        b = step["before"]["monument_progress"].get(mid, 0)
        a = step["after"]["monument_progress"].get(mid, 0)
        if b < 2 <= a:
            return step["turn"]
    return None

def action_counts(trace):
    d = {"TopResource":0, "Conquest":0, "Tribute":0, "Build_Building":0, "Build_Monument":0}
    for step in trace:
        k = step.get("chosen_action", {}).get("kind", "")
        if k in d:
            d[k] += 1
    return d

def before_inv_state(trace, inv_idx=1):
    # 找第一次发生 inv_idx 的前状态
    for step in trace:
        b_inv = step["before"].get("invasions_resolved", step["before"].get("inv", 0))
        a_inv = step["after"].get("invasions_resolved", step["after"].get("inv", 0))
        if b_inv == inv_idx-1 and a_inv == inv_idx:
            return step["before"]
    return trace[-1]["before"] if trace else {}

def main():
    if not CASE_DIR.exists():
        print(f"未找到目录: {CASE_DIR}")
        return

    files = sorted(CASE_DIR.glob("case_score*_seed*.json"))
    if not files:
        print("未找到case JSON。")
        return

    rows = []
    for fp in files:
        data = json.loads(fp.read_text(encoding="utf-8"))
        trace = data.get("trace", [])
        final = data.get("final", {})
        score = data.get("score", 0)

        ac = action_counts(trace)
        total_actions = sum(ac.values()) if sum(ac.values()) > 0 else 1

        pre1 = before_inv_state(trace, 1)
        pre2 = before_inv_state(trace, 2)

        row = {
            "seed": data.get("seed"),
            "score": score,
            "turns": final.get("turn"),
            "final_regions": final.get("occupied_regions"),
            "final_built_count": len(final.get("built_buildings", [])),
            "final_completed_monuments": sum(1 for v in final.get("monument_progress", {}).values() if v >= 2),

            "turn_complete_arc": first_complete_turn(trace, MID_ARC),
            "turn_complete_senate": first_complete_turn(trace, MID_SENATE),
            "turn_complete_pantheon": first_complete_turn(trace, MID_PANTHEON),

            "cnt_top": ac["TopResource"],
            "cnt_conquest": ac["Conquest"],
            "cnt_tribute": ac["Tribute"],
            "cnt_building": ac["Build_Building"],
            "cnt_monument": ac["Build_Monument"],

            "pct_top": ac["TopResource"]/total_actions,
            "pct_conquest": ac["Conquest"]/total_actions,
            "pct_tribute": ac["Tribute"]/total_actions,
            "pct_building": ac["Build_Building"]/total_actions,
            "pct_monument": ac["Build_Monument"]/total_actions,

            "pre_inv1_culture": pre1.get("culture"),
            "pre_inv1_military": pre1.get("military"),
            "pre_inv1_industry": pre1.get("industry"),
            "pre_inv1_regions": pre1.get("occupied_regions"),

            "pre_inv2_culture": pre2.get("culture"),
            "pre_inv2_military": pre2.get("military"),
            "pre_inv2_industry": pre2.get("industry"),
            "pre_inv2_regions": pre2.get("occupied_regions"),
        }
        rows.append(row)

    df = pd.DataFrame(rows)

    # 分组：16+ / 14-15 / <=13
    def grp(x):
        if x >= 16: return "16_plus"
        if x >= 14: return "14_15"
        return "le_13"
    df["score_group"] = df["score"].apply(grp)

    group_mean = (
        df.groupby("score_group")
          .mean(numeric_only=True)
          .reset_index()
          .round(3)
    )

    out_case = CASE_DIR / "mcts_behavior_cases.csv"
    out_group = CASE_DIR / "mcts_behavior_group_mean.csv"

    df.to_csv(out_case, index=False, encoding="utf-8-sig")
    group_mean.to_csv(out_group, index=False, encoding="utf-8-sig")

    print("✅ 画像完成")
    print(f"逐局画像: {out_case}")
    print(f"分组均值: {out_group}")
    print("\n分组数量：")
    print(df["score_group"].value_counts())
    print("\n分组均值预览：")
    print(group_mean.to_string(index=False))


if __name__ == "__main__":
    main()