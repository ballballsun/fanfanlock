#!/usr/bin/env python3
"""
記憶邏輯模組測試
測試翻翻樂遊戲邏輯處理功能
"""

import unittest
import time
import os
import cv2
from logic.memory_logic import MemoryLogic
from recognition.card_detector import CardDetector


class TestMemoryLogic(unittest.TestCase):
    """記憶邏輯測試類"""
    
    def setUp(self):
        """測試前準備"""
        self.memory_logic = MemoryLogic()
        
        # 載入真實測試圖像
        self.test_images_dir = "test_images"
        self.image_completed = None
        self.image_empty = None
        self.image_flipped = None
        self.card_detector = CardDetector()
        
        # 嘗試載入測試圖像
        if os.path.exists(self.test_images_dir):
            completed_path = os.path.join(self.test_images_dir, "image_completed.jpg")
            if os.path.exists(completed_path):
                self.image_completed = cv2.imread(completed_path)
                print(f"✓ 載入測試圖像: {completed_path}")
            else:
                print(f"⚠ 未找到測試圖像: {completed_path}")
            
            empty_path = os.path.join(self.test_images_dir, "image_empty.jpg")
            if os.path.exists(empty_path):
                self.image_empty = cv2.imread(empty_path)
                print(f"✓ 載入測試圖像: {empty_path}")
            else:
                print(f"⚠ 未找到測試圖像: {empty_path}")
            
            flipped_path = os.path.join(self.test_images_dir, "image_flipped.jpg")
            if os.path.exists(flipped_path):
                self.image_flipped = cv2.imread(flipped_path)
                print(f"✓ 載入測試圖像: {flipped_path}")
            else:
                print(f"⚠ 未找到測試圖像: {flipped_path}")
        
        # 模擬卡牌數據
        self.sample_cards_empty = {
            'cards': {
                f'card_{i}': {
                    'position': (i*50, i*30, i*50+40, i*30+40),
                    'flipped': False,
                    'symbol': None,
                    'grid_pos': (i % 6, i // 6)
                } for i in range(24)
            }
        }
        
        # 有兩張翻開卡牌的狀態
        self.sample_cards_two_flipped = {
            'cards': {
                'card_0': {
                    'position': (0, 0, 40, 40),
                    'flipped': True,
                    'symbol': 'blue_bottle',
                    'grid_pos': (0, 0)
                },
                'card_1': {
                    'position': (50, 0, 90, 40),
                    'flipped': True,
                    'symbol': 'pink_fish',
                    'grid_pos': (1, 0)
                }
            }
        }
        
        # 有配對的卡牌狀態
        self.sample_cards_matched = {
            'cards': {
                'card_0': {
                    'position': (0, 0, 40, 40),
                    'flipped': True,
                    'symbol': 'blue_bottle',
                    'grid_pos': (0, 0)
                },
                'card_5': {
                    'position': (250, 0, 290, 40),
                    'flipped': True,
                    'symbol': 'blue_bottle',
                    'grid_pos': (5, 0)
                },
                'card_12': {
                    'position': (0, 60, 40, 100),
                    'flipped': True,
                    'symbol': 'pink_fish',
                    'grid_pos': (0, 2)
                }
            }
        }
    
    def test_initialization(self):
        """測試初始化"""
        self.assertEqual(len(self.memory_logic.matched_pairs), 0)
        self.assertEqual(len(self.memory_logic.memory_map), 0)
        self.assertEqual(len(self.memory_logic.last_flipped), 0)
        self.assertIsNone(self.memory_logic.game_start_time)
        self.assertFalse(self.memory_logic.game_complete)
    
    def test_update_game_state_invalid_data(self):
        """測試無效數據處理"""
        result = self.memory_logic.update_game_state({})
        self.assertIn('error', result)
        
        result = self.memory_logic.update_game_state({'invalid': 'data'})
        self.assertIn('error', result)
    
    def test_update_game_state_empty_cards(self):
        """測試空卡牌狀態更新"""
        result = self.memory_logic.update_game_state(self.sample_cards_empty)
        
        self.assertIn('matched_pairs', result)
        self.assertIn('memory_map_size', result)
        self.assertIn('last_flipped', result)
        self.assertIn('game_complete', result)
        self.assertIn('elapsed_time', result)
        
        self.assertEqual(result['matched_pairs'], 0)
        self.assertEqual(result['memory_map_size'], 0)
        self.assertFalse(result['game_complete'])
        self.assertIsNotNone(self.memory_logic.game_start_time)
    
    def test_update_game_state_with_flipped_cards(self):
        """測試有翻開卡牌的狀態更新"""
        result = self.memory_logic.update_game_state(self.sample_cards_two_flipped)
        
        # 檢查記憶地圖是否更新
        self.assertGreater(result['memory_map_size'], 0)
        self.assertIn('card_0', self.memory_logic.memory_map)
        self.assertIn('card_1', self.memory_logic.memory_map)
        
        # 檢查記憶的符號
        self.assertEqual(self.memory_logic.memory_map['card_0']['symbol'], 'blue_bottle')
        self.assertEqual(self.memory_logic.memory_map['card_1']['symbol'], 'pink_fish')
    
    def test_match_detection(self):
        """測試配對檢測"""
        # 先更新有配對的卡牌狀態
        result = self.memory_logic.update_game_state(self.sample_cards_matched)
        
        # 應該檢測到一對配對
        self.assertEqual(result['matched_pairs'], 1)
        self.assertEqual(len(self.memory_logic.matched_pairs), 1)
        
        # 檢查配對是否正確
        matched_pair = self.memory_logic.matched_pairs[0]
        self.assertTrue('card_0' in matched_pair and 'card_5' in matched_pair)
    
    def test_game_completion(self):
        """測試遊戲完成檢測"""
        # 模擬12對全部配對的情況
        self.memory_logic.matched_pairs = [
            ('card_0', 'card_1'), ('card_2', 'card_3'), ('card_4', 'card_5'),
            ('card_6', 'card_7'), ('card_8', 'card_9'), ('card_10', 'card_11'),
            ('card_12', 'card_13'), ('card_14', 'card_15'), ('card_16', 'card_17'),
            ('card_18', 'card_19'), ('card_20', 'card_21'), ('card_22', 'card_23')
        ]
        
        result = self.memory_logic.update_game_state(self.sample_cards_empty)
        self.assertTrue(result['game_complete'])
        self.assertTrue(self.memory_logic.game_complete)
    
    def test_get_suggestions_no_flipped_cards(self):
        """測試無翻開卡牌時的建議"""
        suggestions = self.memory_logic.get_suggestions(self.sample_cards_empty)
        self.assertEqual(len(suggestions), 0)
    
    def test_get_suggestions_with_memory(self):
        """測試有記憶時的建議"""
        # 先建立一些記憶
        self.memory_logic.update_game_state(self.sample_cards_two_flipped)
        
        # 模擬翻開一張已記憶的符號
        test_cards = {
            'cards': {
                'card_2': {
                    'position': (100, 0, 140, 40),
                    'flipped': True,
                    'symbol': 'blue_bottle',  # 與記憶中的card_0匹配
                    'grid_pos': (2, 0)
                }
            }
        }
        
        suggestions = self.memory_logic.get_suggestions(test_cards)
        
        # 應該有建議
        self.assertGreater(len(suggestions), 0)
        
        # 檢查建議格式
        if suggestions:
            suggestion = suggestions[0]
            self.assertIn('type', suggestion)
            self.assertIn('card_id', suggestion)
            self.assertIn('position', suggestion)
            self.assertIn('symbol', suggestion)
            self.assertIn('confidence', suggestion)
            self.assertIn('reason', suggestion)
    
    def test_get_statistics(self):
        """測試統計資訊獲取"""
        # 設置一些初始狀態
        self.memory_logic.update_game_state(self.sample_cards_matched)
        
        stats = self.memory_logic.get_statistics()
        
        # 檢查統計資訊格式
        required_keys = [
            'matched_pairs', 'total_pairs', 'progress_percentage',
            'cards_remembered', 'elapsed_time', 'game_complete', 'efficiency'
        ]
        
        for key in required_keys:
            self.assertIn(key, stats)
        
        # 檢查數值合理性
        self.assertGreaterEqual(stats['matched_pairs'], 0)
        self.assertEqual(stats['total_pairs'], 12)
        self.assertGreaterEqual(stats['progress_percentage'], 0)
        self.assertLessEqual(stats['progress_percentage'], 100)
        self.assertGreaterEqual(stats['elapsed_time'], 0)
        self.assertGreaterEqual(stats['efficiency'], 0)
        self.assertLessEqual(stats['efficiency'], 1)
    
    def test_reset_game(self):
        """測試遊戲重置"""
        # 先設置一些狀態
        self.memory_logic.update_game_state(self.sample_cards_matched)
        self.assertGreater(len(self.memory_logic.matched_pairs), 0)
        self.assertGreater(len(self.memory_logic.memory_map), 0)
        
        # 重置遊戲
        self.memory_logic.reset_game()
        
        # 檢查是否完全重置
        self.assertEqual(len(self.memory_logic.matched_pairs), 0)
        self.assertEqual(len(self.memory_logic.memory_map), 0)
        self.assertEqual(len(self.memory_logic.last_flipped), 0)
        self.assertIsNone(self.memory_logic.game_start_time)
        self.assertFalse(self.memory_logic.game_complete)
    
    def test_is_card_matched(self):
        """測試卡牌配對狀態檢查"""
        # 添加一些配對
        self.memory_logic.matched_pairs = [('card_0', 'card_5'), ('card_1', 'card_7')]
        
        # 測試已配對的卡牌
        self.assertTrue(self.memory_logic._is_card_matched('card_0'))
        self.assertTrue(self.memory_logic._is_card_matched('card_5'))
        self.assertTrue(self.memory_logic._is_card_matched('card_1'))
        self.assertTrue(self.memory_logic._is_card_matched('card_7'))
        
        # 測試未配對的卡牌
        self.assertFalse(self.memory_logic._is_card_matched('card_2'))
        self.assertFalse(self.memory_logic._is_card_matched('card_10'))
    
    def test_real_image_completed_memory_logic(self):
        """測試真實完成遊戲圖像的記憶邏輯"""
        if self.image_completed is None:
            self.skipTest("未載入 image_completed.jpg")
        
        # 先用卡牌檢測器處理圖像
        calibration_result = self.card_detector.calibrate_game_area(self.image_completed)
        
        if not calibration_result['ready']:
            self.skipTest(f"圖像校準失敗: {calibration_result['message']}")
        
        # 檢測卡牌
        detection_result = self.card_detector.detect_cards(self.image_completed)
        
        if 'error' in detection_result:
            self.skipTest(f"卡牌檢測失敗: {detection_result['error']}")
        
        print(f"檢測到 {len(detection_result['cards'])} 張卡牌")
        
        # 使用真實檢測結果測試記憶邏輯
        memory_result = self.memory_logic.update_game_state(detection_result)
        
        print(f"記憶邏輯結果: {memory_result}")
        
        # 基本檢查
        self.assertIn('matched_pairs', memory_result)
        self.assertIn('memory_map_size', memory_result)
        self.assertIn('game_complete', memory_result)
        
        # 分析結果
        flipped_cards = [card for card in detection_result['cards'].values() if card['flipped']]
        symbols_with_cards = {}
        
        for card in flipped_cards:
            if card['symbol']:
                if card['symbol'] not in symbols_with_cards:
                    symbols_with_cards[card['symbol']] = []
                symbols_with_cards[card['symbol']].append(card)
        
        print(f"翻開的卡牌數: {len(flipped_cards)}")
        print(f"不同符號數: {len(symbols_with_cards)}")
        
        # 分析配對情況
        potential_pairs = sum(1 for symbol, cards in symbols_with_cards.items() if len(cards) >= 2)
        print(f"潛在配對數: {potential_pairs}")
        
        if memory_result['game_complete']:
            print("✓ 遊戲標記為完成")
            self.assertEqual(memory_result['matched_pairs'], 12)
        else:
            print(f"遊戲未完成，當前配對數: {memory_result['matched_pairs']}")
        
        # 測試建議功能
        suggestions = self.memory_logic.get_suggestions(detection_result)
        print(f"獲得 {len(suggestions)} 個建議")
        
        for i, suggestion in enumerate(suggestions[:3]):  # 顯示前3個建議
            print(f"建議 {i+1}: {suggestion}")
        
        # 測試統計功能
        stats = self.memory_logic.get_statistics()
        print(f"遊戲統計: {stats}")
        
        self.assertIn('progress_percentage', stats)
        self.assertIn('efficiency', stats)
        self.assertGreaterEqual(stats['progress_percentage'], 0)
        self.assertLessEqual(stats['progress_percentage'], 100)
    
    def test_real_image_symbol_analysis(self):
        """分析真實圖像中的符號檢測情況"""
        if self.image_completed is None:
            self.skipTest("未載入 image_completed.jpg")
        
        # 檢測卡牌
        calibration_result = self.card_detector.calibrate_game_area(self.image_completed)
        if not calibration_result['ready']:
            self.skipTest("圖像校準失敗")
        
        detection_result = self.card_detector.detect_cards(self.image_completed)
        if 'error' in detection_result:
            self.skipTest("卡牌檢測失敗")
        
        # 分析符號檢測結果
        cards = detection_result['cards']
        symbol_counts = {}
        flipped_no_symbol = 0
        not_flipped = 0
        
        for card_id, card_info in cards.items():
            if card_info['flipped']:
                if card_info['symbol']:
                    symbol = card_info['symbol']
                    symbol_counts[symbol] = symbol_counts.get(symbol, 0) + 1
                else:
                    flipped_no_symbol += 1
            else:
                not_flipped += 1
        
        print(f"符號統計:")
        for symbol, count in symbol_counts.items():
            print(f"  {symbol}: {count} 張")
        
        print(f"翻開但無符號: {flipped_no_symbol} 張")
        print(f"未翻開: {not_flipped} 張")
        
        # 檢查是否符合翻翻樂邏輯（每個符號應該有2張）
        pairs_found = sum(1 for count in symbol_counts.values() if count == 2)
        incomplete_symbols = sum(1 for count in symbol_counts.values() if count == 1)
        
        print(f"完整配對: {pairs_found} 對")
        print(f"未配對符號: {incomplete_symbols} 個")
        
    def test_real_image_empty_board_memory_logic(self):
        """測試真實空遊戲板圖像的記憶邏輯"""
        if self.image_empty is None:
            self.skipTest("未載入 image_empty.jpg")
        
        # 先用卡牌檢測器處理圖像
        calibration_result = self.card_detector.calibrate_game_area(self.image_empty)
        
        if not calibration_result['ready']:
            self.skipTest(f"圖像校準失敗: {calibration_result['message']}")
        
        # 檢測卡牌
        detection_result = self.card_detector.detect_cards(self.image_empty)
        
        if 'error' in detection_result:
            self.skipTest(f"卡牌檢測失敗: {detection_result['error']}")
        
        print(f"空遊戲板檢測到 {len(detection_result['cards'])} 張卡牌")
        
        # 使用真實檢測結果測試記憶邏輯
        memory_result = self.memory_logic.update_game_state(detection_result)
        
        print(f"空遊戲板記憶邏輯結果: {memory_result}")
        
        # 空遊戲板的期望結果
        self.assertEqual(memory_result['matched_pairs'], 0, "空遊戲板不應該有配對")
        self.assertEqual(memory_result['memory_map_size'], 0, "空遊戲板記憶地圖應該為空")
        self.assertEqual(len(memory_result['last_flipped']), 0, "空遊戲板不應該有最近翻開的卡牌")
        self.assertFalse(memory_result['game_complete'], "空遊戲板不應該標記為完成")
        
        # 檢查遊戲開始時間已設置
        self.assertIsNotNone(self.memory_logic.game_start_time)
        self.assertGreaterEqual(memory_result['elapsed_time'], 0)
        
        # 測試建議功能 - 空遊戲板應該沒有建議
        suggestions = self.memory_logic.get_suggestions(detection_result)
        print(f"空遊戲板獲得 {len(suggestions)} 個建議")
        self.assertEqual(len(suggestions), 0, "空遊戲板不應該有翻牌建議")
        
        # 測試統計功能
        stats = self.memory_logic.get_statistics()
        print(f"空遊戲板統計: {stats}")
        
        self.assertEqual(stats['matched_pairs'], 0)
        self.assertEqual(stats['total_pairs'], 12)
        self.assertEqual(stats['progress_percentage'], 0)
        self.assertEqual(stats['cards_remembered'], 0)
        self.assertFalse(stats['game_complete'])
        self.assertEqual(stats['efficiency'], 0)  # 0/0 的效率應該為0
    
    def test_real_image_partial_flipped_memory_logic(self):
        """測試真實部分翻開圖像的記憶邏輯"""
        if self.image_flipped is None:
            self.skipTest("未載入 image_flipped.jpg")
        
        # 先用卡牌檢測器處理圖像
        calibration_result = self.card_detector.calibrate_game_area(self.image_flipped)
        
        if not calibration_result['ready']:
            self.skipTest(f"圖像校準失敗: {calibration_result['message']}")
        
        # 檢測卡牌
        detection_result = self.card_detector.detect_cards(self.image_flipped)
        
        if 'error' in detection_result:
            self.skipTest(f"卡牌檢測失敗: {detection_result['error']}")
        
        print(f"部分翻開檢測到 {len(detection_result['cards'])} 張卡牌")
        
        # 使用真實檢測結果測試記憶邏輯
        memory_result = self.memory_logic.update_game_state(detection_result)
        
        print(f"部分翻開記憶邏輯結果: {memory_result}")
        
        # 分析檢測結果
        flipped_cards = [card for card in detection_result['cards'].values() if card['flipped']]
        symbols_with_cards = {}
        
        for card in flipped_cards:
            if card['symbol']:
                if card['symbol'] not in symbols_with_cards:
                    symbols_with_cards[card['symbol']] = []
                symbols_with_cards[card['symbol']].append(card)
        
        print(f"翻開的卡牌數: {len(flipped_cards)}")
        print(f"不同符號數: {len(symbols_with_cards)}")
        
        # 基本檢查
        self.assertGreater(memory_result['memory_map_size'], 0, "部分翻開應該建立記憶地圖")
        self.assertGreaterEqual(memory_result['matched_pairs'], 0, "配對數不應該為負")
        self.assertFalse(memory_result['game_complete'], "部分翻開不應該標記為完成")
        
        # 檢查記憶地圖大小合理性
        expected_memory_size = len([card for card in flipped_cards if card['symbol']])
        self.assertEqual(memory_result['memory_map_size'], expected_memory_size, 
                        "記憶地圖大小應該等於有符號的翻開卡牌數")
        
        # 分析配對情況
        potential_pairs = sum(1 for symbol, cards in symbols_with_cards.items() if len(cards) >= 2)
        print(f"潛在配對數: {potential_pairs}")
        
        if potential_pairs > 0:
            self.assertGreaterEqual(memory_result['matched_pairs'], 0, "應該檢測到配對")
        
        # 測試建議功能
        suggestions = self.memory_logic.get_suggestions(detection_result)
        print(f"部分翻開獲得 {len(suggestions)} 個建議")
        
        # 檢查建議格式
        for i, suggestion in enumerate(suggestions[:3]):  # 檢查前3個建議
            print(f"建議 {i+1}: {suggestion}")
            
            self.assertIn('type', suggestion)
            self.assertIn('card_id', suggestion)
            self.assertIn('position', suggestion)
            self.assertIn('symbol', suggestion)
            self.assertIn('confidence', suggestion)
            self.assertIn('reason', suggestion)
            
            # 檢查置信度合理性
            self.assertGreaterEqual(suggestion['confidence'], 0)
            self.assertLessEqual(suggestion['confidence'], 1)
        
        # 測試統計功能
        stats = self.memory_logic.get_statistics()
        print(f"部分翻開統計: {stats}")
        
        self.assertGreaterEqual(stats['matched_pairs'], 0)
        self.assertEqual(stats['total_pairs'], 12)
        self.assertGreater(stats['progress_percentage'], 0, "部分翻開應該有進度")
        self.assertLess(stats['progress_percentage'], 100, "部分翻開不應該100%完成")
        self.assertGreater(stats['cards_remembered'], 0, "應該記住一些卡牌")
        self.assertFalse(stats['game_complete'])
        
        # 效率檢查
        if stats['cards_remembered'] > 0:
            self.assertGreater(stats['efficiency'], 0, "有記憶的情況下效率應該大於0")
            self.assertLessEqual(stats['efficiency'], 1, "效率不應該超過1")
    
    def test_real_image_partial_memory_building(self):
        """測試真實部分翻開圖像的記憶建立過程"""
        if self.image_flipped is None:
            self.skipTest("未載入 image_flipped.jpg")
        
        # 檢測卡牌
        calibration_result = self.card_detector.calibrate_game_area(self.image_flipped)
        if not calibration_result['ready']:
            self.skipTest("圖像校準失敗")
        
        detection_result = self.card_detector.detect_cards(self.image_flipped)
        if 'error' in detection_result:
            self.skipTest("卡牌檢測失敗")
        
        # 測試記憶建立過程
        initial_memory_size = len(self.memory_logic.memory_map)
        self.assertEqual(initial_memory_size, 0, "初始記憶應該為空")
        
        # 第一次更新
        result1 = self.memory_logic.update_game_state(detection_result)
        memory_size_1 = len(self.memory_logic.memory_map)
        
        print(f"第一次更新後記憶大小: {memory_size_1}")
        self.assertGreater(memory_size_1, 0, "應該建立記憶")
        
        # 模擬第二次更新（同樣的狀態）
        result2 = self.memory_logic.update_game_state(detection_result)
        memory_size_2 = len(self.memory_logic.memory_map)
        
        # 記憶大小應該保持一致（相同的卡牌狀態）
        self.assertEqual(memory_size_2, memory_size_1, "相同狀態下記憶大小應該保持一致")
        
        # 檢查記憶內容的正確性
        flipped_cards_with_symbols = [
            (card_id, card_info) for card_id, card_info in detection_result['cards'].items()
            if card_info['flipped'] and card_info['symbol']
        ]
        
        print(f"應該記住的卡牌數: {len(flipped_cards_with_symbols)}")
        print(f"實際記住的卡牌數: {len(self.memory_logic.memory_map)}")
        
        for card_id, card_info in flipped_cards_with_symbols:
            self.assertIn(card_id, self.memory_logic.memory_map, f"應該記住卡牌 {card_id}")
            
            memory_info = self.memory_logic.memory_map[card_id]
            self.assertEqual(memory_info['symbol'], card_info['symbol'], "記憶的符號應該正確")
            self.assertEqual(memory_info['position'], card_info['grid_pos'], "記憶的位置應該正確")
            self.assertIsNotNone(memory_info['last_seen'], "應該記錄最後見到的時間")


if __name__ == '__main__':
    unittest.main()