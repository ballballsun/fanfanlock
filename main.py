#!/usr/bin/env python3
"""
翻翻樂遊戲輔助系統主程式
適用於 Raspberry Pi 4 + 500萬畫素攝像頭 (使用 Picamera2)

系統需求:
- Raspberry Pi 4 (推薦 4GB RAM 或以上)
- Raspberry Pi Camera Module (V2/V3 或 HQ Camera)
- Python 3.9+
- Raspberry Pi OS (Bullseye 或更新版本)

安裝說明:
1. 更新系統:
   sudo apt update && sudo apt upgrade -y

2. 啟用攝像頭介面:
   sudo raspi-config
   選擇 Interface Options -> Camera -> Enable

3. 安裝 Picamera2 依賴:
   sudo apt install -y python3-picamera2 python3-opencv python3-pil python3-numpy

4. 安裝 Python 套件:
   pip3 install opencv-python pillow numpy tkinter

5. 重啟系統:
   sudo reboot

故障排除:
- 如果攝像頭無法初始化，請檢查攝像頭連接和 raspi-config 設置
- 如果出現權限錯誤，請確保用戶在 video 群組中: sudo usermod -a -G video $USER
- 如果 Picamera2 導入失敗，請確認使用的是 Raspberry Pi OS Bullseye 或更新版本
"""

import sys
import os
import signal
import subprocess
import importlib

def check_system_requirements():
    """檢查系統需求和依賴"""
    print("檢查系統需求...")
    
    # 檢查是否在 Raspberry Pi 上運行
    try:
        with open('/proc/cpuinfo', 'r') as f:
            cpuinfo = f.read()
        if 'Raspberry Pi' not in cpuinfo:
            print("⚠ 警告: 此程式專為 Raspberry Pi 設計")
    except:
        print("⚠ 警告: 無法確認系統類型")
    
    # 檢查 Python 版本
    if sys.version_info < (3, 9):
        print(f"❌ Python 版本過舊: {sys.version}")
        print("   需要 Python 3.9 或更新版本")
        return False
    else:
        print(f"✓ Python 版本: {sys.version.split()[0]}")
    
    # 檢查必要的套件
    required_packages = {
        'picamera2': 'Picamera2',
        'cv2': 'OpenCV',
        'PIL': 'Pillow',
        'numpy': 'NumPy',
        'tkinter': 'Tkinter'
    }
    
    missing_packages = []
    for package_name, display_name in required_packages.items():
        try:
            importlib.import_module(package_name)
            print(f"✓ {display_name}")
        except ImportError:
            print(f"❌ {display_name} 未安裝")
            missing_packages.append(package_name)
    
    if missing_packages:
        print("\n缺少必要套件，請執行以下安裝命令:")
        if 'picamera2' in missing_packages:
            print("sudo apt install python3-picamera2")
        if 'cv2' in missing_packages:
            print("sudo apt install python3-opencv")
        if 'PIL' in missing_packages:
            print("pip3 install pillow")
        if 'numpy' in missing_packages:
            print("sudo apt install python3-numpy")
        if 'tkinter' in missing_packages:
            print("sudo apt install python3-tk")
        return False
    
    # 檢查攝像頭權限
    try:
        import os
        import grp
        video_gid = grp.getgrnam('video').gr_gid
        if video_gid not in os.getgroups():
            print("⚠ 警告: 用戶不在 video 群組中")
            print("   執行: sudo usermod -a -G video $USER")
            print("   然後重新登入")
    except:
        pass
    
    return True

def check_camera_hardware():
    """檢查攝像頭硬體"""
    print("\n檢查攝像頭硬體...")
    
    try:
        # 檢查攝像頭設備文件
        camera_devices = []
        for i in range(4):  # 檢查 /dev/video0 到 /dev/video3
            device_path = f'/dev/video{i}'
            if os.path.exists(device_path):
                camera_devices.append(device_path)
        
        if camera_devices:
            print(f"✓ 找到攝像頭設備: {', '.join(camera_devices)}")
        else:
            print("❌ 未找到攝像頭設備")
            print("   請檢查:")
            print("   1. 攝像頭是否正確連接")
            print("   2. 是否已在 raspi-config 中啟用攝像頭")
            print("   3. 是否需要重啟系統")
            return False
            
        # 嘗試使用 Picamera2 檢測攝像頭
        try:
            from picamera2 import Picamera2
            picam2 = Picamera2()
            camera_info = picam2.camera_info
            print(f"✓ Picamera2 檢測成功")
            print(f"   攝像頭型號: {camera_info.get('Model', '未知')}")
            picam2.close()
        except Exception as e:
            print(f"❌ Picamera2 初始化失敗: {e}")
            print("   可能的解決方案:")
            print("   1. 確認攝像頭正確連接")
            print("   2. 執行: sudo raspi-config 啟用攝像頭")
            print("   3. 重啟系統: sudo reboot")
            print("   4. 檢查攝像頭排線是否損壞")
            return False
            
    except ImportError:
        print("❌ 無法導入 Picamera2")
        return False
    except Exception as e:
        print(f"❌ 攝像頭檢查失敗: {e}")
        return False
    
    return True

def signal_handler(sig, frame):
    """處理中斷信號"""
    print("\n正在關閉程式...")
    sys.exit(0)

