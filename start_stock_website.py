#!/usr/bin/env python3
"""
QuantMuse 股票分析网站启动器
一键启动股票数据可视化网站
"""

import subprocess
import sys
import os
import webbrowser
import time
import threading

def main():
    """启动股票分析网站"""
    print("🚀 正在启动 QuantMuse 股票分析网站...")
    print("📊 网站将在浏览器中自动打开: http://localhost:8501")
    print("⏹️  按 Ctrl+C 停止网站")
    print("-" * 60)

    # 获取当前脚本目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    dashboard_path = os.path.join(script_dir, "stock_dashboard.py")

    # 检查虚拟环境
    venv_path = os.path.join(script_dir, "venv", "bin", "activate")
    if os.path.exists(venv_path):
        # 在虚拟环境中运行
        python_exe = os.path.join(script_dir, "venv", "bin", "python")
    else:
        # 使用系统Python
        python_exe = sys.executable

    try:
        # 启动Streamlit应用
        print("✅ 正在启动网站服务器...")

        # 构建命令
        cmd = [
            python_exe, "-m", "streamlit", "run", dashboard_path,
            "--server.port", "8501",
            "--server.address", "localhost",
            "--browser.gatherUsageStats", "false"
        ]

        # 启动进程
        process = subprocess.Popen(cmd, cwd=script_dir)

        # 等待服务器启动
        def open_browser():
            time.sleep(3)  # 等待服务器启动
            try:
                webbrowser.open('http://localhost:8501')
                print("🌐 浏览器已自动打开")
            except:
                print("🌐 请手动打开浏览器访问: http://localhost:8501")

        # 在后台线程中打开浏览器
        browser_thread = threading.Thread(target=open_browser)
        browser_thread.daemon = True
        browser_thread.start()

        print("✅ 网站服务器已启动!")
        print("📈 功能特色:")
        print("  • 实时股票数据获取")
        print("  • 20+主流美股分析")
        print("  • 专业技术指标 (RSI, MACD, 布林带)")
        print("  • 多股票对比分析")
        print("  • 行业板块分析")
        print("  • 与基准指数对比")
        print("  • 交互式图表和统计分析")
        print()
        print("🔗 访问地址:")
        print("  本地: http://localhost:8501")
        print()
        print("⚠️  注意: 保持此终端窗口打开以运行网站")

        # 等待进程结束
        process.wait()

    except KeyboardInterrupt:
        print("\n⏹️  网站已停止")
        if 'process' in locals():
            process.terminate()
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        print()
        print("💡 解决方案:")
        print("1. 确保已安装依赖:")
        print("   pip install streamlit plotly yfinance")
        print()
        print("2. 或者激活虚拟环境后安装:")
        print("   source venv/bin/activate")
        print("   pip install streamlit plotly yfinance")

if __name__ == "__main__":
    main()