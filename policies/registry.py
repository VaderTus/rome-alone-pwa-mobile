# policies/registry.py

# 导入基准测试策略
import policies.random_policy as random_policy
import policies.mcts_policy as mcts_policy

# 导入我们当前最强的算牌启发式策略 (V65)
import policies.mcts_distilled_final as mcts_distilled_final

# 注册表字典：将命令行参数映射到对应的函数
POLICIES = {
    "random_policy": random_policy.select_action,
    "mcts_policy": mcts_policy.select_action,
    "mcts_distilled_final": mcts_distilled_final.select_action,
}

def get_policy_fn(name):
    """根据策略名称返回对应的 select_action 函数"""
    if name not in POLICIES:
        raise ValueError(f"未知策略: {name}, 可选列表: {list(POLICIES.keys())}")
    return POLICIES[name]