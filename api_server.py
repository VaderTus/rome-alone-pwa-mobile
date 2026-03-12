# api_server.py
import sys
import copy
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import torch

from core.loader import DataRepo
from core.engine import RomeEngine
from core.encoder import RomeStateEncoder
from scripts.train_deep_value_net_v2 import RomeValueBrainV2

app = FastAPI(title="Rome V5 God API")

# ⚠️ 破解前任留下的第一个坑：允许跨域请求 (CORS)。没有这个，网页根本连不上！
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # 允许任何网页访问
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 唤醒神明 ---
PROJECT_ROOT = Path(__file__).resolve().parent
repo = DataRepo(PROJECT_ROOT / "data")
engine = RomeEngine(repo)
encoder = RomeStateEncoder()
brain = RomeValueBrainV2()

model_path = PROJECT_ROOT / "models" / "value_brain_40d_v5.pth"
brain.load_state_dict(torch.load(model_path, map_location="cpu", weights_only=True))
brain.eval()
print("✅ V5 真神已在 CPU 就绪，等待信徒召唤...")

# --- 定义通信数据包 ---
class GamePayload(BaseModel):
    state: dict
    hand: list
    legal: list

@app.post("/ask_ai")
def ask_ai(payload: GamePayload):
    js_state = payload.state
    legal_acts = payload.legal
    
    if not legal_acts:
        return {"best_index": -1}

    # 1. 把 JS 的状态，完美翻译成 Python 的物理引擎状态
    py_state = engine.new_game() # 借个壳
    py_state.turn_count = js_state.get("turn", 0)
    py_state.invasions_resolved = js_state.get("inv", 0)
    py_state.culture = js_state.get("culture", 0)
    py_state.military = js_state.get("military", 0)
    py_state.industry = js_state.get("industry", 0)
    py_state.rome_occupied = js_state.get("rome", True)
    
    # 解析城市
    cities = js_state.get("cities", {})
    py_state.occupied_culture_regions = sum(1 for k, v in cities.items() if k.startswith('C') and v)
    py_state.occupied_industry_regions = sum(1 for k, v in cities.items() if k.startswith('I') and v)
    
    py_state.built_buildings = set(js_state.get("built", []))
    py_state.monument_progress = js_state.get("mono", {})
    py_state.deck = js_state.get("deck", [])
    py_state.discard = js_state.get("discard", [])

    # 2. V5 开始看盘打分
    best_idx = -1
    max_value = -float('inf')

    for i, act in enumerate(legal_acts):
        next_state = copy.deepcopy(py_state)
        engine.apply_action(next_state, payload.hand, act)
        
        # 引擎兜底：走这步会死吗？
        if len(next_state.deck) == 0:
            engine.resolve_invasion_if_needed(next_state, policy_name="non_random")
            if next_state.game_lost:
                continue # 必死之局，绝对不选
                
        # V5 打分
        tensor = encoder.encode(next_state)
        with torch.no_grad():
            val = brain(tensor).item()
            
        if val > max_value:
            max_value = val
            best_idx = i
            
    # 如果全都会死（极端绝境），随便选一个
    if best_idx == -1:
        best_idx = 0

    return {"best_index": best_idx}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)