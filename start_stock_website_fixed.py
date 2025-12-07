#!/usr/bin/env python3
"""
QuantMuse 股票分析网站启动器 (修复版)
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
    print("🔧 使用简化版本确保稳定运行")
    print("-" * 60)

    # 获取当前脚本目录
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # 使用简化版本
    dashboard_path = os.path.join(script_dir, "stock_simple.py")

    # 检查虚拟环境
    venv_path = os.path.join(script_dir, "venv", "bin", "activate")
    if os.path.exists(venv_path):
        # 在虚拟环境中运行
        python_exe = os.path.join(script_dir, "venv", "bin", "python")
    else:
        # 使用系统Python
        python_exe = sys.executable

    try:
        # 首先清理可能存在的端口占用
        print("🧹 清理端口...")
        try:
            subprocess.run(["pkill", "-f", "streamlit"], capture_output=True)
            time.sleep(2)
        except:
            pass

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
            time.sleep(5)  # 增加等待时间确保服务器启动
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
        print("📈 简化版功能特色:")
        print("  • 实时股票数据获取")
        print("  • 6只热门美股分析 (AAPL, MSFT, GOOGL, TSLA, NVDA, META)")
        print("  • 价格走势图表")
        print("  • 移动平均线分析")
        print("  • 成交量分析")
        print("  • 数据下载功能")
        print()
        print("🔗 访问地址:")
        print("  本地: http://localhost:8501")
        print()
        print("⚠️  注意: 保持此终端窗口打开以运行网站")
        print("💡 如果浏览器显示404，请等待几秒钟后刷新页面")

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
        print()
        print("3. 如果端口被占用，等待几秒钟后重试")

if __name__ == "__main__":
    main()