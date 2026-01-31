import tkinter as tk
from tkinter import ttk, messagebox
import serial
import time
import threading
from pynput import mouse, keyboard

# ==========================================
# 配置
# ==========================================
SERIAL_PORT = 'COM5'
BAUD_RATE = 115200
MOUSE_RATE_LIMIT = 0.005

# ==========================================
# 串口管理器 (线程安全)
# ==========================================
class SerialManager:
    def __init__(self, port, baud):
        self.lock = threading.Lock()
        self.ser = None
        self.connected = False
        self.error_msg = ""
        
        try:
            self.ser = serial.Serial(port, baud, timeout=0.1)
            self.connected = True
            print(f"✅ 串口已连接: {port}")
        except Exception as e:
            self.connected = False
            self.error_msg = str(e)
            print(f"❌ 串口连接失败: {e}")

    def send_packet(self, header, data):
        if self.connected and self.ser and self.ser.is_open:
            payload = f"{header}:{data}\n"
            with self.lock:
                try:
                    self.ser.write(payload.encode('utf-8'))
                except Exception as e:
                    print(f"发送异常: {e}")
    
    def close(self):
        if self.ser:
            with self.lock:
                # 退出前发送复位信号
                try:
                    self.ser.write(b"REL:0\n") 
                    self.ser.close()
                except:
                    pass
            self.connected = False

# ==========================================
# 键鼠镜像逻辑 (后台线程)
# ==========================================
class InputMirror:
    def __init__(self, serial_mgr):
        self.ser_mgr = serial_mgr
        self.target_os = 'WIN'
        self.enabled = False
        self.last_mouse_time = 0
        self.m_listener = None
        self.k_listener = None

    def set_mode(self, os_type):
        self.target_os = os_type # 'WIN' or 'MAC'

    def set_enabled(self, output_enabled):
        self.enabled = output_enabled
        if not self.enabled:
            # 如果关闭了镜像，发送一次松开信号，防止卡键
            self.ser_mgr.send_packet("REL", "0")

    def start_listeners(self):
        # 启动 pynput 监听 (非阻塞)
        self.m_listener = mouse.Listener(on_move=self.on_move, on_click=self.on_click, on_scroll=self.on_scroll)
        self.k_listener = keyboard.Listener(on_press=self.on_press, on_release=self.on_release)
        self.m_listener.start()
        self.k_listener.start()

    def stop_listeners(self):
        if self.m_listener: self.m_listener.stop()
        if self.k_listener: self.k_listener.stop()

    def remap_key_for_mac(self, k):
        if self.target_os != 'MAC': return k
        if k == 'ctrl_l': return 'win'
        if k == 'ctrl_r': return 'win'
        if k == 'cmd':    return 'alt'
        if k == 'win':    return 'alt'
        if k == 'alt_l':  return 'ctrl_l'
        if k == 'alt_r':  return 'ctrl_r'
        return k

    # --- Mouse Events ---
    def on_move(self, x, y):
        if not self.enabled: return
        current_time = time.time()
        if current_time - self.last_mouse_time < MOUSE_RATE_LIMIT: return
        self.last_mouse_time = current_time
        
        # 注意：这里我们简化为发送 "Rel" (如果需要 pynput不支持原生的相对movement，需要自己计算dx/dy)
        # 为了演示，此处假设我们已经在 mirror_input.py 解决了这个问题
        # 实际代码中 mirror_input V3.x 用的还是绝对坐标计算后的相对值
        global prev_x, prev_y
        try: dx, dy = x - prev_x, y - prev_y
        except NameError: dx, dy = 0, 0
        prev_x, prev_y = x, y
        
        if dx != 0 or dy != 0:
            self.ser_mgr.send_packet("M", f"{dx},{dy}")

    def on_click(self, x, y, button, pressed):
        if not self.enabled: return
        btn_code = "L" if button == mouse.Button.left else "R" if button == mouse.Button.right else "M"
        cmd = "MD" if pressed else "MU"
        self.ser_mgr.send_packet(cmd, btn_code)

    def on_scroll(self, x, y, dx, dy):
        if not self.enabled: return
        self.ser_mgr.send_packet("S", str(dy))

    # --- Keyboard Events ---
    def on_press(self, key):
        if not self.enabled: return
        try:
            k = key.char
            if k:
                if 1 <= ord(k) <= 26: k = chr(ord(k) + 96)
                k = self.remap_key_for_mac(k)
                self.ser_mgr.send_packet("KD", k)
        except AttributeError:
            k = str(key).replace('Key.', '')
            if k == 'cmd': k = 'win'
            k = self.remap_key_for_mac(k)
            self.ser_mgr.send_packet("KD", k)

    def on_release(self, key):
        # 即使 disable 了，release 也要处理吗？最好处理，但既然有 enabled 检查，我们假设 disable 时不需要
        if not self.enabled: return 
        try:
            k = key.char
            if k:
                if 1 <= ord(k) <= 26: k = chr(ord(k) + 96)
                k = self.remap_key_for_mac(k)
                self.ser_mgr.send_packet("KU", k)
        except AttributeError:
            k = str(key).replace('Key.', '')
            if k == 'cmd': k = 'win'
            if 'media_' in k: return
            k = self.remap_key_for_mac(k)
            self.ser_mgr.send_packet("KU", k)

