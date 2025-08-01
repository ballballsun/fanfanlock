import cv2
import numpy as np
from typing import Optional

class VideoCapture:
    """攝像頭影像擷取模組 - 使用OpenCV控制攝像頭"""
    
    def __init__(self, camera_id: int = 0):
        """
        初始化攝像頭
        
        Args:
            camera_id: 攝像頭ID，通常0為預設攝像頭
        """
        self.camera_id = camera_id
        self.cap = None
        self.is_initialized = False
        
        # 預設參數
        self.default_width = 1280
        self.default_height = 720
        self.default_fps = 30
        
        self.initialize_camera()
        
    def initialize_camera(self) -> bool:
        """初始化攝像頭連接"""
        try:
            self.cap = cv2.VideoCapture(self.camera_id)
            
            if not self.cap.isOpened():
                print(f"無法開啟攝像頭 {self.camera_id}")
                return False
                
            # 設置預設參數
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.default_width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.default_height)
            self.cap.set(cv2.CAP_PROP_FPS, self.default_fps)
            
            # 設置緩衝區大小，減少延遲
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            self.is_initialized = True
            print(f"攝像頭 {self.camera_id} 初始化成功")
            
            # 驗證設置
            actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            actual_fps = int(self.cap.get(cv2.CAP_PROP_FPS))
            
            print(f"實際解析度: {actual_width}x{actual_height}")
            print(f"實際幀率: {actual_fps} FPS")
            
            return True
            
        except Exception as e:
            print(f"攝像頭初始化錯誤: {e}")
            self.is_initialized = False
            return False
            
    def set_resolution(self, width: int, height: int) -> bool:
        """
        設置攝像頭解析度
        
        Args:
            width: 寬度
            height: 高度
            
        Returns:
            bool: 設置是否成功
        """
        if not self.is_opened():
            print("攝像頭未開啟，無法設置解析度")
            return False
            
        try:
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            
            # 驗證設置
            actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            if actual_width == width and actual_height == height:
                print(f"解析度設置成功: {width}x{height}")
                return True
            else:
                print(f"解析度設置部分成功: 目標 {width}x{height}, 實際 {actual_width}x{actual_height}")
                return False
                
        except Exception as e:
            print(f"設置解析度錯誤: {e}")
            return False
            
    def set_fps(self, fps: int) -> bool:
        """
        設置攝像頭幀率
        
        Args:
            fps: 目標幀率
            
        Returns:
            bool: 設置是否成功
        """
        if not self.is_opened():
            print("攝像頭未開啟，無法設置幀率")
            return False
            
        try:
            self.cap.set(cv2.CAP_PROP_FPS, fps)
            
            # 驗證設置
            actual_fps = int(self.cap.get(cv2.CAP_PROP_FPS))
            
            if actual_fps == fps:
                print(f"幀率設置成功: {fps} FPS")
                return True
            else:
                print(f"幀率設置部分成功: 目標 {fps} FPS, 實際 {actual_fps} FPS")
                return False
                
        except Exception as e:
            print(f"設置幀率錯誤: {e}")
            return False
            
    def is_opened(self) -> bool:
        """
        檢查攝像頭是否成功開啟
        
        Returns:
            bool: 攝像頭是否開啟
        """
        return self.cap is not None and self.cap.isOpened() and self.is_initialized
        
    def get_frame(self) -> Optional[np.ndarray]:
        """
        獲取一幀影像
        
        Returns:
            numpy.ndarray: 影像幀，如果失敗則返回None
        """
        if not self.is_opened():
            return None
            
        try:
            ret, frame = self.cap.read()
            
            if ret and frame is not None:
                return frame
            else:
                print("無法讀取攝像頭幀")
                return None
                
        except Exception as e:
            print(f"讀取幀錯誤: {e}")
            return None

    def digital_zoom(self, frame, scale):
        h, w = frame.shape[:2]
        center_x, center_y = w // 2, h // 2
        radius_x, radius_y = int(w // (2*scale)), int(h // (2*scale))
        min_x, max_x = center_x - radius_x, center_x + radius_x
        min_y, max_y = center_y - radius_y, center_y + radius_y
        cropped = frame[min_y:max_y, min_x:max_x]
        # 放大到原本size
        return cv2.resize(cropped, (w, h))
            
    def get_camera_info(self) -> dict:
        """
        獲取攝像頭資訊
        
        Returns:
            dict: 攝像頭參數資訊
        """
        if not self.is_opened():
            return {"error": "攝像頭未開啟"}
            
        try:
            info = {
                "camera_id": self.camera_id,
                "width": int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                "height": int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                "fps": int(self.cap.get(cv2.CAP_PROP_FPS)),
                "backend": self.cap.getBackendName(),
                "is_opened": self.is_opened()
            }
            return info
            
        except Exception as e:
            return {"error": f"獲取攝像頭資訊錯誤: {e}"}
            
    def release(self):
        """釋放攝像頭資源"""
        try:
            if self.cap is not None:
                self.cap.release()
                self.cap = None
                
            self.is_initialized = False
            print("攝像頭資源已釋放")
            
        except Exception as e:
            print(f"釋放攝像頭資源錯誤: {e}")
