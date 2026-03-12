# scripts/harvest_mcts_patterns.py
from pathlib import Path
import sys
import json
import pandas as pd
import importlib

# === 路径修复：确保从 scripts 直接运行时也能 import core/policies ===
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.loader import DataRepo
from core.engine import RomeEngine

def run_harvest(total_games=10000, start_seed=2000000, min_score=14):
    repo = DataRepo(Path("data"))
    engine = RomeEngine(repo, seed=42)
    
    # 动态加载最强的 MCTS 策略
    try:
        mcts_mod = importlib.import_module("policies.mcts_policy")
        mcts_fn = mcts_mod.select_action
    except ImportError:
        print("错误：找不到 policies/mcts_policy.py 文件，请确认路径。")
        return

    high_score_cases = []
    
    print(f"==========================================")
    print(f"🚀 开始大规模收割 MCTS 高分模式...")
    print(f"目标局数: {total_games} | 起始种子: {start_seed} | 记录门槛: {min_score}分")
    print(f"==========================================\n")
    
    for i in range(total_games):
        seed = start_seed + i
        s = engine.new_game(seed=seed)
        
        # 记录初始牌堆顺序 (第一大回合的 21 张牌)
        # 注意：引擎初始化后，s.deck 是洗好的列表
        initial_deck_order = list(s.deck) 
        # 引擎抽牌是从列表末尾 pop()，所以起手 3 张是列表最后三个元素
        opening_hand = initial_deck_order[-3:] 
        
        first_cycle_actions = []
        
        # 模拟一局完整的游戏
        while (not s.game_lost) and s.invasions_resolved < 3:
            s.turn_count += 1
            hand = engine.draw_hand(s)
            legal = engine.legal_actions(s, hand)
            
            # 调用 MCTS 进行思考
            action = mcts_fn(engine, s, hand, legal)
            
            # 记录第一大回合（即前 21 张牌消耗完之前）的所有操作细节
            if s.invasions_resolved == 0:
                # 获取卡牌名称
                c_name = repo.card_by_id[action['card_id']]['Card_Name']
                first_cycle_actions.append({
                    "turn": s.turn_count,
                    "card_name": c_name,
                    "action_kind": action['kind'],
                    "mode": action['mode'],
                    "meta": action.get('meta', {})
                })
            
            # 应用动作
            engine.apply_action(s, hand, action)
            # 结算入侵
            engine.resolve_invasion_if_needed(s)
            
        final_score = engine.score(s)
        
        # 只记录达到门槛且没有失败的高分样本
        if final_score >= min_score and not s.game_lost:
            # 计分解构
            regions_score = s.occupied_regions()
            bld_score = sum([int(repo.building_by_id[bid].get("Immediate_GP", 0)) for bid in s.built_buildings])
            monu_score = final_score - regions_score - bld_score
            
            high_score_cases.append({
                "seed": seed,
                "total_score": final_score,
                "score_breakdown": {
                    "regions": regions_score,
                    "buildings": bld_score,
                    "monuments": monu_score
                },
                "opening_hand": opening_hand,
                "first_cycle_actions": first_cycle_actions,
                "built_buildings": list(s.built_buildings),
                "monuments_completed": [m for m, p in s.monument_progress.items() if p >= 2]
            })
            
        # 每 50 局打印一次进度，方便观察
        if (i + 1) % 50 == 0:
            print(f"进度: {i+1}/{total_games} | 发现高分局: {len(high_score_cases)}")

    # 创建输出目录
    out_dir = Path("outputs/harvest")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # 导出完整 JSON 数据
    json_path = out_dir / f"mcts_patterns_data.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(high_score_cases, f, ensure_ascii=False, indent=4)
        
    # 导出摘要 CSV
    csv_rows = []
    for c in high_score_cases:
        csv_rows.append({
            "seed": c['seed'],
            "score": c['total_score'],
            "opening_hand": ",".join(c['opening_hand']),
            "regions_val": c['score_breakdown']['regions'],
            "blds_val": c['score_breakdown']['buildings'],
            "mons_val": c['score_breakdown']['monuments'],
            "completed_mons": ",".join(c['monuments_completed'])
        })
    pd.DataFrame(csv_rows).to_csv(out_dir / f"mcts_high_scores_summary.csv", index=False, encoding="utf-8-sig")

    print(f"\n✅ 数据收割完成！")
    print(f"在 {total_games} 局中找到了 {len(high_score_cases)} 个高分剧本。")
    print(f"数据已保存在: {out_dir}")

if __name__ == "__main__":
    # 为了测试耗时，建议第一次运行先用 100 局。
    # 确认没问题后，你可以修改为 5000 或 10000。
    run_harvest(total_games=10000)