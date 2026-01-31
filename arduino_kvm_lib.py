import serial
import time
import threading
from pynput import mouse, keyboard

# ==========================================
# Arduino KVM 核心库
# ==========================================

class ArduinoKVMClient:
    def __init__(self, port='COM5', baud_rate=115200):
        self.port = port
        self.baud_rate = baud_rate
        self.lock = threading.Lock()
        self.ser = None
        self.connected = False
        self.error_msg = ""
        
        # 状态
        self.target_os = 'WIN' # 'WIN' or 'MAC'
        self.mirror_enabled = False
        
        # 监听器
        self.m_listener = None
        self.k_listener = None
        self.last_mouse_time = 0
        self.MOUSE_RATE_LIMIT = 0.005
        
        # 鼠标位移计算
        self.prev_x = 0
        self.prev_y = 0
        self.first_move = True

    def connect(self):
        try:
            self.ser = serial.Serial(self.port, self.baud_rate, timeout=0.1)
            self.connected = True
            print(f"✅ [Lib] 串口已连接: {self.port}")
            return True
        except Exception as e:
            self.connected = False
            self.error_msg = str(e)
            print(f"❌ [Lib] 串口连接失败: {e}")
            return False

    def disconnect(self):
        if self.ser:
            with self.lock:
                try:
                    self.send_packet_raw("REL", "0") # 安全复位
                    self.ser.close()
                except:
                    pass
            self.ser = None
            self.connected = False
            print(f"🔌 [Lib] 串口已断开")

    def send_packet_raw(self, header, data):
        """直接发送底层指令"""
        if self.connected and self.ser and self.ser.is_open:
            payload = f"{header}:{data}\n"
            with self.lock:
                try:
                    self.ser.write(payload.encode('utf-8'))
                except Exception as e:
                    print(f"发送异常: {e}")

    # --- 高级控制 API (供外部程序调用) ---

    def send_key_down(self, key):
        self.send_packet_raw("KD", key)

    def send_key_up(self, key):
        self.send_packet_raw("KU", key)
        
    def send_key_click(self, key, duration=0.05):
        self.send_key_down(key)
        time.sleep(duration)
        self.send_key_up(key)

    def send_combo(self, keys, duration=0.02):
        """发送组合键列表 ['ctrl_l', 'c']"""
        for k in keys:
            self.send_key_down(k)
            time.sleep(duration)
        time.sleep(0.05)
        for k in reversed(keys):
            self.send_key_up(k)
            time.sleep(duration)

    def type_text(self, text, delay=0.02):
        """输入文本"""
        for char in text:
            # 简单处理
            self.send_key_down(char)
            self.send_key_up(char)
            time.sleep(delay)

    def mouse_move(self, dx, dy):
        self.send_packet_raw("M", f"{dx},{dy}")
        
    def mouse_click(self, button="L"):
        """L, R, M"""
        self.send_packet_raw("MD", button)
        time.sleep(0.05)
        self.send_packet_raw("MU", button)

    # --- 镜像功能设置 ---

    def set_target_os(self, os_type):
        """ 'WIN' or 'MAC' """
        self.target_os = os_type

    def start_mirroring(self):
        if self.mirror_enabled: return
        
        # 初始化鼠标位置，防止第一次跳变
        m_controller = mouse.Controller()
        self.prev_x, self.prev_y = m_controller.position
        self.first_move = True
        
        self.m_listener = mouse.Listener(on_move=self._on_move, on_click=self._on_click, on_scroll=self._on_scroll)
        self.k_listener = keyboard.Listener(on_press=self._on_press, on_release=self._on_release)
        
        self.m_listener.start()
        self.k_listener.start()
        self.mirror_enabled = True
        print("🟢 [Lib] 镜像已启动")

    def stop_mirroring(self):
        if not self.mirror_enabled: return
        
        if self.m_listener: self.m_listener.stop()
        if self.k_listener: self.k_listener.stop()
        
        # 发送复位防止卡键
        self.send_packet_raw("REL", "0")
        self.mirror_enabled = False
        print("⚪ [Lib] 镜像已停止")

    # --- 内部事件处理 ---

    def _remap_key_for_mac(self, k):
        if self.target_os != 'MAC': return k
        if k == 'ctrl_l': return 'win'
        if k == 'ctrl_r': return 'win'
        if k == 'cmd':    return 'alt'
        if k == 'win':    return 'alt'
        if k == 'alt_l':  return 'ctrl_l'
        if k == 'alt_r':  return 'ctrl_r'
        return k

    def _on_move(self, x, y):
        current_time = time.time()
        if current_time - self.last_mouse_time < self.MOUSE_RATE_LIMIT: return
        self.last_mouse_time = current_time
        
        if self.first_move:
            self.prev_x, self.prev_y = x, y
            self.first_move = False
            return

        dx, dy = x - self.prev_x, y - self.prev_y
        self.prev_x, self.prev_y = x, y
        
        if dx != 0 or dy != 0:
            self.send_packet_raw("M", f"{dx},{dy}")

    def _on_click(self, x, y, button, pressed):
        btn_code = "L" if button == mouse.Button.left else "R" if button == mouse.Button.right else "M"
        cmd = "MD" if pressed else "MU"
        self.send_packet_raw(cmd, btn_code)

    def _on_scroll(self, x, y, dx, dy):
        self.send_packet_raw("S", str(dy))

    def _on_press(self, key):
        try:
            k = key.char
            if k:
                if 1 <= ord(k) <= 26: k = chr(ord(k) + 96)
                k = self._remap_key_for_mac(k)
                self.send_packet_raw("KD", k)
        except AttributeError:
            k = str(key).replace('Key.', '')
            if k == 'cmd': k = 'win'
            k = self._remap_key_for_mac(k)
            self.send_packet_raw("KD", k)

    def _on_release(self, key):
        try:
            k = key.char
            if k:
                if 1 <= ord(k) <= 26: k = chr(ord(k) + 96)
                k = self._remap_key_for_mac(k)
                self.send_packet_raw("KU", k)
        except AttributeError:
            k = str(key).replace('Key.', '')
            if k == 'cmd': k = 'win'
            if 'media_' in k: return
            k = self._remap_key_for_mac(k)
            self.send_packet_raw("KU", k)

if __name__ == "__main__":
    # 简单的库文件测试
    print("📚 这只是一个库文件，请运行 'run_kvm_gui.py' 或其他主程序。")
    client = ArduinoKVMClient()
    if client.connect():
        print("测试: 输入 Hello")
        client.type_text("Hello")
        client.disconnect()
