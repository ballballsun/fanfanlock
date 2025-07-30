import tkinter as tk
from tkinter import ttk, messagebox
import cv2
from PIL import Image, ImageTk
import threading
import time

class GameGUI:
    """翻翻樂遊戲輔助系統GUI"""
    
    def __init__(self, video_capture, card_detector, memory_logic):
        self.video_capture = video_capture
        self.card_detector = card_detector
        self.memory_logic = memory_logic
        
        self.root = tk.Tk()
        self.root.title("翻翻樂遊戲輔助系統")
        self.root.geometry("1200x800")
        
        self.is_running = False
        self.current_frame = None
        self.setup_complete = False
        
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
        
        # 校準按鈕
        self.calibrate_btn = ttk.Button(control_frame, text="開始校準", command=self.start_calibration)
        self.calibrate_btn.grid(row=1, column=0, columnspan=2, pady=5, sticky="ew")
        
        # 遊戲控制
        ttk.Separator(control_frame, orient='horizontal').grid(row=2, column=0, columnspan=2, sticky="ew", pady=10)
        
        self.start_btn = ttk.Button(control_frame, text="開始遊戲", command=self.start_game, state="disabled")
        self.start_btn.grid(row=3, column=0, pady=5, sticky="ew")
        
        self.reset_btn = ttk.Button(control_frame, text="重置遊戲", command=self.reset_game)
        self.reset_btn.grid(row=3, column=1, pady=5, sticky="ew")
        
        # 遊戲統計
        stats_frame = ttk.LabelFrame(control_frame, text="遊戲統計", padding="5")
        stats_frame.grid(row=4, column=0, columnspan=2, sticky="ew", pady=10)
        
        self.progress_var = tk.StringVar(value="進度: 0/12")
        ttk.Label(stats_frame, textvariable=self.progress_var).grid(row=0, column=0, sticky="w")
        
        self.time_var = tk.StringVar(value="時間: 00:00")
        ttk.Label(stats_frame, textvariable=self.time_var).grid(row=1, column=0, sticky="w")
        
        self.efficiency_var = tk.StringVar(value="效率: 0%")
        ttk.Label(stats_frame, textvariable=self.efficiency_var).grid(row=2, column=0, sticky="w")
        
        # 建議區域
        suggestions_frame = ttk.LabelFrame(control_frame, text="翻牌建議", padding="5")
        suggestions_frame.grid(row=5, column=0, columnspan=2, sticky="ew", pady=10)
        
        self.suggestions_text = tk.Text(suggestions_frame, height=8, width=30, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(suggestions_frame, orient="vertical", command=self.suggestions_text.yview)
        self.suggestions_text.configure(yscrollcommand=scrollbar.set)
        
        self.suggestions_text.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        
        suggestions_frame.columnconfigure(0, weight=1)
        suggestions_frame.rowconfigure(0, weight=1)
        
        # 右側視頻顯示
        video_frame = ttk.LabelFrame(main_frame, text="攝像頭畫面", padding="5")
        video_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        
        self.video_label = ttk.Label(video_frame)
        self.video_label.grid(row=0, column=0)
        
        # 校準提示
        self.calibration_label = ttk.Label(video_frame, text="", font=("Arial", 14), foreground="red")
        self.calibration_label.grid(row=1, column=0, pady=5)
        
    def start_video_thread(self):
        """啟動視頻處理線程"""
        self.is_running = True
        video_thread = threading.Thread(target=self.video_loop, daemon=True)
        video_thread.start()
        
    def video_loop(self):
        """視頻處理循環"""
        while self.is_running:
            try:
                frame = self.video_capture.get_frame()
                if frame is not None:
                    self.current_frame = frame.copy()
                    
                    # 顯示視頻
                    display_frame = cv2.resize(frame, (640, 480))
                    display_frame = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
                    
                    image = Image.fromarray(display_frame)
                    photo = ImageTk.PhotoImage(image)
                    
                    self.video_label.configure(image=photo)
                    self.video_label.image = photo
                    
                    # 如果遊戲開始，處理卡牌檢測
                    if self.setup_complete and hasattr(self, 'game_started') and self.game_started:
                        self.process_game_frame(frame)
                        
                time.sleep(0.033)  # 約30 FPS
                
            except Exception as e:
                print(f"視頻處理錯誤: {e}")
                time.sleep(0.1)
                
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
            # 檢測卡牌
            detected_cards = self.card_detector.detect_cards(frame)
            
            if 'error' not in detected_cards:
                # 更新遊戲邏輯
                game_state = self.memory_logic.update_game_state(detected_cards)
                
                # 獲取建議
                suggestions = self.memory_logic.get_suggestions(detected_cards)
                
                # 更新建議顯示
                self.root.after(0, lambda: self.update_suggestions(suggestions))
                
                # 檢查遊戲是否完成
                if game_state.get('game_complete', False):
                    self.root.after(0, self.game_complete)
                    
        except Exception as e:
            print(f"遊戲處理錯誤: {e}")
            
    def update_suggestions(self, suggestions):
        """更新建議顯示"""
        self.suggestions_text.delete(1.0, tk.END)
        
        if not suggestions:
            self.suggestions_text.insert(tk.END, "暫無建議\n\n請翻開更多卡牌以獲得建議")
        else:
            self.suggestions_text.insert(tk.END, "翻牌建議：\n\n")
            
            for i, suggestion in enumerate(suggestions, 1):
                text = f"{i}. 位置 {suggestion['position']}\n"
                text += f"   符號: {suggestion['symbol']}\n"
                text += f"   原因: {suggestion['reason']}\n"
                text += f"   信心度: {suggestion['confidence']:.0%}\n\n"
                
                self.suggestions_text.insert(tk.END, text)
                
    def update_stats_loop(self):
        """更新統計資訊循環"""
        while hasattr(self, 'game_started') and self.game_started:
            try:
                stats = self.memory_logic.get_statistics()
                
                # 更新進度
                progress_text = f"進度: {stats['matched_pairs']}/12"
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
        
        message = f"恭喜完成遊戲！\n\n"
        message += f"用時: {minutes:02d}:{seconds:02d}\n"
        message += f"效率: {stats['efficiency']*100:.1f}%\n"
        message += f"記憶卡牌數: {stats['cards_remembered']}"
        
        messagebox.showinfo("遊戲完成", message)
        
        self.status_label.configure(text="遊戲完成")
        self.start_btn.configure(text="開始新遊戲", state="normal")
        
    def reset_game(self):
        """重置遊戲"""
        self.game_started = False
        self.memory_logic.reset_game()
        self.status_label.configure(text="遊戲已重置")
        self.start_btn.configure(text="開始遊戲", state="normal" if self.setup_complete else "disabled")
        
        # 清空建議
        self.suggestions_text.delete(1.0, tk.END)
        self.suggestions_text.insert(tk.END, "遊戲重置\n\n等待開始新遊戲")
        
        # 重置統計
        self.progress_var.set("進度: 0/12")
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
