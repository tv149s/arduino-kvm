import tkinter as tk
from tkinter import ttk, messagebox
import arduino_kvm_lib  # 引入刚才生成的库

# ==========================================
# 配置
# ==========================================
# SERIAL_PORT = 'COM5' (在库里默认了，也可以传入)

class KVMGuiApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Arduino KVM 控制台 (基于 Lib)")
        self.root.geometry("700x600")
        
        # 1. 初始化核心库 (尝试自动检测，但不强制连接成功)
        self.kvm = arduino_kvm_lib.ArduinoKVMClient()
        
        self.setup_ui()
        
        # 尝试自动连接
        if self.kvm.port:
            if self.kvm.connect():
                self.set_status(f"已连接: {self.kvm.port}", "green")
                self.combo_ports.set(self.kvm.port)
            else:
                self.set_status(f"连接失败: {self.kvm.port}", "red")
        else:
            self.set_status("未检测到设备", "orange")

    def set_status(self, text, color):
        self.lbl_status.config(text=text, foreground=color)

    def setup_ui(self):
        # --- 顶部：连接设置 ---
        conn_frame = ttk.LabelFrame(self.root, text="连接设置", padding=10)
        conn_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(conn_frame, text="端口:").pack(side=tk.LEFT, padx=5)
        
        self.port_list = arduino_kvm_lib.ArduinoKVMClient.list_ports()
        self.combo_ports = ttk.Combobox(conn_frame, values=self.port_list, width=10)
        self.combo_ports.pack(side=tk.LEFT, padx=5)
        
        btn_refresh = ttk.Button(conn_frame, text="刷新", command=self.on_refresh_ports)
        btn_refresh.pack(side=tk.LEFT, padx=5)
        
        btn_connect = ttk.Button(conn_frame, text="连接", command=self.on_connect)
        btn_connect.pack(side=tk.LEFT, padx=5)

        self.lbl_status = ttk.Label(conn_frame, text="等待连接...", font=("Arial", 10, "bold"))
        self.lbl_status.pack(side=tk.LEFT, padx=20)

        # --- 设置状态区域 ---
        top_frame = ttk.LabelFrame(self.root, text="功能开关", padding=10)
        top_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 镜像开关
        self.var_mirror_enable = tk.BooleanVar(value=False)
        chk_mirror = ttk.Checkbutton(top_frame, text="启用键盘鼠标镜像", variable=self.var_mirror_enable, command=self.on_toggle_mirror)
        chk_mirror.pack(side=tk.LEFT, padx=20)
        
        # 系统模式
        ttk.Label(top_frame, text="系统模式:").pack(side=tk.LEFT, padx=(20, 5))
        self.var_os_mode = tk.StringVar(value="WIN")
        r1 = ttk.Radiobutton(top_frame, text="Windows", variable=self.var_os_mode, value="WIN", command=self.on_change_mode)
        r2 = ttk.Radiobutton(top_frame, text="Mac", variable=self.var_os_mode, value="MAC", command=self.on_change_mode)
        r1.pack(side=tk.LEFT, padx=5)
        r2.pack(side=tk.LEFT, padx=5)
        
        # --- 快捷按键区域 ---
        deck_frame = ttk.LabelFrame(self.root, text="快捷控制", padding=10)
        deck_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        buttons = [
            (0, 0, "复制 (Ctrl+C)", ['ctrl_l', 'c']),
            (0, 1, "粘贴 (Ctrl+V)", ['ctrl_l', 'v']),
            (0, 2, "全选 (Ctrl+A)", ['ctrl_l', 'a']),
            (1, 0, "锁屏 (Win+L)", ['win', 'l']),
            (1, 1, "桌面 (Win+D)", ['win', 'd']),
            (1, 2, "任务 (Ctrl+Shift+Esc)", ['ctrl_l', 'shift_l', 'esc']),
            (2, 0, "回车 Enter", ['enter']),
            (2, 1, "退格 Backspace", ['backspace']),
            (2, 2, "Tab键", ['tab']),
        ]
        
        for r, c, text, keys in buttons:
            btn = ttk.Button(deck_frame, text=text, 
                           command=lambda k=keys: self.kvm.send_combo(k))
            btn.grid(row=r, column=c, padx=5, pady=5, sticky="nsew")

        # 文本框测试
        input_frame = ttk.Frame(deck_frame)
        input_frame.grid(row=3, column=0, columnspan=3, pady=20, sticky="ew")
        
        self.entry_text = ttk.Entry(input_frame)
        self.entry_text.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.entry_text.insert(0, "输入测试文本...")
        
        btn_send = ttk.Button(input_frame, text="发送文本", command=self.on_send_text)
        btn_send.pack(side=tk.LEFT, padx=5)
        
        for i in range(3): deck_frame.columnconfigure(i, weight=1)

    # --- 逻辑 ---
    def on_toggle_mirror(self):
        if self.var_mirror_enable.get():
            self.kvm.start_mirroring()
        else:
            self.kvm.stop_mirroring()

    def on_change_mode(self):
        self.kvm.set_target_os(self.var_os_mode.get())

    def on_send_text(self):
        txt = self.entry_text.get()
        self.kvm.type_text(txt)

    def on_refresh_ports(self):
        self.port_list = arduino_kvm_lib.ArduinoKVMClient.list_ports()
        self.combo_ports['values'] = self.port_list
        if self.port_list:
            self.combo_ports.current(0)
            
    def on_connect(self):
        selected_port = self.combo_ports.get()
        if not selected_port:
            return
            
        if self.kvm.connected:
            self.kvm.disconnect()
            
        self.kvm.port = selected_port
        if self.kvm.connect():
             self.set_status(f"已连接: {selected_port}", "green")
        else:
             self.set_status(f"连接失败: {self.kvm.error_msg}", "red")
             messagebox.showerror("连接失败", self.kvm.error_msg)

    def on_close(self):
        self.kvm.stop_mirroring()
        self.kvm.disconnect()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = KVMGuiApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()
