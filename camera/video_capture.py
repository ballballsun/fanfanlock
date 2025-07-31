import numpy as np
from typing import Optional
from picamera2 import Picamera2
import time

class VideoCapture:
    """攝像頭影像擷取模組 - 使用Picamera2控制Raspberry Pi攝像頭"""
    
    def __init__(self, camera_id: int = 0):
        """
        初始化攝像頭
        
        Args:
            camera_id: 攝像頭ID (picamera2中通常為0，多攝像頭時可能需要調整)
        """
        self.camera_id = camera_id
        self.picam2 = None
        self.is_initialized = False
        
        # 預設參數
        self.default_width = 1280
        self.default_height = 720
        self.default_fps = 30
        
        self.initialize_camera()
        
    def initialize_camera(self) -> bool:
        """初始化攝像頭連接"""
        try:
            # 創建Picamera2實例
            self.picam2 = Picamera2(self.camera_id)
            
            # 獲取攝像頭預設配置
            config = self.picam2.create_still_configuration(
                main={"size": (self.default_width, self.default_height), "format": "RGB888"},
                controls={"FrameRate": self.default_fps}
            )
            
            # 應用配置
            self.picam2.configure(config)
            
            # 啟動攝像頭
            self.picam2.start()
            
            # 等待攝像頭穩定
            time.sleep(2)
            
            self.is_initialized = True
            print(f"攝像頭 {self.camera_id} 初始化成功")
            
            # 顯示實際配置資訊
            sensor_resolution = self.picam2.sensor_resolution
            print(f"感應器解析度: {sensor_resolution}")
            print(f"配置解析度: {self.default_width}x{self.default_height}")
            print(f"目標幀率: {self.default_fps} FPS")
            
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
            # 停止當前攝像頭
            self.picam2.stop()
            
            # 創建新配置
            config = self.picam2.create_still_configuration(
                main={"size": (width, height), "format": "RGB888"},
                controls={"FrameRate": self.default_fps}
            )
            
            # 應用新配置
            self.picam2.configure(config)
            self.picam2.start()
            
            # 等待穩定
            time.sleep(1)
            
            self.default_width = width
            self.default_height = height
            
            print(f"解析度設置成功: {width}x{height}")
            return True
                
        except Exception as e:
            print(f"設置解析度錯誤: {e}")
            # 嘗試恢復之前的配置
            try:
                config = self.picam2.create_still_configuration(
                    main={"size": (self.default_width, self.default_height), "format": "RGB888"},
                    controls={"FrameRate": self.default_fps}
                )
                self.picam2.configure(config)
                self.picam2.start()
            except:
                self.is_initialized = False
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
            # 停止當前攝像頭
            self.picam2.stop()
            
            # 創建新配置
            config = self.picam2.create_still_configuration(
                main={"size": (self.default_width, self.default_height), "format": "RGB888"},
                controls={"FrameRate": fps}
            )
            
            # 應用新配置
            self.picam2.configure(config)
            self.picam2.start()
            
            # 等待穩定
            time.sleep(1)
            
            self.default_fps = fps
            print(f"幀率設置成功: {fps} FPS")
            return True
                
        except Exception as e:
            print(f"設置幀率錯誤: {e}")
            # 嘗試恢復之前的配置
            try:
                config = self.picam2.create_still_configuration(
                    main={"size": (self.default_width, self.default_height), "format": "RGB888"},
                    controls={"FrameRate": self.default_fps}
                )
                self.picam2.configure(config)
                self.picam2.start()
            except:
                self.is_initialized = False
            return False
            
    def is_opened(self) -> bool:
        """
        檢查攝像頭是否成功開啟
        
        Returns:
            bool: 攝像頭是否開啟
        """
        return (self.picam2 is not None and 
                self.is_initialized and 
                self.picam2.started)
        
    def get_frame(self) -> Optional[np.ndarray]:
        """
        獲取一幀影像
        
        Returns:
            numpy.ndarray: 影像幀 (RGB格式)，如果失敗則返回None
        """
        if not self.is_opened():
            return None
            
        try:
            # 捕獲幀 (RGB格式)
            frame = self.picam2.capture_array()
            
            if frame is not None and frame.size > 0:
                return frame
            else:
                print("無法讀取攝像頭幀")
                return None
                
        except Exception as e:
            print(f"讀取幀錯誤: {e}")
            return None
            
    def get_camera_info(self) -> dict:
        """
        獲取攝像頭資訊
        
        Returns:
            dict: 攝像頭參數資訊
        """
        if not self.is_opened():
            return {"error": "攝像頭未開啟"}
            
        try:
            # 獲取攝像頭資訊
            sensor_modes = self.picam2.sensor_modes
            sensor_resolution = self.picam2.sensor_resolution
            
            info = {
                "camera_id": self.camera_id,
                "width": self.default_width,
                "height": self.default_height,
                "fps": self.default_fps,
                "sensor_resolution": sensor_resolution,
                "sensor_modes_count": len(sensor_modes),
                "is_opened": self.is_opened(),
                "started": self.picam2.started if self.picam2 else False
            }
            return info
            
        except Exception as e:
            return {"error": f"獲取攝像頭資訊錯誤: {e}"}
    
    def set_camera_controls(self, controls: dict) -> bool:
        """
        設置攝像頭控制參數
        
        Args:
            controls: 控制參數字典，例如 {"Brightness": 0.1, "Contrast": 1.2}
            
        Returns:
            bool: 設置是否成功
        """
        if not self.is_opened():
            print("攝像頭未開啟，無法設置控制參數")
            return False
            
        try:
            self.picam2.set_controls(controls)
            print(f"攝像頭控制參數設置成功: {controls}")
            return True
        except Exception as e:
            print(f"設置攝像頭控制參數錯誤: {e}")
            return False
    
    def auto_focus(self) -> bool:
        """
        觸發自動對焦 (如果攝像頭支援)
        
        Returns:
            bool: 操作是否成功
        """
        if not self.is_opened():
            print("攝像頭未開啟，無法執行自動對焦")
            return False
            
        try:
            # 嘗試設置自動對焦
            self.picam2.set_controls({"AfMode": 2, "AfTrigger": 0})
            time.sleep(0.5)  # 等待對焦完成
            print("自動對焦完成")
            return True
        except Exception as e:
            print(f"自動對焦錯誤 (可能不支援): {e}")
            return False
            
    def release(self):
        """釋放攝像頭資源"""
        try:
            if self.picam2 is not None:
                if self.picam2.started:
                    self.picam2.stop()
                self.picam2.close()
                self.picam2 = None
                
            self.is_initialized = False
            print("攝像頭資源已釋放")
            
        except Exception as e:
            print(f"釋放攝像頭資源錯誤: {e}")