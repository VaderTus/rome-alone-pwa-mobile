from pathlib import Path
import json
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
CASE_DIR = ROOT / "logs" / "strategy_cases" / "arc_policy_v3_highroll"

MID_ARC = "M_KaiXuanMen"
MID_SENATE = "M_DiGuoGuangChang"

KEY_CARD_IDS = {
    "帝国广场1": "C14",
    "帝国广场2": "C15",
    "凯旋门1": "C18",
    "凯旋门2": "C19",
    "军团要塞": "C03",
    "圆形竞技场": "C05",
    "帝国金矿": "C04",
    "凯旋雕塑": "C01",
    "帝国引水道": "C02",
}

BUILDING_IDS = [
    "B_JunTuanYaoSai",
    "B_YuanXingJingJiChang",
    "B_DiGuoJinKuang",
    "B_KaiXuanDiaoSu",
    "B_DiGuoYinShuiDao",
]

def first_seen_turn(trace, card_id):
    for step in trace:
        if card_id in step.get("hand", []):
            return step.get("turn")
    return None

def first_complete_turn(trace, monument_id):
    for step in trace:
        b = step["before"]["monument_progress"].get(monument_id, 0)
        a = step["after"]["monument_progress"].get(monument_id, 0)
        if b < 2 and a >= 2:
            return step["turn"]
    return None

def conquest_before_inv(trace, inv_idx=1):
    c = 0
    for step in trace:
        if step["before"]["invasions_resolved"] >= inv_idx:
            break
        if step.get("chosen_action", {}).get("kind") == "Conquest":
            c += 1
    return c

def state_before_inv(trace, inv_idx=1):
    for step in trace:
        if step.get("invasion_happened", 0) == 1 and step["before"]["invasions_resolved"] == (inv_idx - 1):
            return step["before"]
    return trace[-1]["before"] if trace else {}

def build_turns(trace):
    out = {}
    for step in trace:
        a = step.get("chosen_action", {})
        if a.get("kind") == "Build_Building":
            bid = a.get("meta", {}).get("building_id")
            if bid and bid not in out:
                out[bid] = step.get("turn")
    return out

def summarize_buildings(df):
    rows = []
    for bid in BUILDING_IDS:
        col = f"build_turn_{bid}"
        mask = df[col].notna()
        rows.append({
            "building_id": bid,
            "build_rate_percent": round(mask.mean() * 100, 2),
            "avg_build_turn_if_built": round(df.loc[mask, col].mean(), 2) if mask.any() else None
        })
    return pd.DataFrame(rows)

def summarize_seen(df):
    rows = []
    cols = [c for c in df.columns if c.startswith("seen_turn_")]
    for c in cols:
        s = df[c].dropna()
        rows.append({
            "key_card": c.replace("seen_turn_", ""),
            "seen_rate_percent": round(len(s) / len(df) * 100, 2) if len(df) else 0.0,
            "avg_first_seen_turn": round(s.mean(), 2) if len(s) else None,
            "median_first_seen_turn": round(s.median(), 2) if len(s) else None,
        })
    return pd.DataFrame(rows)

def main():
    if not CASE_DIR.exists():
        print(f"未找到目录: {CASE_DIR}")
        print("请先运行：")
        print(r"python .\scripts\run_policy_trace_top_cases.py --policy arc_policy_v3_highroll --games 10000 --seed 9000000 --score-threshold 16 --max-cases 100")
        return

    files = sorted(CASE_DIR.glob("case_score*_seed*.json"))
    if not files:
        print("未找到 case JSON。请先跑 trace 抽取脚本。")
        return

    rows = []
    for fp in files:
        data = json.loads(fp.read_text(encoding="utf-8"))
        trace = data.get("trace", [])
        final = data.get("final", {})

        bturns = build_turns(trace)
        pre1 = state_before_inv(trace, 1)
        pre2 = state_before_inv(trace, 2)

        row = {
            "seed": data.get("seed"),
            "score": data.get("score"),
            "turns": final.get("turn"),
            "turn_complete_arc": first_complete_turn(trace, MID_ARC),
            "turn_complete_senate": first_complete_turn(trace, MID_SENATE),
            "conquest_before_inv1": conquest_before_inv(trace, 1),
            "conquest_before_inv2": conquest_before_inv(trace, 2),
            "pre_inv1_culture": pre1.get("culture"),
            "pre_inv1_military": pre1.get("military"),
            "pre_inv1_industry": pre1.get("industry"),
            "pre_inv1_regions": pre1.get("occupied_regions"),
            "pre_inv2_culture": pre2.get("culture"),
            "pre_inv2_military": pre2.get("military"),
            "pre_inv2_industry": pre2.get("industry"),
            "pre_inv2_regions": pre2.get("occupied_regions"),
            "final_regions": final.get("occupied_regions"),
            "final_built_count": len(final.get("built_buildings", [])),
            "final_completed_monuments": sum(1 for v in final.get("monument_progress", {}).values() if v >= 2),
            "file": fp.name
        }

        for bid in BUILDING_IDS:
            row[f"build_turn_{bid}"] = bturns.get(bid)

        for name, cid in KEY_CARD_IDS.items():
            row[f"seen_turn_{name}"] = first_seen_turn(trace, cid)

        rows.append(row)

    df = pd.DataFrame(rows).sort_values(["score", "seed"], ascending=[False, True])

    out_case = CASE_DIR / "arc_v3_highroll_top_cases_features.csv"
    out_build = CASE_DIR / "arc_v3_highroll_building_summary.csv"
    out_seen = CASE_DIR / "arc_v3_highroll_key_seen_summary.csv"
    out_mean = CASE_DIR / "arc_v3_highroll_feature_mean.csv"

    df.to_csv(out_case, index=False, encoding="utf-8-sig")
    summarize_buildings(df).to_csv(out_build, index=False, encoding="utf-8-sig")
    summarize_seen(df).to_csv(out_seen, index=False, encoding="utf-8-sig")

    mean_cols = [
        "score","turns","turn_complete_arc","turn_complete_senate",
        "conquest_before_inv1","conquest_before_inv2",
        "pre_inv1_culture","pre_inv1_military","pre_inv1_industry","pre_inv1_regions",
        "pre_inv2_culture","pre_inv2_military","pre_inv2_industry","pre_inv2_regions",
        "final_regions","final_built_count","final_completed_monuments"
    ]
    pd.DataFrame([df[mean_cols].mean(numeric_only=True)]).round(3).to_csv(out_mean, index=False, encoding="utf-8-sig")

    print("✅ 分析完成")
    print(f"案例特征: {out_case}")
    print(f"建筑汇总: {out_build}")
    print(f"首见汇总: {out_seen}")
    print(f"均值汇总: {out_mean}")

if __name__ == "__main__":
    main()