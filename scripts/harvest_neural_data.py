# scripts/harvest_neural_data.py
import sys
import time
from pathlib import Path
import torch

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.loader import DataRepo
from core.engine import RomeEngine
from core.encoder import RomeStateEncoder
from policies.mcts_distilled_final import select_action as coach_policy

def harvest_massive_data(num_games=10000):
    print("="*50)
    print(f"🚜 启动重工业级数据挖掘 | 目标: {num_games} 局全谱数据")
    print("="*50)
    
    repo = DataRepo(PROJECT_ROOT / "data")
    engine = RomeEngine(repo)
    encoder = RomeStateEncoder()
    
    X_data, Y_data = [], []
    deaths, total_score = 0, 0
    start_time = time.time()
    
    for i in range(num_games):
        state = engine.new_game(seed=int(time.time() * 1000) % 1000000 + i)
        history_tensors = []
        
        while (not state.game_lost) and state.invasions_resolved < 3:
            state.turn_count += 1
            hand = engine.draw_hand(state)
            if not hand: break
            
            # 记录当前 40维 局面
            history_tensors.append(encoder.encode(state))
            
            # 教官下棋
            legal_acts = engine.legal_actions(state, hand)
            action = coach_policy(engine, state, hand, legal_acts)
            engine.apply_action(state, hand, action)
            engine.resolve_invasion_if_needed(state, policy_name="coach")
            
        final_score = engine.score(state) if not state.game_lost else 0.0
        if state.game_lost: deaths += 1
        total_score += final_score
        
        # 贴标签
        for tensor in history_tensors:
            X_data.append(tensor)
            Y_data.append(float(final_score))
            
        if (i + 1) % 1000 == 0:
            print(f"  [进度 {i+1}/{num_games}] 已收集残局: {len(X_data)} 条 | 耗时: {time.time()-start_time:.1f}s")
            
    print("\n✅ 挖掘完毕！")
    print(f"📊 收集到 {len(X_data)} 条高质量数据，包含暴毙反面教材 {deaths} 局。教官均分: {total_score/num_games:.2f}")
    
    # 永久存盘
    save_dir = PROJECT_ROOT / "data" / "_legacy_datasets"
    save_dir.mkdir(parents=True, exist_ok=True)
    torch.save({"X": torch.stack(X_data), "Y": torch.tensor(Y_data, dtype=torch.float32).unsqueeze(1)}, 
               save_dir / "massive_40d_dataset.pt")
    print(f"💾 数据已永久封存于 {save_dir / 'massive_40d_dataset.pt'}")

if __name__ == "__main__":
    harvest_massive_data(10000)