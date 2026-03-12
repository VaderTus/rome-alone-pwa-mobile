from pathlib import Path
import json
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
CASE_DIR = ROOT / "logs" / "strategy_cases" / "arc_policy"

# 关键牌（可按你理解继续补充）
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

def safe_get_meta(chosen_action):
    return chosen_action.get("meta", {}) if isinstance(chosen_action, dict) else {}

def first_seen_turn(trace, card_id):
    """卡牌首次出现在手牌的回合"""
    for step in trace:
        hand = step.get("hand", [])
        if card_id in hand:
            return step.get("turn")
    return None

def parse_case(fp: Path):
    data = json.loads(fp.read_text(encoding="utf-8"))
    seed = data.get("seed")
    score = data.get("score")
    final = data.get("final", {})
    trace = data.get("trace", [])

    # 开局前2回合（最多6张可见牌）
    opening_cards = []
    for step in trace[:2]:
        opening_cards.extend(step.get("hand", []))

    # 建筑建造回合
    built_turns = {}
    for step in trace:
        a = step.get("chosen_action", {})
        if a.get("kind") == "Build_Building":
            bid = safe_get_meta(a).get("building_id")
            if bid and bid not in built_turns:
                built_turns[bid] = step.get("turn")

    # 关键牌首见回合
    key_seen = {name: first_seen_turn(trace, cid) for name, cid in KEY_CARD_IDS.items()}

    row = {
        "seed": seed,
        "score": score,
        "turns": final.get("turn"),
        "final_regions": final.get("occupied_regions"),
        "final_built_count": len(final.get("built_buildings", [])),
        "final_built_list": "|".join(final.get("built_buildings", [])),
        "opening_cards": "|".join(opening_cards),
    }

    # 建筑建造时机字段（固定你当前5建筑）
    for bid in ["B_JunTuanYaoSai", "B_YuanXingJingJiChang", "B_DiGuoJinKuang", "B_KaiXuanDiaoSu", "B_DiGuoYinShuiDao"]:
        row[f"build_turn_{bid}"] = built_turns.get(bid)

    # 关键牌首见时机
    for k, v in key_seen.items():
        row[f"seen_turn_{k}"] = v

    return row, built_turns

def summarize_buildings(df):
    """统计高分局里建筑出现率与平均建造回合"""
    out = []
    building_ids = [
        "B_JunTuanYaoSai",
        "B_YuanXingJingJiChang",
        "B_DiGuoJinKuang",
        "B_KaiXuanDiaoSu",
        "B_DiGuoYinShuiDao",
    ]
    for bid in building_ids:
        col = f"build_turn_{bid}"
        built_mask = df[col].notna()
        rate = built_mask.mean() * 100
        avg_turn = df.loc[built_mask, col].mean() if built_mask.any() else None
        out.append({
            "building_id": bid,
            "build_rate_percent": round(rate, 2),
            "avg_build_turn_if_built": round(avg_turn, 2) if avg_turn is not None else None
        })
    return pd.DataFrame(out)

def summarize_key_seen(df):
    """关键牌首见回合统计"""
    rows = []
    seen_cols = [c for c in df.columns if c.startswith("seen_turn_")]
    for c in seen_cols:
        seen = df[c].dropna()
        rows.append({
            "key_card": c.replace("seen_turn_", ""),
            "seen_rate_percent": round(len(seen) / len(df) * 100, 2) if len(df) else 0.0,
            "avg_first_seen_turn": round(seen.mean(), 2) if len(seen) else None,
            "median_first_seen_turn": round(seen.median(), 2) if len(seen) else None,
        })
    return pd.DataFrame(rows)

def main():
    if not CASE_DIR.exists():
        print(f"未找到目录: {CASE_DIR}")
        print("请先跑: run_policy_trace_top_cases.py")
        return

    files = sorted(CASE_DIR.glob("case_score*_seed*.json"))
    if not files:
        print("未找到 case JSON 文件。")
        return

    case_rows = []
    for fp in files:
        row, _ = parse_case(fp)
        case_rows.append(row)

    df = pd.DataFrame(case_rows).sort_values(["score", "seed"], ascending=[False, True])

    # 导出1：逐局明细（你可以逐个看）
    out_case = CASE_DIR / "arc_top_cases_opening_buildings.csv"
    df.to_csv(out_case, index=False, encoding="utf-8-sig")

    # 导出2：建筑汇总
    bsum = summarize_buildings(df)
    out_b = CASE_DIR / "arc_top_building_summary.csv"
    bsum.to_csv(out_b, index=False, encoding="utf-8-sig")

    # 导出3：关键牌首见汇总
    ksum = summarize_key_seen(df)
    out_k = CASE_DIR / "arc_top_key_seen_summary.csv"
    ksum.to_csv(out_k, index=False, encoding="utf-8-sig")

    print("✅ 分析完成")
    print(f"逐局开局+建筑明细: {out_case}")
    print(f"建筑汇总: {out_b}")
    print(f"关键牌首见汇总: {out_k}")
    print("\n建筑汇总预览：")
    print(bsum.to_string(index=False))
    print("\n关键牌首见预览：")
    print(ksum.to_string(index=False))

if __name__ == "__main__":
    main()