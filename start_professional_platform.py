#!/usr/bin/env python3
"""
QuantMuse 专业股票分析平台启动器
一键启动完整版股票分析系统
"""

import subprocess
import sys
import os
import webbrowser
import time
import threading

def main():
    """启动专业股票分析平台"""
    print("🚀 正在启动 QuantMuse 专业股票分析平台...")
    print("📊 网站将在浏览器中自动打开: http://localhost:8502")
    print("⏹️  按 Ctrl+C 停止网站")
    print("🔬 专业版本 - 集成量化因子分析和预测判断")
    print("-" * 70)

    # 获取当前脚本目录
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # 使用专业版本
    dashboard_path = os.path.join(script_dir, "stock_professional.py")

    # 检查虚拟环境
    venv_path = os.path.join(script_dir, "venv", "bin", "activate")
    if os.path.exists(venv_path):
        python_exe = os.path.join(script_dir, "venv", "bin", "python")
    else:
        python_exe = sys.executable

    try:
        # 清理端口
        print("🧹 清理端口...")
        try:
            subprocess.run(["pkill", "-f", "streamlit"], capture_output=True)
            time.sleep(3)
        except:
            pass

        # 启动Streamlit应用
        print("✅ 正在启动专业分析平台...")

        # 构建命令 - 使用8502端口避免冲突
        cmd = [
            python_exe, "-m", "streamlit", "run", dashboard_path,
            "--server.port", "8502",
            "--server.address", "localhost",
            "--browser.gatherUsageStats", "false"
        ]

        # 启动进程
        process = subprocess.Popen(cmd, cwd=script_dir)

        # 等待服务器启动并打开浏览器
        def open_browser():
            time.sleep(8)  # 专业版需要更多加载时间
            try:
                webbrowser.open('http://localhost:8502')
                print("🌐 浏览器已自动打开")
            except:
                print("🌐 请手动打开浏览器访问: http://localhost:8502")

        browser_thread = threading.Thread(target=open_browser)
        browser_thread.daemon = True
        browser_thread.start()

        print("✅ 专业分析平台已启动!")
        print()
        print("🎯 专业版功能特色:")
        print("  📈 80+股票覆盖 (超大盘/大盘/中盘/小盘)")
        print("  🔬 6大类量化因子分析:")
        print("     • 动量因子 (短中长期动量、相对强度)")
        print("     • 技术因子 (RSI、MACD、布林带、均线)")
        print("     • 基本面因子 (PE、PB、ROE、财务质量)")
        print("     • 波动率因子 (历史波动、价格稳定性)")
        print("     • 成交量因子 (量价关系、成交量趋势)")
        print("     • 趋势因子 (趋势强度、支撑阻力)")
        print("  🎯 智能预测判断系统:")
        print("     • 综合评分 (0-100分)")
        print("     • 买入/持有/回避建议")
        print("     • 置信度评估")
        print("  📊 专业可视化:")
        print("     • 4层技术分析图表")
        print("     • 因子评分卡片")
        print("     • 基准指数对比")
        print("  🏭 按行业/市值分类选股")
        print()
        print("🔗 访问地址:")
        print("  本地: http://localhost:8502")
        print()
        print("⚠️  注意: 保持此终端窗口打开以运行网站")
        print("💡 如果浏览器显示加载中，请等待量化因子计算完成")

        # 等待进程结束
        process.wait()

    except KeyboardInterrupt:
        print("\n⏹️  专业分析平台已停止")
        if 'process' in locals():
            process.terminate()
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        print()
        print("💡 解决方案:")
        print("1. 确保已安装依赖:")
        print("   pip install streamlit plotly yfinance pandas numpy")
        print()
        print("2. 或者激活虚拟环境后安装:")
        print("   source venv/bin/activate")
        print("   pip install streamlit plotly yfinance pandas numpy")

if __name__ == "__main__":
    main()