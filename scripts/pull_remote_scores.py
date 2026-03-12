import os
import json
from pathlib import Path
from urllib import request, parse
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "logs" / "processed"
OUT_DIR.mkdir(parents=True, exist_ok=True)

CONFIG_FILE = ROOT / "config" / "supabase.local.json"


def load_config():
    # 1) 先读环境变量
    url = os.getenv("SUPABASE_URL", "").strip()
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip() or os.getenv("SUPABASE_KEY", "").strip()
    table = os.getenv("SUPABASE_TABLE", "rome_highscores").strip()

    # 2) 如果环境变量不全，读本地配置
    if (not url or not key) and CONFIG_FILE.exists():
        cfg = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        url = url or cfg.get("SUPABASE_URL", "").strip()
        key = key or cfg.get("SUPABASE_KEY", "").strip()
        table = table or cfg.get("SUPABASE_TABLE", "rome_highscores").strip()

    return url, key, table


def main():
    supabase_url, supabase_key, table = load_config()

    if not supabase_url or not supabase_key:
        print("❌ 缺少 Supabase 配置。")
        print("可选方式：")
        print("1) 设置环境变量 SUPABASE_URL + SUPABASE_SERVICE_ROLE_KEY(或SUPABASE_KEY)")
        print(f"2) 创建配置文件 {CONFIG_FILE}")
        return

    q = parse.urlencode({
        "select": "id,created_at,session_id,final_score,lost,turns,source,app_version,payload",
        "order": "created_at.desc",
        "limit": "5000"
    })
    url = f"{supabase_url}/rest/v1/{table}?{q}"

    req = request.Request(url, method="GET")
    req.add_header("apikey", supabase_key)
    req.add_header("Authorization", f"Bearer {supabase_key}")

    with request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    df = pd.DataFrame(data)
    out = OUT_DIR / "remote_highscores.csv"
    df.to_csv(out, index=False, encoding="utf-8-sig")
    print(f"✅ 已拉取 {len(df)} 条 -> {out}")


if __name__ == "__main__":
    main()