# scripts/run_auto_tune.py
import random
import pandas as pd
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))

from core.loader import DataRepo
from core.engine import RomeEngine
from policies.mcts_distilled_tuned import select_action as tuned_policy

def main():
    repo = DataRepo(ROOT / "data")
    engine = RomeEngine(repo, seed=42)
    
    best_avg = 0
    best_weights = None
    
    print("🚀 开始自动调参优化...")

    for trial in range(50):
        # 随机生成一组接近 V3 的参数
        test_weights = {
            "amphi": random.randint(600, 900),
            "senate": random.randint(400, 600),
            "arc": random.randint(400, 600),
            "pan": random.randint(200, 400),
            "conq_base": random.randint(150, 250),
            "conq_arc": random.randint(350, 550),
            "trib": random.randint(50, 150),
            "top_cul": random.randint(35, 55),
            "top_mil": random.randint(20, 40),
            "top_ind": random.randint(10, 25)
        }
        
        # 跑 500 局快速测试
        scores = []
        for i in range(500):
            res = engine.play_game(lambda e,s,h,l: tuned_policy(e,s,h,l, test_weights), seed=10000+i)
            scores.append(res["总分"])
        
        avg = sum(scores) / len(scores)
        print(f"Trial {trial+1}: 平均分 = {avg:.3f}")
        
        if avg > best_avg:
            best_avg = avg
            best_weights = test_weights
            print(f"✨ 发现更优参数! 目前最高: {best_avg:.3f}")

    print("\n" + "="*30)
    print(f"🏆 调参结束！最高平均分: {best_avg:.3f}")
    print("最佳权重组合如下，请将其更新至 mcts_distilled_final.py:")
    print(best_weights)
    print("="*30)

if __name__ == "__main__":
    main()