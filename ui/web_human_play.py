import streamlit as st
import json, copy, pandas as pd
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))

from core.loader import DataRepo
from core.engine import RomeEngine
from policies.registry import POLICIES

# 使用我们刚刚调优成功的最终版策略
COACH = POLICIES["mcts_distilled_final"]

st.set_page_config(page_title="Rome Alone AI Coach", layout="wide")
st.title("🏛 Rome Alone - AI 策略教练")

repo = DataRepo(ROOT / "data")
engine = RomeEngine(repo)

if "state" not in st.session_state:
    st.session_state.state = engine.new_game()
    st.session_state.trace = []
    st.session_state.hand = []

s = st.session_state.state

# 侧边栏状态
with st.sidebar:
    st.metric("当前得分", engine.score(s))
    st.write(f"回合: {s.turn_count} | 地区: {s.occupied_regions()}")
    if st.button("新游戏"):
        st.session_state.state = engine.new_game()
        st.session_state.trace = []
        st.rerun()

# 游戏结束
if s.game_lost or s.invasions_resolved >= 3:
    st.header("🏁 对局结束")
    st.subheader("AI 复盘建议")
    review = []
    for t in st.session_state.trace:
        # 重建状态进行 AI 评估
        ai_move = COACH(engine, t['before_obj'], t['hand'], t['legal'])
        is_match = (t['choice']['card_id'] == ai_move['card_id'] and t['choice']['mode'] == ai_move['mode'])
        review.append({
            "回合": t['turn'],
            "你的选择": f"{t['choice']['card_id']} ({t['choice']['mode']})",
            "AI 建议": f"{ai_move['card_id']} ({ai_move['mode']})",
            "匹配": "✅" if is_match else "❌"
        })
    st.table(pd.DataFrame(review))
    st.stop()

# 正常回合
if not st.session_state.hand:
    s.turn_count += 1
    st.session_state.hand = engine.draw_hand(s)
    st.session_state.legal = engine.legal_actions(s, st.session_state.hand)

hand = st.session_state.hand
legal = st.session_state.legal

# 获取 AI 建议
ai_sug = COACH(engine, s, hand, legal)

st.subheader("当前手牌 (黄色高亮为 AI 推荐)")
cols = st.columns(3)
for i, cid in enumerate(hand):
    card = repo.card_by_id[cid]
    with cols[i]:
        is_ai_card = (ai_sug['card_id'] == cid)
        color = "#fffde7" if is_ai_card else "#ffffff"
        with st.container():
            st.markdown(f"<div style='background:{color}; padding:10px; border-radius:5px; border:1px solid #ddd;'><b>{card['Card_Name']}</b></div>", unsafe_allow_html=True)
            # 按钮选择动作...
            # (此处省略具体按钮生成代码，保持与上一版逻辑一致)

# 执行确认与记录...
# (记录 trace 时务必保存原始 state 对象以供复盘)