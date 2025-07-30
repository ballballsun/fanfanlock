import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional
from utils.image_utils import ImageUtils
from recognition.symbol_recognizer import SymbolRecognizer

class CardDetector:
    """卡牌檢測器 - 檢測翻翻樂中的卡牌位置和狀態"""
    
    def __init__(self):
        self.image_utils = ImageUtils()
        self.symbol_recognizer = SymbolRecognizer()
        self.grid_size = (6, 4)  # 6列4行
        self.card_positions = []
        self.back_template = None
        self.setup_complete = False
        
    def calibrate_game_area(self, frame: np.ndarray) -> Dict:
        """校準遊戲區域和卡牌位置"""
        result = {
            'ready': False,
            'message': '',
            'grid_detected': False,
            'distance_ok': False,
            'lighting_ok': False
        }
        
        if frame is None:
            result['message'] = "無法獲取攝像頭畫面"
            return result
            
        # 檢查圖像品質
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # 檢查光線條件
        mean_brightness = np.mean(gray)
        if mean_brightness < 50:
            result['message'] = "光線太暗，請增加光線"
        elif mean_brightness > 200:
            result['message'] = "光線太亮，請減少光線或調整角度"
        else:
            result['lighting_ok'] = True
            
        # 檢測遊戲網格
        grid_detected, positions = self._detect_game_grid(frame)
        if grid_detected:
            result['grid_detected'] = True
            self.card_positions = positions
            
            # 檢查距離（基於卡牌大小）
            if positions:
                card_width = abs(positions[0][2] - positions[0][0])
                card_height = abs(positions[0][3] - positions[0][1])
                
                if card_width < 30 or card_height < 30:
                    result['message'] = "距離太遠，請靠近一些"
                elif card_width > 150 or card_height > 150:
                    result['message'] = "距離太近，請遠離一些"
                else:
                    result['distance_ok'] = True
        else:
            result['message'] = "無法檢測到6x4遊戲網格，請調整攝像頭位置"
            
        # 檢查是否所有條件都滿足
        if result['lighting_ok'] and result['grid_detected'] and result['distance_ok']:
            result['ready'] = True
            result['message'] = "系統準備就緒！"
            self.setup_complete = True
            
        return result
        
    def _detect_game_grid(self, frame: np.ndarray) -> Tuple[bool, List]:
        """檢測6x4遊戲網格"""
        print("=== 開始檢測遊戲網格 ===")
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        print(f"影像轉換為灰度圖，尺寸: {gray.shape}")
        
        # 使用邊緣檢測
        edges = cv2.Canny(gray, 50, 150)
        print("已完成 Canny 邊緣檢測 (閾值: 50-150)")
        
        # 尋找輪廓
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        print(f"找到 {len(contours)} 個輪廓")
        
        # 篩選矩形卡牌
        card_contours = []
        print("開始篩選矩形卡牌...")
        
        for i, contour in enumerate(contours):
            # 計算輪廓面積
            area = cv2.contourArea(contour)
            
            if area < 500:  # 太小的區域忽略
                print(f"  輪廓 {i}: 面積 {area:.1f} 太小，忽略")
                continue
            
            print(f"  輪廓 {i}: 面積 {area:.1f}")
            
            # 近似輪廓為多邊形
            epsilon = 0.02 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)
            
            print(f"    → 多邊形近似結果: {len(approx)} 個頂點")
            
            # 檢查是否為矩形（4個頂點）
            if len(approx) == 4:
                x, y, w, h = cv2.boundingRect(contour)
                aspect_ratio = w / h
                
                print(f"    → 邊界矩形: ({x}, {y}, {w}, {h}), 長寬比: {aspect_ratio:.2f}")
                
                # 檢查長寬比是否合理（卡牌通常接近正方形）
                if 0.7 < aspect_ratio < 1.5:
                    card_contours.append((x, y, x+w, y+h, area))
                    print(f"    → ✓ 符合條件，加入候選卡牌 (總數: {len(card_contours)})")
                else:
                    print(f"    → ✗ 長寬比不符合 (0.7 < {aspect_ratio:.2f} < 1.5)")
            else:
                print(f"    → ✗ 非矩形 ({len(approx)} 個頂點)")
        
        print(f"\n篩選完成，找到 {len(card_contours)} 個候選卡牌")
        
        # 檢查是否找到24張卡牌
        if len(card_contours) == 24:
            print("✓ 找到正確數量的卡牌 (24張)")
            
            # 按位置排序
            print("開始按位置排序...")
            card_contours.sort(key=lambda x: (x[1], x[0]))  # 先按y排序，再按x排序
            print("排序完成")
            
            # 驗證網格排列
            print("開始驗證網格排列...")
            if self._verify_grid_layout(card_contours):
                print("✓ 網格排列驗證通過")
                print("=== 網格檢測成功 ===\n")
                return True, card_contours
            else:
                print("✗ 網格排列驗證失敗")
        else:
            print(f"✗ 卡牌數量不正確 (需要24張，找到{len(card_contours)}張)")
        
        print("=== 網格檢測失敗 ===\n")
        return False, []

        
    def _verify_grid_layout(self, positions: List) -> bool:
        """驗證卡牌是否按6x4網格排列"""
        if len(positions) != 24:
            return False
            
        # 檢查每行是否有6張卡，共4行
        rows = [[] for _ in range(4)]
        
        # 按y座標分組
        sorted_by_y = sorted(positions, key=lambda x: x[1])
        
        for i, pos in enumerate(sorted_by_y):
            row_idx = i // 6
            if row_idx < 4:
                rows[row_idx].append(pos)
                
        # 檢查每行是否有6張卡
        for row in rows:
            if len(row) != 6:
                return False
                
        return True
        
    def detect_cards(self, frame: np.ndarray) -> Dict:
        """檢測所有卡牌狀態"""
        if not self.setup_complete:
            return {'error': '系統未校準，請先執行校準'}
            
        cards = {}
        
        for i, (x1, y1, x2, y2, _) in enumerate(self.card_positions):
            # 提取卡牌區域
            card_region = frame[y1:y2, x1:x2]
            
            if card_region.size == 0:
                continue
                
            # 判斷卡牌狀態（翻開或未翻開）
            is_flipped = self._is_card_flipped(card_region)
            
            card_info = {
                'position': (x1, y1, x2, y2),
                'flipped': is_flipped,
                'symbol': None,
                'grid_pos': (i % 6, i // 6)  # (col, row)
            }
            
            # 如果卡牌翻開，識別符號
            if is_flipped:
                symbol = self.symbol_recognizer.recognize_symbol(card_region)
                card_info['symbol'] = symbol
                
            cards[f'card_{i}'] = card_info
            
        return {'cards': cards, 'timestamp': cv2.getTickCount()}
        
    def _is_card_flipped(self, card_image: np.ndarray) -> bool:
        """判斷卡牌是否翻開"""
        if card_image.size == 0:
            return False
            
        # 計算圖像的平均顏色和方差
        mean_color = np.mean(card_image, axis=(0, 1))
        color_variance = np.var(card_image, axis=(0, 1))
        
        # 未翻開的卡牌通常顏色較單一，方差較小
        total_variance = np.sum(color_variance)
        
        # 根據方差判斷（需要根據實際情況調整閾值）
        return total_variance > 1000  # 翻開的卡牌顏色變化較大
        
    def update_back_template(self, back_image: np.ndarray):
        """更新卡牌背面模板"""
        if back_image is not None and back_image.size > 0:
            self.back_template = cv2.resize(back_image, (64, 64))
            
    def get_game_progress(self, cards: Dict) -> Dict:
        """獲取遊戲進度"""
        if 'cards' not in cards:
            return {'progress': 0, 'matched_pairs': 0, 'total_pairs': 12}
            
        flipped_cards = [card for card in cards['cards'].values() if card['flipped']]
        
        # 計算已配對的卡牌
        symbol_counts = {}
        for card in flipped_cards:
            if card['symbol']:
                symbol_counts[card['symbol']] = symbol_counts.get(card['symbol'], 0) + 1
                
        matched_pairs = sum(1 for count in symbol_counts.values() if count == 2) // 2
        progress = (matched_pairs / 12) * 100
        
        return {
            'progress': progress,
            'matched_pairs': matched_pairs,
            'total_pairs': 12,
            'flipped_count': len(flipped_cards),
            'game_complete': matched_pairs == 12
        }
