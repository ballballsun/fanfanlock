import cv2
import time

def diagnose_camera():
    print("=== 攝像頭診斷 ===")
    
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("❌ 攝像頭無法開啟")
        return
    
    print("✅ 攝像頭開啟成功")
    
    # 檢查攝像頭屬性
    width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    print(f"解析度: {width} x {height}")
    print(f"FPS: {fps}")
    
    # 等待攝像頭初始化
    print("等待攝像頭初始化...")
    time.sleep(2)
    
    # 嘗試讀取多次
    success_count = 0
    for i in range(10):
        ret, frame = cap.read()
        if ret:
            success_count += 1
            if i == 0:
                print(f"✅ 成功讀取第一幀，大小: {frame.shape}")
        time.sleep(0.1)
    
    print(f"10次嘗試中成功 {success_count} 次")
    
    cap.release()

# 執行診斷
diagnose_camera()
