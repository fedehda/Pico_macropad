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
i2c = busio.I2C(board.GP7, board.GP6)
display = adafruit_ssd1306.SSD1306_I2C(128, 32, i2c)


# --- FUNCIÓN DE ACTUALIZACIÓN DE PANTALLA CON 4 ICONOS ---

def update_display(layer_input):
    try:
        display.fill(0)  # Limpiar pantalla

        # Título superior fijo estándar
        display.text("- MACROPAD v1.0 -", 10, 2, 1)

        layer_str = str(layer_input).upper()

        # --- CAPA 0: STREAM ---
        if "0" in layer_str or "STREAM" in layer_str:
            display.fill_rect(4, 16, 10, 8, 1)  # Ícono cámara
            display.fill_rect(14, 18, 3, 4, 1)  
            display.text("STREAM", 24, 18, 1)  # Texto normal
            
            # --- NÚMERO "0" GIGANTE (Hecho con rectángulos a la derecha) ---
            display.fill_rect(108, 14, 12, 16, 1) # Bloque blanco
            display.fill_rect(112, 18, 4, 8, 0)   # Centro negro para hacer el hueco

        # --- CAPA 1: WORK (MONITOR VUELVE ACÁ) ---
        elif "1" in layer_str or "WORK" in layer_str:
            # --- ÍCONO DE MONITOR SÓLIDO (X base = 4, Y base = 16) ---
            display.fill_rect(4, 16, 14, 8, 1)  # Pantalla del monitor
            display.fill_rect(9, 24, 4, 2, 1)   # Cuello del soporte
            display.fill_rect(6, 26, 10, 2, 1)  # Base de apoyo
            display.text("WORK", 24, 18, 1)    # Texto normal
            
            # --- NÚMERO "1" GIGANTE ---
            display.fill_rect(112, 14, 4, 16, 1)  # Barra vertical alta
        # --- CAPA 2: GAMING ---
        elif "2" in layer_str or "GAME" in layer_str:
            display.fill_rect(4, 18, 14, 7, 1)  # Ícono joystick
            display.fill_rect(4, 25, 4, 3, 1)   
            display.fill_rect(14, 25, 4, 3, 1)  
            display.fill_rect(6, 20, 2, 2, 0)   
            display.fill_rect(12, 20, 2, 2, 0)  
            display.text("GAMING", 24, 18, 1)
            
            # --- NÚMERO "2" GIGANTE ---
            display.fill_rect(108, 14, 12, 4, 1)  # Techo
            display.fill_rect(116, 18, 4, 4, 1)   # Barra derecha alta
            display.fill_rect(108, 22, 12, 4, 1)  # Centro
            display.fill_rect(108, 26, 4, 4, 1)   # Barra izquierda baja
            display.fill_rect(108, 28, 12, 4, 1)  # Piso

        # --- CAPA 3: MEDIA ---
        elif "3" in layer_str or "MEDIA" in layer_str:
            display.fill_rect(5, 17, 3, 11, 1)  # Ícono nota musical
            display.fill_rect(12, 17, 3, 9, 1)  
            display.fill_rect(5, 17, 10, 3, 1)  
            display.fill_rect(2, 25, 5, 4, 1)   
            display.fill_rect(9, 23, 5, 4, 1)   
            display.text("MEDIA", 24, 18, 1)
            
            # --- NÚMERO "3" GIGANTE ---
            display.fill_rect(108, 14, 12, 16, 1) # Bloque completo
            display.fill_rect(108, 18, 8, 3, 0)   # Hueco negro superior izquierdo
            display.fill_rect(108, 25, 8, 3, 0)   # Hueco negro inferior izquierdo

        display.show()
    except Exception as e:
        print("Error en pantalla:", e)


# 4. Configurar el Botón de Capa (Layer Switch) - Pin GP15
layer_button = digitalio.DigitalInOut(board.GP15)
layer_button.direction = digitalio.Direction.INPUT
layer_button.pull = digitalio.Pull.UP
current_layer = 0
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

