from pathlib import Path
import json
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
HUMAN_DIR = ROOT / "logs" / "human_play"
MOBILE_DIR = ROOT / "logs" / "mobile_import"
OUT_DIR = ROOT / "logs" / "processed"
OUT_DIR.mkdir(parents=True, exist_ok=True)

def flatten_common_record(rec, source_file, source_type, session_id):
    b = rec.get("before", {})
    a = rec.get("after", {})
    ch = rec.get("chosen_action", {})
    return {
        "source_type": source_type,                 # python_ui / mobile_pwa
        "source_file": source_file,
        "session_id": session_id,
        "turn": rec.get("turn"),
        "timestamp": rec.get("timestamp"),
        "before_culture": b.get("culture"),
        "before_military": b.get("military"),
        "before_industry": b.get("industry"),
        "before_regions": b.get("occupied_regions"),
        "before_invasions": b.get("invasions_resolved") if "invasions_resolved" in b else b.get("inv"),
        "deck_left_before": b.get("deck_left"),
        "action_card": ch.get("card_id"),
        "action_mode": ch.get("mode"),
        "action_kind": ch.get("kind"),
        "action_meta": str(ch.get("meta", {})),
        "after_culture": a.get("culture"),
        "after_military": a.get("military"),
        "after_industry": a.get("industry"),
        "after_regions": a.get("occupied_regions"),
        "after_invasions": a.get("invasions_resolved") if "invasions_resolved" in a else a.get("inv"),
        "after_score": rec.get("after_score"),
    }

def ingest_python_ui_jsonl():
    rows = []
    sessions = []

    files = sorted(HUMAN_DIR.glob("human_trace_*.jsonl"))
    for fp in files:
        session_id = fp.stem
        count = 0
        with open(fp, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                rows.append(flatten_common_record(rec, fp.name, "python_ui", session_id))
                count += 1
        sessions.append({
            "source_type": "python_ui",
            "source_file": fp.name,
            "session_id": session_id,
            "records_count": count
        })
    return rows, sessions

def ingest_mobile_json():
    rows = []
    sessions = []

    files = sorted(MOBILE_DIR.glob("mobile_trace_*.json"))
    for fp in files:
        data = json.loads(fp.read_text(encoding="utf-8"))
        session_id = data.get("session_id", fp.stem)
        recs = data.get("records", [])

        sessions.append({
            "source_type": "mobile_pwa",
            "source_file": fp.name,
            "session_id": session_id,
            "created_at": data.get("created_at"),
            "final_score": data.get("final_summary", {}).get("score"),
            "lost": data.get("final_summary", {}).get("lost"),
            "turns": data.get("final_summary", {}).get("turns"),
            "invasions_resolved": data.get("final_summary", {}).get("invasions_resolved"),
            "records_count": len(recs),
        })

        for rec in recs:
            rows.append(flatten_common_record(rec, fp.name, "mobile_pwa", session_id))

    return rows, sessions

def main():
    all_rows = []
    all_sessions = []

    if HUMAN_DIR.exists():
        r, s = ingest_python_ui_jsonl()
        all_rows.extend(r)
        all_sessions.extend(s)

    if MOBILE_DIR.exists():
        r, s = ingest_mobile_json()
        all_rows.extend(r)
        all_sessions.extend(s)

    if not all_rows:
        print("未找到可整合日志。请先在以下目录放日志：")
        print(f"  - {HUMAN_DIR}")
        print(f"  - {MOBILE_DIR}")
        return

    df_steps = pd.DataFrame(all_rows).sort_values(["session_id", "turn"]).reset_index(drop=True)
    df_sessions = pd.DataFrame(all_sessions)

    steps_path = OUT_DIR / "human_all_steps.csv"
    sessions_path = OUT_DIR / "human_all_sessions.csv"

    df_steps.to_csv(steps_path, index=False, encoding="utf-8-sig")
    df_sessions.to_csv(sessions_path, index=False, encoding="utf-8-sig")

    print("✅ 合并完成")
    print(f"步骤级数据: {steps_path}")
    print(f"局级数据: {sessions_path}")
    print(f"总会话数: {df_steps['session_id'].nunique()}")
    print(f"总步骤数: {len(df_steps)}")

if __name__ == "__main__":
    main()