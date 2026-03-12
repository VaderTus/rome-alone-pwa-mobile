# scripts/harvest_hd_data_v2.py
import pandas as pd
from pathlib import Path
import importlib
import random
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
from core.loader import DataRepo
from core.engine import RomeEngine

# 定义固定的感官顺序 (总计 49 维 = 17 维状态 + 21 维记牌 + 5 维动作特征)
BUILDINGS = ["B_KaiXuanDiaoSu", "B_DiGuoYinShuiDao", "B_JunTuanYaoSai", "B_DiGuoJinKuang", "B_YuanXingJingJiChang"]
MONUMENTS = ["M_WanShenMiao", "M_LuoMaDouShouChang", "M_DiGuoGuangChang", "M_HaDeLiangLingQin", "M_KaiXuanMen", "M_TuLaZhenShiChang"]
ALL_CARDS = [f"C{i:02d}" for i in range(1, 22)]

def run_harvest(total_games=10000):
    repo = DataRepo(Path("data"))
    engine = RomeEngine(repo)
    # 调用最强的 MCTS 作为我们的原始素材来源
    mcts_fn = importlib.import_module("policies.mcts_policy").select_action
    
    all_step_data = []
    print(f"📡 开启全量高清收割模式 | 目标: {total_games} 局...")

    for i in range(total_games):
        seed = random.randint(0, 9999999)
        s = engine.new_game(seed=seed)
        
        game_history = []
        
        while (not s.game_lost) and s.invasions_resolved < 3:
            s.turn_count += 1
            hand = engine.draw_hand(s)
            legal = engine.legal_actions(s, hand)
            
            # --- 1. 构造 44 维环境感官快照 ---
            feat = {
                "turn": s.turn_count / 21.0,
                "c": s.culture / 9.0, "m": s.military / 9.0, "i": s.industry / 9.0,
                "reg": s.occupied_regions() / 7.0,
                "inv": s.invasions_resolved / 2.0
            }
            # 建筑感官 (5维)
            for b in BUILDINGS: feat[f"b_{b}"] = 1.0 if b in s.built_buildings else 0.0
            # 奇观感官 (6维)
            for m in MONUMENTS: feat[f"m_{m}"] = s.monument_progress.get(m, 0) / 2.0
            
            # 💡 记牌器感官 (21维) —— 游戏引擎会在入侵后自动清空 discard，
            # 所以 AI 看着 discard 就能完美知道当前回合哪些牌已经出过了。
            for card_id in ALL_CARDS: 
                feat[f"card_{card_id}"] = 1.0 if card_id in s.discard else 0.0
            
            # --- 2. 获取大神动作 ---
            action = mcts_fn(engine, s, hand, legal)
            
            # 动作特征 (5维)
            feat["act_top"] = 1.0 if action['mode'] == 'top' else 0.0
            feat["act_conq"] = 1.0 if action['kind'] == 'Conquest' else 0.0
            feat["act_trib"] = 1.0 if action['kind'] == 'Tribute' else 0.0
            feat["act_build"] = 1.0 if action['kind'] == 'Build_Building' else 0.0
            feat["act_monu"] = 1.0 if action['kind'] == 'Build_Monument' else 0.0
            
            game_history.append(feat)
            
            # 执行动作与入侵判定
            engine.apply_action(s, hand, action)
            engine.resolve_invasion_if_needed(s)
            
        # --- 3. 结果赋值 (强化学习的核心) ---
        # 赢了根据分数给奖励 (18分为满分 1.0)
        # 输了直接给 -1.0 的重罚，教它做人
        if s.game_lost:
            final_val = -1.0 
        else:
            final_val = engine.score(s) / 18.0 
            
        for step in game_history:
            step["target_value"] = final_val
            all_step_data.append(step)

        if (i + 1) % 100 == 0: 
            print(f"进度: {i+1}/{total_games} | 已采集 {len(all_step_data)} 个决策瞬间")

    # 存盘
    out_dir = PROJECT_ROOT / "data"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "hd_training_data_v2.csv"
    pd.DataFrame(all_step_data).to_csv(out_path, index=False)
    print(f"\n✅ 高清教材制作完成！文件保存在: {out_path}")

if __name__ == "__main__":
    # 为了保证数据量，我们直接跑 10000 局 (约产生 21 万条训练数据)
    run_harvest(total_games=10000)