import time
import board
import digitalio
import rotaryio
import usb_hid
import busio
import keypad  
import adafruit_ssd1306
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode
from adafruit_hid.consumer_control import ConsumerControl
from adafruit_hid.consumer_control_code import ConsumerControlCode

# 1. Liberar cualquier bus trabado antes de empezar (Anti-cuelgues)
import displayio
displayio.release_displays()

# 2. Inicializar el teclado y controles multimedia
kbd = Keyboard(usb_hid.devices)
cc = ConsumerControl(usb_hid.devices)

# 3. Configurar Pantalla OLED SSD1306 (128x64)
i2c = busio.I2C(board.GP7, board.GP6)
display = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c)


# --- FUNCIÓN DE ACTUALIZACIÓN DE PANTALLA (128x64) ---
def update_display(layer_input):
    try:
        display.fill(0)  # Limpiar pantalla
        layer_str = str(layer_input).upper()

        if "0" in layer_str or "STREAM" in layer_str:
            display.text("STREAM", 4, 4, 1)
            display.text("#0", 110, 4, 1)
            display.fill_rect(52, 26, 20, 16, 1)  
            display.fill_rect(72, 30, 6, 8, 1)    

        elif "1" in layer_str or "WORK" in layer_str:
            display.text("WORK", 4, 4, 1)
            display.text("#1", 110, 4, 1)
            display.fill_rect(48, 22, 32, 18, 1)  
            display.fill_rect(48, 40, 32, 2, 0)   
            display.fill_rect(62, 40, 4, 6, 1)    
            display.fill_rect(54, 46, 20, 3, 1)   

        elif "2" in layer_str or "GAME" in layer_str:
            display.text("GAMING", 4, 4, 1)
            display.text("#2", 110, 4, 1)
            display.fill_rect(46, 24, 36, 16, 1)  
            display.fill_rect(46, 40, 8, 8, 1)    
            display.fill_rect(74, 40, 8, 8, 1)    
            display.fill_rect(52, 30, 4, 4, 0)    
            display.fill_rect(72, 30, 4, 4, 0)    

        elif "3" in layer_str or "MEDIA" in layer_str:
            display.text("MEDIA", 4, 4, 1)
            display.text("#3", 110, 4, 1)
            display.fill_rect(52, 22, 4, 22, 1)   
            display.fill_rect(70, 22, 4, 18, 1)   
            display.fill_rect(52, 22, 22, 5, 1)   
            display.fill_rect(44, 38, 10, 8, 1)   
            display.fill_rect(62, 34, 10, 8, 1)   

        display.show()
    except Exception as e:
        print("Error en pantalla:", e)


# --- PANTALLA DE INICIO (SPLASH SCREEN) ---
display.fill(0)
display.rect(0, 0, 128, 64, 1)
display.text("MACROPAD", 38, 28, 1)
display.show()
time.sleep(1.0)


# 4. CONFIGURAR EL BOTÓN DE CAPA INDEPENDIENTE (GP15)
layer_button = digitalio.DigitalInOut(board.GP15)
layer_button.direction = digitalio.Direction.INPUT
layer_button.pull = digitalio.Pull.UP

current_layer = 0
last_layer_btn_state = True
last_debounce_time = 0.0  

# Mostrar la capa inicial
update_display(current_layer)


# 5. CONFIGURACIÓN DE LA MATRIZ REPARADA (3x3 = 9 teclas)
filas = (board.GP0, board.GP1, board.GP2)       
columnas = (board.GP3, board.GP18, board.GP19)     

# Reemplazado col_pins por column_pins de forma exitosa
matrix = keypad.KeyMatrix(
    row_pins=filas,
    column_pins=columnas,
    columns_to_anodes=False  
)


# 6. Configurar los 2 Encoders Rotativos
encoder1 = rotaryio.IncrementalEncoder(board.GP11, board.GP12)
encoder2 = rotaryio.IncrementalEncoder(board.GP13, board.GP14)
last_enc1_pos = encoder1.position
last_enc2_pos = encoder2.position

enc1_switch = digitalio.DigitalInOut(board.GP22)
enc1_switch.direction = digitalio.Direction.INPUT
enc1_switch.pull = digitalio.Pull.UP
last_enc1_sw_state = True

enc2_switch = digitalio.DigitalInOut(board.GP16)
enc2_switch.direction = digitalio.Direction.INPUT
enc2_switch.pull = digitalio.Pull.UP
last_enc2_sw_state = True


