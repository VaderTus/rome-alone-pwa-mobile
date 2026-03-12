from pathlib import Path
import json
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
CASE_DIR = ROOT / "logs" / "strategy_cases" / "mcts_policy"

def check_case(data):
    errs = []
    warns = []

    seed = data.get("seed")
    score = data.get("score")
    trace = data.get("trace", [])
    final = data.get("final", {})

    # 基本检查
    if not trace:
        errs.append("trace为空")
        return errs, warns

    # 逐步检查
    last_turn = 0
    for i, step in enumerate(trace):
        turn = step.get("turn")
        before = step.get("before", {})
        after = step.get("after", {})
        a = step.get("chosen_action", {})
        kind = a.get("kind")
        mode = a.get("mode")
        inv_happened = int(step.get("invasion_happened", 0))

        # turn递增
        if turn is None or turn < 1:
            errs.append(f"step#{i}: turn非法")
        if turn < last_turn:
            errs.append(f"step#{i}: turn倒退")
        last_turn = turn

        # 资源范围
        for rk in ["culture", "military", "industry"]:
            bv = before.get(rk)
            av = after.get(rk)
            if bv is None or av is None:
                errs.append(f"step#{i}: 缺少资源字段 {rk}")
                continue
            if not (0 <= bv <= 9):
                errs.append(f"step#{i}: before.{rk}超界 {bv}")
            if not (0 <= av <= 9):
                errs.append(f"step#{i}: after.{rk}超界 {av}")

        # 入侵计数单调，最多+1
        b_inv = before.get("invasions_resolved", before.get("inv", 0))
        a_inv = after.get("invasions_resolved", after.get("inv", 0))
        if a_inv < b_inv:
            errs.append(f"step#{i}: 入侵计数倒退")
        if a_inv - b_inv > 1:
            errs.append(f"step#{i}: 单步入侵增加>1")
        if inv_happened == 1 and a_inv == b_inv:
            warns.append(f"step#{i}: invasion_happened=1 但计数未变")

        # 建筑数量应不下降
        b_built = before.get("built_buildings", [])
        a_built = after.get("built_buildings", [])
        if len(a_built) < len(b_built):
            errs.append(f"step#{i}: 建筑数量下降")

        # 纪念物进度应在0..2且不下降
        b_m = before.get("monument_progress", before.get("mono", {}))
        a_m = after.get("monument_progress", after.get("mono", {}))
        for mid, bv in b_m.items():
            av = a_m.get(mid, bv)
            if bv < 0 or bv > 2 or av < 0 or av > 2:
                errs.append(f"step#{i}: 纪念物进度越界 {mid}: {bv}->{av}")
            if av < bv:
                errs.append(f"step#{i}: 纪念物进度下降 {mid}: {bv}->{av}")

        # 动作与地区变化的弱一致性（告警级别）
        b_regions = before.get("occupied_regions")
        a_regions = after.get("occupied_regions")
        if b_regions is not None and a_regions is not None:
            if kind == "Conquest" and a_regions < b_regions:
                warns.append(f"step#{i}: Conquest后地区未增长（可能同回合入侵导致）")
            if mode == "top" and abs(a_regions - b_regions) > 2:
                warns.append(f"step#{i}: top动作地区变化异常大 {b_regions}->{a_regions}")

    # 终局一致性
    if final:
        f_turn = final.get("turn")
        if f_turn is not None and f_turn != trace[-1].get("turn"):
            warns.append(f"final.turn({f_turn}) 与最后trace.turn({trace[-1].get('turn')})不一致")

    # 分数合理范围（你这版常见0~18）
    if score is None:
        errs.append("缺少score")
    else:
        if score < 0 or score > 30:
            warns.append(f"score异常范围: {score}")

    return errs, warns


def main():
    if not CASE_DIR.exists():
        print(f"未找到目录: {CASE_DIR}")
        print("请先运行 run_policy_trace_top_cases.py 导出 mcts_policy 案例")
        return

    files = sorted(CASE_DIR.glob("case_score*_seed*.json"))
    if not files:
        print("未找到case文件。")
        return

    rows = []
    total_err = 0
    total_warn = 0

    for fp in files:
        data = json.loads(fp.read_text(encoding="utf-8"))
        errs, warns = check_case(data)
        total_err += len(errs)
        total_warn += len(warns)

        rows.append({
            "file": fp.name,
            "seed": data.get("seed"),
            "score": data.get("score"),
            "error_count": len(errs),
            "warn_count": len(warns),
            "errors": " | ".join(errs[:5]),
            "warnings": " | ".join(warns[:5]),
        })

    df = pd.DataFrame(rows).sort_values(["error_count", "warn_count", "score"], ascending=[False, False, False])

    out_csv = CASE_DIR / "mcts_audit_report.csv"
    df.to_csv(out_csv, index=False, encoding="utf-8-sig")

    print("✅ 审计完成")
    print(f"案例数: {len(df)}")
    print(f"总错误: {total_err}, 总警告: {total_warn}")
    print(f"报告: {out_csv}")

    print("\n错误Top10：")
    print(df.head(10).to_string(index=False))


if __name__ == "__main__":
    main()