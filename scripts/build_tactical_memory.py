# scripts/build_tactical_memory.py
import json
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
JSON_PATH = PROJECT_ROOT / "outputs" / "full_knowledge" / "full_mcts_data.json"

def build_memory():
    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    memory_rows = []
    
    print("🧹 正在从高分对局中提取神级直觉...")
    
    for case in data:
        # 只提取 16 分以上的种子对局
        if case['score'] < 16 or case['lost']: continue
        
        for step in case['history']:
            memory_rows.append({
                "turn": step['turn'],
                "c": step['res_before']['C'],
                "m": step['res_before']['M'],
                "i": step['res_before']['I'],
                "reg": step['reg_before'],
                "best_action": step['action'],
                "best_mode": step['mode'],
                "card_id": step['card'] # 记录具体的卡牌名，用于匹配
            })
            
    df = pd.DataFrame(memory_rows)
    # 对相同的状态进行去重，只保留最频繁出现的动作
    # 这一步是提取'共识战术'
    consensus = df.groupby(['turn', 'c', 'm', 'i', 'reg']).apply(
        lambda x: x[['best_action', 'best_mode']].mode().iloc[0]
    ).reset_index()
    
    out_path = PROJECT_ROOT / "data" / "tactical_memory.csv"
    consensus.to_csv(out_path, index=False)
    print(f"✅ 战术库构建完成！共记录 {len(consensus)} 条神级状态反应。")
    print(f"保存至: {out_path}")

if __name__ == "__main__":
    build_memory()