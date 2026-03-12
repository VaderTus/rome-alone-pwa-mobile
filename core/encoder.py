# core/encoder.py
import torch
import numpy as np

# 严格对齐您的 CSV 数据 ID
BUILDING_IDS = [
    "B_KaiXuanDiaoSu", "B_DiGuoYinShuiDao", "B_JunTuanYaoSai", 
    "B_DiGuoJinKuang", "B_YuanXingJingJiChang"
]

MONUMENT_IDS = [
    "M_WanShenMiao", "M_LuoMaDouShouChang", "M_DiGuoGuangChang",
    "M_HaDeLiangLingQin", "M_KaiXuanMen", "M_TuLaZhenShiChang"
]

# 卡牌 ID C01 到 C21
CARD_IDS = [f"C{str(i).zfill(2)}" for i in range(1, 22)]

class RomeStateEncoder:
    """
    将 GameState 物理状态转化为 40 维的神经网络输入张量 (Tensor)
    """
    def __init__(self):
        self.feature_dim = 40

    def encode(self, state) -> torch.Tensor:
        """
        输入: core.state.GameState 对象
        输出: 形状为 (40,) 的 torch.Tensor (全 float32，均归一化至 0~1 左右)
        """
        features = []

        # 1. 时间与生存红线 (2维)
        features.append(state.turn_count / 21.0) # 游戏进度
        features.append(state.invasions_resolved / 3.0) # 入侵进度

        # 2. 资源状态 (3维 - 除以最大值9进行归一化)
        features.append(state.culture / 9.0)
        features.append(state.military / 9.0)
        features.append(state.industry / 9.0)

        # 3. 领土状态 (3维)
        features.append(1.0 if state.rome_occupied else 0.0)
        features.append(state.occupied_culture_regions / 6.0)  # 假设极大多拿6个
        features.append(state.occupied_industry_regions / 6.0)

        # 4. 普通建筑 (5维 - One-hot)
        for bid in BUILDING_IDS:
            features.append(1.0 if bid in state.built_buildings else 0.0)

        # 5. 纪念物进度 (6维 - 除以2归一化，因为满进度是2个cube)
        for mid in MONUMENT_IDS:
            prog = state.monument_progress.get(mid, 0)
            features.append(prog / 2.0)

        # 6. 终极算牌雷达 (21维)
        # 只要这牌还在 state.deck 里（意味着未来可能抽到），就是 1，否则是 0
        deck_set = set(state.deck)
        for cid in CARD_IDS:
            features.append(1.0 if cid in deck_set else 0.0)

        # 转换为 PyTorch Tensor
        tensor = torch.tensor(features, dtype=torch.float32)
        return tensor

# ==========================================
# 独立测试模块：确保编码器能在您的环境中跑通
# ==========================================
if __name__ == "__main__":
    import sys
    from pathlib import Path
    
    # 动态将项目根目录加入 sys.path，防止找不到 core 模块
    PROJECT_ROOT = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(PROJECT_ROOT))
    
    try:
        from core.loader import DataRepo
        from core.engine import RomeEngine
        
        print("✅ 成功导入引擎与数据仓库！")
        repo = DataRepo(PROJECT_ROOT / "data")
        engine = RomeEngine(repo)
        
        # 创建一个新游戏状态
        state = engine.new_game()
        
        # 模拟玩了一步（人为修改状态测试）
        state.turn_count = 5
        state.culture = 4
        state.built_buildings.add("B_YuanXingJingJiChang")
        state.monument_progress["M_DiGuoGuangChang"] = 1
        state.deck.pop() # 假装抽走了一张牌
        
        # 测试编码器
        encoder = RomeStateEncoder()
        tensor = encoder.encode(state)
        
        print(f"\n📊 编码器输出维度: {tensor.shape}")
        print("📊 前 19 维 (基础属性):", tensor[:19].numpy().round(2))
        print("📊 后 21 维 (算牌雷达):", tensor[19:].numpy())
        print("\n🚀 第一步：赛博视神经测试通过！张量生成完美。")
        
    except Exception as e:
        print(f"❌ 测试失败，请检查环境: {e}")