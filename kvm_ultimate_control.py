import tkinter as tk
from tkinter import ttk, messagebox
import serial
import serial.tools.list_ports
import time
import threading
from pynput import mouse, keyboard
import sys

# =============================================================================
# Arduino KVM Ultimate Control Panel
# Version: 4.1 (Force Overwrite)
# Features: GUI, Auto-COM, Mirror Mode, Macro Buttons, Ctrl+Alt+Del Support
# =============================================================================

class KVMApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Arduino KVM 终极控制台")
        self.root.geometry("800x650")
        
        self.ser = None
        self.is_mirroring = False
        self.mirror_thread = None
        self.mouse_listener = None
        self.key_listener = None
        self.stop_mirror_event = threading.Event()
        
        self.target_os = "WIN" # WIN or MAC

        self.setup_ui()
        self.auto_scan_ports()

    def setup_ui(self):
        # --- 顶部: 连接区域 ---
        top_frame = ttk.LabelFrame(self.root, text="设备连接", padding=10)
        top_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(top_frame, text="端口:").pack(side=tk.LEFT, padx=5)
        self.port_combo = ttk.Combobox(top_frame, width=30)
        self.port_combo.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(top_frame, text="刷新", command=self.auto_scan_ports).pack(side=tk.LEFT, padx=5)
        self.btn_connect = ttk.Button(top_frame, text="连接", command=self.toggle_connection)
        self.btn_connect.pack(side=tk.LEFT, padx=5)
        
        self.lbl_status = ttk.Label(top_frame, text="未连接", foreground="red")
        self.lbl_status.pack(side=tk.LEFT, padx=20)
        
        # --- 中部: 常用宏按钮 (Stream Deck 风格) ---
        deck_frame = ttk.LabelFrame(self.root, text="快捷宏 (点击即发送)", padding=10)
        deck_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 定义按钮布局 (Row, Col, Label, Command)
        macros = [
            # 系统管理
            (0, 0, "🔴 Ctrl+Alt+Del\n(慎用)", lambda: self.send_ctrl_alt_del()),
            (0, 1, "🔒 锁屏\nWin + L", lambda: self.send_combo(['win', 'l'])),
            (0, 2, "💻 桌面\nWin + D", lambda: self.send_combo(['win', 'd'])),
            (0, 3, "🏃 运行\nWin + R", lambda: self.send_combo(['win', 'r'])),
            
            # 常用编辑
            (1, 0, "📄 复制\nCtrl + C", lambda: self.send_combo(['ctrl_l', 'c'])),
            (1, 1, "📋 粘贴\nCtrl + V", lambda: self.send_combo(['ctrl_l', 'v'])),
            (1, 2, "✂️ 剪切\nCtrl + X", lambda: self.send_combo(['ctrl_l', 'x'])),
            (1, 3, "🎨 截图\nWin+Shift+S", lambda: self.send_combo(['win', 'shift_l', 's'])),
            
            # 多媒体 / 窗口
            (2, 0, "Tab 切换\nAlt + Tab", lambda: self.send_alt_tab_quick()),
            (2, 1, "关闭窗口\nAlt + F4", lambda: self.send_combo(['alt_l', 'f4'])),
            (2, 2, "任务管理\nCtrl+Shift+Esc", lambda: self.send_combo(['ctrl_l', 'shift_l', 'esc'])),
            (2, 3, "文件资源器\nWin + E", lambda: self.send_combo(['win', 'e'])),
        ]
        
        # 动态网格布局
        for r, c, txt, cmd in macros:
            btn = tk.Button(deck_frame, text=txt, command=cmd, height=3, width=15, 
                            font=("Microsoft YaHei", 10), bg="#f0f0f0", relief="raised")
            btn.grid(row=r, column=c, padx=5, pady=5, sticky="nsew")
            
        for i in range(4): deck_frame.columnconfigure(i, weight=1)
        
        # --- 底部: 镜像控制 ---
        mirror_frame = ttk.LabelFrame(self.root, text="沉浸式控制 (镜像模式)", padding=10)
        mirror_frame.pack(fill=tk.X, padx=10, pady=10)
        
        lbl_info = ttk.Label(mirror_frame, text="开启后，本机的鼠标键盘操作将直接传输给目标电脑。\n按住 [ESC] 键 1秒钟 可强制退出镜像模式。", 
                             foreground="gray", justify=tk.LEFT)
        lbl_info.pack(side=tk.TOP, pady=5)
        
        self.btn_mirror = ttk.Button(mirror_frame, text="🚀 启动镜像模式 (Windows)", command=self.start_mirror, state=tk.DISABLED)
        self.btn_mirror.pack(side=tk.TOP, fill=tk.X, pady=5)

    # ================= 串口逻辑 =================
    def auto_scan_ports(self):
        ports = serial.tools.list_ports.comports()
        port_list = [f"{p.device} - {p.description}" for p in ports]
        self.port_combo['values'] = port_list
        if port_list:
            self.port_combo.current(0)
            # 自动寻找可能是 CH340 的设备
            for i, p in enumerate(port_list):
                if "CH340" in p or "USB-SERIAL" in p or "COM5" in p:
                    self.port_combo.current(i)
                    break

    def toggle_connection(self):
        if self.ser and self.ser.is_open:
            self.ser.close()
            self.ser = None
            self.btn_connect.config(text="连接")
            self.lbl_status.config(text="未连接", foreground="red")
            self.btn_mirror.config(state=tk.DISABLED)
        else:
            try:
                selected = self.port_combo.get().split(' - ')[0]
                if not selected: return
                
                self.ser = serial.Serial(selected, 115200, timeout=0.1)
                self.btn_connect.config(text="断开")
                self.lbl_status.config(text=f"已连接: {selected}", foreground="green")
                self.btn_mirror.config(state=tk.NORMAL)
                
                # 发送复位信号
                self.send_packet("REL", "0")
                
            except Exception as e:
                messagebox.showerror("连接失败", str(e))

    def send_packet(self, header, data):
        if self.ser and self.ser.is_open:
            try:
                payload = f"{header}:{data}\n"
                self.ser.write(payload.encode('utf-8'))
            except:
                pass

    # ================= 宏命令逻辑 =================
    def send_ctrl_alt_del(self):
        """发送 Ctrl+Alt+Del 组合键"""
        messagebox.showinfo("提示", "即将发送 Ctrl+Alt+Del。\n这会触发目标电脑的安全菜单。")
        self.send_combo(['ctrl_l', 'alt_l', 'delete'])
        
    def send_combo(self, keys):
        """通用组合键发送器"""
        if not self.ser: return
        # 1. 依次按下
        for k in keys:
            self.send_packet("KD", k)
            time.sleep(0.02)
        # 2. 保持一下
        time.sleep(0.05)
        # 3. 反向松开
        for k in reversed(keys):
            self.send_packet("KU", k)
            time.sleep(0.02)

    def send_alt_tab_quick(self):
        """快速切换一次窗口"""
        self.send_packet("KD", "alt_l")
        time.sleep(0.05)
        self.send_packet("KD", "tab")
        time.sleep(0.05)
        self.send_packet("KU", "tab")
        time.sleep(0.05)
        self.send_packet("KU", "alt_l")

    # ================= 镜像逻辑 (复杂) =================
    def start_mirror(self):
        if self.is_mirroring: return
        
        self.is_mirroring = True
        self.stop_mirror_event.clear()
        
        # 禁用主界面，变为全屏遮罩提示
        self.overlay = tk.Toplevel(self.root)
        self.overlay.title("镜像模式运行中")
        self.overlay.attributes('-fullscreen', True)
        self.overlay.attributes('-alpha', 0.8) # 半透明
        self.overlay.configure(bg='black')
        # [Fix] 拦截窗口关闭事件，防止 Alt+F4 误关遮罩
        self.overlay.protocol("WM_DELETE_WINDOW", lambda: None)
        
        lbl = tk.Label(self.overlay, text="正在控制对方电脑\n\n按下 [ESC] 退出控制", 
                       font=("Helvetica", 30), fg="white", bg="black")
        lbl.pack(expand=True)
        self.overlay.update()
        
        # 启动监听线程
        self.mirror_thread = threading.Thread(target=self.mirror_worker)
        self.mirror_thread.daemon = True
        self.mirror_thread.start()

    def stop_mirror(self):
        self.is_mirroring = False
        self.stop_mirror_event.set()
        
        if self.mouse_listener: self.mouse_listener.stop()
        if self.key_listener: self.key_listener.stop()
        
        self.send_packet("REL", "0") # 安全复位
        
        if hasattr(self, 'overlay'):
            self.overlay.destroy()
            
        messagebox.showinfo("已恢复", "已退出镜像控制模式")

    def mirror_worker(self):
        # [Rollback] 恢复原始逻辑 (不强制锁定)
        # 放弃鼠标锁定尝试，恢复到最初最稳定的“绝对位移”计算方式
        # 虽然这会导致碰到屏幕边缘无法移动，但至少移动是准确且不漂移的
        
        self.mouse_ctl = mouse.Controller()
        # 记录初始位置
        self.prev_x, self.prev_y = self.mouse_ctl.position
        self.last_mouse_time = 0

        def on_move(x, y):
            if not self.is_mirroring: return
            
            # 计算位移 (普通版本)
            dx = int(x) - int(self.prev_x)
            dy = int(y) - int(self.prev_y)
            
            self.prev_x, self.prev_y = x, y
            
            # 如果没有位移，直接返回
            if dx == 0 and dy == 0: return

            # 简单的限流
            cur_time = time.time()
            if cur_time - self.last_mouse_time < 0.005: 
                return
            self.last_mouse_time = cur_time
            
            # Arduino 格式限制 (-127 ~ 127)
            dx_send = max(-127, min(127, dx))
            dy_send = max(-127, min(127, dy))
            
            if dx_send != 0 or dy_send != 0:
                self.send_packet("M", f"{dx_send},{dy_send}")
            
            # 这里没有任何 force position 的操作了
            # 纯粹的被动监听，最稳定

        def on_click(x, y, button, pressed):
            if not self.is_mirroring: return
            btn = "L" if button == mouse.Button.left else "R" if button == mouse.Button.right else "M"
            cmd = "MD" if pressed else "MU"
            self.send_packet(cmd, btn)

        def on_scroll(x, y, dx, dy):
            if not self.is_mirroring: return
            self.send_packet("S", str(dy))

        # 键盘处理
        def on_press(key):
            if not self.is_mirroring: return
            k_str = self.parse_key(key)
            if k_str: self.send_packet("KD", k_str)

        def on_release(key):
            if key == keyboard.Key.esc:
                # 在主线程回调停止
                self.root.after(10, self.stop_mirror)
                return False
                
            if not self.is_mirroring: return
            k_str = self.parse_key(key)
            if k_str: self.send_packet("KU", k_str)

        # 启动监听
        self.mouse_listener = mouse.Listener(on_move=on_move, on_click=on_click, on_scroll=on_scroll)
        self.key_listener = keyboard.Listener(on_press=on_press, on_release=on_release)
        
        self.mouse_listener.start()
        self.key_listener.start()
        
        self.mouse_listener.join()
        self.key_listener.join()

    def parse_key(self, key):
        try:
            if hasattr(key, 'char') and key.char:
                # 修复: 当按住 Ctrl 时, pynput 可能返回 ASCII 控制字符 (1-26)
                # 例如 Ctrl+A 返回 \x01, 需要转换回 'a'
                if len(key.char) == 1:
                    code = ord(key.char)
                    if 1 <= code <= 26:
                        return chr(code + 96) # 0x01('^A') -> 'a'
                return key.char # 普通字符
            else:
                return str(key).replace('Key.', '') # 特殊键
        except:
            return None

if __name__ == "__main__":
    root = tk.Tk()
    app = KVMApp(root)
    root.mainloop()

