# scripts/train_distill_alphazero_v2.py
import sys
import copy
import time
from pathlib import Path

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset, random_split

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.loader import DataRepo
from core.engine import RomeEngine
from core.encoder import RomeStateEncoder
from scripts.train_deep_value_net_v2 import RomeValueBrainV2

# =========================
# 配置：先跑“小但不至于没意义”
# =========================
HARVEST_GAMES = 400          # 深搜采集局数（400~800 都行；越大越稳但越慢）
NUM_FUTURES = 5              # 每步模拟的平行宇宙数
TRAIN_EPOCHS_MAX = 20
TRAIN_BATCH = 256
LR = 2e-4
WEIGHT_DECAY = 1e-4
EARLY_STOP_PATIENCE = 3

EVAL_GAMES_DEEP = 800        # 两步验收局数（建议 800~2000）
EVAL_GAMES_FAST = 800        # 单步对照局数（可同上）

BASE_MODEL = PROJECT_ROOT / "models" / "value_brain_40d_v5.pth"
OUT_MODEL = PROJECT_ROOT / "models" / "value_brain_40d_v6_distill_deep.pth"


def get_device():
    if torch.cuda.is_available():
        return torch.device("cuda")
    if torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


# =========================
# 核心：两步搜索，同时返回“师傅期望分”
# =========================
def deep_search_with_expected_value(engine, state, hand, legal_actions, brain, encoder, device, num_futures=5):
    """
    返回: (best_action, expected_value)
    expected_value = 该动作下，未来 num_futures 个平行宇宙里“下一回合最优一步后的局面价值”的平均
    这是师傅当下的“内心评估分”（比 final_score 噪音小很多）
    """
    if not legal_actions:
        return {"card_id": hand[0], "mode": "top", "kind": "TopResource", "meta": {}}, 0.0

    best_act = None
    best_ev = -float("inf")

    for act in legal_actions:
        s1 = copy.deepcopy(state)
        engine.apply_action(s1, hand, act)

        # 当前回合末可能触发入侵（这里做物理兜底）
        if len(s1.deck) == 0:
            engine.resolve_invasion_if_needed(s1, policy_name="non_random")
            if s1.game_lost:
                continue

        # 如果已经结束，期望值直接用终局分
        if s1.game_lost:
            continue
        if s1.invasions_resolved >= 3:
            ev = float(engine.score(s1))
            if ev > best_ev:
                best_ev = ev
                best_act = act
            continue

        # 第二步：采样未来发牌 -> 在未来手牌下选一步最优 -> 用 ValueNet 给叶子打分
        total = 0.0
        cnt = 0

        for _ in range(num_futures):
            sf = copy.deepcopy(s1)
            engine.rng.shuffle(sf.deck)

            sf.turn_count += 1
            h2 = engine.draw_hand(sf)
            if not h2:
                continue
            leg2 = engine.legal_actions(sf, h2)
            if not leg2:
                continue

            best_leaf = -float("inf")
            for a2 in leg2:
                leaf = copy.deepcopy(sf)
                engine.apply_action(leaf, h2, a2)

                if len(leaf.deck) == 0:
                    engine.resolve_invasion_if_needed(leaf, policy_name="non_random")
                    if leaf.game_lost:
                        continue

                x = encoder.encode(leaf).to(device)
                with torch.no_grad():
                    v = float(brain(x).item())
                if v > best_leaf:
                    best_leaf = v

            if best_leaf != -float("inf"):
                total += best_leaf
                cnt += 1

        ev = total / cnt if cnt > 0 else -1e9
        if ev > best_ev:
            best_ev = ev
            best_act = act

    if best_act is None:
        best_act = legal_actions[0]
        best_ev = 0.0
    return best_act, float(best_ev)


# =========================
# 单步策略（对照）
# =========================
def fast_policy_1step(engine, state, hand, legal_actions, brain, encoder, device):
    if not legal_actions:
        return {"card_id": hand[0], "mode": "top", "kind": "TopResource", "meta": {}}

    best_act = None
    best_v = -float("inf")
    for act in legal_actions:
        ns = copy.deepcopy(state)
        engine.apply_action(ns, hand, act)
        if len(ns.deck) == 0:
            engine.resolve_invasion_if_needed(ns, policy_name="non_random")
            if ns.game_lost:
                continue
        x = encoder.encode(ns).to(device)
        with torch.no_grad():
            v = float(brain(x).item())
        if v > best_v:
            best_v = v
            best_act = act

    return best_act if best_act is not None else legal_actions[0]


# =========================
# 采集：标签是“师傅期望分”（去噪）
# =========================
def harvest_dataset_distill_expected(num_games):
    repo = DataRepo(PROJECT_ROOT / "data")
    engine = RomeEngine(repo)
    encoder = RomeStateEncoder()

    device = get_device()
    brain = RomeValueBrainV2().to(device)
    brain.load_state_dict(torch.load(BASE_MODEL, map_location=device, weights_only=True))
    brain.eval()

    X, Y = [], []
    start = time.time()
    total_steps = 0

    for gi in range(num_games):
        s = engine.new_game(seed=int(time.time() * 1000) % 1_000_000 + gi)

        while (not s.game_lost) and s.invasions_resolved < 3:
            s.turn_count += 1
            hand = engine.draw_hand(s)
            if not hand:
                break
            legal = engine.legal_actions(s, hand)

            # 当前状态编码
            X.append(encoder.encode(s))

            # 读心术标签：师傅两步搜索得出的期望值
            _, ev = deep_search_with_expected_value(
                engine, s, hand, legal, brain, encoder, device, num_futures=NUM_FUTURES
            )
            Y.append(ev)

            # 为了走完对局，我们还需要真的执行师傅动作（保持数据分布一致）
            act, _ = deep_search_with_expected_value(
                engine, s, hand, legal, brain, encoder, device, num_futures=NUM_FUTURES
            )
            engine.apply_action(s, hand, act)
            engine.resolve_invasion_if_needed(s, policy_name="deep_auto")

            total_steps += 1

        if (gi + 1) % 50 == 0:
            elapsed = time.time() - start
            print(f"[HARVEST] {gi+1}/{num_games} games | steps={total_steps} | {elapsed/60:.1f} min")

    X = torch.stack(X)
    Y = torch.tensor(Y, dtype=torch.float32).unsqueeze(1)
    print(f"[HARVEST DONE] X={tuple(X.shape)}, Y={tuple(Y.shape)}")
    return X, Y


