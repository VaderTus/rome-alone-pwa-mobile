from pathlib import Path
import shutil
import argparse

TARGET_DIRS = [
    "data",
    "core",
    "policies",
    "experiments",
    "ui",
    "scripts",
    "docs",
    "outputs",
    "logs",
    "logs/human_play",
    "logs/mobile_import",
    "logs/processed",
    "pwa-mobile",
]

INIT_FILES = [
    "core/__init__.py",
    "policies/__init__.py",
    "experiments/__init__.py",
    "ui/__init__.py",
]

# 如果你之前有这些文件，会自动迁移到统一位置（仅当目标不存在时）
MOVE_MAP = [
    ("run_single_strategy.py", "experiments/run_single_strategy.py"),
    ("control_center.py", "ui/control_center.py"),
    ("cli_panel.py", "ui/cli_panel.py"),
    ("web_human_play.py", "ui/web_human_play.py"),
    ("ingest_human_logs.py", "scripts/ingest_human_logs.py"),
]

PWA_PLACEHOLDERS = {
    "pwa-mobile/index.html": """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Rome Alone Mobile</title>
  <link rel="manifest" href="./manifest.json">
  <link rel="stylesheet" href="./styles.css">
</head>
<body>
  <h1>Rome Alone Mobile (PWA)</h1>
  <p>占位版本：后续将接入完整离线游玩逻辑。</p>
  <script src="./app.js"></script>
</body>
</html>
""",
    "pwa-mobile/app.js": """console.log("PWA placeholder loaded.");""",
    "pwa-mobile/styles.css": """body { font-family: sans-serif; padding: 16px; }""",
    "pwa-mobile/manifest.json": """{
  "name": "Rome Alone Mobile",
  "short_name": "RomeAlone",
  "start_url": "./index.html",
  "display": "standalone",
  "background_color": "#ffffff",
  "theme_color": "#222222",
  "icons": []
}""",
    "pwa-mobile/sw.js": """self.addEventListener('install', () => self.skipWaiting());""",
    "docs/PROJECT_STRUCTURE.md": """# 项目结构说明

- core/            纯规则引擎
- policies/        策略模块（可单独迭代）
- experiments/     批量实验脚本
- ui/              交互界面（CLI/网页）
- pwa-mobile/      移动端离线PWA子项目
- logs/            人类与模拟日志
"""
}


def safe_move(src: Path, dst: Path, dry_run=True):
    if not src.exists():
        return
    if dst.exists():
        print(f"[SKIP] 目标已存在，不覆盖: {dst}")
        return
    print(f"[MOVE] {src} -> {dst}")
    if not dry_run:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))


def ensure_dir(p: Path, dry_run=True):
    if p.exists():
        return
    print(f"[MKDIR] {p}")
    if not dry_run:
        p.mkdir(parents=True, exist_ok=True)


def ensure_file(p: Path, content: str = "", dry_run=True):
    if p.exists():
        return
    print(f"[CREATE] {p}")
    if not dry_run:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8-sig")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="真正执行；默认仅预览(dry-run)")
    args = parser.parse_args()

    dry_run = not args.apply
    root = Path(__file__).resolve().parent.parent

    print(f"项目根目录: {root}")
    print("模式:", "DRY-RUN(预览)" if dry_run else "APPLY(执行)")
    print("-" * 60)

    # 1) 创建目录
    for d in TARGET_DIRS:
        ensure_dir(root / d, dry_run=dry_run)

    # 2) 创建 __init__.py
    for f in INIT_FILES:
        ensure_file(root / f, content="# package\n", dry_run=dry_run)

    # 3) 迁移散落文件（如果有）
    for src_rel, dst_rel in MOVE_MAP:
        safe_move(root / src_rel, root / dst_rel, dry_run=dry_run)

    # 4) 创建 PWA 占位文件（不存在才创建）
    for rel, content in PWA_PLACEHOLDERS.items():
        ensure_file(root / rel, content=content, dry_run=dry_run)

    print("-" * 60)
    if dry_run:
        print("✅ 预览完成。确认无误后执行：")
        print("   python .\\scripts\\restructure_project.py --apply")
    else:
        print("✅ 结构整理完成。")


if __name__ == "__main__":
    main()