# ==========================================
# 主界面 (Tkinter)
# ==========================================
class KVMApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Arduino KVM 终极控制台")
        self.root.geometry("800x600")
        
        # 1. 连接串口
        self.serial_mgr = SerialManager(SERIAL_PORT, BAUD_RATE)
        if not self.serial_mgr.connected:
            messagebox.showerror("错误", f"无法连接串口:\n{self.serial_mgr.error_msg}\n请先关闭其他 Python 程序！")
            root.destroy()
            return
            
        # 2. 初始化镜像引擎
        self.mirror = InputMirror(self.serial_mgr)
        # 初始化鼠标坐标
        global prev_x, prev_y
        m_controller = mouse.Controller()
        prev_x, prev_y = m_controller.position
        
        self.mirror.start_listeners() # 启动监听，但 enabled 默认为 False
        
        # 3. 构建 UI
        self.setup_ui()
        
    def setup_ui(self):
        # --- 顶部：设置区域 ---
        top_frame = ttk.LabelFrame(self.root, text="设置 & 状态", padding=10)
        top_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 镜像开关
        self.var_mirror_enable = tk.BooleanVar(value=False)
        chk_mirror = ttk.Checkbutton(top_frame, text="启用键盘鼠标镜像 (Mirroring)", variable=self.var_mirror_enable, command=self.on_toggle_mirror)
        chk_mirror.pack(side=tk.LEFT, padx=20)
        
        # 系统模式
        ttk.Label(top_frame, text="目标系统模式:").pack(side=tk.LEFT, padx=(20, 5))
        self.var_os_mode = tk.StringVar(value="WIN")
        r1 = ttk.Radiobutton(top_frame, text="Windows", variable=self.var_os_mode, value="WIN", command=self.on_change_mode)
        r2 = ttk.Radiobutton(top_frame, text="Mac (自动改键)", variable=self.var_os_mode, value="MAC", command=self.on_change_mode)
        r1.pack(side=tk.LEFT, padx=5)
        r2.pack(side=tk.LEFT, padx=5)
        
        # 状态指示
        self.lbl_status = ttk.Label(top_frame, text=f"已连接 {SERIAL_PORT}", foreground="green")
        self.lbl_status.pack(side=tk.RIGHT, padx=10)

        # --- 中部：Stream Deck 按钮区域 ---
        deck_frame = ttk.LabelFrame(self.root, text="直播控制面板 (Stream Deck)", padding=10)
        deck_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 样式
        style = ttk.Style()
        style.configure("Deck.TButton", font=("Microsoft YaHei UI", 11), padding=10)
        
        # 定义按钮
        buttons = [
            (0, 0, "复制\nCtrl+C", ['ctrl_l', 'c']),
            (0, 1, "粘贴\nCtrl+V", ['ctrl_l', 'v']),
            (0, 2, "全选\nCtrl+A", ['ctrl_l', 'a']),
            (0, 3, "静音\nCtrl+M", ['ctrl_l', 'm']),
            
            (1, 0, "任务管理\nCtrl+Shift+Esc", ['ctrl_l', 'shift_l', 'esc']),
            (1, 1, "锁屏\nWin+L", ['win', 'l']),
            (1, 2, "显示桌面\nWin+D", ['win', 'd']),
            (1, 3, "运行\nWin+R", ['win', 'r']),
            
            (2, 0, "场景 1\nOBS-1", ['ctrl_l', 'alt_l', '1']),
            (2, 1, "场景 2\nOBS-2", ['ctrl_l', 'alt_l', '2']),
            (2, 2, "直播开始\nStart", ['ctrl_l', 'alt_l', 's']),
            (2, 3, "截图\nWin+Shift+S", ['win', 'shift_l', 's']),
        ]
        
        # 动态创建按钮 (使用 grid)
        for r, c, text, combo in buttons:
            btn = ttk.Button(deck_frame, text=text, style="Deck.TButton",
                           # 注意 lambda 闭包问题，需要 default argument
                           command=lambda k=combo: self.send_combo(k))
            btn.grid(row=r, column=c, padx=5, pady=5, sticky="nsew")
            
        # 还有文本宏
        (ttk.Button(deck_frame, text="输入 Email", style="Deck.TButton", command=lambda: self.type_text("user@example.com"))
            .grid(row=3, column=0, columnspan=2, sticky="nsew", padx=5, pady=5))
            
        (ttk.Button(deck_frame, text="输入 Hello", style="Deck.TButton", command=lambda: self.type_text("Hello World!"))
            .grid(row=3, column=2, columnspan=2, sticky="nsew", padx=5, pady=5))

        # 配置权重
        for i in range(4): deck_frame.columnconfigure(i, weight=1)
        for i in range(4): deck_frame.rowconfigure(i, weight=1)

    # --- 逻辑处理 ---
    def on_toggle_mirror(self):
        is_enabled = self.var_mirror_enable.get()
        self.mirror.set_enabled(is_enabled)
        state = "🟢 正在运行" if is_enabled else "⚪ 已暂停"
        self.lbl_status.config(text=f"镜像: {state} | 端口: {SERIAL_PORT}")

    def on_change_mode(self):
        mode = self.var_os_mode.get()
        self.mirror.set_mode(mode)
        print(f"模式已切换为: {mode}")

    def send_combo(self, keys):
        print(f"执行宏: {keys}")
        for k in keys:
            self.serial_mgr.send_packet("KD", k)
            time.sleep(0.02)
        time.sleep(0.05)
        for k in reversed(keys):
            self.serial_mgr.send_packet("KU", k)
            time.sleep(0.02)

    def type_text(self, text):
        print(f"执行输入: {text}")
        for char in text:
            # 简单处理
            self.serial_mgr.send_packet("KD", char)
            self.serial_mgr.send_packet("KU", char)
            time.sleep(0.02)

    def on_close(self):
        print("正在关闭...")
        self.mirror.stop_listeners()
        self.serial_mgr.close()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = KVMApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()
