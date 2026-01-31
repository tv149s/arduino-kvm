import serial
import time

SERIAL_PORT = 'COM5'
BAUD_RATE = 9600

def test_sequence():
    try:
        print(f"🔌 连接 {SERIAL_PORT}...")
        with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=2) as ser:
            time.sleep(2) # 等待串口初始化
            
            # 测试序列 (仅测试鼠标，避免发送 'A' 导致输入 'a')
            commands = ['M']
            
            for char in commands:
                print(f"\n📤 发送: {char}")
                ser.write(char.encode('utf-8'))
                
                # 等待接收回复
                time.sleep(0.5) 
                if ser.in_waiting > 0:
                    response = ser.read(ser.in_waiting).decode('utf-8').strip()
                    print(f"📩 收到回复: {response}")
                else:
                    print(f"📭 (无回复) - Arduino可能未定义此命令 '{char}' 的处理逻辑")
                    
    except Exception as e:
        print(f"❌ 错误: {e}")

if __name__ == "__main__":
    test_sequence()