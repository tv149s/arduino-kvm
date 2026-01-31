import serial
import time

SERIAL_PORT = 'COM5'
BAUD_RATE = 9600

def echo_test():
    print(f"🔄 正在测试模块回环 (Loopback) - 端口: {SERIAL_PORT}")
    print("--------------------------------------------------")
    print("请确认：已使用杜邦线将模块的 TX 和 RX 直接短接")
    print("--------------------------------------------------")
    
    try:
        with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1) as ser:
            test_str = "Hello World Loopback Test"
            print(f"📤 发送数据: {test_str}")
            
            # 发送
            ser.write(test_str.encode('utf-8'))
            time.sleep(0.5)
            
            # 接收
            if ser.in_waiting > 0:
                received = ser.read(ser.in_waiting).decode('utf-8')
                print(f"📥 接收回显: {received}")
                
                if received == test_str:
                    print("\n✅ 测试成功！模块工作正常。")
                    print("结论：既然模块没问题，问题一定出在和 Arduino 的连接上。")
                else:
                    print("\n⚠️ 数据已接收但有误码。可能接触不良。")
            else:
                print("\n❌ 未接收到数据！")
                print("可能原因：")
                print("1. 短接没接好")
                print("2. 模块驱动有问题")
                print("3. 模块硬件损坏")

    except Exception as e:
        print(f"❌ 无法打开串口: {e}")

if __name__ == "__main__":
    echo_test()