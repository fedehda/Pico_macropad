import time
import board
import digitalio
import rotaryio
import usb_hid
import busio
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

# 3. Configurar Pantalla OLED SSD1306 (128x32)
# GP6 para SDA y GP7 para SCL
i2c = busio.I2C(board.GP7, board.GP6)
display = adafruit_ssd1306.SSD1306_I2C(128, 32, i2c)

# Mapeo de nombres de capas
layer_names = {0: "STREAM", 1: "WORK"}


# --- FUNCIÓN DE ACTUALIZACIÓN DE PANTALLA BLINDADA ---

def update_display(layer_input):
    try:
        display.fill(0)  # Limpiar pantalla

        # Título superior siempre fijo
        display.text("- MACROPAD v1.0 -", 10, 2, 1)

        # Convertimos lo que sea que reciba a texto en mayúsculas para comparar sin fallar
        layer_str = str(layer_input).upper()

        # Si recibe el número 0, o la palabra STREAM u OBS:
        if "0" in layer_str or "STREAM" in layer_str or "OBS" in layer_str:
            # --- ÍCONO DE CÁMARA SÓLIDA ---
            display.fill_rect(4, 16, 10, 8, 1)  # Cuerpo de la cámara
            display.fill_rect(14, 18, 3, 4, 1)  # Lente frontal
            display.text("    STREAM", 26, 18, 1)

        # Si recibe el número 1, o WORK o PRODUCTIVIDAD:
        elif "1" in layer_str or "WORK" in layer_str or "PROD" in layer_str:
            # --- ÍCONO DE TUERCA SÓLIDA ---
            display.fill_rect(7, 19, 8, 8, 1)   # Cuerpo central de la tuerca
            display.fill_rect(10, 16, 2, 3, 1)  # Diente superior
            display.fill_rect(10, 27, 2, 3, 1)  # Diente inferior
            display.fill_rect(4, 22, 3, 2, 1)   # Diente izquierdo
            display.fill_rect(15, 22, 3, 2, 1)  # Diente derecho
            display.fill_rect(10, 22, 2, 2, 0)  # Agujero del centro (negro)
            display.text("     WORK", 26, 18, 1)

        display.show()  # Refrescar la pantalla
    except Exception as e:
        print("Error en pantalla:", e)


# 4. Configurar el Botón de Capa (Layer Switch) - Pin GP15
layer_button = digitalio.DigitalInOut(board.GP15)
layer_button.direction = digitalio.Direction.INPUT
layer_button.pull = digitalio.Pull.UP
current_layer = 0
# FIX #1: last_layer_btn_state inicializado antes del bucle para evitar NameError
last_layer_btn_state = True

# Mostrar la capa inicial al encender
update_display(current_layer)

# 5. Configurar la Matriz 3x3
button_pins = [
    board.GP0,  board.GP1,  board.GP2,   # Fila 1
    board.GP3,  board.GP18, board.GP19,  # Fila 2
    board.GP20, board.GP21, board.GP8    # Fila 3
]

buttons = []
for pin in button_pins:
    btn = digitalio.DigitalInOut(pin)
    btn.direction = digitalio.Direction.INPUT
    btn.pull = digitalio.Pull.UP
    buttons.append(btn)

last_button_states = [True] * 9

# 6. Configurar los 2 Encoders Rotativos
encoder1 = rotaryio.IncrementalEncoder(board.GP11, board.GP12)
encoder2 = rotaryio.IncrementalEncoder(board.GP13, board.GP14)
last_enc1_pos = encoder1.position
last_enc2_pos = encoder2.position

# Click Encoder 1 - Pin GP22
enc1_switch = digitalio.DigitalInOut(board.GP22)
enc1_switch.direction = digitalio.Direction.INPUT
enc1_switch.pull = digitalio.Pull.UP
last_enc1_sw_state = True

# Click Encoder 2 - Pin GP16
enc2_switch = digitalio.DigitalInOut(board.GP16)
enc2_switch.direction = digitalio.Direction.INPUT
enc2_switch.pull = digitalio.Pull.UP
last_enc2_sw_state = True

