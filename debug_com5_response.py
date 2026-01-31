import serial
import time

SERIAL_PORT = 'COM5'
BAUD_RATE = 9600

def debug_mouse_response():
    print(f"🕵️‍♀️ 深度分析 COM5 返回数据 - {SERIAL_PORT}")
    try:
        with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=2) as ser:
            time.sleep(2)
            
            # 清空之前的残留
            ser.reset_input_buffer()
            
            print("📤 发送指令: 'M' (Simulate Mouse Move)")
            ser.write(b'M')
            
            print("📥 等待 2 秒，读取所有返回内容...")
            time.sleep(2)
            
            if ser.in_waiting > 0:
                raw_data = ser.read_all()
                print(f"\n--- [收到原始数据] ---")
                print(f"字节长度: {len(raw_data)}")
                print(f"十六进制 (Hex): {raw_data.hex(' ')}")
                try:
                    print(f"UTF-8 解码: {raw_data.decode('utf-8', errors='replace')}")
                except:
                    pass
                print("----------------------")
            else:
                print("❌ 未收到任何数据")
                
    except Exception as e:
        print(f"❌ 发生错误: {e}")

if __name__ == "__main__":
    debug_mouse_response()
