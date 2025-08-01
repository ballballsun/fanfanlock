import tkinter as tk
from tkinter import ttk, messagebox
import cv2
from PIL import Image, ImageTk
import threading
import time
import numpy as np

class GameGUI:
    """翻翻樂遊戲輔助系統GUI - 適配Picamera2"""
    
    def __init__(self, video_capture, card_detector, memory_logic):
        self.video_capture = video_capture
        self.card_detector = card_detector
        self.memory_logic = memory_logic
        
        self.root = tk.Tk()
        self.root.title("翻翻樂遊戲輔助系統 - Picamera2版本")
        self.root.geometry("1600x1000")  # 增大視窗尺寸
        
        self.is_running = False
        self.current_frame = None
        self.setup_complete = False
        
        # 網格按鈕矩陣 (6x4)
        self.grid_buttons = []
        self.grid_colors = {
            'normal': '#f0f0f0',      # 正常狀態 - 淺灰色
            'flipped': '#87CEEB',     # 已翻開 - 天藍色
            'suggested': '#FFD700',   # 建議翻開 - 金色
            'matched': '#90EE90'      # 已配對 - 淺綠色
        }
        
        self.setup_ui()
        self.start_video_thread()
        
    def setup_ui(self):
        """設置用戶界面"""
        # 主框架
        main_frame = ttk.Frame(self.root)
        main_frame.grid(row=0, column=0, sticky="nsew")
        
        # 配置網格權重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(0, weight=1)
        
        # 左側控制面板
        control_frame = ttk.LabelFrame(main_frame, text="控制面板", padding="10")
        control_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        # 系統狀態
        self.status_label = ttk.Label(control_frame, text="系統啟動中...", font=("Arial", 12))
        self.status_label.grid(row=0, column=0, columnspan=2, pady=5)
        
        # 攝像頭控制按鈕
        camera_frame = ttk.LabelFrame(control_frame, text="攝像頭控制", padding="5")
        camera_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=5)
        
        camera_frame.columnconfigure(0, weight=1)
        camera_frame.columnconfigure(1, weight=1)
        
        # 校準按鈕
        self.calibrate_btn = ttk.Button(control_frame, text="開始校準", command=self.start_calibration)
        self.calibrate_btn.grid(row=2, column=0, columnspan=2, pady=5, sticky="ew")
        
        # 遊戲控制
        ttk.Separator(control_frame, orient='horizontal').grid(row=3, column=0, columnspan=2, sticky="ew", pady=10)
        
        self.start_btn = ttk.Button(control_frame, text="開始遊戲", command=self.start_game, state="disabled")
        self.start_btn.grid(row=4, column=0, pady=5, sticky="ew")
        
        self.reset_btn = ttk.Button(control_frame, text="重置遊戲", command=self.reset_game)
        self.reset_btn.grid(row=4, column=1, pady=5, sticky="ew")
        
        # 遊戲統計
        stats_frame = ttk.LabelFrame(control_frame, text="遊戲統計", padding="5")
        stats_frame.grid(row=5, column=0, columnspan=2, sticky="ew", pady=10)
        
        self.progress_var = tk.StringVar(value="進度: 0/12")
        ttk.Label(stats_frame, textvariable=self.progress_var, font=("Arial", 11)).grid(row=0, column=0, sticky="w")
        
        self.time_var = tk.StringVar(value="時間: 00:00")
        ttk.Label(stats_frame, textvariable=self.time_var, font=("Arial", 11)).grid(row=1, column=0, sticky="w")
        
        self.efficiency_var = tk.StringVar(value="效率: 0%")
        ttk.Label(stats_frame, textvariable=self.efficiency_var, font=("Arial", 11)).grid(row=2, column=0, sticky="w")
        
        # 視覺化建議區域 (6x4 網格)
        grid_frame = ttk.LabelFrame(control_frame, text="視覺化建議 (6x4 網格)", padding="5")
        grid_frame.grid(row=6, column=0, columnspan=2, sticky="ew", pady=10)
        
        self.setup_grid_display(grid_frame)
        
        # 文字建議區域 (加大一倍)
        suggestions_frame = ttk.LabelFrame(control_frame, text="詳細建議", padding="5")
        suggestions_frame.grid(row=7, column=0, columnspan=2, sticky="ew", pady=10)
        
        # 加大文字區域高度從8改為16
        self.suggestions_text = tk.Text(suggestions_frame, height=16, width=35, wrap=tk.WORD, font=("Arial", 10))
        scrollbar = ttk.Scrollbar(suggestions_frame, orient="vertical", command=self.suggestions_text.yview)
        self.suggestions_text.configure(yscrollcommand=scrollbar.set)
        
        self.suggestions_text.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        
        suggestions_frame.columnconfigure(0, weight=1)
        suggestions_frame.rowconfigure(0, weight=1)
        
        # 右側視頻顯示
        video_frame = ttk.LabelFrame(main_frame, text="攝像頭畫面 (Picamera2)", padding="5")
        video_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        
        self.video_label = ttk.Label(video_frame)
        self.video_label.grid(row=0, column=0)
        
        # 校準提示
        self.calibration_label = ttk.Label(video_frame, text="", font=("Arial", 14), foreground="red")
        self.calibration_label.grid(row=1, column=0, pady=5)
        
    def setup_grid_display(self, parent_frame):
        """設置6x4網格顯示"""
        # 創建網格容器
        grid_container = ttk.Frame(parent_frame)
        grid_container.grid(row=0, column=0, sticky="ew")
        
        # 創建6x4的按鈕網格
        self.grid_buttons = []
        for row in range(4):  # 4行
            button_row = []
            for col in range(6):  # 6列
                btn = tk.Label(
                    grid_container,
                    text=f"{row*6+col+1}",  # 顯示卡牌編號 1-24
                    width=4,
                    height=2,
                    bg=self.grid_colors['normal'],
                    font=("Arial", 8, "bold"),
                    relief="raised",
                    bd=2
                )
                btn.grid(row=row, column=col, padx=1, pady=1)
                button_row.append(btn)
            self.grid_buttons.append(button_row)
        
        # 添加圖例
        legend_frame = ttk.Frame(parent_frame)
        legend_frame.grid(row=1, column=0, sticky="ew", pady=5)
        
        # 圖例說明
        legends = [
            ("正常", self.grid_colors['normal']),
            ("已翻開", self.grid_colors['flipped']),
            ("建議", self.grid_colors['suggested']),
            ("已配對", self.grid_colors['matched'])
        ]
        
        for i, (text, color) in enumerate(legends):
            legend_btn = tk.Label(
                legend_frame,
                text=text,
                bg=color,
                width=6,
                height=1,
                font=("Arial", 8),
                #state="disabled",
                relief="flat"
            )
            legend_btn.grid(row=0, column=i, padx=2)
            
    def update_grid_display(self, cards_data, suggestions):
        """更新網格顯示"""
        if not cards_data or 'cards' not in cards_data:
            return
            
        cards = cards_data['cards']
        
        # 重置所有按鈕為正常狀態
        for row in range(4):
            for col in range(6):
                self.grid_buttons[row][col].configure(
                    bg=self.grid_colors['normal'],
                    relief="raised"
                )
        
        # 獲取建議位置
        suggested_positions = set()
        for suggestion in suggestions:
            if 'position' in suggestion:
                pos = suggestion['position']
                if isinstance(pos, tuple) and len(pos) >= 2:
                    col, row = pos[0], pos[1]
                    if 0 <= row < 4 and 0 <= col < 6:
                        suggested_positions.add((row, col))
        
        # 更新卡牌狀態
        matched_cards = set()
        if hasattr(self.memory_logic, 'matched_pairs'):
            for pair in self.memory_logic.matched_pairs:
                matched_cards.update(pair)
        
        for card_id, card_info in cards.items():
            if 'grid_pos' in card_info:
                col, row = card_info['grid_pos']
                if 0 <= row < 4 and 0 <= col < 6:
                    btn = self.grid_buttons[row][col]
                    
                    # 確定按鈕狀態和顏色
                    if card_id in matched_cards:
                        # 已配對
                        btn.configure(
                            bg=self.grid_colors['matched'],
                            relief="sunken"
                        )
                    elif card_info.get('flipped', False):
                        # 已翻開但未配對
                        btn.configure(
                            bg=self.grid_colors['flipped'],
                            relief="sunken"
                        )
                        # 顯示符號（如果有）
                        if card_info.get('symbol'):
                            symbol_text = card_info['symbol'][:3]  # 限制3個字符
                            btn.configure(text=symbol_text)
                    elif (row, col) in suggested_positions:
                        # 建議翻開
                        btn.configure(
                            bg=self.grid_colors['suggested'],
                            relief="raised"
                        )
                    
    def start_video_thread(self):
        """啟動視頻處理線程"""
        self.is_running = True
        video_thread = threading.Thread(target=self.video_loop, daemon=True)
        video_thread.start()
        
    def video_loop(self):
        """視頻處理循環 - 適配Picamera2的RGB格式"""
        while self.is_running:
            try:
                # 從picamera2獲取RGB格式的幀
                frame_rgb = self.video_capture.get_frame()
                if frame_rgb is not None:
                    # 保存當前幀（轉換為BGR格式供OpenCV處理）
                    self.current_frame = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
                    
                    # 顯示視頻（RGB格式直接用於Tkinter）
                    display_frame = cv2.resize(frame_rgb, (640, 480))
                    
                    image = Image.fromarray(display_frame)
                    photo = ImageTk.PhotoImage(image)
                    
                    self.video_label.configure(image=photo)
                    self.video_label.image = photo
                    
                    # 如果遊戲開始，處理卡牌檢測（使用BGR格式）
                    if self.setup_complete and hasattr(self, 'game_started') and self.game_started:
                        self.process_game_frame(self.current_frame)
                        
                time.sleep(0.033)  # 約30 FPS
                
            except Exception as e:
                print(f"視頻處理錯誤: {e}")
                time.sleep(0.1)
    
    def auto_focus(self):
        """觸發自動對焦"""
        if self.video_capture.auto_focus():
            self.status_label.configure(text="自動對焦完成")
        else:
            self.status_label.configure(text="自動對焦失敗或不支援")
    
    def adjust_brightness(self):
        """調整亮度"""
        try:
            # 創建亮度調整對話框
            brightness_window = tk.Toplevel(self.root)
            brightness_window.title("調整亮度")
            brightness_window.geometry("300x150")
            brightness_window.transient(self.root)
            brightness_window.grab_set()
            
            ttk.Label(brightness_window, text="亮度調整 (-1.0 到 1.0):").pack(pady=10)
            
            brightness_var = tk.DoubleVar(value=0.0)
            brightness_scale = ttk.Scale(brightness_window, from_=-1.0, to=1.0, 
                                       variable=brightness_var, orient=tk.HORIZONTAL)
            brightness_scale.pack(fill=tk.X, padx=20, pady=10)
            
            def apply_brightness():
                brightness_value = brightness_var.get()
                controls = {"Brightness": brightness_value}
                if self.video_capture.set_camera_controls(controls):
                    self.status_label.configure(text=f"亮度設置為: {brightness_value:.2f}")
                else:
                    self.status_label.configure(text="亮度調整失敗")
                brightness_window.destroy()
            
            ttk.Button(brightness_window, text="應用", command=apply_brightness).pack(pady=10)
            
        except Exception as e:
            print(f"亮度調整錯誤: {e}")
                
    def start_calibration(self):
        """開始校準"""
        if self.current_frame is None:
            messagebox.showerror("錯誤", "無法獲取攝像頭畫面")
            return
            
        def calibration_loop():
            while not self.setup_complete:
                if self.current_frame is not None:
                    result = self.card_detector.calibrate_game_area(self.current_frame)
                    
                    # 更新UI
                    self.root.after(0, lambda: self.update_calibration_status(result))
                    
                    if result['ready']:
                        self.setup_complete = True
                        self.root.after(0, self.calibration_complete)
                        break
                        
                time.sleep(0.5)
                
        calibration_thread = threading.Thread(target=calibration_loop, daemon=True)
        calibration_thread.start()
        
    def update_calibration_status(self, result):
        """更新校準狀態"""
        self.calibration_label.configure(text=result['message'])
        
        if result['ready']:
            self.calibration_label.configure(foreground="green")
        else:
            self.calibration_label.configure(foreground="red")
            
    def calibration_complete(self):
        """校準完成"""
        self.status_label.configure(text="校準完成，可以開始遊戲")
        self.start_btn.configure(state="normal")
        self.calibrate_btn.configure(text="重新校準")
        
    def start_game(self):
        """開始遊戲"""
        self.game_started = True
        self.memory_logic.reset_game()
        self.status_label.configure(text="遊戲進行中...")
        self.start_btn.configure(text="遊戲中", state="disabled")
        
        # 開始統計更新線程
        stats_thread = threading.Thread(target=self.update_stats_loop, daemon=True)
        stats_thread.start()
        
    def process_game_frame(self, frame):
        """處理遊戲幀"""
        try:
            # 檢測卡牌（使用BGR格式的幀）
            detected_cards = self.card_detector.detect_cards(frame)
            
            if 'error' not in detected_cards:
                # 更新遊戲邏輯
                game_state = self.memory_logic.update_game_state(detected_cards)
                
                # 獲取建議
                suggestions = self.memory_logic.get_suggestions(detected_cards)
                
                # 更新建議顯示（文字和網格）
                self.root.after(0, lambda: self.update_suggestions(suggestions))
                self.root.after(0, lambda: self.update_grid_display(detected_cards, suggestions))
                
                # 檢查遊戲是否完成
                if game_state.get('game_complete', False):
                    self.root.after(0, self.game_complete)
                    
        except Exception as e:
            print(f"遊戲處理錯誤: {e}")
            
    def update_suggestions(self, suggestions):
        """更新文字建議顯示"""
        self.suggestions_text.delete(1.0, tk.END)
        
        if not suggestions:
            self.suggestions_text.insert(tk.END, "📋 目前暫無建議\n\n")
            self.suggestions_text.insert(tk.END, "💡 請翻開更多卡牌以獲得智能建議\n\n")
            self.suggestions_text.insert(tk.END, "遊戲提示：\n")
            self.suggestions_text.insert(tk.END, "• 記住已看過的符號位置\n")
            self.suggestions_text.insert(tk.END, "• 優先找出容易記住的配對\n")
            self.suggestions_text.insert(tk.END, "• 觀察符號的顏色和形狀特徵")
        else:
            self.suggestions_text.insert(tk.END, "🎯 智能翻牌建議：\n")
            self.suggestions_text.insert(tk.END, "=" * 35 + "\n\n")
            
            for i, suggestion in enumerate(suggestions, 1):
                # 添加建議編號和位置
                pos_text = f"位置: 第{suggestion['position'][1]+1}行第{suggestion['position'][0]+1}列"
                self.suggestions_text.insert(tk.END, f"🔸 建議 {i}：{pos_text}\n")
                
                # 添加符號資訊
                symbol = suggestion.get('symbol', '未知')
                self.suggestions_text.insert(tk.END, f"   🔍 目標符號: {symbol}\n")
                
                # 添加建議原因
                reason = suggestion.get('reason', '無說明')
                self.suggestions_text.insert(tk.END, f"   💭 推薦原因: {reason}\n")
                
                # 添加信心度
                confidence = suggestion.get('confidence', 0)
                confidence_bar = "█" * int(confidence * 10) + "░" * (10 - int(confidence * 10))
                self.suggestions_text.insert(tk.END, f"   📊 信心度: {confidence:.0%} [{confidence_bar}]\n")
                
                # 添加分隔線
                if i < len(suggestions):
                    self.suggestions_text.insert(tk.END, "\n" + "-" * 35 + "\n\n")
                    
            # 添加策略提示
            self.suggestions_text.insert(tk.END, "\n\n💡 遊戲策略提示：\n")
            self.suggestions_text.insert(tk.END, "• 優先選擇高信心度的建議\n")
            self.suggestions_text.insert(tk.END, "• 記住每次翻開的新符號位置\n")
            self.suggestions_text.insert(tk.END, "• 利用視覺化網格輔助記憶")
                
    def update_stats_loop(self):
        """更新統計資訊循環"""
        while hasattr(self, 'game_started') and self.game_started:
            try:
                stats = self.memory_logic.get_statistics()
                
                # 更新進度
                progress_text = f"進度: {stats['matched_pairs']}/12 ({stats['progress_percentage']:.1f}%)"
                self.root.after(0, lambda: self.progress_var.set(progress_text))
                
                # 更新時間
                minutes = int(stats['elapsed_time'] // 60)
                seconds = int(stats['elapsed_time'] % 60)
                time_text = f"時間: {minutes:02d}:{seconds:02d}"
                self.root.after(0, lambda: self.time_var.set(time_text))
                
                # 更新效率
                efficiency = stats['efficiency'] * 100
                efficiency_text = f"效率: {efficiency:.1f}%"
                self.root.after(0, lambda: self.efficiency_var.set(efficiency_text))
                
                time.sleep(1)
                
            except Exception as e:
                print(f"統計更新錯誤: {e}")
                time.sleep(1)
                
    def game_complete(self):
        """遊戲完成"""
        self.game_started = False
        stats = self.memory_logic.get_statistics()
        
        minutes = int(stats['elapsed_time'] // 60)
        seconds = int(stats['elapsed_time'] % 60)
        
        message = f"🎉 恭喜完成遊戲！\n\n"
        message += f"⏱️ 用時: {minutes:02d}:{seconds:02d}\n"
        message += f"📈 效率: {stats['efficiency']*100:.1f}%\n"
        message += f"🧠 記憶卡牌數: {stats['cards_remembered']}\n\n"
        message += f"🏆 表現評價: "
        
        if stats['efficiency'] > 0.8:
            message += "優秀！記憶力驚人！"
        elif stats['efficiency'] > 0.6:
            message += "良好！繼續保持！"
        else:
            message += "不錯！多練習會更好！"
        
        messagebox.showinfo("遊戲完成", message)
        
        self.status_label.configure(text="🎮 遊戲完成")
        self.start_btn.configure(text="開始新遊戲", state="normal")
        
    def reset_game(self):
        """重置遊戲"""
        self.game_started = False
        self.memory_logic.reset_game()
        self.status_label.configure(text="🔄 遊戲已重置")
        self.start_btn.configure(text="開始遊戲", state="normal" if self.setup_complete else "disabled")
        
        # 清空建議
        self.suggestions_text.delete(1.0, tk.END)
        self.suggestions_text.insert(tk.END, "🎮 遊戲已重置\n\n")
        self.suggestions_text.insert(tk.END, "🚀 準備開始新的挑戰！\n\n")
        self.suggestions_text.insert(tk.END, "點擊 '開始遊戲' 按鈕開始")
        
        # 重置網格顯示
        for row in range(4):
            for col in range(6):
                self.grid_buttons[row][col].configure(
                    bg=self.grid_colors['normal'],
                    text=f"{row*6+col+1}",
                    relief="raised"
                )
        
        # 重置統計
        self.progress_var.set("進度: 0/12 (0.0%)")
        self.time_var.set("時間: 00:00") 
        self.efficiency_var.set("效率: 0%")
        
    def run(self):
        """運行GUI"""
        try:
            self.root.mainloop()
        finally:
            self.is_running = False
            
    def close(self):
        """關閉GUI"""
        self.is_running = False
        self.root.quit()
        self.root.destroy()