# 7. DEFINICIÓN DE ATAJOS POR CAPA
layers = {
    0: {  # CAPA 0: Streaming / OBS
        "buttons": [
            [Keycode.F13], [Keycode.F14], [Keycode.F15],
            [Keycode.F16], [Keycode.F17], [Keycode.F18],
            [Keycode.F19], [Keycode.F20], [Keycode.F21]
        ]
    },
    1: {  # CAPA 1: Productividad
        "buttons": [
            [Keycode.CONTROL, Keycode.Z],           # Deshacer
            [Keycode.CONTROL, Keycode.Y],           # Rehacer
            [Keycode.CONTROL, Keycode.SHIFT, Keycode.S],  # Guardar como
            [Keycode.CONTROL, Keycode.C],           # Copiar
            [Keycode.CONTROL, Keycode.V],           # Pegar
            [Keycode.CONTROL, Keycode.X],           # Cortar
            [Keycode.GUI, Keycode.SHIFT, Keycode.S],      # Captura región (Win)
            [Keycode.CONTROL, Keycode.GRAVE_ACCENT],      # Terminal (VS Code)
            [Keycode.ALT, Keycode.F4]               # Cerrar ventana
        ]
    }
}


# 8. BUCLE PRINCIPAL
while True:

    # --- LÓGICA DEL BOTÓN DE CAPA ---
    layer_btn_state = layer_button.value
    if not layer_btn_state and last_layer_btn_state:
        current_layer = 1 if current_layer == 0 else 0
        update_display(current_layer)
        time.sleep(0.2)  # Debounce
    last_layer_btn_state = layer_btn_state

    # --- LÓGICA DE LOS 9 BOTONES ---
    for i in range(9):
        btn_state = buttons[i].value
        if not btn_state and last_button_states[i]:
            keys = layers[current_layer]["buttons"][i]
            if len(keys) == 1:
                kbd.press(keys[0])
            elif len(keys) == 2:
                kbd.press(keys[0], keys[1])
            elif len(keys) == 3:
                kbd.press(keys[0], keys[1], keys[2])
        elif btn_state and not last_button_states[i]:
            kbd.release_all()
        last_button_states[i] = btn_state

    # --- LÓGICA ENCODER 1 ---
    current_enc1_pos = encoder1.position
    if current_enc1_pos != last_enc1_pos:
        if current_enc1_pos > last_enc1_pos:
            if current_layer == 0:
                cc.send(ConsumerControlCode.VOLUME_INCREMENT)
            else:
                # FIX #2a: kbd.send() con 1 tecla es correcto, no se modifica
                kbd.send(Keycode.RIGHT_ARROW)
        else:
            if current_layer == 0:
                cc.send(ConsumerControlCode.VOLUME_DECREMENT)
            else:
                kbd.send(Keycode.LEFT_ARROW)
        last_enc1_pos = current_enc1_pos

    enc1_sw = enc1_switch.value
    if not enc1_sw and last_enc1_sw_state:
        if current_layer == 0:
            cc.send(ConsumerControlCode.MUTE)
        else:
            # FIX #2b: kbd.send() no soporta múltiples keycodes → usar press/release
            kbd.press(Keycode.CONTROL, Keycode.F)
            kbd.release_all()
        time.sleep(0.2)  # Debounce
    last_enc1_sw_state = enc1_sw

    # --- LÓGICA ENCODER 2 ---
    current_enc2_pos = encoder2.position
    if current_enc2_pos != last_enc2_pos:
        if current_enc2_pos > last_enc2_pos:
            if current_layer == 0:
                cc.send(ConsumerControlCode.SCAN_NEXT_TRACK)
            else:
                # FIX #2c: kbd.send() no soporta múltiples keycodes → usar press/release
                kbd.press(Keycode.CONTROL, Keycode.KEYPAD_PLUS)
                kbd.release_all()
        else:
            if current_layer == 0:
                cc.send(ConsumerControlCode.SCAN_PREVIOUS_TRACK)
            else:
                # FIX #2d: ídem
                kbd.press(Keycode.CONTROL, Keycode.KEYPAD_MINUS)
                kbd.release_all()
        last_enc2_pos = current_enc2_pos

    enc2_sw = enc2_switch.value
    if not enc2_sw and last_enc2_sw_state:
        if current_layer == 0:
            cc.send(ConsumerControlCode.PLAY_PAUSE)
        else:
            # FIX #2e: ídem
            kbd.press(Keycode.CONTROL, Keycode.ZERO)
            kbd.release_all()
        time.sleep(0.2)  # FIX #3: debounce dentro del bloque if, indentación correcta
    last_enc2_sw_state = enc2_sw

    time.sleep(0.01)