# scripts/critique_human_play.py
from pathlib import Path
import json
import pandas as pd
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))

from core.loader import DataRepo
from core.engine import RomeEngine
from policies.mcts_distilled_final import select_action as machine_policy

def main():
    # 1. 寻找最近的一份人类游玩日志
    log_dir = ROOT / "logs" / "human_play"
    log_files = list(log_dir.glob("human_trace_*.jsonl"))
    
    if not log_files:
        print("❌ 未找到人类游玩日志。请先在网页版或手机版玩一局并导出日志！")
        return
    
    latest_log = max(log_files, key=lambda x: x.stat().st_mtime)
    print(f"📖 正在分析对局: {latest_log.name}")

    repo = DataRepo(ROOT / "data")
    engine = RomeEngine(repo, seed=42)
    
    mismatches = []
    
    with open(latest_log, "r", encoding="utf-8") as f:
        for line in f:
            record = json.loads(line)
            turn = record["turn"]
            hand = record["hand"]
            human_action = record["chosen_action"]
            
            # 我们需要重建那一回合的状态
            # 注意：这里的 state 比较复杂，我们直接使用记录中的 before 镜像
            # 为了让机器策略能运行，我们需要构造一个临时的 state 对象
            from core.state import GameState
            b = record["before"]
            s = GameState(
                culture=b["culture"], military=b["military"], industry=b["industry"],
                rome_occupied=b["rome_occupied"],
                occupied_culture_regions=b["occupied_culture_regions"],
                occupied_industry_regions=b["occupied_industry_regions"],
                built_buildings=set(b["built_buildings"]),
                monument_progress=b["monument_progress"],
                deck=list(range(b["deck_left"])), # 占位，只需长度
                turn_count=turn
            )
            
            legal = engine.legal_actions(s, hand)
            machine_action = machine_policy(engine, s, hand, legal)
            
            # 比较动作
            is_same = (human_action["card_id"] == machine_action["card_id"]) and \
                      (human_action["mode"] == machine_action["mode"])
            
            if not is_same:
                mismatches.append({
                    "回合": turn,
                    "人类选择": f"{human_action['card_id']}({human_action['mode']})",
                    "机器建议": f"{machine_action['card_id']}({machine_action['mode']})",
                    "机器理由": "权重最高" 
                })

    if mismatches:
        print("\n🔍 发现分歧点（建议复盘）：")
        print(pd.DataFrame(mismatches).to_string(index=False))
    else:
        print("\n✅ 英雄所见略同！你在所有关键决策上都与机器达成了一致。")

if __name__ == "__main__":
    main()