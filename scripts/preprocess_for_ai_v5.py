# scripts/preprocess_for_ai.py
import json
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
JSON_PATH = PROJECT_ROOT / "outputs" / "full_knowledge" / "full_mcts_data.json"

def preprocess():
    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    records = []
    print("🎯 正在构建【动作-价值】特征矩阵...")
    
    for case in data:
        # 归一化最终得分 (0 到 1 之间)
        # 失败局记为 -0.5 (让 AI 极其恐惧失败)
        final_val = (case['score'] / 18.0) if not case['lost'] else -0.5

        for step in case['history']:
            # 获取卡牌的具体属性
            # 这里的逻辑需要能访问 repo，我们直接从录像里推断动作带来的即时变化
            row = {
                "turn": step['turn'] / 21.0,
                "c": step['res_before']['C'] / 9.0,
                "m": step['res_before']['M'] / 9.0,
                "i": step['res_before']['I'] / 9.0,
                "reg": step['reg_before'] / 7.0,
                # 动作编码
                "act_is_top": 1.0 if step['mode'] == 'top' else 0.0,
                "act_is_conq": 1.0 if step['action'] == 'Conquest' else 0.0,
                "act_is_trib": 1.0 if step['action'] == 'Tribute' else 0.0,
                "act_is_build": 1.0 if step['action'] == 'Build_Building' else 0.0,
                "act_is_monu": 1.0 if step['action'] == 'Build_Monument' else 0.0,
                # 目标：这手动作最终导向的胜率/价值
                "label_value": final_val 
            }
            records.append(row)

    df = pd.DataFrame(records)
    df.to_csv(PROJECT_ROOT / "data/ai_value_training_v5.csv", index=False)
    print(f"✅ 价值教材制作完成！样本数：{len(df)}")

if __name__ == "__main__":
    preprocess()