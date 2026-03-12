# policies/neural_pure_agent.py
import torch
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
from policies.neural_brain import RomePPOBrain

MODEL_PATH = PROJECT_ROOT / "data" / "ppo_rome_brain.pth"
BUILDINGS = ["B_KaiXuanDiaoSu", "B_DiGuoYinShuiDao", "B_JunTuanYaoSai", "B_DiGuoJinKuang", "B_YuanXingJingJiChang"]
MONUMENTS = ["M_WanShenMiao", "M_LuoMaDouShouChang", "M_DiGuoGuangChang", "M_HaDeLiangLingQin", "M_KaiXuanMen", "M_TuLaZhenShiChang"]
ALL_CARDS = [f"C{i:02d}" for i in range(1, 22)]
AMAP = {"TopResource": 0, "Conquest": 1, "Tribute": 2, "Build_Building": 3, "Build_Monument": 4}

BRAIN = RomePPOBrain(input_size=43)
if MODEL_PATH.exists():
    BRAIN.load_state_dict(torch.load(MODEL_PATH, weights_only=True))
    BRAIN.eval()

def select_action(engine, state, hand, legal_actions):
    if not legal_actions: return {"card_id": hand[0], "mode": "top", "kind": "TopResource", "meta": {}}

    # 1. 提取 43 维感官信息
    feat = [
        state.turn_count / 21.0, state.culture / 9.0, state.military / 9.0, state.industry / 9.0,
        state.occupied_regions() / 7.0, state.invasions_resolved / 2.0
    ]
    for b in BUILDINGS: feat.append(1.0 if b in state.built_buildings else 0.0)
    for m in MONUMENTS: feat.append(state.monument_progress.get(m, 0) / 2.0)
    for c in ALL_CARDS: feat.append(1.0 if c in state.discard else 0.0)

    # 2. 构造合法动作遮罩
    legal_mask = torch.zeros(5, dtype=torch.bool)
    action_buckets = {i: [] for i in range(5)}
    
    for act in legal_actions:
        tid = AMAP.get(act['kind'], 0)
        if act['mode'] == 'top': tid = 0
        legal_mask[tid] = True
        action_buckets[tid].append(act)

    input_t = torch.tensor([feat], dtype=torch.float32)

    # 3. 神经网络发号施令 (绝对纯净)
    with torch.no_grad():
        logits, _ = BRAIN(input_t)
        logits = logits.squeeze(0)
        
        # 屏蔽非法动作
        logits = logits.masked_fill(~legal_mask, -1e9)
        # 找出神经网络认为最该做的动作大类
        best_type_idx = torch.argmax(logits).item()

    # 从大类中随便取一个具体的卡牌动作（后续可优化微操，目前先让它学大方向）
    return action_buckets[best_type_idx][0]