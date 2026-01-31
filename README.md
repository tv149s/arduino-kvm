# Arduino KVM Project

This project implements a software-based KVM (Keyboard, Video, Mouse) switch solution using an **Arduino Leonardo** (or compatible ATmega32u4 board) and Python. It allows you to control a second computer using the mouse and keyboard of your primary computer.

## Features

- **Hardware Level Input Simulation**: Uses Arduino HID capabilities, undetectable by most software.
- **Cross-Platform**: Supports Windows and macOS targets.
- **High Performance**: Optimized serial protocol @ 115200 baud for smooth mouse movement.
- **Reusable Library**: `arduino_kvm_lib.py` provides a simple API for developers.
- **GUI Application**: Included Tkinter-based control panel with macro keys.

## Project Structure

- **`arduino_kvm_firmware/`**: The C++ firmware for the Arduino.
- **`arduino_kvm_lib.py`**: The core Python library (SDK).
- **`run_kvm_gui.py`**: A complete GUI application example.
- **`kvm_completed_app.py`**: (Deprecated) All-in-one script.

## Getting Started

### 1. Hardware Setup
Flash the firmware located in `arduino_kvm_firmware/` to your Arduino Leonardo.

### 2. Software Requirements
Install the required Python packages:
```bash
pip install pyserial pynput tk
```

### 3. Running the GUI
```bash
python run_kvm_gui.py
```

## Library Usage

You can use the library in your own scripts:

```python
import arduino_kvm_lib

kvm = arduino_kvm_lib.ArduinoKVMClient()
if kvm.connect():
    kvm.type_text("Hello World")
```