# 7. DEFINICIÓN DE ATAJOS POR CAPA
layers = {
    0: {
        "buttons": [
            [Keycode.F13], [Keycode.F14], [Keycode.F15],
            [Keycode.F16], [Keycode.F17], [Keycode.F18],
            [Keycode.F19], [Keycode.F20], [Keycode.F21]
        ]
    },
    1: {
        "buttons": [
            [Keycode.CONTROL, Keycode.Z], [Keycode.CONTROL, Keycode.Y], [Keycode.CONTROL, Keycode.SHIFT, Keycode.S],
            [Keycode.CONTROL, Keycode.C], [Keycode.CONTROL, Keycode.V], [Keycode.CONTROL, Keycode.X],
            [Keycode.GUI, Keycode.SHIFT, Keycode.S], [Keycode.CONTROL, Keycode.GRAVE_ACCENT], [Keycode.ALT, Keycode.F4]
        ]
    },
    2: {
        "buttons": [
            [Keycode.CONTROL, Keycode.SHIFT, Keycode.M], [Keycode.CONTROL, Keycode.SHIFT, Keycode.D], [Keycode.GUI, Keycode.PRINT_SCREEN],
            [Keycode.ALT, Keycode.Z], [Keycode.GUI, Keycode.G], [Keycode.ALT, Keycode.TAB],
            [Keycode.CONTROL, Keycode.ALT, Keycode.UP_ARROW], [Keycode.CONTROL, Keycode.ALT, Keycode.DOWN_ARROW], [Keycode.F12]
        ]
    },
    3: {
        "buttons": [
            [Keycode.CONTROL, Keycode.T], [Keycode.CONTROL, Keycode.W], [Keycode.CONTROL, Keycode.SHIFT, Keycode.T],
            [Keycode.ALT, Keycode.LEFT_ARROW], [Keycode.ALT, Keycode.RIGHT_ARROW], [Keycode.CONTROL, Keycode.R],
            [Keycode.CONTROL, Keycode.F], [Keycode.CONTROL, Keycode.H], [Keycode.CONTROL, Keycode.SHIFT, Keycode.O]
        ]
    }
}


# 8. BUCLE PRINCIPAL
while True:
    current_time = time.monotonic()  

    # --- LÓGICA DEL BOTÓN DE CAPA ---
    layer_btn_state = layer_button.value
    if not layer_btn_state and last_layer_btn_state:
        if (current_time - last_debounce_time) > 0.25:
            current_layer = (current_layer + 1) % 4
            update_display(current_layer)
            last_debounce_time = current_time  
    last_layer_btn_state = layer_btn_state

    # --- LÓGICA DE BOTONES CON KEYPAD ---
    event = matrix.events.get()
    if event:
        btn_num = event.key_number
        keys = layers[current_layer]["buttons"][btn_num]
        
        if event.pressed:
            if len(keys) == 1: kbd.press(keys[0])
            elif len(keys) == 2: kbd.press(keys[0], keys[1])
            elif len(keys) == 3: kbd.press(keys[0], keys[1], keys[2])
        elif event.released:
            kbd.release_all()

    # --- LÓGICA ENCODER 1 ---
    current_enc1_pos = encoder1.position
    if current_enc1_pos != last_enc1_pos:
        if current_enc1_pos > last_enc1_pos:
            if current_layer in (0, 2, 3): cc.send(ConsumerControlCode.VOLUME_INCREMENT)
            else: kbd.send(Keycode.RIGHT_ARROW)
        else:
            if current_layer in (0, 2, 3): cc.send(ConsumerControlCode.VOLUME_DECREMENT)
            else: kbd.send(Keycode.LEFT_ARROW)
        last_enc1_pos = current_enc1_pos

    enc1_sw = enc1_switch.value
    if not enc1_sw and last_enc1_sw_state:
        if current_layer in (0, 2, 3): cc.send(ConsumerControlCode.MUTE)
        else:
            kbd.press(Keycode.CONTROL, Keycode.F)
            kbd.release_all()
        time.sleep(0.2)
    last_enc1_sw_state = enc1_sw

    # --- LÓGICA ENCODER 2 ---
    current_enc2_pos = encoder2.position
    if current_enc2_pos != last_enc2_pos:
        if current_enc2_pos > last_enc2_pos:
            if current_layer in (0, 2, 3): cc.send(ConsumerControlCode.SCAN_NEXT_TRACK)
            else:
                kbd.press(Keycode.CONTROL, Keycode.KEYPAD_PLUS)
                kbd.release_all()
        else:
            if current_layer in (0, 2, 3): cc.send(ConsumerControlCode.SCAN_PREVIOUS_TRACK)
            else:
                kbd.press(Keycode.CONTROL, Keycode.KEYPAD_MINUS)
                kbd.release_all()
        last_enc2_pos = current_enc2_pos

    enc2_sw = enc2_switch.value
    if not enc2_sw and last_enc2_sw_state:
        if current_layer in (0, 2, 3): cc.send(ConsumerControlCode.PLAY_PAUSE)
        else:
            kbd.press(Keycode.CONTROL, Keycode.ZERO)
            kbd.release_all()
        time.sleep(0.2)
    last_enc2_sw_state = enc2_sw

    time.sleep(0.01)
