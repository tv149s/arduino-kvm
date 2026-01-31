import tkinter as tk
from tkinter import ttk, messagebox
import serial
import time
import threading

# ==========================================
# 配置
# ==========================================
SERIAL_PORT = 'COM5'
BAUD_RATE = 115200

class StreamDeckApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Arduino Stream Deck Controller")
        self.root.geometry("600x400")
        
        self.ser = None
        self.connect_serial()
        
        # 样式设置
        style = ttk.Style()
        style.configure("Big.TButton", font=("Helvetica", 12, "bold"), padding=10)
        
        # 主框架
        main_frame = ttk.Frame(root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        ttk.Label(main_frame, text="🔴 直播控制面板 (Stream Deck)", font=("Helvetica", 16)).pack(pady=(0, 20))
        
        # 按钮网格区域
        grid_frame = ttk.Frame(main_frame)
        grid_frame.pack(fill=tk.BOTH, expand=True)
        
        # 定义按钮布局 (行, 列, 标签, 动作函数)
        buttons = [
            # 第一行：常用操作
            (0, 0, "复制\nCtrl+C", lambda: self.send_combo(['ctrl_l', 'c'])),
            (0, 1, "粘贴\nCtrl+V", lambda: self.send_combo(['ctrl_l', 'v'])),
            (0, 2, "全选\nCtrl+A", lambda: self.send_combo(['ctrl_l', 'a'])),
            (0, 3, "撤销\nCtrl+Z", lambda: self.send_combo(['ctrl_l', 'z'])),
            
            # 第二行：系统控制
            (1, 0, "任务管理器\nCtrl+Shift+Esc", lambda: self.send_combo(['ctrl_l', 'shift_l', 'esc'])),
            (1, 1, "锁定屏幕\nWin+L", lambda: self.send_combo(['win', 'l'])),
            (1, 2, "桌面\nWin+D", lambda: self.send_combo(['win', 'd'])),
            (1, 3, "运行\nWin+R", lambda: self.send_combo(['win', 'r'])),

            # 第三行：模拟 OBS 控制 (通常使用 F13-F24 或 复杂组合键)
            (2, 0, "切换场景 1\nCtrl+Alt+1", lambda: self.send_combo(['ctrl_l', 'alt_l', '1'])),
            (2, 1, "切换场景 2\nCtrl+Alt+2", lambda: self.send_combo(['ctrl_l', 'alt_l', '2'])),
            (2, 2, "静音麦克风\nCtrl+M", lambda: self.send_combo(['ctrl_l', 'm'])),
            (2, 3, "开始直播\nCtrl+Alt+S", lambda: self.send_combo(['ctrl_l', 'alt_l', 's'])),
            
            # 第四行：文本宏
            (3, 0, "输入\nHello", lambda: self.type_text("Hello World!")),
            (3, 1, "输入\nEmail", lambda: self.type_text("myname@example.com")),
            (3, 2, "Enter", lambda: self.send_key_press("enter")),
            (3, 3, "Backspace", lambda: self.send_key_press("backspace")),
        ]
        
        for r, c, text, cmd in buttons:
            btn = ttk.Button(grid_frame, text=text, command=cmd, style="Big.TButton")
            btn.grid(row=r, column=c, padx=5, pady=5, sticky="nsew")
            
        # 让网格自适应
        for i in range(4):
            grid_frame.columnconfigure(i, weight=1)
            grid_frame.rowconfigure(i, weight=1)

        # 底部状态栏
        self.status_var = tk.StringVar(value="就绪")
        ttk.Label(root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W).pack(side=tk.BOTTOM, fill=tk.X)

    def connect_serial(self):
        try:
            self.ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.1)
            print(f"✅ GUI已连接到 {SERIAL_PORT}")
        except Exception as e:
            messagebox.showerror("连接错误", f"无法打开串口 {SERIAL_PORT}:\n{e}\n\n请确保 mirror_input.py 未在运行！")
            self.root.destroy()

    def send_packet(self, header, data):
        if self.ser and self.ser.is_open:
            payload = f"{header}:{data}\n"
            self.ser.write(payload.encode('utf-8'))
            time.sleep(0.01) # 极短延迟防止丢包

    def send_key_press(self, key):
        """按下并松开单个键"""
        self.status_var.set(f"发送按键: {key}")
        self.send_packet("KD", key)
        time.sleep(0.05)
        self.send_packet("KU", key)

    def send_combo(self, keys):
        """发送组合键: 按下 A -> 按下 B ... -> 松开 B -> 松开 A"""
        self.status_var.set(f"发送组合: {'+'.join(keys)}")
        
        # 依次按下
        for k in keys:
            self.send_packet("KD", k)
            time.sleep(0.02)
            
        time.sleep(0.05) # 保持一小会儿
        
        # 反向依次松开
        for k in reversed(keys):
            self.send_packet("KU", k)
            time.sleep(0.02)

    def type_text(self, text):
        """输入一串文本"""
        self.status_var.set(f"输入文本: {text}")
        for char in text:
            # 简单处理大小写
            if char.isupper() or char in "!@#$%^&*()_+{}|:\"<>?":
                # 需要按 Shift 的情况 (简化处理)
                self.send_packet("KD", "shift")
                self.send_packet("KD", char.lower()) # 这里Arduino端只认小写字符
                self.send_packet("KU", char.lower())
                self.send_packet("KU", "shift")
            else:
                self.send_packet("KD", char)
                self.send_packet("KU", char)
            time.sleep(0.02)

    def on_closing(self):
        if self.ser and self.ser.is_open:
            # 安全释放所有键
            self.send_packet("REL", "0")
            self.ser.close()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = StreamDeckApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
