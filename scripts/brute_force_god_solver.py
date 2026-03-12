# scripts/brute_force_god_solver.py
from pathlib import Path
import sys
import copy

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.loader import DataRepo
from core.engine import RomeEngine

def solve():
    repo = DataRepo(Path("data"))
    # 我们选一个 MCTS 跑了 14 分的种子，看看上帝能跑多少
    target_seed = 5000000 
    engine = RomeEngine(repo, seed=target_seed)
    s = engine.new_game(seed=target_seed)
    
    # 核心：预先锁定 3 轮的牌堆序列
    # 第一轮
    cycle1_deck = list(s.deck)
    # 第二轮 (假设 MCTS 弃掉的牌全回来了)
    # 这里我们简化模型：假设每一轮的初始牌堆顺序是一样的，以便寻找最优解
    full_game_deck = cycle1_deck + cycle1_deck + cycle1_deck
    
    best_ever = {"score": 0, "path": []}
    memo = {}

    def get_max_val(state, step_idx):
        # 状态压缩，用于记忆化搜索
        state_key = (
            state.culture, state.military, state.industry,
            state.occupied_regions(),
            tuple(sorted(state.built_buildings)),
            tuple(sorted(state.monument_progress.items())),
            step_idx
        )
        if state_key in memo: return memo[state_key]
        if state.game_lost: return -1
        if step_idx >= 21: return engine.score(state)

        # 模拟当前手牌 (每 3 张是一手)
        # 注意：这里我们模拟 21 手动作
        hand_start = (step_idx // 1) * 3
        # 简单模拟牌堆循环
        current_hand = full_game_deck[hand_start : hand_start+3]
        legal_actions = engine.legal_actions(state, current_hand)
        
        res_max = -1
        for act in legal_actions:
            # 深度克隆状态
            temp_s = copy.deepcopy(state)
            engine.apply_action(temp_s, current_hand, act)
            # 每 7 手模拟一次洗牌和入侵
            if (step_idx + 1) % 7 == 0:
                engine.resolve_invasion_if_needed(temp_s)
            
            val = get_max_val(temp_s, step_idx + 1)
            res_max = max(res_max, val)
        
        memo[state_key] = res_max
        return res_max

    print(f"🕵️ 正在暴力拆解 Seed {target_seed} 的所有 21 手可能性...")
    print("这可能需要几分钟，取决于决策树的分叉情况...")
    
    absolute_max = get_max_val(s, 0)
    
    print(f"\n==========================================")
    print(f"🏆 该种子的【上帝极限分】: {absolute_max} 分")
    print(f"==========================================")

if __name__ == "__main__":
    solve()