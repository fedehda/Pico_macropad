# Pico_macropad
A macropad made with a 3d printer and powered by a Raspberry Pi Pico, coded with CircuitPython (because it has Arduino HID bundled with it).

It has a matrix of 3x3 buttons, an oled SSD1306 display (128x32), two rotary encoders and an extra button for layer switching. 

**Current inputs:**
- SSD1306 Oled Display is connected to individual GND and 3v from Pico, and SDA to GP6 and SCL to GP7
- Layer Switch Button to GP15, but it will be changed to join the keyboard matrix later
- Rows and columns yet to be defined.


I'm currently using modules from here:
https://circuitpython.org/board/raspberry_pi_pico/

Also, I've downloaded the CircuitPython bundle and community bundle:
- https://github.com/adafruit/Adafruit_CircuitPython_Bundle/releases/download/20260508/adafruit-circuitpython-bundle-10.x-mpy-20260508.zip
- https://github.com/adafruit/CircuitPython_Community_Bundle