def main():
    """主程式入口"""
    print("=" * 60)
    print("翻翻樂遊戲輔助系統")
    print("適用平台: Raspberry Pi 4 + Picamera2")
    print("攝像頭: 500萬畫素 Camera Module")
    print("目標: 6x4 翻翻樂遊戲輔助")
    print("=" * 60)
    
    # 註冊信號處理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 檢查系統需求
    if not check_system_requirements():
        print("\n❌ 系統需求檢查失敗，請安裝缺少的套件後重試")
        return 1
    
    # 檢查攝像頭硬體
    if not check_camera_hardware():
        print("\n❌ 攝像頭檢查失敗，請檢查硬體連接和配置")
        return 1
    
    print("\n" + "=" * 40)
    print("開始初始化系統組件...")
    print("=" * 40)
    
    # 初始化組件
    video_capture = None
    gui = None
    
    try:
        # 導入項目模組
        try:
            from camera.video_capture import VideoCapture
            from recognition.card_detector import CardDetector
            from logic.memory_logic import MemoryLogic
            from ui.gui import GameGUI
        except ImportError as e:
            print(f"❌ 導入項目模組失敗: {e}")
            print("   請確認所有項目文件都在正確位置")
            return 1
        
        # 初始化視頻捕獲
        print("初始化 Picamera2 攝像頭...")
        try:
            video_capture = VideoCapture(camera_id=0)
            
            if not video_capture.is_opened():
                raise Exception("攝像頭初始化失敗")
                
            # 設置攝像頭參數（針對 Raspberry Pi 4 優化）
            print("配置攝像頭參數...")
            
            # 設置適中解析度平衡品質和性能
            if not video_capture.set_resolution(1280, 720):
                print("⚠ 警告: 無法設置 1280x720 解析度，使用預設值")
            
            # 設置幀率
            if not video_capture.set_fps(30):
                print("⚠ 警告: 無法設置 30 FPS，使用預設值")
            
            # 顯示攝像頭資訊
            camera_info = video_capture.get_camera_info()
            print(f"✓ 攝像頭初始化成功")
            print(f"   解析度: {camera_info.get('width', 'N/A')}x{camera_info.get('height', 'N/A')}")
            print(f"   幀率: {camera_info.get('fps', 'N/A')} FPS")
            print(f"   感應器解析度: {camera_info.get('sensor_resolution', 'N/A')}")
            
        except Exception as e:
            print(f"❌ 攝像頭初始化錯誤: {e}")
            print("   故障排除步驟:")
            print("   1. 檢查攝像頭連接")
            print("   2. 確認已啟用攝像頭介面 (raspi-config)")
            print("   3. 重啟系統")
            print("   4. 檢查是否有其他程式正在使用攝像頭")
            return 1
        
        # 初始化卡牌檢測器
        print("\n初始化卡牌檢測器...")
        try:
            card_detector = CardDetector()
            
            # 載入符號模板（如果存在）
            template_dir = "templates"
            if os.path.exists(template_dir):
                card_detector.symbol_recognizer.load_templates()
                print(f"✓ 載入符號模板目錄: {template_dir}")
            else:
                print("⚠ 未找到符號模板目錄，將使用實時學習模式")
                print(f"   可創建 {template_dir} 目錄並放入符號模板圖片")
                
            print("✓ 卡牌檢測器初始化成功")
            
        except Exception as e:
            print(f"❌ 卡牌檢測器初始化錯誤: {e}")
            return 1
        
        # 初始化記憶邏輯
        print("\n初始化遊戲邏輯...")
        try:
            memory_logic = MemoryLogic()
            print("✓ 遊戲邏輯初始化成功")
        except Exception as e:
            print(f"❌ 遊戲邏輯初始化錯誤: {e}")
            return 1
        
        # 初始化GUI
        print("\n啟動用戶介面...")
        try:
            gui = GameGUI(video_capture, card_detector, memory_logic)
            print("✓ 用戶介面啟動成功")
        except Exception as e:
            print(f"❌ 用戶介面初始化錯誤: {e}")
            print("   可能的原因:")
            print("   1. 缺少 Tkinter 套件")
            print("   2. 顯示環境問題 (如果使用 SSH，需要 X11 轉發)")
            print("   3. 記憶體不足")
            return 1
        
        print("\n" + "=" * 50)
        print("🎮 系統準備就緒！")
        print("=" * 50)
        print("使用說明:")
        print("1. 點擊 '開始校準' 調整攝像頭位置")
        print("   - 確保能清楚看到 6x4 的卡牌網格")
        print("   - 調整距離使卡牌大小適中")
        print("   - 確保光線充足且均勻")
        print("2. 校準完成後點擊 '開始遊戲'")
        print("3. 系統將自動識別翻牌並提供建議")
        print("4. 使用 Ctrl+C 可隨時退出程式")
        print("-" * 50)
        
        # 運行GUI
        gui.run()
        
    except KeyboardInterrupt:
        print("\n👋 用戶中斷程式")
        
    except Exception as e:
        print(f"\n❌ 程式執行錯誤: {e}")
        print("請檢查錯誤訊息並確認系統配置")
        return 1
        
    finally:
        # 清理資源
        print("\n正在清理系統資源...")
        
        try:
            if gui:
                gui.close()
                print("✓ GUI 資源已釋放")
        except:
            pass
            
        try:
            if video_capture:
                video_capture.release()
                print("✓ 攝像頭資源已釋放")
        except:
            pass
            
        print("✓ 程式已安全關閉")
        
    return 0

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:
        print(f"程式啟動失敗: {e}")
        sys.exit(1)