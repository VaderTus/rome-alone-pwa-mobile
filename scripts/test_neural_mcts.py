# 测试脚本 (比如放在 scripts/test_neural_mcts.py)
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.loader import DataRepo
from core.engine import RomeEngine
from policies.neural_mcts_policy import select_action

repo = DataRepo(PROJECT_ROOT / "data")
engine = RomeEngine(repo)

total_score = 0
deaths = 0
games = 50 # 先测 50 局看看威力

print(f"🚀 启动神谕贝叶斯搜索 (Neural MCTS)... 盲打 {games} 局")
for i in range(games):
    state = engine.new_game(seed=i+8888)
    while not state.game_lost and state.invasions_resolved < 3:
        state.turn_count += 1
        hand = engine.draw_hand(state)
        if not hand: break
        legal = engine.legal_actions(state, hand)
        # 调用我们刚写的最强策略！
        act = select_action(engine, state, hand, legal)
        engine.apply_action(state, hand, act)
        engine.resolve_invasion_if_needed(state, policy_name="neural")
    
    if state.game_lost:
        deaths += 1
    else:
        total_score += engine.score(state)

print(f"\n📊 测试完毕 | 暴毙率: {deaths/games*100}% | 盲打均分: {total_score/games:.2f} 分")