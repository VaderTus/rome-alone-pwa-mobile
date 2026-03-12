# scripts/find_god_limit.py
from pathlib import Path
import sys
import copy

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.loader import DataRepo
from core.engine import RomeEngine

def solve_god_mode(seed):
    repo = DataRepo(Path("data"))
    engine = RomeEngine(repo, seed=seed)
    s = engine.new_game(seed=seed)
    
    # 获取这局游戏确定的 21 张牌顺序 (上帝视角)
    fixed_deck = list(s.deck)
    
    memo = {}

    def get_max_score(current_state, deck_index):
        state_key = (
            current_state.culture, current_state.military, current_state.industry,
            current_state.occupied_regions(),
            tuple(sorted(current_state.built_buildings)),
            tuple(sorted(current_state.monument_progress.items())),
            deck_index
        )
        
        if state_key in memo: return memo[state_key]
        if current_state.game_lost: return -1
        if deck_index <= 0: return engine.score(current_state)

        # 模拟抽 3 选 1
        # 注意：引擎是从 deck 末尾取牌
        hand = fixed_deck[deck_index-3 : deck_index]
        legal_actions = engine.legal_actions(current_state, hand)
        
        best_val = -1
        for action in legal_actions:
            # 深度复制状态，进行分叉搜索
            next_s = copy.deepcopy(current_state)
            engine.apply_action(next_s, hand, action)
            engine.resolve_invasion_if_needed(next_s)
            
            res = get_max_score(next_s, deck_index - 3)
            best_val = max(best_val, res)
            
        memo[state_key] = best_val
        return best_val

    print(f"🕵️ 正在暴力破解 Seed {seed} 的上帝上限...")
    limit = get_max_score(s, 21)
    print(f"🏆 该种子的绝对最高得分是: {limit} 分")
    return limit

if __name__ == "__main__":
    # 我们拿那个 11.7 分策略只打了 14 分的种子来试试
    solve_god_mode(5000000)