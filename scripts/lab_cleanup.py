# scripts/lab_cleanup.py
import os
import shutil
from pathlib import Path

def cleanup():
    # 需要归档的文件列表（你可以根据实际情况添加）
    TO_ARCHIVE = [
        "scripts/train_warlord.py",
        "scripts/train_architect.py",
        "scripts/train_endgame_specialists.py",
        "scripts/optimize_ensemble_v2.py",
        "scripts/cluster_mcts_strategies.py",
        "outputs/warlord_gene.csv",
        "outputs/architect_gene.csv",
        "outputs/optimization_log.csv"
    ]
    
    archive_dir = Path("archive")
    archive_dir.mkdir(exist_ok=True)
    
    print("🧹 正在清理实验室...")
    for file_path in TO_ARCHIVE:
        p = Path(file_path)
        if p.exists():
            print(f"  ∟ 归档: {p.name}")
            shutil.move(str(p), str(archive_dir / p.name))
    
    print("\n✅ 环境已重置。现在你的 scripts 目录只保留核心工具。")

if __name__ == "__main__":
    cleanup()