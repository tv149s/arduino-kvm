import time
import ctypes

# 定义 Windows API 结构体
class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

def get_mouse_position():
    pt = POINT()
    ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
    return pt.x, pt.y

def main():
    print("🖱️ 开始监控鼠标坐标 (按 Ctrl+C 停止)...")
    print("----------------------------------------")
    
    last_x, last_y = get_mouse_position()
    
    try:
        while True:
            x, y = get_mouse_position()
            
            # 只有当坐标发生变化时才输出，或者每隔一定时间输出
            if x != last_x or y != last_y:
                print(f"📍 坐标: X={x}, Y={y}")
                last_x, last_y = x, y
            
            time.sleep(0.1)  # 刷新频率 10Hz
            
    except KeyboardInterrupt:
        print("\n🛑 监控已停止")

if __name__ == "__main__":
    main()
