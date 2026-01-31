#include <Keyboard.h>
#include <Mouse.h>

// ==========================================
// Arduino KVM Firmware
// Version: 3.5 (Stable Release)
// Features: Safety Reset (REL), CMD/Win Map, Full HID Spoofing
// ==========================================
// 改进点：
// 1. 全面支持 KeyDown/KeyUp，完美支持组合键 (Ctrl+C, Alt+Tab, Win+L 等)
// 2. 映射表覆盖常用功能键
// 3. 保持高速通信 115200

void setup() {
  Serial1.begin(115200); 
  
  Mouse.begin();
  Keyboard.begin();
}

String inputString = "";         
boolean stringComplete = false;  

void loop() {
  serialEvent(); 
  if (stringComplete) {
    inputString.trim(); 
    parseCommand(inputString);
    inputString = "";
    stringComplete = false;
  }
}

void serialEvent() {
  while (Serial1.available()) {
    char inChar = (char)Serial1.read();
    if (inChar == '\n') {
      stringComplete = true;
    } else {
      inputString += inChar;
    }
  }
}

void parseCommand(String cmd) {
  int splitIndex = cmd.indexOf(':');
  if (splitIndex == -1) return;

  String type = cmd.substring(0, splitIndex);
  String data = cmd.substring(splitIndex + 1);

  // --- 鼠标部分 ---
  if (type == "M") {
    int commaIndex = data.indexOf(',');
    if (commaIndex != -1) {
      int dx = data.substring(0, commaIndex).toInt();
      int dy = data.substring(commaIndex + 1).toInt();
      Mouse.move(dx, dy, 0);
    }
  }
  else if (type == "MD") {
    if (data == "L") Mouse.press(MOUSE_LEFT);
    if (data == "R") Mouse.press(MOUSE_RIGHT);
    if (data == "M") Mouse.press(MOUSE_MIDDLE);
  }
  else if (type == "MU") {
    if (data == "L") Mouse.release(MOUSE_LEFT);
    if (data == "R") Mouse.release(MOUSE_RIGHT);
    if (data == "M") Mouse.release(MOUSE_MIDDLE);
  }
  else if (type == "S") {
    Mouse.move(0, 0, data.toInt());
  }
  
  // --- 键盘部分 (核心改进) ---
  else if (type == "KD") {
    pressKey(data);
  }
  else if (type == "KU") {
    releaseKey(data);
  }
  // --- 全局重置 ---
  else if (type == "REL") {
     Keyboard.releaseAll();
     Mouse.release(MOUSE_LEFT);
     Mouse.release(MOUSE_RIGHT);
     Mouse.release(MOUSE_MIDDLE);
  }
}

// 解析键值或字符
void pressKey(String k) {
  if (k.length() == 1) {
    Keyboard.press(k.charAt(0));
  } else {
    int code = getSpecialKeyCode(k);
    if (code != 0) Keyboard.press(code);
  }
}

void releaseKey(String k) {
  if (k.length() == 1) {
    Keyboard.release(k.charAt(0));
  } else {
    int code = getSpecialKeyCode(k);
    if (code != 0) Keyboard.release(code);
  }
}

// 特殊按键映射表
int getSpecialKeyCode(String k) {
  if (k == "enter") return KEY_RETURN;
  if (k == "esc") return KEY_ESC;
  if (k == "backspace") return KEY_BACKSPACE;
  if (k == "delete") return KEY_DELETE;
  if (k == "insert") return KEY_INSERT;
  if (k == "tab") return KEY_TAB;
  if (k == "space") return ' '; // space is just space
  
  if (k == "up") return KEY_UP_ARROW;
  if (k == "down") return KEY_DOWN_ARROW;
  if (k == "left") return KEY_LEFT_ARROW;
  if (k == "right") return KEY_RIGHT_ARROW;

  if (k == "page_up") return KEY_PAGE_UP;
  if (k == "page_down") return KEY_PAGE_DOWN;
  if (k == "home") return KEY_HOME;
  if (k == "end") return KEY_END;

  // 补充常用功能键
  if (k == "print_screen") return 206; // Print Screen (0xCE)
  if (k == "scroll_lock")  return 207; // Scroll Lock (0xCF)
  if (k == "pause")        return 208; // Pause (0xD0)
  
  if (k == "caps_lock") return KEY_CAPS_LOCK;
  if (k == "num_lock") return 219; // Num Lock
  if (k == "scroll_lock") return 207; // Scroll Lock
  
  if (k == "f1") return KEY_F1;
  if (k == "f2") return KEY_F2;
  if (k == "f3") return KEY_F3;
  if (k == "f4") return KEY_F4;
  if (k == "f5") return KEY_F5;
  if (k == "f6") return KEY_F6;
  if (k == "f7") return KEY_F7;
  if (k == "f8") return KEY_F8;
  if (k == "f9") return KEY_F9;
  if (k == "f10") return KEY_F10;
  if (k == "f11") return KEY_F11;
  if (k == "f12") return KEY_F12;

  // 修饰键 (关键！)
  if (k == "shift" || k == "shift_l" || k == "shift_r") return KEY_LEFT_SHIFT; 
  if (k == "ctrl" || k == "ctrl_l" || k == "ctrl_r") return KEY_LEFT_CTRL;
  if (k == "alt" || k == "alt_l" || k == "alt_r") return KEY_LEFT_ALT;
  if (k == "cmd" || k == "cmd_l" || k == "cmd_r" || k == "win") return KEY_LEFT_GUI;

  return 0; // 未知按键
}
