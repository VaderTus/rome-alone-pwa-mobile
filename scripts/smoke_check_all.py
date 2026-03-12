from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent

def run(cmd, name):
    print(f"\n[CHECK] {name}")
    print(">", " ".join(str(x) for x in cmd))
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    print(r.stdout[-1200:] if r.stdout else "")
    if r.returncode != 0:
        print(r.stderr[-1200:] if r.stderr else "")
        raise RuntimeError(f"{name} 失败")

def exists_or_skip(rel, name):
    p = ROOT / rel
    if not p.exists():
        print(f"[SKIP] {name}（文件不存在）")
        return False
    return True

def main():
    py = sys.executable

    # 1) 数据文件检查
    for f in ["data/Cards.csv", "data/Buildings.csv", "data/Monuments.csv", "data/Invasions.csv"]:
        if not (ROOT / f).exists():
            raise FileNotFoundError(f"缺少数据文件: {f}")
    print("✅ 数据文件存在")

    # 2) 单策略快速跑（各20局）
    if exists_or_skip("experiments/run_single_strategy.py", "单策略脚本"):
        for p in ["random_policy", "arc_policy", "pantheon_policy"]:
            run([py, "experiments/run_single_strategy.py", "--policy", p, "--games", "20", "--seed", "123450"], f"run_single_strategy:{p}")

    # 3) 日志整合脚本（若存在）
    if exists_or_skip("scripts/ingest_human_logs.py", "人类日志整合"):
        run([py, "scripts/ingest_human_logs.py"], "ingest_human_logs")

    # 4) 控制面板语法检查（不启动交互）
    if exists_or_skip("ui/control_center.py", "控制面板"):
        run([py, "-m", "py_compile", "ui/control_center.py"], "py_compile:control_center")

    # 5) 网页脚本语法检查（不启动streamlit）
    if exists_or_skip("ui/web_human_play.py", "网页游玩"):
        run([py, "-m", "py_compile", "ui/web_human_play.py"], "py_compile:web_human_play")

    print("\n🎉 全部关键检查通过")

if __name__ == "__main__":
    main()