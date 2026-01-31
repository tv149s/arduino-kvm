from pynput import keyboard

def on_press(key):
    try:
        print(f"Alphanumeric key pressed: {key.char!r} (vk: {getattr(key, 'vk', 'N/A')})")
    except AttributeError:
        # Check standard name
        name = getattr(key, 'name', 'N/A')
        print(f"Special key pressed: {key} (name: {name})")
        # Also print the raw string representation
        print(f"Raw string: {str(key)}")
        print(f"Computed k: {str(key).replace('Key.', '')}")

def on_release(key):
    print(f"Key released: {key}")
    if key == keyboard.Key.esc:
        return False

# Collect events until released
with keyboard.Listener(
        on_press=on_press,
        on_release=on_release) as listener:
    listener.join()
