# scripts/prep_god_data.py
import pandas as pd
import json
import torch
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
from core.loader import DataRepo
from core.engine import RomeEngine

BUILDINGS = ["B_KaiXuanDiaoSu", "B_DiGuoYinShuiDao", "B_JunTuanYaoSai", "B_DiGuoJinKuang", "B_YuanXingJingJiChang"]
MONUMENTS = ["M_WanShenMiao", "M_LuoMaDouShouChang", "M_DiGuoGuangChang", "M_HaDeLiangLingQin", "M_KaiXuanMen", "M_TuLaZhenShiChang"]
ALL_CARDS = [f"C{i:02d}" for i in range(1, 22)]
AMAP = {"TopResource": 0, "Conquest": 1, "Tribute": 2, "Build_Building": 3, "Build_Monument": 4}

def prep_god_data():
    repo = DataRepo(Path("data"))
    god_file = PROJECT_ROOT / "outputs" / "god_limits.csv"
    
    if not god_file.exists():
        print("❌ 找不到上帝记录文件！")
        return

    df_god = pd.read_csv(god_file)
    records = []
    
    print(f"🧠 正在提取 {len(df_god)} 局【上帝视角】操作，提炼终极直觉...")
    
    for _, row in df_god.iterrows():
        seed = int(row['seed'])
        path_str = str(row['perfect_path'])
        if not path_str or pd.isna(path_str): continue
        
        # 解析上帝的动作序列
        actions_str = path_str.split('|')
        
        engine = RomeEngine(repo, seed=seed)
        s = engine.new_game(seed=seed)
        
        # 为了上帝视角的还原，我们需要重现当时的手牌
        cycle_deck = list(s.deck)
        full_deck = cycle_deck + cycle_deck + cycle_deck
        
        for turn_idx, step_desc in enumerate(actions_str):
            hand_start = turn_idx * 3
            current_hand = full_deck[hand_start : hand_start+3]
            legal_actions = engine.legal_actions(s, current_hand)
            
            # 从上帝的历史记录中反推他选了哪个合法动作
            # 格式例如: T_TopR_C04
            parts = step_desc.split('_')
            target_mode = 'top' if parts[0] == 'T' else 'bottom'
            target_card = parts[2]
            
            chosen_act = None
            for act in legal_actions:
                if act['mode'] == target_mode and act['card_id'] == target_card:
                    chosen_act = act; break
                    
            if not chosen_act: break # 万一解析出错，跳过该局后续
            
            # --- 构建 43 维感官特征 ---
            feat = [
                s.turn_count / 21.0, s.culture / 9.0, s.military / 9.0, s.industry / 9.0,
                s.occupied_regions() / 7.0, s.invasions_resolved / 2.0
            ]
            for b in BUILDINGS: feat.append(1.0 if b in s.built_buildings else 0.0)
            for m in MONUMENTS: feat.append(s.monument_progress.get(m, 0) / 2.0)
            for c in ALL_CARDS: feat.append(1.0 if c in s.discard else 0.0)
            
            # 记录此时的正确选择 (作为监督学习的 Target)
            action_type = 'TopResource' if chosen_act['mode'] == 'top' else chosen_act['kind']
            
            records.append({
                "features": feat,
                "label": AMAP.get(action_type, 0)
            })
            
            # 状态推进
            engine.apply_action(s, current_hand, chosen_act)
            if (turn_idx + 1) % 7 == 0: engine.resolve_invasion_if_needed(s)

    # 存盘为供 AI 训练的格式
    df_train = pd.DataFrame([r['features'] + [r['label']] for r in records])
    out_path = PROJECT_ROOT / "data" / "god_training_data.csv"
    df_train.to_csv(out_path, index=False, header=False)
    print(f"✅ 上帝教材制作完成！包含 {len(df_train)} 条绝对真理。保存至: {out_path}")

if __name__ == "__main__":
    prep_god_data()