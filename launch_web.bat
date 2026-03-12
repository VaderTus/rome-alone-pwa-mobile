@echo off
cd /d %~dp0
python -m streamlit run .\ui\web_human_play.py
pause