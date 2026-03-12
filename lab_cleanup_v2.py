import os
import shutil
from pathlib import Path

# 项目根目录
BASE_DIR = Path(__file__).resolve().parent

def ensure_dir(path):
    path.mkdir(parents=True, exist_ok=True)
    return path

def safe_move(src_path, dest_dir):
    if src_path.exists():
        try:
            shutil.move(str(src_path), str(dest_dir / src_path.name))
            print(f"  [归档] {src_path.name} -> {dest_dir.name}/")
        except Exception as e:
            print(f"  [警告] 无法移动 {src_path.name}: {e}")

def main():
    print("🧹 启动《孤城罗马》AI 实验室 - 核心资产提纯协议 🧹\n")

    # 1. 整理模型权重 (Models)
    print(">>> 1. 提取神经网络大脑权重 (.pth)...")
    models_dir = ensure_dir(BASE_DIR / "models")
    data_dir = BASE_DIR / "data"
    if data_dir.exists():
        for pth_file in data_dir.glob("*.pth"):
            safe_move(pth_file, models_dir)
        # 顺便把 json 权重也移过去
        for json_weight in data_dir.glob("*.json"):
            if "weight" in json_weight.name or "brain" in json_weight.name:
                safe_move(json_weight, models_dir)

    # 2. 净化 Data 文件夹 (保留核心规则，归档训练残渣)
    print("\n>>> 2. 净化基础数据库...")
    legacy_data_dir = ensure_dir(data_dir / "_legacy_datasets")
    core_csvs = ["Cards.csv", "Buildings.csv", "Monuments.csv", "Invasions.csv"]
    for csv_file in data_dir.glob("*.csv"):
        if csv_file.name not in core_csvs:
            safe_move(csv_file, legacy_data_dir)

    # 3. 封存海量实验日志和残局 (Logs & Cases)
    print("\n>>> 3. 封存海量战报与 JSON 残局...")
    archive_cases_dir = ensure_dir(BASE_DIR / "_archive_cases")
    
    logs_study_dir = BASE_DIR / "logs" / "mcts_deep_study"
    if logs_study_dir.exists():
        safe_move(logs_study_dir, archive_cases_dir)
        
    strategy_cases_dir = BASE_DIR / "strategy_cases"
    if strategy_cases_dir.exists():
        safe_move(strategy_cases_dir, archive_cases_dir)

    # 4. 封存一次性分析脚本
    print("\n>>> 4. 封存一次性分析代码...")
    scripts_dir = BASE_DIR / "scripts"
    legacy_scripts_dir = ensure_dir(scripts_dir / "_legacy_analysis")
    if scripts_dir.exists():
        for py_file in scripts_dir.glob("*.py"):
            # 保留核心运行脚本，归档带 analyze_, cluster_, harvest_ 前缀的
            name = py_file.name
            if name.startswith("analyze_") or name.startswith("cluster_") or \
               name.startswith("harvest_") or name.startswith("audit_"):
                safe_move(py_file, legacy_scripts_dir)

    # 5. 清理讨厌的缓存
    print("\n>>> 5. 焚毁无用的缓存文件 (__pycache__)...")
    cache_count = 0
    for pycache_dir in BASE_DIR.rglob("__pycache__"):
        try:
            shutil.rmtree(pycache_dir)
            cache_count += 1
        except Exception:
            pass
    print(f"  [清理] 共销毁 {cache_count} 个 __pycache__ 文件夹。")

    print("\n✅ 实验室重构完毕！长官，现在的系统无比纯净且高效。")

if __name__ == "__main__":
    main()