# 7. DEFINICIÓN DE ATAJOS POR CAPA (4 CAPAS TOTALES)
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
            [Keycode.CONTROL, Keycode.Z], [Keycode.CONTROL, Keycode.Y], [Keycode.CONTROL, Keycode.SHIFT, Keycode.S],
            [Keycode.CONTROL, Keycode.C], [Keycode.CONTROL, Keycode.V], [Keycode.CONTROL, Keycode.X],
            [Keycode.GUI, Keycode.SHIFT, Keycode.S], [Keycode.CONTROL, Keycode.GRAVE_ACCENT], [Keycode.ALT, Keycode.F4]
        ]
    },
    2: {  # CAPA 2: Gaming / Discord (Atajos por defecto de Discord)
        "buttons": [
            [Keycode.CONTROL, Keycode.SHIFT, Keycode.M],  # Mutear Micrófono Discord
            [Keycode.CONTROL, Keycode.SHIFT, Keycode.D],  # Ensordecer Audio Discord
            [Keycode.GUI, Keycode.PRINT_SCREEN],          # Captura de pantalla rápida
            [Keycode.ALT, Keycode.Z],                     # Abrir Overlay (GeForce / etc)
            [Keycode.GUI, Keycode.G],                     # Game Bar de Windows
            [Keycode.ALT, Keycode.TAB],                   # Cambiar rápido de ventana
            [Keycode.CONTROL, Keycode.ALT, Keycode.UP_ARROW],   # CORREGIDO: Moverse de canal Discord
            [Keycode.CONTROL, Keycode.ALT, Keycode.DOWN_ARROW], # CORREGIDO: Moverse de canal Discord
            [Keycode.F12]                                 # Captura general / Steam
        ]
    },
    3: {  # CAPA 3: Media / Navegación web
        "buttons": [
            [Keycode.CONTROL, Keycode.T],                 # Nueva pestaña navegador
            [Keycode.CONTROL, Keycode.W],                 # Cerrar pestaña actual
            [Keycode.CONTROL, Keycode.SHIFT, Keycode.T],  # Reabrir pestaña cerrada
            [Keycode.ALT, Keycode.LEFT_ARROW],            # Página anterior en historial
            [Keycode.ALT, Keycode.RIGHT_ARROW],           # Página siguiente en historial
            [Keycode.CONTROL, Keycode.R],                 # Recargar página (F5)
            [Keycode.CONTROL, Keycode.F],                 # Buscar texto en la página
            [Keycode.CONTROL, Keycode.H],                 # Abrir Historial
            [Keycode.CONTROL, Keycode.SHIFT, Keycode.O]   # Abrir Marcadores / Favoritos
        ]
    }
}


# 8. BUCLE PRINCIPAL
while True:

    # --- LÓGICA DEL BOTÓN DE CAPA (Cicla entre las 4 capas: 0, 1, 2, 3) ---
    layer_btn_state = layer_button.value
    if not layer_btn_state and last_layer_btn_state:
        current_layer = (current_layer + 1) % 4  # Cicla dinámicamente de 0 a 3
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
            # Capas multimedia / gaming usan volumen
            if current_layer == 0 or current_layer == 2 or current_layer == 3:
                cc.send(ConsumerControlCode.VOLUME_INCREMENT)
            else:  # Capa de laburo usa flechas
                kbd.send(Keycode.RIGHT_ARROW)
        else:
            if current_layer == 0 or current_layer == 2 or current_layer == 3:
                cc.send(ConsumerControlCode.VOLUME_DECREMENT)
            else:
                kbd.send(Keycode.LEFT_ARROW)
        last_enc1_pos = current_enc1_pos

    enc1_sw = enc1_switch.value
    if not enc1_sw and last_enc1_sw_state:
        if current_layer == 0 or current_layer == 2 or current_layer == 3:
            cc.send(ConsumerControlCode.MUTE)
        else:
            kbd.press(Keycode.CONTROL, Keycode.F)
            kbd.release_all()
        time.sleep(0.2)  # Debounce
    last_enc1_sw_state = enc1_sw

    # --- LÓGICA ENCODER 2 ---
    current_enc2_pos = encoder2.position
    if current_enc2_pos != last_enc2_pos:
        if current_enc2_pos > last_enc2_pos:
            if current_layer == 0 or current_layer == 2 or current_layer == 3:
                cc.send(ConsumerControlCode.SCAN_NEXT_TRACK)
            else:
                kbd.press(Keycode.CONTROL, Keycode.KEYPAD_PLUS)
                kbd.release_all()
        else:
            if current_layer == 0 or current_layer == 2 or current_layer == 3:
                cc.send(ConsumerControlCode.SCAN_PREVIOUS_TRACK)
            else:
                kbd.press(Keycode.CONTROL, Keycode.KEYPAD_MINUS)
                kbd.release_all()
        last_enc2_pos = current_enc2_pos

    enc2_sw = enc2_switch.value
    if not enc2_sw and last_enc2_sw_state:
        if current_layer == 0 or current_layer == 2 or current_layer == 3:
            cc.send(ConsumerControlCode.PLAY_PAUSE)
        else:
            kbd.press(Keycode.CONTROL, Keycode.ZERO)
            kbd.release_all()
        time.sleep(0.2)  # Debounce
    last_enc2_sw_state = enc2_sw

    time.sleep(0.01) 
