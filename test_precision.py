import ctypes
import os
import sys

# Simular el entorno de agente.py
user32 = ctypes.windll.user32
SCREEN_W = user32.GetSystemMetrics(0)
SCREEN_H = user32.GetSystemMetrics(1)
VISION_W = 1280 # Estandarizado para que Ashly siempre vea 1280 de ancho
SCALE_FACTOR = SCREEN_W / VISION_W

def test_scaling(x, y):
    rx = int(round(float(x) * SCALE_FACTOR))
    ry = int(round(float(y) * SCALE_FACTOR))
    return rx, ry

print(f"Resolución detectada: {SCREEN_W}x{SCREEN_H}")
print(f"Factor de escala: {SCALE_FACTOR}")

# Prueba con una coordenada típica (centro de la imagen 1280x720)
test_x, test_y = 640, 360
real_x, real_y = test_scaling(test_x, test_y)

print(f"Imagen ({test_x}, {test_y}) -> Pantalla ({real_x}, {real_y})")

# Verificar si el centro coincide
expected_x = SCREEN_W // 2
expected_y = int(360 * SCALE_FACTOR) # La altura es proporcional

print(f"Esperado (aprox): {expected_x}, {expected_y}")

if abs(real_x - expected_x) <= 2:
    print("✅ Precisión X confirmada.")
else:
    print("❌ Error en precisión X.")

import pyautogui
print(f"Posición actual del mouse: {pyautogui.position()}")
