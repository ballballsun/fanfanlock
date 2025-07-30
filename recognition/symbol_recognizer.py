import cv2
import numpy as np
from typing import Optional, Dict, List, Tuple
import os
from pathlib import Path

class SymbolRecognizer:
    """符號識別器 - 使用模板匹配識別翻翻樂符號，具備持久性學習功能"""
    
    def __init__(self, template_dir: str = "templates"):
        self.template_dir = template_dir
        self.templates = {}
        self.symbol_names = [
            'blue_bottle', 'pink_fish', 'demon_mask', 'green_mask',
            'red_mask', 'pastry', 'cake', 'galaxy', 'drink_can',
            'yellow_mask', 'blue_mask', 'red_bottle'
        ]
        self.match_threshold = 0.7
        self.load_templates()  # 初始化時自動載入所有已保存的模板

    def load_templates(self):
        """載入符號模板圖像，從指定模板目錄讀取所有模板文件"""
        template_path = Path(self.template_dir)
        self.templates.clear()
        
        if not template_path.exists():
            print(f"模板目錄 {self.template_dir} 不存在，將使用實時學習模式")
            return
        
        # 載入目錄中的所有 PNG 模板文件
        loaded_count = 0
        for file in template_path.glob('*.png'):
            symbol_name = file.stem
            template = cv2.imread(str(file))
            if template is not None:
                self.templates[symbol_name] = template
                loaded_count += 1
        
        print(f"已載入 {loaded_count} 個符號模板")

    def learn_symbol(self, symbol_image: np.ndarray, symbol_name: str):
        """學習新符號並將模板保存到檔案系統"""
        if symbol_image is not None and symbol_image.size > 0:
            # 調整圖像尺寸並加入記憶體模板
            resized_image = cv2.resize(symbol_image, (64, 64))
            self.templates[symbol_name] = resized_image
            
            # 確保模板目錄存在
            Path(self.template_dir).mkdir(parents=True, exist_ok=True)
            
            # 將新學習的符號保存為 PNG 文件
            save_path = Path(self.template_dir) / f"{symbol_name}.png"
            success = cv2.imwrite(str(save_path), resized_image)
            
            if success:
                print(f"✓ 已保存新符號模板：{save_path}")
            else:
                print(f"✗ 保存符號模板失敗：{save_path}")

    def extract_symbol_features(self, symbol_image: np.ndarray) -> Dict:
        """提取符號特徵"""
        # 轉換為HSV色彩空間
        hsv = cv2.cvtColor(symbol_image, cv2.COLOR_BGR2HSV)
        
        # 計算顏色直方圖
        hist_h = cv2.calcHist([hsv], [0], None, [180], [0, 180])
        hist_s = cv2.calcHist([hsv], [1], None, [256], [0, 256])
        hist_v = cv2.calcHist([hsv], [2], None, [256], [0, 256])
        
        # 計算形狀特徵
        gray = cv2.cvtColor(symbol_image, cv2.COLOR_BGR2GRAY)
        contours, _ = cv2.findContours(gray, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        shape_features = {}
        if contours:
            largest_contour = max(contours, key=cv2.contourArea)
            shape_features['area'] = cv2.contourArea(largest_contour)
            shape_features['perimeter'] = cv2.arcLength(largest_contour, True)
        
        return {
            'color_hist_h': hist_h,
            'color_hist_s': hist_s,
            'color_hist_v': hist_v,
            'shape_features': shape_features,
            'mean_color': np.mean(symbol_image, axis=(0,1))
        }

    def compare_features(self, features1: Dict, features2: Dict) -> float:
        """比較兩組特徵的相似度"""
        # 比較顏色直方圖
        hist_score = 0
        for hist_key in ['color_hist_h', 'color_hist_s', 'color_hist_v']:
            if hist_key in features1 and hist_key in features2:
                score = cv2.compareHist(features1[hist_key], features2[hist_key], cv2.HISTCMP_CORREL)
                hist_score += score
        hist_score /= 3
        
        # 比較平均顏色
        color_diff = np.linalg.norm(features1['mean_color'] - features2['mean_color'])
        color_score = max(0, 1 - color_diff / 255)
        
        # 綜合評分
        return (hist_score * 0.7 + color_score * 0.3)

    def recognize_symbol(self, symbol_image: np.ndarray) -> Optional[str]:
        """識別符號"""
        if symbol_image is None or symbol_image.size == 0:
            return None

        # 預處理圖像
        symbol_image = cv2.resize(symbol_image, (64, 64))

        # 如果有模板，使用模板匹配
        if self.templates:
            best_match = None
            best_score = 0
            
            for symbol_name, template in self.templates.items():
                template_resized = cv2.resize(template, (64, 64))
                result = cv2.matchTemplate(symbol_image, template_resized, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, _ = cv2.minMaxLoc(result)
                
                if max_val > best_score and max_val > self.match_threshold:
                    best_score = max_val
                    best_match = symbol_name
            
            return best_match

        # 如果沒有模板，返回特徵哈希作為識別符
        features = self.extract_symbol_features(symbol_image)
        symbol_hash = hash(str(features['mean_color']))
        return f"symbol_{abs(symbol_hash) % 1000}"
