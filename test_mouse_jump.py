import time
import ctypes
import serial

# Windows API 定义
class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

def get_mouse_position():
    pt = POINT()
    ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
    return pt.x, pt.y

def move_mouse_relative(dx, dy):
    # mouse_event(dwFlags, dx, dy, dwData, dwExtraInfo)
    # MOUSEEVENTF_MOVE = 0x0001
    ctypes.windll.user32.mouse_event(0x0001, dx, dy, 0, 0)

def main():
    print("🖱️ 鼠标跳动测试程序")
    print("----------------------------------------")
    
    # 1. 获取初始位置
    start_x, start_y = get_mouse_position()
    print(f"📍 初始坐标: X={start_x}, Y={start_y}")
    
    # 2. 发送 COM5 指令 (可选，看是否叠加效果)
    try:
        print("🔌 尝试向 COM5 发送 'M' 指令...")
        with serial.Serial('COM5', 9600, timeout=1) as ser:
            ser.write(b'M')
    except Exception as e:
        print(f"⚠️ 无法连接串口 (不影响本地测试): {e}")

    time.sleep(0.5)

    # 3. 执行本地强制偏移
    offset_x, offset_y = 100, 100
    print(f"🚀 执行本地鼠标偏移 (Offset: {offset_x}, {offset_y})...")
    move_mouse_relative(offset_x, offset_y)
    
    time.sleep(0.5)

    # 4. 获取结束位置
    end_x, end_y = get_mouse_position()
    print(f"📍 结束坐标: X={end_x}, Y={end_y}")
    
    # 5. 计算并显示结果
    diff_x = end_x - start_x
    diff_y = end_y - start_y
    print("----------------------------------------")
    print(f"📊 实际位移结果: X+{diff_x}, Y+{diff_y}")
    
    if abs(diff_x - offset_x) < 5 and abs(diff_y - offset_y) < 5:
        print("✅ 测试成功：观察到鼠标跳动！")
    else:
        print("⚠️ 注意：实际位移与预期有轻微差异 (可能是鼠标加速/系统缩放影响)")

if __name__ == "__main__":
    main()
