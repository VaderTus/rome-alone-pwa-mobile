# scripts/find_absolute_limit_v2.py
from pathlib import Path
import sys
import copy

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.loader import DataRepo
from core.engine import RomeEngine

def calculate_theoretical_max():
    """
    专家级数学推演：
    在 21 个动作预算中，如何实现 GP 最大化？
    """
    print("🧠 正在执行《孤城罗马》数学模型上限推演...")
    
    # 预算分配模型：
    # 总动作数：21
    # 1. 必选得分项：
    #   - 6 次 Conquest (为了 7 地区 + 凯旋门倍率) -> 6 Actions
    #   - 2 次 Monument (凯旋门) -> 2 Actions
    #   - 2 次 Monument (万神庙 +4) -> 2 Actions
    #   - 2 次 Build (雕塑/引水道 +4) -> 2 Actions
    #   - 1 次 Monument (元老院 +2) -> 1 Action (假设已有一半)
    #   - 1 次 Monument (图拉真市场) -> 1 Action (假设已有一半)
    #   合计建设动作：14 次
    
    # 2. 剩余动作：7 次
    #   这 7 次必须完成：
    #   - 凑齐 3 种引擎的成本
    #   - 凑齐 6 次征服的军事 (约 21 点)
    #   - 凑齐 4 个纪念物的成本 (约 15-20 点)
    
    theoretical_limit = (
        7 + 7 + # 地区 + 凯旋门
        4 +     # 万神庙
        4 +     # 基础建筑
        2 +     # 元老院
        9       # 图拉真 (最大化)
    )
    
    print(f"📊 理想状态下的绝对数学天花板：{theoretical_limit} 分")
    print("⚠️  但在 21 动作约束下，资源的获取（Top动作）会占用大量名额，实际天花板远低于此。")

if __name__ == "__main__":
    calculate_theoretical_max()