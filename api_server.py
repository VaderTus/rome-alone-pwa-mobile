# api_server.py
import sys
import copy
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn
import torch

from core.loader import DataRepo
from core.engine import RomeEngine
from core.encoder import RomeStateEncoder
from scripts.train_deep_value_net_v2 import RomeValueBrainV2

app = FastAPI(title="Rome V5 God API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)

PROJECT_ROOT = Path(__file__).resolve().parent
repo = DataRepo(PROJECT_ROOT / "data")
engine = RomeEngine(repo)
encoder = RomeStateEncoder()
brain = RomeValueBrainV2()

model_path = PROJECT_ROOT / "models" / "value_brain_40d_v5.pth"
brain.load_state_dict(torch.load(model_path, map_location="cpu", weights_only=True))
brain.eval()
print("✅ V5 真神已在 CPU 就绪，等待信徒召唤...")

class GamePayload(BaseModel):
    state: dict
    hand: list
    legal: list

@app.post("/ask_ai")
def ask_ai(payload: GamePayload):
    js_state = payload.state
    
    py_state = engine.new_game() 
    py_state.turn_count = js_state.get("turn", 0)
    py_state.invasions_resolved = js_state.get("inv", 0)
    py_state.culture = js_state.get("culture", 0)
    py_state.military = js_state.get("military", 0)
    py_state.industry = js_state.get("industry", 0)
    py_state.rome_occupied = js_state.get("rome", True)
    
    cities = js_state.get("cities", {})
    py_state.occupied_culture_regions = sum(1 for k, v in cities.items() if k.startswith('C') and v)
    py_state.occupied_industry_regions = sum(1 for k, v in cities.items() if k.startswith('I') and v)
    
    py_state.built_buildings = set(js_state.get("built", []))
    py_state.monument_progress = js_state.get("mono", {})
    py_state.deck = js_state.get("deck", [])
    py_state.discard = js_state.get("discard", [])

    real_legal_acts = engine.legal_actions(py_state, payload.hand)
    if not real_legal_acts:
        return {"best_card": None, "best_mode": None, "best_meta": {}}

    best_act = None
    max_value = -float('inf')

    for act in real_legal_acts:
        next_state = copy.deepcopy(py_state)
        engine.apply_action(next_state, payload.hand, act)
        if len(next_state.deck) == 0:
            engine.resolve_invasion_if_needed(next_state, policy_name="non_random")
            if next_state.game_lost:
                continue 
                
        tensor = encoder.encode(next_state)
        with torch.no_grad():
            val = brain(tensor).item()
            
        if val > max_value:
            max_value = val
            best_act = act
            
    if best_act is None:
        best_act = real_legal_acts[0]

    return {
        "best_card": best_act["card_id"],
        "best_mode": best_act["mode"],
        "best_meta": best_act.get("meta", {})
    }

# 🚀 【神级挂载】：把 PWA 文件夹直接当做网页根目录发出去！(这句必须写在 /ask_ai 路由的下面)
pwa_path = PROJECT_ROOT / "pwa-mobile"
app.mount("/", StaticFiles(directory=pwa_path, html=True), name="pwa")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)