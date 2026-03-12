from pathlib import Path
import random
import pandas as pd
from collections import defaultdict

ROOT = Path(__file__).resolve().parent.parent

# 核心牌 ID
CORE_CARDS = {
    "C05", # 圆形竞技场 (Amphi)
    "C14", "C15", # 帝国广场 (Senate)
    "C18", "C19", # 凯旋门 (Arc)
    "C10", "C11"  # 万神庙 (Pantheon)
}

# 简易卡牌库 (ID -> Cost)
CARD_COSTS = {
    "C01": {"c":1, "m":0, "i":2}, "C02": {"c":1, "m":0, "i":2}, "C03": {"c":0, "m":1, "i":2}, "C04": {"c":0, "m":0, "i":3}, "C05": {"c":1, "m":0, "i":2},
    "C06": {"c":0, "m":0, "i":0}, "C07": {"c":0, "m":0, "i":0}, "C08": {"c":0, "m":0, "i":0}, "C09": {"c":0, "m":0, "i":0}, # Action 无费用(征服除外)
    "C10": {"c":3, "m":0, "i":0}, "C11": {"c":3, "m":0, "i":1}, "C12": {"c":3, "m":0, "i":0}, "C13": {"c":0, "m":1, "i":2},
    "C14": {"c":3, "m":0, "i":0}, "C15": {"c":0, "m":0, "i":3}, "C16": {"c":0, "m":1, "i":2}, "C17": {"c":3, "m":0, "i":0},
    "C18": {"c":3, "m":0, "i":0}, "C19": {"c":0, "m":1, "i":2}, "C20": {"c":1, "m":0, "i":2}, "C21": {"c":3, "m":0, "i":0}
}

# 模拟初始资源 (假设第一回合)
INIT_RES = {"c": 1, "m": 1, "i": 1}

def can_afford(cost, res):
    return res["c"] >= cost["c"] and res["m"] >= cost["m"] and res["i"] >= cost["i"]

def analyze_one_hand(hand_ids, current_res):
    """分析一手牌(3张)的质量"""
    core_cnt = sum(1 for cid in hand_ids if cid in CORE_CARDS)
    
    playable_cnt = 0
    for cid in hand_ids:
        cost = CARD_COSTS.get(cid, {"c":0,"m":0,"i":0})
        # 简单判定：如果是征服/征收，首回合通常不视为“有效建设动作”
        if cid in ["C06","C07","C08","C09"]: 
            continue 
        if can_afford(cost, current_res):
            playable_cnt += 1
            
    return core_cnt, playable_cnt

def simulate_opening(rng):
    deck = list(CARD_COSTS.keys())
    rng.shuffle(deck)
    
    # 模拟前 3 回合
    res = INIT_RES.copy()
    
    conflict_events = 0 # 核心牌冲突次数
    stuck_events = 0    # 卡手次数(无建设牌可打)
    perfect_turns = 0   # 完美回合(恰好1张核心且买得起)
    
    for _ in range(3):
        hand = [deck.pop() for _ in range(3)]
        core_n, playable_n = analyze_one_hand(hand, res)
        
        if core_n >= 2:
            conflict_events += 1
        elif core_n == 1 and playable_n >= 1:
            perfect_turns += 1
            
        if playable_n == 0:
            stuck_events += 1
            
        # 简单模拟资源增长(假设拿了上半)
        # 这里简化处理，每回合平均获得 1.5 资源
        res["c"] += 1
        res["m"] += 1
        res["i"] += 1

    return {
        "has_conflict": conflict_events > 0,
        "is_stuck": stuck_events > 0,
        "is_perfect_flow": perfect_turns >= 2, # 3回合里有2回合是完美衔接
        "total_conflicts": conflict_events
    }

def main():
    rng = random.Random(42)
    N = 10_000
    stats = defaultdict(int)
    
    print(f"正在模拟 {N} 次开局 (前3回合)...")
    
    for _ in range(N):
        res = simulate_opening(rng)
        if res["has_conflict"]: stats["conflict"] += 1
        if res["is_stuck"]: stats["stuck"] += 1
        if res["is_perfect_flow"]: stats["perfect"] += 1
        
    print("\n=== 开局运势分析 (基于'一回合一动作'原则) ===")
    print(f"核心牌冲突率 (好牌扎堆来，被迫弃牌): {stats['conflict']/N*100:.2f}%")
    print(f"卡手率 (全是买不起的牌/废牌):       {stats['stuck']/N*100:.2f}%")
    print(f"完美节奏率 (核心牌错峰且买得起):     {stats['perfect']/N*100:.2f}%")

if __name__ == "__main__":
    main()