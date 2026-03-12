from pathlib import Path
import json
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
CASE_DIR = ROOT / "logs" / "strategy_cases" / "arc_policy"

MID_ARC = "M_KaiXuanMen"
MID_SENATE = "M_DiGuoGuangChang"

def first_turn_monument_completed(trace, monument_id):
    for step in trace:
        before = step["before"]["monument_progress"].get(monument_id, 0)
        after = step["after"]["monument_progress"].get(monument_id, 0)
        if before < 2 and after >= 2:
            return step["turn"]
    return None

def count_conquest_before_inv1(trace):
    c = 0
    for step in trace:
        if step["before"]["invasions_resolved"] >= 1:
            break
        a = step["chosen_action"]
        if a.get("kind") == "Conquest":
            c += 1
    return c

def state_before_first_invasion(trace):
    # 找到第一次入侵发生回合（invasion_happened=1且 before.inv==0）
    for step in trace:
        if step.get("invasion_happened", 0) == 1 and step["before"]["invasions_resolved"] == 0:
            return step["before"]
    # 如果没发生（极端），返回最后一步before
    return trace[-1]["before"] if trace else None

def main():
    if not CASE_DIR.exists():
        print(f"未找到目录: {CASE_DIR}")
        print("请先运行 run_policy_trace_top_cases.py")
        return

    files = sorted(CASE_DIR.glob("case_score*_seed*.json"))
    if not files:
        print("未找到案例 JSON。")
        return

    rows = []
    for fp in files:
        data = json.loads(fp.read_text(encoding="utf-8"))
        trace = data.get("trace", [])
        final = data.get("final", {})

        t_arc = first_turn_monument_completed(trace, MID_ARC)
        t_senate = first_turn_monument_completed(trace, MID_SENATE)
        conquest_b1 = count_conquest_before_inv1(trace)
        pre1 = state_before_first_invasion(trace) or {}

        rows.append({
            "seed": data.get("seed"),
            "score": data.get("score"),
            "turns": final.get("turn"),
            "turn_complete_arc": t_arc,
            "turn_complete_senate": t_senate,
            "conquest_before_inv1": conquest_b1,
            "pre_inv1_culture": pre1.get("culture"),
            "pre_inv1_military": pre1.get("military"),
            "pre_inv1_industry": pre1.get("industry"),
            "pre_inv1_regions": pre1.get("occupied_regions"),
            "final_regions": final.get("occupied_regions"),
            "final_built_count": len(final.get("built_buildings", [])),
            "final_completed_monuments": sum(1 for v in final.get("monument_progress", {}).values() if v >= 2),
            "file": fp.name
        })

    df = pd.DataFrame(rows).sort_values(["score", "seed"], ascending=[False, True])

    out_csv = CASE_DIR / "arc_top_case_features.csv"
    out_mean = CASE_DIR / "arc_top_case_feature_mean.csv"

    df.to_csv(out_csv, index=False, encoding="utf-8-sig")

    # 均值总结
    numeric_cols = [
        "score","turns","turn_complete_arc","turn_complete_senate",
        "conquest_before_inv1",
        "pre_inv1_culture","pre_inv1_military","pre_inv1_industry","pre_inv1_regions",
        "final_regions","final_built_count","final_completed_monuments"
    ]
    mean_df = pd.DataFrame([df[numeric_cols].mean(numeric_only=True)]).round(3)
    mean_df.to_csv(out_mean, index=False, encoding="utf-8-sig")

    print("✅ 分析完成")
    print(f"案例特征表: {out_csv}")
    print(f"均值汇总: {out_mean}")
    print("\nTop案例预览：")
    print(df.head(10).to_string(index=False))


if __name__ == "__main__":
    main()