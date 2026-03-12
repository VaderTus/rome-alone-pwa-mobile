# scripts/prep_policy_data.py
import json
import pandas as pd
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
JSON_PATH = PROJECT_ROOT / "outputs" / "full_knowledge" / "full_mcts_data.json"

def prep():
    if not JSON_PATH.exists():
        print(f"❌ 找不到文件: {JSON_PATH}")
        return

    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    records = []
    BUILDINGS = ["B_KaiXuanDiaoSu", "B_DiGuoYinShuiDao", "B_JunTuanYaoSai", "B_DiGuoJinKuang", "B_YuanXingJingJiChang"]
    MONUMENTS = ["M_WanShenMiao", "M_LuoMaDouShouChang", "M_DiGuoGuangChang", "M_HaDeLiangLingQin", "M_KaiXuanMen", "M_TuLaZhenShiChang"]
    ALL_CARDS = [f"C{i:02d}" for i in range(1, 22)]
    AMAP = {"TopResource": 0, "Conquest": 1, "Tribute": 2, "Build_Building": 3, "Build_Monument": 4}

    print("🧠 正在提取 MCTS 的肌肉记忆 (含智能状态补全)...")
    for case in data:
        # 只学习 12 分以上的正常/高分局
        if case['lost'] or case['score'] < 12: continue
        
        # 💡 AI 追踪器：由于 JSON 每一步没有存建筑，我们在遍历时自己推算
        current_built = set()
        current_monu = {m: 0 for m in MONUMENTS}
        used_cards = set()

        for step in case['history']:
            # 1. 组装感官数据
            row = {
                "turn": step['turn'] / 21.0,
                "c": step['res_before']['C'] / 9.0,
                "m": step['res_before']['M'] / 9.0,
                "i": step['res_before']['I'] / 9.0,
                "reg": step['reg_before'] / 7.0,
                "inv": ((step['turn'] - 1) // 7) / 2.0,
            }
            
            # 把追踪器里的数据填进去
            for b in BUILDINGS: 
                row[f"b_{b}"] = 1.0 if b in current_built else 0.0
            for m in MONUMENTS: 
                row[f"m_{m}"] = current_monu[m] / 2.0
            for c in ALL_CARDS: 
                row[f"c_{c}"] = 1.0 if c in used_cards else 0.0
            
            # 2. 提取标签 (MCTS 选了啥)
            action_type = 'TopResource' if step['mode'] == 'top' else step['action']
            row['label'] = AMAP.get(action_type, 0)
            
            records.append(row)

            # 3. 动作发生！更新追踪器，供下一回合使用
            card_id = step.get('card', '')
            used_cards.add(card_id)
            
            # 清空弃牌堆 (模拟洗牌机制：第7, 14手结束时洗牌)
            if step['turn'] % 7 == 0:
                used_cards.clear()

            # 因为我们的 json 没有记录具体的 building_id，我们需要做模糊匹配
            # 在实际工程中，最好依靠引擎提供准确数据。这里为了提取，我们通过 card_id 猜测
            if step['action'] == 'Build_Building':
                # 简单映射：前 5 张牌对应建筑
                if card_id == "C01": current_built.add("B_KaiXuanDiaoSu")
                elif card_id == "C02": current_built.add("B_DiGuoYinShuiDao")
                elif card_id == "C03": current_built.add("B_JunTuanYaoSai")
                elif card_id == "C04": current_built.add("B_DiGuoJinKuang")
                elif card_id == "C05": current_built.add("B_YuanXingJingJiChang")
                
            elif step['action'] == 'Build_Monument':
                if card_id in ["C10", "C11"]: current_monu["M_WanShenMiao"] = min(2, current_monu["M_WanShenMiao"] + 1)
                elif card_id in ["C12", "C13"]: current_monu["M_LuoMaDouShouChang"] = min(2, current_monu["M_LuoMaDouShouChang"] + 1)
                elif card_id in ["C14", "C15"]: current_monu["M_DiGuoGuangChang"] = min(2, current_monu["M_DiGuoGuangChang"] + 1)
                elif card_id in ["C16", "C17"]: current_monu["M_HaDeLiangLingQin"] = min(2, current_monu["M_HaDeLiangLingQin"] + 1)
                elif card_id in ["C18", "C19"]: current_monu["M_KaiXuanMen"] = min(2, current_monu["M_KaiXuanMen"] + 1)
                elif card_id in ["C20", "C21"]: current_monu["M_TuLaZhenShiChang"] = min(2, current_monu["M_TuLaZhenShiChang"] + 1)

    df = pd.DataFrame(records)
    out = PROJECT_ROOT / "data" / "policy_training_data.csv"
    df.to_csv(out, index=False)
    print(f"✅ 教材生成完毕！包含 {len(df)} 条大神肌肉记忆。保存至: {out}")

if __name__ == "__main__":
    prep()