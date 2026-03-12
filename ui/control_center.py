# ui/control_center.py (V4.0 真神纪元)
import os
import subprocess
import webbrowser
from pathlib import Path

# 获取项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent.parent

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def deploy_to_github():
    print("\n" + "="*50)
    print("📦 [阶段 1] 正在扫描并添加修改文件...")
    subprocess.run(["git", "add", "."], cwd=PROJECT_ROOT)
    
    print("📝 [阶段 2] 正在提交版本 (V5 Neural God)...")
    subprocess.run(["git", "commit", "-m", "Auto-deploy: 部署 V5 机械神明与通信接口"], cwd=PROJECT_ROOT)
    
    print("🚀 [阶段 3] 正在推送到云端服务器...")
    res = subprocess.run(["git", "push"], cwd=PROJECT_ROOT)
    
    if res.returncode == 0:
        print("✅ 推送成功！正在呼叫浏览器打开部署监控台...")
        try:
            # 自动解析您的 GitHub 仓库地址
            repo_url = subprocess.check_output(["git", "config", "--get", "remote.origin.url"], cwd=PROJECT_ROOT).decode().strip()
            if repo_url.endswith(".git"): 
                repo_url = repo_url[:-4]
            if repo_url.startswith("git@github.com:"): 
                repo_url = repo_url.replace("git@github.com:", "https://github.com/")
            
            # 直接跳转到 GitHub Actions 页面查看部署进度
            actions_url = f"{repo_url}/actions"
            webbrowser.open(actions_url)
        except Exception as e:
            print("⚠️ 无法自动解析 GitHub 地址，请手动前往网页查看。")
    else:
        print("❌ 推送失败，请检查网络或 Git 登录状态。")

def start_api_server():
    print("\n⚡ 正在呼叫 V5 神明苏醒...")
    server_script = PROJECT_ROOT / "api_server.py"
    
    if os.name == 'nt':
        # Windows: 弹出一个独立的酷炫黑框运行服务器
        os.system(f'start "Rome V5 God Server" cmd /k "cd /d {PROJECT_ROOT} && python api_server.py"')
        print("✅ 服务器已在独立窗口启动！(关闭该黑框即可停止 AI)")
    else:
        # Mac/Linux: 提示手动启动
        print(f"⚠️ 请打开一个新的终端窗口，运行:\ncd {PROJECT_ROOT} && python api_server.py")

def open_local_pwa():
    pwa_path = PROJECT_ROOT / "pwa-mobile" / "index.html"
    print(f"\n📱 正在浏览器中加载本地前哨站: {pwa_path}")
    webbrowser.open(f"file://{pwa_path}")
    print("✅ 已打开。请确保您已经先启动了 [1] AI API 服务器！")

def main_menu():
    while True:
        clear_screen()
        print("🏛️  ROME ALONE LAB - 最高统帅部 v4.0 (真神纪元)")
        print("="*60)
        print("👑 当前主脑: V5 (Neural Intuition) | 盲打均分: 14.339")
        print("="*60)
        print("【工程落地区】")
        print("  1. ⚡ 启动 V5 云端军师服务器 (弹出独立后台)")
        print("  2. 📱 打开本地 PWA 网页版 (实机游玩连线测试)")
        print("  3. 🌐 一键推送 Web 版本至 GitHub 并查看进度")
        print("-" * 60)
        print("【实验室区】")
        print("  4. 🔬 运行 V5 行为解剖仪 (生成战术报告)")
        print("  5. 🌌 启动 Alpha 自动进化引擎 (挂机炼丹)")
        print("  9. 🧹 执行实验室大扫除 (一键归档旧数据)")
        print("="*60)
        print("  0. 拔掉电源 (退出)")
        print("="*60)
        
        c = input("长官，请下达指令: ")
        
        if c == '1':
            start_api_server()
        elif c == '2':
            open_local_pwa()
        elif c == '3':
            deploy_to_github()
        elif c == '4':
            subprocess.run(["python", str(PROJECT_ROOT / "scripts" / "analyze_v5_god.py")], cwd=PROJECT_ROOT)
        elif c == '5':
            subprocess.run(["python", str(PROJECT_ROOT / "scripts" / "auto_evolve_pipeline.py")], cwd=PROJECT_ROOT)
        elif c == '9':
            subprocess.run(["python", str(PROJECT_ROOT / "lab_cleanup_v2.py")], cwd=PROJECT_ROOT)
        elif c == '0':
            print("🔌 系统已关闭，祝您罗马武运昌隆。")
            break
        else:
            print("⚠️ 无效的指令。")
            
        input("\n[按下 回车键 返回主菜单...]")

if __name__ == "__main__":
    main_menu()