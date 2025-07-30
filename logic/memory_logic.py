from typing import Dict, List, Tuple, Optional
import time

class MemoryLogic:
    """翻翻樂遊戲邏輯處理器"""
    
    def __init__(self):
        self.game_state = {}
        self.matched_pairs = []
        self.memory_map = {}  # 記住已看過的卡牌
        self.last_flipped = []  # 最近翻開的卡牌
        self.game_start_time = None
        self.game_complete = False
        
    def update_game_state(self, detected_cards: Dict) -> Dict:
        """更新遊戲狀態"""
        if 'cards' not in detected_cards:
            return {'error': '無效的卡牌數據'}
            
        current_time = time.time()
        if self.game_start_time is None:
            self.game_start_time = current_time
            
        cards = detected_cards['cards']
        
        # 更新記憶地圖
        for card_id, card_info in cards.items():
            if card_info['flipped'] and card_info['symbol']:
                self.memory_map[card_id] = {
                    'symbol': card_info['symbol'],
                    'position': card_info['grid_pos'],
                    'last_seen': current_time
                }
                
        # 檢測新翻開的卡牌
        current_flipped = [card_id for card_id, card_info in cards.items() 
                          if card_info['flipped']]
        
        # 更新最近翻開的卡牌列表
        self.last_flipped = current_flipped[-2:] if len(current_flipped) >= 2 else current_flipped
        
        # 檢查配對
        self._check_for_matches(cards)
        
        # 檢查遊戲是否完成
        self.game_complete = len(self.matched_pairs) == 12
        
        return {
            'matched_pairs': len(self.matched_pairs),
            'memory_map_size': len(self.memory_map),
            'last_flipped': self.last_flipped,
            'game_complete': self.game_complete,
            'elapsed_time': current_time - self.game_start_time if self.game_start_time else 0
        }
        
    def _check_for_matches(self, cards: Dict):
        """檢查是否有新的配對"""
        # 找出當前翻開且未配對的卡牌
        flipped_unmatched = []
        for card_id, card_info in cards.items():
            if (card_info['flipped'] and 
                card_info['symbol'] and 
                not self._is_card_matched(card_id)):
                flipped_unmatched.append((card_id, card_info['symbol']))
                
        # 檢查是否有配對
        symbols_seen = {}
        for card_id, symbol in flipped_unmatched:
            if symbol in symbols_seen:
                # 找到配對
                pair = (symbols_seen[symbol], card_id)
                if pair not in self.matched_pairs and (pair[1], pair[0]) not in self.matched_pairs:
                    self.matched_pairs.append(pair)
            else:
                symbols_seen[symbol] = card_id
                
    def _is_card_matched(self, card_id: str) -> bool:
        """檢查卡牌是否已配對"""
        for pair in self.matched_pairs:
            if card_id in pair:
                return True
        return False
        
    def get_suggestions(self, current_cards: Dict) -> List[Dict]:
        """獲取翻牌建議"""
        if 'cards' not in current_cards:
            return []
            
        suggestions = []
        cards = current_cards['cards']
        
        # 找出當前翻開的卡牌
        currently_flipped = []
        for card_id, card_info in cards.items():
            if card_info['flipped'] and not self._is_card_matched(card_id):
                currently_flipped.append((card_id, card_info['symbol'], card_info['grid_pos']))
                
        # 如果有一張卡翻開，尋找其配對
        if len(currently_flipped) == 1:
            target_symbol = currently_flipped[0][1]
            
            # 在記憶中尋找配對
            for card_id, memory_info in self.memory_map.items():
                if (memory_info['symbol'] == target_symbol and 
                    card_id != currently_flipped[0][0] and
                    not self._is_card_matched(card_id)):
                    
                    suggestions.append({
                        'type': 'direct_match',
                        'card_id': card_id,
                        'position': memory_info['position'],
                        'symbol': target_symbol,
                        'confidence': 0.9,
                        'reason': f'記憶中的{target_symbol}配對'
                    })
                    
        # 如果沒有直接配對，提供記憶中的建議
        if not suggestions:
            # 尋找記憶中的配對機會
            symbol_positions = {}
            for card_id, memory_info in self.memory_map.items():
                if not self._is_card_matched(card_id):
                    symbol = memory_info['symbol']
                    if symbol not in symbol_positions:
                        symbol_positions[symbol] = []
                    symbol_positions[symbol].append({
                        'card_id': card_id,
                        'position': memory_info['position'],
                        'last_seen': memory_info['last_seen']
                    })
                    
            # 推薦有配對可能的符號
            for symbol, positions in symbol_positions.items():
                if len(positions) == 2:  # 記住了兩張相同符號的卡
                    for pos_info in positions:
                        suggestions.append({
                            'type': 'memory_pair',
                            'card_id': pos_info['card_id'],
                            'position': pos_info['position'],
                            'symbol': symbol,
                            'confidence': 0.7,
                            'reason': f'記憶中的{symbol}配對組合'
                        })
                        
        # 按置信度排序
        suggestions.sort(key=lambda x: x['confidence'], reverse=True)
        
        return suggestions[:3]  # 返回最多3個建議
        
    def get_statistics(self) -> Dict:
        """獲取遊戲統計資訊"""
        current_time = time.time()
        elapsed_time = current_time - self.game_start_time if self.game_start_time else 0
        
        return {
            'matched_pairs': len(self.matched_pairs),
            'total_pairs': 12,
            'progress_percentage': (len(self.matched_pairs) / 12) * 100,
            'cards_remembered': len(self.memory_map),
            'elapsed_time': elapsed_time,
            'game_complete': self.game_complete,
            'efficiency': len(self.matched_pairs) / max(len(self.memory_map), 1)
        }
        
    def reset_game(self):
        """重置遊戲狀態"""
        self.game_state = {}
        self.matched_pairs = []
        self.memory_map = {}
        self.last_flipped = []
        self.game_start_time = None
        self.game_complete = False
