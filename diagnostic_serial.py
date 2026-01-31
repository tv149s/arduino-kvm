import serial
import time

SERIAL_PORT = 'COM5'
BAUD_RATES = [9600, 115200]  # 尝试最常见的两种波特率

def full_diagnostic():
    print("🔬 开始全面串口诊断...")
    print("----------------------------------------")
    
    for baud in BAUD_RATES:
        print(f"\n[测试 1] 尝试波特率: {baud}")
        try:
            with serial.Serial(SERIAL_PORT, baud, timeout=2) as ser:
                # 给 DTR/RTS 一个信号，有时能唤醒某些板子
                ser.dtr = True
                ser.rts = True
                time.sleep(2) # 等待重新复位/稳定
                
                # 清空缓冲区
                ser.reset_input_buffer()
                
                test_payloads = [
                    (b'A', "纯字符 'A'"),
                    (b'A\n', "带换行 'A\\n'"),
                    (b'E', "纯字符 'E'"), 
                ]
                
                for data, desc in test_payloads:
                    print(f"  👉 发送 {desc} ... ", end='', flush=True)
                    ser.write(data)
                    
                    # 快速读取
                    time.sleep(0.5)
                    if ser.in_waiting > 0:
                        raw = ser.read_all()
                        try:
                            text = raw.decode('utf-8', errors='ignore').strip()
                            print(f"✅ 收到回复: [{text}] (Raw: {raw})")
                            return # 如果成功了，就直接结束整个测试
                        except:
                            print(f"⚠️收到乱码: {raw}")
                    else:
                        print("❌ 无回应")
                        
        except Exception as e:
            print(f"  ❌ 打开串口失败: {e}")

    print("\n----------------------------------------")
    print("🏁 诊断结束。如果全都是❌，请确认：")
    print("1. Arduino代码里确实写了 Serial1.println(...)")
    print("2. 模块的 GND 和 Arduino 的 GND 确实连在一起了")

if __name__ == "__main__":
    full_diagnostic()