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
    # 我们要让 AI 记住这 6 个奇观的每一个进度
    MONUMENTS = ["M_WanShenMiao", "M_LuoMaDouShouChang", "M_DiGuoGuangChang", "M_HaDeLiangLingQin", "M_KaiXuanMen", "M_TuLaZhenShiChang"]

    print("🔬 正在进行【高分辨率】感官建模...")
    for case in data:
        # 调整奖励权重：把高分局的吸引力拉得更高
        # 18分 = 1.5, 14分 = 0.5, 失败 = -2.0
        if case['lost']: final_val = -2.0
        else: final_val = (case['score'] - 10) / 8.0 

        curr_m = {m: 0 for m in MONUMENTS}
        for step in case['history']:
            row = {
                "turn": step['turn'] / 21.0,
                "c": step['res_before']['C'] / 9.0,
                "m": step['res_before']['M'] / 9.0,
                "i": step['res_before']['I'] / 9.0,
                "reg": step['reg_before'] / 7.0,
            }
            # 精准奇观感官：0, 1, 2 分别代表不同阶段
            for m in MONUMENTS: 
                row[f"m_{m}"] = curr_m[m]
            
            row["state_value"] = final_val 
            records.append(row)

            if step['action'] == 'Build_Monument':
                for m in MONUMENTS:
                    if m in str(step.get('card','')): curr_m[m] = min(2, curr_m[m] + 1)

    pd.DataFrame(records).to_csv(PROJECT_ROOT / "data/ai_state_value_v6.csv", index=False)
    print(f"✅ V6 版高精度教材已就绪。")

if __name__ == "__main__":
    preprocess()