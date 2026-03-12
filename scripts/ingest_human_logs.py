from pathlib import Path
import json
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
IN_DIR = ROOT / "logs" / "mobile_import"
OUT_DIR = ROOT / "logs" / "processed"
OUT_DIR.mkdir(parents=True, exist_ok=True)

def flatten_record(rec, source_file, session_id):
    b = rec.get("before", {})
    a = rec.get("after", {})
    ch = rec.get("chosen_action", {})
    return {
        "source_file": source_file,
        "session_id": session_id,
        "turn": rec.get("turn"),
        "timestamp": rec.get("timestamp"),
        "before_culture": b.get("culture"),
        "before_military": b.get("military"),
        "before_industry": b.get("industry"),
        "before_regions": b.get("occupied_regions"),
        "before_invasions": b.get("invasions_resolved"),
        "deck_left_before": b.get("deck_left"),
        "action_card": ch.get("card_id"),
        "action_mode": ch.get("mode"),
        "action_kind": ch.get("kind"),
        "action_meta": str(ch.get("meta", {})),
        "after_culture": a.get("culture"),
        "after_military": a.get("military"),
        "after_industry": a.get("industry"),
        "after_regions": a.get("occupied_regions"),
        "after_invasions": a.get("invasions_resolved"),
        "after_score": rec.get("after_score"),
    }

def main():
    IN_DIR.mkdir(parents=True, exist_ok=True)
    files = sorted(IN_DIR.glob("mobile_trace_*.json"))
    if not files:
        print(f"未找到手机日志文件，请把JSON放到: {IN_DIR}")
        return

    rows = []
    sessions = []

    for fp in files:
        data = json.loads(fp.read_text(encoding="utf-8"))
        sid = data.get("session_id", fp.stem)
        sessions.append({
            "source_file": fp.name,
            "session_id": sid,
            "source": data.get("source"),
            "app_version": data.get("app_version"),
            "created_at": data.get("created_at"),
            "final_score": data.get("final_summary", {}).get("score"),
            "lost": data.get("final_summary", {}).get("lost"),
            "turns": data.get("final_summary", {}).get("turns"),
            "invasions_resolved": data.get("final_summary", {}).get("invasions_resolved"),
            "records_count": len(data.get("records", [])),
        })
        for r in data.get("records", []):
            rows.append(flatten_record(r, fp.name, sid))

    df_steps = pd.DataFrame(rows)
    df_sessions = pd.DataFrame(sessions)

    steps_path = OUT_DIR / "mobile_dataset_steps.csv"
    sess_path = OUT_DIR / "mobile_dataset_sessions.csv"

    df_steps.to_csv(steps_path, index=False, encoding="utf-8-sig")
    df_sessions.to_csv(sess_path, index=False, encoding="utf-8-sig")

    print("✅ 导入完成")
    print(f"步骤数据: {steps_path}")
    print(f"局级数据: {sess_path}")
    print(f"会话数: {len(df_sessions)}, 步骤数: {len(df_steps)}")

if __name__ == "__main__":
    main()