import cv2

cap = cv2.VideoCapture(0)

# 方法1：使用 isOpened()
try:
    if cap.isOpened():
        print("攝像頭開啟成功")
        ret, frame = cap.read()
        if ret:
            print("成功讀取幀")
        else:
            print("無法讀取幀")
    else:
        print("攝像頭開啟失敗")
except AttributeError as e:
    print(f"方法不存在: {e}")

cap.release()
