from pathlib import Path
import json
import pandas as pd
from collections import Counter

ROOT = Path(__file__).resolve().parent.parent
CASE_DIR = ROOT / "logs" / "strategy_cases" / "mcts_policy"

MONU_NAME = {
    "M_WanShenMiao": "万神庙",
    "M_LuoMaDouShouChang": "罗马斗兽场",
    "M_DiGuoGuangChang": "帝国广场",
    "M_HaDeLiangLingQin": "哈德良陵寝",
    "M_KaiXuanMen": "凯旋门",
    "M_TuLaZhenShiChang": "图拉真市场",
}
BUILD_NAME = {
    "B_KaiXuanDiaoSu": "凯旋雕塑",
    "B_DiGuoYinShuiDao": "帝国引水道",
    "B_JunTuanYaoSai": "军团要塞",
    "B_DiGuoJinKuang": "帝国金矿",
    "B_YuanXingJingJiChang": "圆形竞技场",
}

def main():
    files = sorted(CASE_DIR.glob("case_score*_seed*.json"))
    if not files:
        print("未找到 mcts case json")
        return

    rows = []
    monument_combo_counter = Counter()
    building_combo_counter = Counter()

    for fp in files:
        data = json.loads(fp.read_text(encoding="utf-8"))
        final = data.get("final", {})
        trace = data.get("trace", [])

        mono_prog = final.get("monument_progress", {})
        built = sorted(final.get("built_buildings", []))
        score = data.get("score", 0)

        completed_m = sorted([m for m, p in mono_prog.items() if p >= 2])
        m_combo = "+".join(completed_m) if completed_m else "None"
        b_combo = "+".join(built) if built else "None"

        monument_combo_counter[m_combo] += 1
        building_combo_counter[b_combo] += 1

        # 动作计数
        cnt = {"TopResource":0,"Conquest":0,"Tribute":0,"Build_Building":0,"Build_Monument":0}
        for st in trace:
            k = st.get("chosen_action", {}).get("kind")
            if k in cnt:
                cnt[k] += 1

        rows.append({
            "seed": data.get("seed"),
            "score": score,
            "completed_monuments_ids": m_combo,
            "completed_monuments_names": "+".join([MONU_NAME.get(x, x) for x in completed_m]) if completed_m else "无",
            "built_buildings_ids": b_combo,
            "built_buildings_names": "+".join([BUILD_NAME.get(x, x) for x in built]) if built else "无",
            **cnt
        })

    df = pd.DataFrame(rows).sort_values(["score","seed"], ascending=[False,True])

    # 只看高分组
    high = df[df["score"] >= 16].copy()

    combo_m_df = pd.DataFrame(
        [{"monument_combo":k, "count":v} for k,v in monument_combo_counter.items()]
    ).sort_values("count", ascending=False)

    combo_b_df = pd.DataFrame(
        [{"building_combo":k, "count":v} for k,v in building_combo_counter.items()]
    ).sort_values("count", ascending=False)

    out1 = CASE_DIR / "mcts_case_combo_detail.csv"
    out2 = CASE_DIR / "mcts_monument_combo_count.csv"
    out3 = CASE_DIR / "mcts_building_combo_count.csv"
    out4 = CASE_DIR / "mcts_high16_action_mean.csv"

    df.to_csv(out1, index=False, encoding="utf-8-sig")
    combo_m_df.to_csv(out2, index=False, encoding="utf-8-sig")
    combo_b_df.to_csv(out3, index=False, encoding="utf-8-sig")

    if len(high):
        high[["TopResource","Conquest","Tribute","Build_Building","Build_Monument"]].mean().to_frame("mean").to_csv(out4, encoding="utf-8-sig")
    else:
        pd.DataFrame().to_csv(out4, encoding="utf-8-sig")

    print("✅ 完成")
    print(out1)
    print(out2)
    print(out3)
    print(out4)

if __name__ == "__main__":
    main()