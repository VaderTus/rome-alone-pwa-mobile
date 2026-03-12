# scripts/grow_decision_tree.py
import json
import pandas as pd
from pathlib import Path
from sklearn.tree import DecisionTreeClassifier, export_text

PROJECT_ROOT = Path(__file__).resolve().parents[1]
JSON_PATH = PROJECT_ROOT / "outputs" / "full_knowledge" / "full_mcts_data.json"

def grow_tree():
    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 1. 提取所有决策样本
    samples = []
    for case in data:
        if case['score'] < 16 or case['lost']: continue # 只跟高手学习
        
        for step in case['history']:
            samples.append({
                "turn": step['turn'],
                "c": step['res_before']['C'],
                "m": step['res_before']['M'],
                "i": step['res_before']['I'],
                "reg": step['reg_before'],
                "target_action": f"{step['mode']}_{step['action']}"
            })
    
    df = pd.DataFrame(samples)
    X = df.drop("target_action", axis=1)
    y = df["target_action"]

    # 2. 种一棵深度为 5 的决策树（提取最核心的 5 层逻辑分支）
    clf = DecisionTreeClassifier(max_depth=5, min_samples_leaf=20)
    clf.fit(X, y)

    # 3. 导出人类可读的“战术说明书”
    tree_rules = export_text(clf, feature_names=list(X.columns))
    
    print("\n" + "="*60)
    print("🌲 自动生成的《孤城罗马：神级逻辑决策树》")
    print("="*60)
    print(tree_rules)
    print("="*60)

if __name__ == "__main__":
    grow_tree()