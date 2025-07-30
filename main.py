#!/usr/bin/env python3
"""
翻翻樂遊戲輔助系統主程式
適用於 Raspberry Pi 4 + 500萬畫素攝像頭
"""

import sys
import os
import signal
from camera.video_capture import VideoCapture
from recognition.card_detector import CardDetector
from logic.memory_logic import MemoryLogic
from ui.gui import GameGUI

def signal_handler(sig, frame):
    """處理中斷信號"""
    print("\n正在關閉程式...")
    sys.exit(0)

def main():
    """主程式入口"""
    print("翻翻樂遊戲輔助系統啟動中...")
    print("適用平台: Raspberry Pi 4")
    print("攝像頭: 500萬畫素")
    print("目標: 6x4 翻翻樂遊戲輔助")
    print("-" * 40)
    
    # 註冊信號處理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 初始化組件
    video_capture = None
    gui = None
    
    try:
        # 初始化視頻捕獲
        print("初始化攝像頭...")
        video_capture = VideoCapture(camera_id=0)  # Raspberry Pi 攝像頭通常是 0
        
        # 設置攝像頭參數（針對 Raspberry Pi 優化）
        video_capture.set_resolution(1280, 720)  # 設置適中解析度平衡品質和性能
        video_capture.set_fps(30)  # 設置幀率
        
        if not video_capture.is_opened():
            raise Exception("無法開啟攝像頭")
            
        print("✓ 攝像頭初始化成功")
        
        # 初始化卡牌檢測器
        print("初始化卡牌檢測器...")
        card_detector = CardDetector()
        
        # 載入符號模板（如果存在）
        template_dir = "templates"
        if os.path.exists(template_dir):
            card_detector.symbol_recognizer.load_templates(template_dir)
            print(f"✓ 載入符號模板: {template_dir}")
        else:
            print("⚠ 未找到符號模板，將使用實時學習模式")
            
        print("✓ 卡牌檢測器初始化成功")
        
        # 初始化記憶邏輯
        print("初始化遊戲邏輯...")
        memory_logic = MemoryLogic()
        print("✓ 遊戲邏輯初始化成功")
        
        # 初始化GUI
        print("啟動用戶介面...")
        gui = GameGUI(video_capture, card_detector, memory_logic)
        print("✓ 用戶介面啟動成功")
        
        print("\n系統準備就緒！")
        print("使用說明:")
        print("1. 點擊 '開始校準' 調整攝像頭位置")
        print("2. 根據提示調整距離和光線")
        print("3. 校準完成後點擊 '開始遊戲'")
        print("4. 系統將自動識別翻牌並提供建議")
        print("-" * 40)
        
        # 運行GUI
        gui.run()
        
    except KeyboardInterrupt:
        print("\n用戶中斷程式")
        
    except Exception as e:
        print(f"錯誤: {e}")
        return 1
        
    finally:
        # 清理資源
        print("清理資源中...")
        
        if gui:
            gui.close()
            
        if video_capture:
            video_capture.release()
            
        print("程式已關閉")
        
    return 0

if __name__ == "__main__":
    sys.exit(main())