# =========================
# 训练：拟合期望值标签
# =========================
def train_value_net(X, Y):
    device = get_device()
    brain = RomeValueBrainV2().to(device)
    brain.load_state_dict(torch.load(BASE_MODEL, map_location=device, weights_only=True))

    dataset = TensorDataset(X, Y)
    train_size = int(0.8 * len(dataset))
    val_size = len(dataset) - train_size
    train_ds, val_ds = random_split(dataset, [train_size, val_size])

    train_loader = DataLoader(train_ds, batch_size=TRAIN_BATCH, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=TRAIN_BATCH, shuffle=False)

    opt = optim.Adam(brain.parameters(), lr=LR, weight_decay=WEIGHT_DECAY)
    sched = optim.lr_scheduler.ReduceLROnPlateau(opt, mode="min", patience=2, factor=0.5)
    loss_fn = nn.MSELoss()

    best_val = float("inf")
    bad = 0
    start = time.time()

    for ep in range(TRAIN_EPOCHS_MAX):
        brain.train()
        tr = 0.0
        for bx, by in train_loader:
            bx = bx.to(device)
            by = by.to(device)
            opt.zero_grad()
            pred = brain(bx)
            loss = loss_fn(pred, by)
            loss.backward()
            opt.step()
            tr += float(loss.item())
        tr /= max(1, len(train_loader))

        brain.eval()
        va = 0.0
        with torch.no_grad():
            for bx, by in val_loader:
                bx = bx.to(device)
                by = by.to(device)
                va += float(loss_fn(brain(bx), by).item())
        va /= max(1, len(val_loader))
        sched.step(va)

        mark = ""
        if va < best_val:
            best_val = va
            bad = 0
            torch.save(brain.state_dict(), OUT_MODEL)
            mark = "⭐ saved"
        else:
            bad += 1
            mark = f"({bad}/{EARLY_STOP_PATIENCE})"

        print(f"[TRAIN] ep={ep+1:02d} train={tr:.4f} val={va:.4f} {mark} | {time.time()-start:.1f}s")

        if bad >= EARLY_STOP_PATIENCE:
            break

    print(f"[TRAIN DONE] best_val={best_val:.4f} saved_to={OUT_MODEL}")


# =========================
# 验收：两步/单步都跑，主看两步
# =========================
def eval_policy(num_games, use_deep):
    repo = DataRepo(PROJECT_ROOT / "data")
    engine = RomeEngine(repo)
    encoder = RomeStateEncoder()

    device = get_device()
    brain = RomeValueBrainV2().to(device)
    brain.load_state_dict(torch.load(OUT_MODEL, map_location=device, weights_only=True))
    brain.eval()

    total = 0
    deaths = 0
    start = time.time()

    for i in range(num_games):
        s = engine.new_game(seed=i + 999999)

        while (not s.game_lost) and s.invasions_resolved < 3:
            s.turn_count += 1
            hand = engine.draw_hand(s)
            if not hand:
                break
            legal = engine.legal_actions(s, hand)

            if use_deep:
                act, _ = deep_search_with_expected_value(
                    engine, s, hand, legal, brain, encoder, device, num_futures=NUM_FUTURES
                )
            else:
                act = fast_policy_1step(engine, s, hand, legal, brain, encoder, device)

            engine.apply_action(s, hand, act)
            engine.resolve_invasion_if_needed(s, policy_name="eval")

        if s.game_lost:
            deaths += 1
            total += 0
        else:
            total += engine.score(s)

        if (i + 1) % 200 == 0:
            print(f"[EVAL] {i+1}/{num_games} | avg={total/(i+1):.3f} | deaths={deaths} | {time.time()-start:.1f}s")

    return total / num_games, deaths / num_games


def main():
    print("=== Distill Deep Expected-Value Labels (V5 -> V6) ===")
    print(f"harvest_games={HARVEST_GAMES}, futures={NUM_FUTURES}, eval_deep={EVAL_GAMES_DEEP}, eval_fast={EVAL_GAMES_FAST}")
    print(f"base_model={BASE_MODEL.name}")
    X, Y = harvest_dataset_distill_expected(HARVEST_GAMES)
    train_value_net(X, Y)

    avg_fast, death_fast = eval_policy(EVAL_GAMES_FAST, use_deep=False)
    avg_deep, death_deep = eval_policy(EVAL_GAMES_DEEP, use_deep=True)

    print("\n" + "=" * 60)
    print(f"[RESULT] V6 (distilled) FAST 1-step avg={avg_fast:.3f} death={death_fast*100:.2f}%")
    print(f"[RESULT] V6 (distilled) DEEP 2-step avg={avg_deep:.3f} death={death_deep*100:.2f}%")
    print("主看 DEEP 2-step，因为这才是你要的“深蓝本体战力”。")
    print("=" * 60)


if __name__ == "__main__":
    main()