import serial
import time
import sys

# 配置部分
SERIAL_PORT = 'COM5'  # 你的 USB-TTL 模块端口
BAUD_RATE = 9600      # 必须与 Arduino 代码中的 Serial1.begin(9600) 一致

def main():
    try:
        # 打开串口
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        print(f"✅ 成功连接到 {SERIAL_PORT}")
        print("------------------------------------------")
        print("请输入指令并回车:")
        print("  A -> 在目标电脑输入 'a'")
        print("  E -> 在目标电脑按下回车")
        print("  M -> 在目标电脑晃动鼠标")
        print("  Q -> 退出")
        print("------------------------------------------")

        while True:
            # 获取用户输入
            cmd = input("发送指令 > ").upper().strip()

            if cmd == 'Q':
                break
            
            if cmd in ['A', 'E', 'M']:
                # 发送单字节指令
                ser.write(cmd.encode('utf-8'))
                print(f"🚀 已发送: {cmd}")
                
                # 读取 Arduino 的回复 (可选)
                time.sleep(0.1) # 给一点处理时间
                if ser.in_waiting > 0:
                    response = ser.readline().decode('utf-8').strip()
                    print(f"📩 Arduino回复: {response}")
            else:
                print("⚠️ 无效指令，请重试")

    except serial.SerialException as e:
        print(f"❌ 无法打开串口 {SERIAL_PORT}: {e}")
        print("请检查：1. 模块是否插好 2. 端口号是否正确 3. 串口是否被占用")
    except KeyboardInterrupt:
        print("\n程序已停止")
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()
            print("串口已关闭")

if __name__ == "__main__":
    main()
