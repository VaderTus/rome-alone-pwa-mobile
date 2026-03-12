def select_action(engine, state, hand, legal_actions):
    if not legal_actions:
        return {"card_id": hand[0], "mode": "top", "kind": "TopResource", "meta": {}}
    return engine.rng.choice(legal_actions)
