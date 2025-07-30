"""
影像處理工具函式
"""
import cv2
import numpy as np

class ImageUtils:
    @staticmethod
    def resize_image(image, width=None, height=None):
        """調整圖像大小"""
        if width is None and height is None:
            return image
        
        h, w = image.shape[:2]
        
        if width is None:
            ratio = height / float(h)
            width = int(w * ratio)
        elif height is None:
            ratio = width / float(w)
            height = int(h * ratio)
        
        return cv2.resize(image, (width, height))
    
    @staticmethod
    def enhance_contrast(image, alpha=1.5, beta=0):
        """增強對比度"""
        return cv2.convertScaleAbs(image, alpha=alpha, beta=beta)
    
    @staticmethod
    def remove_noise(image, kernel_size=5):
        """去除噪聲"""
        kernel = np.ones((kernel_size, kernel_size), np.uint8)
        opening = cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel)
        closing = cv2.morphologyEx(opening, cv2.MORPH_CLOSE, kernel)
        return closing
    
    @staticmethod
    def calculate_distance(point1, point2):
        """計算兩點間距離"""
        return np.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)
    
    @staticmethod
    def get_dominant_color(image, k=4):
        """獲取圖像主要顏色"""
        # 重塑圖像數據
        data = image.reshape((-1, 3))
        data = np.float32(data)
        
        # 使用K-means聚類
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)
        _, labels, centers = cv2.kmeans(data, k, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
        
        # 獲取最主要的顏色
        dominant_color = centers[0]
        return dominant_color.astype(int)
