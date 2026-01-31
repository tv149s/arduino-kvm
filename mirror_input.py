# ==========================================
# Python KVM Mirror Input Client
# Version: 3.5 (Stable Release)
# Features: Mac/Win Mode, Safe-Exit (Anti-Stuck), 115200 Baud, Full Map
# ==========================================
import serial
import time
import threading
from pynput import mouse, keyboard
import sys

# ==========================================
# 配置
# ==========================================
SERIAL_PORT = 'COM5'
BAUD_RATE = 115200
MOUSE_RATE_LIMIT = 0.005 

# 目标系统模式: 'WIN' 或 'MAC'
# WIN模式: 1:1 透传 (Ctrl->Ctrl, Win->Win)
# MAC模式: 键位互换以符合 Mac 习惯
#   - L_Ctrl -> Command (Win键) [方便复制粘贴]
#   - L_Win  -> Option (Alt键)
#   - L_Alt  -> Control
TARGET_OS = 'WIN' 

# 全局变量
serial_lock = threading.Lock()
ser = None
last_mouse_time = 0

def init_serial():
    global ser
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.1)
        print(f"✅ 已连接到 {SERIAL_PORT}")
        return True
    except Exception as e:
        print(f"❌ 串口连接失败: {e}")
        return False

def remap_key_for_mac(k):
    """
    将 Windows 键位映射为 Mac 常用布局
    Pynput Name  ->  Arduino Name
    """
    if TARGET_OS != 'MAC':
        return k
        
    # 核心映射：让 PC 的 Ctrl 变成 Mac 的 Command
    if k == 'ctrl_l': return 'win'      # L_Ctrl -> Command
    if k == 'ctrl_r': return 'win'      # R_Ctrl -> Command
    
    # PC Win -> Mac Option
    if k == 'cmd':    return 'alt'      # Win -> Option
    if k == 'win':    return 'alt'
    
    # PC Alt -> Mac Control
    if k == 'alt_l':  return 'ctrl_l'   # L_Alt -> Control
    if k == 'alt_r':  return 'ctrl_r'   # R_Alt -> Control
    
    return k

def send_packet(header, data_str):
    """
    发送简单的文本协议。
    例如: 
       鼠标: "M:10,-5\n"
       键盘: "K:a\n"
    """
    global ser
    if not ser or not ser.is_open:
        return

    try:
        payload = f"{header}:{data_str}\n" 
        with serial_lock:
            ser.write(payload.encode('utf-8'))
            # print(f"Sent: {payload.strip()}") # 调试用，太快可以注释掉
    except Exception as e:
        print(f"发送失败: {e}")

# ==========================================
# 鼠标监听
# ==========================================
def on_move(x, y):
    global last_mouse_time
    current_time = time.time()
    
    # 简单的频率限制
    if current_time - last_mouse_time < MOUSE_RATE_LIMIT:
        return
    
    last_mouse_time = current_time
    
    # 这里我们简化处理：
    # 真实的 KVM 需要计算 "相对位移" (dx, dy)，而不是绝对坐标 (x, y)。
    # pynput 只提供绝对坐标 x, y。我们需要记录上一次的位置。
    # 但为了演示效果，我们先发送当前坐标，
    # 或者如果不方便计算，就发送一个固定方向测试。
    
    # 下面是计算相对位移的逻辑
    global prev_x, prev_y
    try:
        dx = x - prev_x
        dy = y - prev_y
    except NameError:
        dx, dy = 0, 0
    
    prev_x, prev_y = x, y
    
    if dx != 0 or dy != 0:
        # 发送 M:dx,dy
        send_packet("M", f"{dx},{dy}")

def on_click(x, y, button, pressed):
    btn_code = "L" if button == mouse.Button.left else "R" if button == mouse.Button.right else "M"
    
    if pressed:
        send_packet("MD", btn_code) # Mouse Down
    else:
        send_packet("MU", btn_code) # Mouse Up

def on_scroll(x, y, dx, dy):
    send_packet("S", str(dy)) # S:1 (Scroll Up)

# ==========================================
# 键盘监听
# ==========================================
def on_press(key):
    try:
        # 普通按键
        k = key.char
        if k:
            if 1 <= ord(k) <= 26:
                k = chr(ord(k) + 96)
            k = remap_key_for_mac(k)
            send_packet("KD", k)
    except AttributeError:
        # 特殊按键
        k = str(key).replace('Key.', '')
        
        # 兼容性处理
        if k == 'cmd': k = 'win'
        
        k = remap_key_for_mac(k)
        send_packet("KD", k)

def on_release(key):
    if key == keyboard.Key.esc:
        print("\n🛑 停止监听")
        return False
        
    try:
        k = key.char
        if k:
            if 1 <= ord(k) <= 26:
                k = chr(ord(k) + 96)
            k = remap_key_for_mac(k)
            send_packet("KU", k)
    except AttributeError:
        k = str(key).replace('Key.', '')
        if k == 'cmd': k = 'win'
        if 'media_' in k: return

        k = remap_key_for_mac(k)
        send_packet("KU", k)

# ==========================================
# 主程序
# ==========================================
def main():
    global TARGET_OS
    print("🖥️  Arduino KVM Input Mirror V3.0")
    print("---------------------------------------------")
    choice = input("Select Target System (1=Windows, 2=Mac): ").strip()
    if choice == '2':
        TARGET_OS = 'MAC'
        print("🍏 Mac Mode Selected: Ctrl->Cmd, Win->Opt, Alt->Ctrl")
    else:
        TARGET_OS = 'WIN'
        print("🪟 Windows Mode Selected: Standard Mapping")
        
    if not init_serial():
        return

    # 初始化鼠标位置
    mouse_controller = mouse.Controller()
    global prev_x, prev_y
    prev_x, prev_y = mouse_controller.position

    print("🚀 开始镜像输入...")
    print("---------------------------------------------")
    print("当您在本机移动鼠标或按键时，")
    print("信号将通过 COM5 发送到 Arduino。")
    print("注意：Arduino 端必须有对应的解析代码才能生效！")
    print("---------------------------------------------")
    print("按 [ESC] 键退出程序")

    # 启动监听器
    # 使用非阻塞方式启动
    m_listener = mouse.Listener(
        on_move=on_move,
        on_click=on_click,
        on_scroll=on_scroll)
    
    k_listener = keyboard.Listener(
        on_press=on_press,
        on_release=on_release)

    m_listener.start()
    k_listener.start()

    # 发送一次初始复位，防止上次异常残留
    send_packet("REL", "0")

    try:
        k_listener.join() # 等待键盘监听停止 (ESC)
    except KeyboardInterrupt:
        pass
    finally:
        print("\n🧹 正在停止... 发送全键释放信号")
        send_packet("REL", "0")
        time.sleep(0.2) # 确保发出去
        
        m_listener.stop()
        if ser:
            ser.close()

if __name__ == "__main__":
    main()
